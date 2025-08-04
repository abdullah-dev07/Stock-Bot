# FILE: backend/gemini_client.py
# PURPOSE: Handles all communication with the Google Gemini API using the new hybrid model.

import os
import json
from google import genai
from google.genai import types

# --- Configuration ---
# Make sure to set your GEMINI_API_KEY environment variable

# --- NEW: Helper function for conversation summarization ---
def summarize_conversation(history):
    """Uses a fast model to summarize the older part of a conversation."""
    print("[GEMINI] Summarizing older conversation history...")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = 'gemini-1.5-flash'
    
    # Convert history to a simple string format for the prompt
    history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in history])
    
    prompt = f"""
    Concisely summarize the key points of the following conversation into a single paragraph. 
    This summary will be used as context for an ongoing chat.

    Conversation:
    {history_text}
    """
    
    try:
        response = client.models.generate_content(contents=prompt, model=model)
        return response.text
    except Exception as e:
        print(f"[GEMINI] Error during summarization: {e}")
        return "" # Return empty string on failure

def get_intent(user_prompt, history=[]):
    """
    Uses Gemini to determine the user's intent and extract the main entity.
    This now includes more nuanced intents for the hybrid model.
    """
    print(f"\n[GEMINI] Calling get_intent for prompt: '{user_prompt}'")
    model = 'gemini-2.5-flash' # Using a fast model for classification
    
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # --- NEW: Sliding Window Logic ---
    context_summary = ""
    if len(history) > 4:
        older_history = history[:-4]
        recent_history = history[-4:]
        context_summary = f"CONVERSATION SUMMARY:\n{summarize_conversation(older_history)}\n\n"
    else:
        recent_history = history

    history_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in recent_history])

    # Updated prompt with new intents and history
    prompt = f"""
        You are an intent classifier for a stock-focused assistant. Your goal is to categorize the user's LATEST query into one of the following intents.
        
        INTENT TYPES:
        - 'get_specific_data': The user is asking for CURRENT, real-time stock data (price, open, close, volume, etc.) for a single company.
        - 'get_qualitative_analysis': The user is asking for an explanation of PAST events, reasoning, or trends.
        - 'get_prediction_or_advice': The user is asking for a FUTURE prediction, forecast, opinion, or advice about a stock. This includes any questions about whether a stock will go up or down, what its future price might be, or if they should buy or sell it.
        - 'general_knowledge': The user is asking about general financial concepts (e.g., "What is a dividend?")

        RULES:
        1. If the query contains words like "predict", "forecast", "will it go up", "should I buy", "future of", "is it a good investment," or asks for an opinion on future performance, the intent is 'get_prediction_or_advice'.
        2. If the query is a simple request for the current price or quote, the intent is 'get_specific_data'.
        3. Analyze ONLY the last user query in the context of the conversation.
        
        Return only a JSON object with:
        - "intent": one of the four intent values above
        - "entity": company name or stock ticker mentioned, or null

        {context_summary}

        RECENT CONVERSATION:
        {history_text}

        user: {user_prompt}
        ---

        Analyze the last user query based on the conversation context. Identify the intent and primary entity.

        LAST User Query: "{user_prompt}"

        JSON Output:
        """

    response = client.models.generate_content(contents=prompt, model=model)
    
    try:
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[GEMINI] Error decoding intent JSON from Gemini: {e}")
        return {"intent": "general_knowledge", "entity": user_prompt}


