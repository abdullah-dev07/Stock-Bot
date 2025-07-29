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
        You are an intent classifier for a stock-focused assistant.

        INTENT TYPES:
        - 'get_specific_data': The user is asking for **real-time stock data** (price, open, close, volume, etc.) about a **single company**. Your system uses the Alpha Vantage API for this.
        - 'get_qualitative_analysis': The user is asking for an explanation, reasoning, or trends.
        - 'get_personalized_advice': The user is asking what they should do personally (e.g., "Should I buy Tesla?")
        - 'general_knowledge': The user is asking about general concepts (e.g., "What is a dividend?")

        RULES:
        1. If the user wants the current **stock price or quote data** for **a single company** (even if they just mention the company name), set:
        - intent = 'get_specific_data'
        - entity = company name (you’ll resolve the ticker elsewhere)
        
        2. If the query is broader, interpret accordingly and choose the appropriate intent.

        3. Return only a JSON object with:
        - "intent": one of the four intent values above
        - "entity": company name or null

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
