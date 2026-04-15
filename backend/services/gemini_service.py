import json

from ..utils.gemini import get_model, format_history
from ..prompts import gemini as prompts
from ..constants import MSG_GENERATION_ERROR, MSG_PREDICTION_ERROR, MSG_QUOTE_FALLBACK


def generate_chat_title(message_text):
    """Generates a concise title from a user's first message."""
    try:
        model = get_model()
        response = model.generate_content(prompts.chat_title(message_text))
        title = response.text.strip().replace("*", "").replace('"', "")
        return title if title else "Untitled"
    except Exception as e:
        print(f"[GEMINI] Error generating chat title: {e}")
        return message_text[:35] + "..." if len(message_text) > 35 else message_text


def summarize_conversation(history):
    """Summarizes the older part of a conversation for context compression."""
    model = get_model()
    history_text = "\n".join(f"{msg['role']}: {msg['text']}" for msg in history)
    try:
        response = model.generate_content(prompts.conversation_summary(history_text))
        return response.text
    except Exception as e:
        print(f"[GEMINI] Error during summarization: {e}")
        return ""


def get_intent(user_prompt, history=None):
    """Classifies user intent and extracts the stock entity."""
    if history is None:
        history = []
    model = get_model()

    older, history_text = format_history(history)
    context_summary = ""
    if older:
        context_summary = f"CONVERSATION SUMMARY:\n{summarize_conversation(older)}\n\n"

    prompt = prompts.intent_classification(context_summary, history_text, user_prompt)

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[GEMINI] Error decoding intent JSON: {e}")
        return {"intent": "general_knowledge", "entity": user_prompt}


def generate_prediction_response(prediction_data, user_prompt):
    """Streamed stock prediction analysis from fundamentals/technicals."""
    model = get_model()
    prompt = prompts.prediction_analysis(prediction_data, user_prompt)
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[GEMINI] Error in prediction response: {e}")
        yield MSG_PREDICTION_ERROR


def generate_grounded_response(prompt, history=None):
    """General chat response with history context, streamed."""
    if history is None:
        history = []
    model = get_model()

    older, history_text = format_history(history)
    context_summary = summarize_conversation(older) if older else ""

    summary_section = ""
    if context_summary:
        summary_section = "SUMMARY OF EARLIER CONVERSATION: " + context_summary + "\n\n"

    full_prompt = prompts.grounded_response(summary_section, history_text, prompt)

    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text + "\n"
    except Exception as e:
        print(f"[GEMINI] Error in grounded response: {e}")
        yield MSG_GENERATION_ERROR


def generate_response_from_quote(company, quote_data):
    """Human-readable streamed response from stock quote data."""
    model = get_model()
    prompt = prompts.quote_response(company, json.dumps(quote_data))
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[GEMINI] Error in quote response: {e}")
        yield MSG_QUOTE_FALLBACK.format(company=company)
