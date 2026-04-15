import os
import json
import google.generativeai as genai

from ..config import GEMINI_API_KEY


def _ensure_configured():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    genai.configure(api_key=GEMINI_API_KEY)


def generate_chat_title(message_text):
    """Generates a concise title from a user's first message."""
    try:
        _ensure_configured()
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f'Generate a concise title, not more than 5 words, for the following message:\n\n'
            f'Message: "{message_text}"\n\n'
            f'The title should be short, descriptive, and capture the essence of the message.\n\nTitle:'
        )
        response = model.generate_content(prompt)
        title = response.text.strip().replace("*", "").replace('"', "")
        return title if title else "Untitled"
    except Exception as e:
        print(f"[GEMINI] Error generating chat title: {e}")
        return message_text[:35] + "..." if len(message_text) > 35 else message_text


def summarize_conversation(history):
    """Summarizes the older part of a conversation for context compression."""
    _ensure_configured()
    model = genai.GenerativeModel('gemini-2.5-flash')
    history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in history])
    prompt = (
        f"Concisely summarize the key points of the following conversation "
        f"into a single paragraph. This summary will be used as context for an ongoing chat.\n\n"
        f"Conversation:\n{history_text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[GEMINI] Error during summarization: {e}")
        return ""


def get_intent(user_prompt, history=None):
    """Classifies user intent and extracts the stock entity."""
    if history is None:
        history = []
    _ensure_configured()
    model = genai.GenerativeModel('gemini-2.5-flash')

    context_summary = ""
    if len(history) > 4:
        older_history = history[:-4]
        recent_history = history[-4:]
        context_summary = f"CONVERSATION SUMMARY:\n{summarize_conversation(older_history)}\n\n"
    else:
        recent_history = history

    history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in recent_history])

    prompt = f"""
        You are an intent classifier for a stock-focused assistant. Your goal is to categorize the user's LATEST query into one of the following intents.
        
        INTENT TYPES:
        - 'get_specific_data': The user is asking for CURRENT, real-time stock data (price, open, close, volume, etc.) for a single company.
        - 'get_qualitative_analysis': The user is asking for an explanation of PAST events, reasoning, or trends.
        - 'get_prediction_or_advice': The user is asking for a FUTURE prediction, forecast, opinion, or advice about a stock.
        - 'general_knowledge': The user is asking about general financial concepts (e.g., "What is a dividend?")

        Return only a JSON object with:
        - "intent": one of the four intent values above
        - "entity": company name or stock ticker mentioned, or null

        {context_summary}

        RECENT CONVERSATION:
        {history_text}

        LAST User Query: "{user_prompt}"

        JSON Output:
        """

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[GEMINI] Error decoding intent JSON: {e}")
        return {"intent": "general_knowledge", "entity": user_prompt}


def generate_prediction_response(prediction_data, user_prompt):
    """Streamed stock prediction analysis from fundamentals/technicals."""
    _ensure_configured()
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
        You are an expert financial analyst. Your task is to provide a stock price prediction based ONLY on the recently fetched technical and fundamental data.

        **User's Original Question:** "{user_prompt}"

        **Analyze the following data for {prediction_data.get('company_name', 'this company')}:**
        - P/E Ratio: {prediction_data.get('pe_ratio', 'N/A')}
        - Earnings Per Share (EPS): {prediction_data.get('eps', 'N/A')}
        - 12-Month Analyst Target Price: {prediction_data.get('analyst_target_price', 'N/A')}
        - Current Stock Price: {prediction_data.get('current_price', 'N/A')}
        - Relative Strength Index (RSI): {prediction_data.get('rsi', 'N/A')}
        - 50-Day Simple Moving Average (SMA): {prediction_data.get('sma_50', 'N/A')}
        - 200-Day Simple Moving Average (SMA): {prediction_data.get('sma_200', 'N/A')}

        Provide your analysis in markdown format. Conclude with: "This is a prediction based on available data and not financial advice. Stock markets are volatile, and past performance is not indicative of future results. Always do your own research."
        """
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[GEMINI] Error in prediction response: {e}")
        yield "Sorry, an error occurred while generating the prediction."


def generate_grounded_response(prompt, history=None):
    """General chat response with history context, streamed."""
    if history is None:
        history = []
    _ensure_configured()
    model = genai.GenerativeModel('gemini-2.5-flash')

    context_summary = ""
    if len(history) > 4:
        older_history = history[:-4]
        recent_history = history[-4:]
        context_summary = summarize_conversation(older_history)
    else:
        recent_history = history

    history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in recent_history])

    summary_section = ""
    if context_summary:
        summary_section = "SUMMARY OF EARLIER CONVERSATION: " + context_summary + "\n\n"

    full_prompt = f"""
    {summary_section}RECENT CONVERSATION:
    {history_text}

    {prompt}

    IMPORTANT: If this query asks for any form of financial suggestion or advice, conclude your response with: 'This is not financial advice. Please do your own research or consult with a professional financial advisor.'
    """

    try:
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text + "\n"
    except Exception as e:
        print(f"[GEMINI] Error in grounded response: {e}")
        yield "Sorry, an error occurred while generating the response."


def generate_response_from_quote(company, quote_data):
    """Human-readable streamed response from stock quote data."""
    _ensure_configured()
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    A user asked for the stock price of {company}.
    Using the latest market data below, formulate a friendly and clear response starting with, "Based on the latest data,".
    Data: {json.dumps(quote_data)}
    """
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[GEMINI] Error in quote response: {e}")
        yield f"Based on the latest data for {company}, I couldn't retrieve the information."
