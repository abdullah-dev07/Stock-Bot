import asyncio

from . import gemini_service, stock_service
from ..db import chat_repository
from ..constants import (
    MSG_INTERNAL_ERROR,
    MSG_NO_PRICE_DATA,
    MSG_NO_PREDICTION_DATA,
    MSG_NEED_STOCK_NAME,
    MSG_CLARIFICATION,
    MSG_UNKNOWN_REQUEST,
)


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
                "message": MSG_CLARIFICATION.format(entity=entity),
                "choices": matches,
                "original_intent": intent,
            }
    return None


def _proceed_with_intent(intent, ticker, entity):
    """Handle non-streaming intents that return a generator."""
    if intent == "get_specific_data":
        quote_data = stock_service.get_stock_quote(ticker)
        if not quote_data:
            return iter([MSG_NO_PRICE_DATA.format(ticker=ticker)])
        return gemini_service.generate_response_from_quote(entity, quote_data)
    return iter([MSG_UNKNOWN_REQUEST])


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
                    generator = iter([MSG_NO_PREDICTION_DATA.format(ticker=ticker)])
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
                    generator = iter([MSG_NEED_STOCK_NAME])
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
                            generator = iter([MSG_NO_PREDICTION_DATA.format(ticker=ticker)])
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
        yield MSG_INTERNAL_ERROR
        await asyncio.to_thread(
            chat_repository.add_message_to_chat, user_id, chat_id, "model", MSG_INTERNAL_ERROR
        )
