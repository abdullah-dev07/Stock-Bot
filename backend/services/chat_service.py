import asyncio

from . import gemini_service, stock_service
from ..db import chat_repository


def is_likely_ticker(s):
    if not isinstance(s, str):
        return False
    return s.isupper() and ' ' not in s and 1 <= len(s) <= 5


async def check_clarification_needed(user_message, history, context):
    """Returns a clarification dict if disambiguation is needed, else None."""
    if context.get('awaiting_clarification'):
        return None

    intent_data = await asyncio.to_thread(gemini_service.get_intent, user_message, history)
    intent = intent_data.get("intent", "general_knowledge")
    entity = intent_data.get("entity")

    if intent in ['get_specific_data', 'get_prediction_or_advice'] and entity:
        matches = await asyncio.to_thread(stock_service.search_ticker_symbols, entity)
        if matches and len(matches) > 1 and not is_likely_ticker(entity):
            return {
                "response_type": "clarification",
                "message": f"I found a few potential matches for '{entity}'.",
                "choices": matches,
                "original_intent": intent,
            }
    return None


def _proceed_with_intent(intent, ticker, entity):
    """Handle non-streaming intents that return a generator."""
    if intent == "get_specific_data":
        quote_data = stock_service.get_stock_quote(ticker)
        if not quote_data:
            return iter([f"Sorry, I couldn't retrieve valid price data for {ticker}."])
        return gemini_service.generate_response_from_quote(entity, quote_data)
    return iter(["I'm not sure how to proceed with that request."])


async def build_chat_response(user_message, context, history, user_id, chat_id):
    """Async generator — yields response chunks and persists the full reply."""
    full_response = ""
    generator = None

    try:
        if context.get('awaiting_clarification'):
            intent = context.get('original_intent')
            ticker = user_message
            if intent == 'get_prediction_or_advice':
                prediction_data = await asyncio.to_thread(stock_service.get_prediction_data, ticker)
                if not prediction_data:
                    generator = iter([f"Sorry, I couldn't gather enough data for {ticker}."])
                else:
                    generator = gemini_service.generate_prediction_response(prediction_data, user_message)
            else:
                generator = _proceed_with_intent(intent, ticker, ticker)
        else:
            intent_data = await asyncio.to_thread(gemini_service.get_intent, user_message, history)
            intent = intent_data.get("intent", "general_knowledge")
            entity = intent_data.get("entity")

            if intent in ['get_specific_data', 'get_prediction_or_advice']:
                if not entity:
                    generator = iter(["I need to know which stock you're interested in."])
                else:
                    if is_likely_ticker(entity):
                        ticker = entity
                    else:
                        matches = await asyncio.to_thread(stock_service.search_ticker_symbols, entity)
                        ticker = matches[0]['symbol']

                    if intent == 'get_specific_data':
                        generator = _proceed_with_intent(intent, ticker, entity)
                    elif intent == 'get_prediction_or_advice':
                        prediction_data = await asyncio.to_thread(stock_service.get_prediction_data, ticker)
                        if not prediction_data:
                            generator = iter([f"Sorry, I couldn't gather enough data for {ticker}."])
                        else:
                            generator = gemini_service.generate_prediction_response(prediction_data, user_message)
            else:
                generator = gemini_service.generate_grounded_response(user_message, history)

        for chunk in generator:
            full_response += chunk
            yield chunk

        await asyncio.to_thread(
            chat_repository.add_message_to_chat, user_id, chat_id, "model", full_response
        )

    except Exception as e:
        print(f"[CHAT] Error during processing: {type(e).__name__} - {e}")
        error_msg = "Sorry, an internal error occurred."
        yield error_msg
        await asyncio.to_thread(
            chat_repository.add_message_to_chat, user_id, chat_id, "model", error_msg
        )
