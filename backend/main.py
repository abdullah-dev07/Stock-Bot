# FILE: backend/main.py
# PURPOSE: Main FastAPI application file, now acting as a pure API server.

from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from dotenv import load_dotenv
import json
from datetime import datetime, timezone, timedelta
from starlette.concurrency import iterate_in_threadpool

# --- Initialize Firebase at the very start of the application ---
from . import firebase_init

# --- Import your project's modules ---
from . import gemini_client
from . import stock_api
from .auth import auth_router, get_current_user

load_dotenv()

app = FastAPI()

# --- CORS Middleware ---
# This allows your React app and a potential static build test to make requests to this backend directly.
origins = [
    "http://localhost:3000",  # Standard React Dev Server
    "http://127.0.0.1:3000",  # Accessing React Dev Server via IP
    "http://localhost:8081",  # For testing a production build locally
    "http://127.0.0.1:8081",  # For testing a production build locally via IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include the authentication routes ---
app.include_router(auth_router)

# --- Server-Side Cache ---
CACHE = {
    "ticker_data": {"data": None, "timestamp": None},
    "movers_data": {"data": None, "timestamp": None},
    "news_data": {"data": None, "timestamp": None},
    "ipo_data": {"data": None, "timestamp": None},
}
CACHE_DURATION_MINUTES = 600

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    context: dict = {}
    history: List[Dict[str, Any]] = Field(default_factory=list)

# --- Helper Functions ---
def is_likely_ticker(s: str):
    if not isinstance(s, str): return False
    return s.isupper() and ' ' not in s and 1 <= len(s) <= 5

def is_cache_stale(cache_key: str):
    timestamp = CACHE[cache_key]["timestamp"]
    if not timestamp:
        return True
    return datetime.now(timezone.utc) - timestamp > timedelta(minutes=CACHE_DURATION_MINUTES)

# --- API Routes ---

@app.get("/ticker-data", tags=["Application"])
def get_ticker_data(user: dict = Depends(get_current_user)):
    cache_key = "ticker_data"
    if is_cache_stale(cache_key) or not CACHE[cache_key]["data"]:
        print(f"[CACHE] {cache_key} cache is stale or empty. Fetching new data.")
        tickers = ["AAPL", "NVDA", "GOOGL", "MSFT", "AMZN"]
        CACHE[cache_key]["data"] = gemini_client.get_batch_stock_prices(tickers)
        CACHE[cache_key]["timestamp"] = datetime.now(timezone.utc)
    else:
        print(f"[CACHE] Serving {cache_key} data from cache.")
    return JSONResponse(content=CACHE[cache_key]["data"] or [])

@app.get("/market-movers", tags=["Application"])
def get_market_movers(user: dict = Depends(get_current_user)):
    cache_key = "movers_data"
    if is_cache_stale(cache_key) or not CACHE[cache_key]["data"]:
        print(f"[CACHE] {cache_key} cache is stale or empty. Fetching new data.")
        CACHE[cache_key]["data"] = stock_api.get_market_movers()
        CACHE[cache_key]["timestamp"] = datetime.now(timezone.utc)
    else:
        print(f"[CACHE] Serving {cache_key} data from cache.")
    return JSONResponse(content=CACHE[cache_key]["data"] or {"top_gainers": [], "top_losers": []})

@app.get("/market-news", tags=["Application"])
def get_market_news(user: dict = Depends(get_current_user)):
    cache_key = "news_data"
    if is_cache_stale(cache_key) or not CACHE[cache_key]["data"]:
        print(f"[CACHE] {cache_key} cache is stale or empty. Fetching new data.")
        CACHE[cache_key]["data"] = stock_api.get_market_news()
        CACHE[cache_key]["timestamp"] = datetime.now(timezone.utc)
    else:
        print(f"[CACHE] Serving {cache_key} data from cache.")
    return JSONResponse(content=CACHE[cache_key]["data"] or [])

@app.get("/ipo-calendar", tags=["Application"])
def get_ipo_calendar(user: dict = Depends(get_current_user)):
    cache_key = "ipo_data"
    if is_cache_stale(cache_key) or not CACHE[cache_key]["data"]:
        print(f"[CACHE] {cache_key} cache is stale or empty. Fetching new data.")
        CACHE[cache_key]["data"] = stock_api.get_ipo_calendar()
        CACHE[cache_key]["timestamp"] = datetime.now(timezone.utc)
    else:
        print(f"[CACHE] Serving {cache_key} data from cache.")
    return JSONResponse(content=CACHE[cache_key]["data"] or [])

def proceed_with_intent(intent: str, ticker: str, entity: str):
    """Handles non-streaming intents that result in a stream."""
    if intent == "get_specific_data":
        quote_data = stock_api.get_stock_quote(ticker)
        if not quote_data:
            return StreamingResponse(iter([f"Sorry, I couldn't retrieve valid price data for {ticker}."]), media_type="text/plain")
        
        # Assume generate_response_from_quote is a generator, suitable for streaming
        return StreamingResponse(gemini_client.generate_response_from_quote(entity, quote_data), media_type="text/plain")
    
    return StreamingResponse(iter(["I'm not sure how to proceed with that request."]), media_type="text/plain")

@app.post("/chat", tags=["Application"])
async def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    user_message = payload.message
    context = payload.context
    history = payload.history

    print(f"\n[APP] User '{user.get('email')}' sent message: '{user_message}' with history length: {len(history)}")

    try:
        if context.get('awaiting_clarification'):
            intent = context.get('original_intent')
            ticker = user_message
            return proceed_with_intent(intent, ticker, ticker)

        intent_data = gemini_client.get_intent(user_message, history)
        intent = intent_data.get("intent", "general_knowledge")
        entity = intent_data.get("entity")
        
        print(f"[APP] Gemini identified Intent: '{intent}', Entity: '{entity}'")

        if intent == 'get_specific_data':
            if not entity:
                return StreamingResponse(iter(["It looks like you're asking for specific data, but I couldn't identify the stock."]), media_type="text/plain")
            
            if is_likely_ticker(entity):
                return proceed_with_intent(intent, entity, entity)
            
            matches = stock_api.search_ticker_symbols(entity)
            if not matches:
                return StreamingResponse(iter([f"Sorry, I couldn't find any stock tickers for '{entity}'."]), media_type="text/plain")

            if len(matches) > 1:
                return {
                    "response_type": "clarification",
                    "message": f"I found a few potential matches for '{entity}'. Which one did you mean?",
                    "choices": matches,
                    "original_intent": intent
                }

            ticker_to_use = matches[0]['symbol']
            return proceed_with_intent(intent, ticker_to_use, entity)

        # --- THIS IS THE FINAL, CORRECTED STREAMING LOGIC ---
        elif intent in ['get_qualitative_analysis', 'get_personalized_advice', 'general_knowledge']:
            # This is a synchronous generator function from your library
            sync_generator = gemini_client.generate_grounded_response(user_message, history)
            
            # This runs the synchronous generator in a separate thread to prevent blocking
            # and lets us await it like an async generator.
            async_iterator = iterate_in_threadpool(sync_generator)
            
            return StreamingResponse(async_iterator, media_type="text/plain")

        else:
            # Fallback for any other intents that should be treated as general chat
            sync_generator = gemini_client.generate_grounded_response(user_message, history)
            async_iterator = iterate_in_threadpool(sync_generator)
            return StreamingResponse(async_iterator, media_type="text/plain")
            
    except Exception as e:
        print(f"[APP] An unexpected error occurred: {type(e).__name__} - {e}")
        return StreamingResponse(iter(["Sorry, an internal error occurred."]), media_type="text/plain", status_code=500)