def generate_prediction_response(prediction_data):
    """
    Generates a stock prediction analysis based on provided data.
    """
    print(f"\n[GEMINI] Calling generate_prediction_response for: '{prediction_data.get('company_name')}'")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = 'gemini-2.5-flash'

    prompt = f"""
        You are an expert financial analyst. Your task is to provide a stock price prediction based ONLY on the recently fetched technical and fundamental data. Your response must be tailored to the user's specific question.

        **User's Original Question:** "{user_prompt}"

        **Analyze the following data for {prediction_data.get('company_name', 'this company')}:**

        **Fundamental Data:**
        - P/E Ratio: {prediction_data.get('pe_ratio', 'N/A')}
        - Earnings Per Share (EPS): {prediction_data.get('eps', 'N/A')}
        - 12-Month Analyst Target Price: {prediction_data.get('analyst_target_price', 'N/A')}

        **Technical Indicators:**
        - Current Stock Price: {prediction_data.get('current_price', 'N/A')}
        - Relative Strength Index (RSI): {prediction_data.get('rsi', 'N/A')}
        - 50-Day Simple Moving Average (SMA): {prediction_data.get('sma_50', 'N/A')}
        - 200-Day Simple Moving Average (SMA): {prediction_data.get('sma_200', 'N/A')}

        **Based on this data, provide the following in your analysis, in markdown format:**
        1.  **Analysis Summary:** In a conversational sentence, state your outlook for the stock's trend and provide a potential short-term price range. For example: "Based on the bullish indicators, the stock could test the [higher price] range, while support may be found around [lower price]."
        2.  **Confidence:** Provide a confidence level for your prediction (Low, Medium, or High).
        3.  **Justification:** In a few bullet points, explain your reasoning by referencing the specific data points provided.
        4.  **Regarding Your Question:** Directly address the user's original question. If they asked about profit or loss in a specific timeframe, use your analysis of the trend to answer. For example: "Regarding your question about profit in 2 days, if the current bullish trend continues, there is potential for the stock to move towards the higher end of the predicted range. However, this is highly speculative and markets can change unexpectedly." Frame the answer responsibly.
        5.  **Important Note:** You must include a realistic disclaimer about the nature of the price range and short-term predictions. State clearly that this range is a speculative estimate based on current technical levels and is not a guarantee.
        6.  **Disclaimer:** Conclude your response VERBATIM with: "This is a prediction based on available data and not financial advice. Stock markets are volatile, and past performance is not indicative of future results. Always do your own research."
        """

    response = client.models.generate_content_stream(
        model = model,
        contents = prompt
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text


def generate_grounded_response(prompt, history=[]):
    """
    Generates a response for complex, qualitative, or advice-seeking questions
    by using the powerful Gemini 2.5 Pro model with Google Search grounding.
    """
    print(f"\n[GEMINI] Calling generate_grounded_response for prompt: '{prompt}'")
    
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # --- NEW: Sliding Window Logic ---
    context_summary = ""
    if len(history) > 4:
        older_history = history[:-4]
        recent_history = history[-4:]
        context_summary = summarize_conversation(older_history)
    else:
        recent_history = history
    

    # Construct the full conversation history for the model
    model_contents = []
    if context_summary:
        # Add the summary as the first piece of context
        model_contents.append(types.Content(role='user', parts=[types.Part.from_text(text=f"SUMMARY OF EARLIER CONVERSATION: {context_summary}")]))
        model_contents.append(types.Content(role='model', parts=[types.Part.from_text(text="Okay, I have the summary. Let's continue.")]))

    for msg in recent_history:
        role = 'user' if msg['role'] == 'user' else 'model'
        model_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['text'])]))

    for msg in recent_history:
        role = 'user' if msg['role'] == 'user' else 'model'
        model_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['text'])]))    
    
    # Add the current user prompt
    prompt_with_disclaimer = f"""
    {prompt}

    IMPORTANT: If this query asks for any form of financial suggestion or advice, you must conclude your response VERBATIM with the following disclaimer: 'This is not financial advice. Please do your own research or consult with a professional financial advisor.'
    """
    model_contents.append(types.Content(role='user', parts=[types.Part.from_text(text=prompt_with_disclaimer)]))
    
    config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature = 0.7
        )


    # Make the request using the client
    try:
        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=model_contents,
            config=config 
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text + "\n"
    except Exception as e:
        # Log the actual error to your server console for debugging
        print(f"An error occurred in the Gemini stream: {type(e).__name__} - {e}")
        
        # Yield a user-friendly error message to the frontend
        yield "Sorry, an error occurred while generating the response. The request may have been blocked due to safety settings."

def generate_response_from_quote(company, quote_data):
    """Generates a human-readable response from structured stock quote data."""
    print(f"\n[GEMINI] Calling generate_response_from_quote for company: '{company}'")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = 'gemini-2.5-flash'
    
    prompt = f"""
    A user asked for the stock price of {company}.
    Using the latest market data below, formulate a friendly and clear response starting with, "Based on the latest data,".
    Data: {json.dumps(quote_data)}
    """

    response = client.models.generate_content_stream(
        model=model,
        contents=prompt
    )
    
    for chunk in response:
        if chunk.text:
            yield chunk.text

def get_batch_stock_prices(tickers):
    """
    Uses Gemini with Google Search to get prices for multiple stocks at once.
    """
    print(f"\n[GEMINI] Calling get_batch_stock_prices for tickers: {tickers}")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    ticker_list_str = ", ".join(tickers)

    prompt = f"""
        Using a Google search, find the latest closing stock price, the dollar change, and the percentage change for the following US stock tickers: {ticker_list_str}.

        Return ONLY a valid JSON array. Each object in the array must include these four keys exactly: "symbol", "price", "change", "change_percent".

        The values should follow this format:
        - "symbol": the stock ticker symbol as a string (e.g., "AAPL")
        - "price": the latest closing price as a string with 2 decimal places (e.g., "213.25")
        - "change": the absolute dollar change as a string with a "+" or "-" sign (e.g., "+2.50" or "-1.20")
        - "change_percent": the percentage change as a string with a "+" or "-" sign and a "%" symbol (e.g., "+1.18%")

        Output ONLY the JSON array and nothing else. Do NOT include any explanation or extra text.

        Example format (use this structure exactly):

        [
        {{
            "symbol": "AAPL",
            "price": "213.25",
            "change": "+2.50",
            "change_percent": "+1.18%"
        }},
        ...
]

    """

    try:
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        config = types.GenerateContentConfig(
            tools=[grounding_tool]
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_text)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"[GEMINI] Error decoding batch price JSON from Gemini: {e}")
        return None
    except Exception as e:
        print(f"[GEMINI] An unexpected error occurred during batch price fetch: {e}")
        return None
