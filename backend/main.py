# FILE: backend/main.py
# PURPOSE: Main FastAPI application file, now acting as a pure API server.

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from dotenv import load_dotenv
import json
from datetime import datetime, timezone, timedelta
from starlette.concurrency import iterate_in_threadpool
import os
from . import firebase_init
from . import rag_pipeline
from . import gemini_client
from . import stock_api
from . import firebase_db
from .auth import auth_router, get_current_user
import asyncio



load_dotenv()

app = FastAPI()

# --- CORS Middleware ---
# This allows the React app and a potential static build test to make requests to this backend directly.
origins = [
    "http://localhost:5173",  # Standard React Dev Server
    "http://127.0.0.1:3000",  # Accessing React Dev Server via IP
    "http://localhost:8081",  # For testing a production build locally
    "http://127.0.0.1:8081", 
    "http://0.0.0.0:8000",
    "http://localhost:5173", # Add Vite's default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

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
    chat_id: str

class RagInitiateRequest(BaseModel):
    company_name: str
    context : dict = {}

class RagQueryRequest(BaseModel):
    company_name: str
    question: str    

class NewChatRequest(BaseModel):
    message: str

class ChatHistoryRequest(BaseModel):
    chat_id: str
    message: str
    context : dict = {}


# --- Helper Functions ---
def is_likely_ticker(s: str):
    if not isinstance(s, str): return False
    return s.isupper() and ' ' not in s and 1 <= len(s) <= 5

def is_cache_stale(cache_key: str):
    timestamp = CACHE[cache_key]["timestamp"]
    if not timestamp:
        return True
    return datetime.now(timezone.utc) - timestamp > timedelta(minutes=CACHE_DURATION_MINUTES)

def proceed_with_intent(intent: str, ticker: str, entity: str, user_id: str, chat_id: str):
    """Handles non-streaming intents that result in a stream."""
    if intent == "get_specific_data":
        quote_data = stock_api.get_stock_quote(ticker)
        if not quote_data:
            return StreamingResponse(iter([f"Sorry, I couldn't retrieve valid price data for {ticker}."]), media_type="text/plain")
        
        return StreamingResponse(save_and_yield(
            gemini_client.generate_response_from_quote(quote_data, entity),
            user_id=user_id,  # No user context needed for this response
            chat_id=chat_id,  # No chat context needed for this response
            role="assistant"
        ), media_type="text/plain")
    
    return StreamingResponse(iter(["I'm not sure how to proceed with that request."]), media_type="text/plain")


# --- API Routes ---

@app.get("/ticker-data", tags=["Application"])
def get_ticker_data(user: dict = Depends(get_current_user)):
    cache_key = "ticker_data"
    if is_cache_stale(cache_key) or not CACHE[cache_key]["data"]:
        print(f"[CACHE] {cache_key} cache is stale or empty. Fetching new data.")
        tickers = ["AAPL", "NVDA", "AMD","GOOGL", "MSFT", "AMZN"]
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

@app.post("/chat", tags=["Chat"])
async def chat(payload: ChatHistoryRequest, user: dict = Depends(get_current_user)):
    user_id = user['uid']
    chat_id = payload.chat_id
    user_message = payload.message
    context = payload.context
    
    history = await asyncio.to_thread(firebase_db.get_chat_history, user_id, chat_id)
    await asyncio.to_thread(firebase_db.add_message_to_chat, user_id, chat_id, "user", user_message)

    if not context.get('awaiting_clarification'):
        intent_data = await asyncio.to_thread(gemini_client.get_intent, user_message, history)
        intent = intent_data.get("intent", "general_knowledge")
        entity = intent_data.get("entity")
        if intent in ['get_specific_data', 'get_prediction_or_advice'] and entity:
             matches = await asyncio.to_thread(stock_api.search_ticker_symbols, entity)
             if matches and len(matches) > 1 and not is_likely_ticker(entity):
                 return JSONResponse(content={"response_type": "clarification", "message": f"I found a few potential matches for '{entity}'.", "choices": matches, "original_intent": intent})

    async def stream_and_save_response():
        full_response_text = ""
        generator = None
        try:
            if context.get('awaiting_clarification'):
                intent = context.get('original_intent')
                ticker = user_message
                if intent == 'get_prediction_or_advice':
                    prediction_data = await asyncio.to_thread(stock_api.get_prediction_data, ticker)
                    if not prediction_data:
                        generator = iter([f"Sorry, I couldn't gather enough data for {ticker}."])
                    else:
                        generator = gemini_client.generate_prediction_response(prediction_data, user_message)
                else:
                    generator = proceed_with_intent(intent, ticker, ticker)
            else:
                intent_data = await asyncio.to_thread(gemini_client.get_intent, user_message, history)
                intent = intent_data.get("intent", "general_knowledge")
                entity = intent_data.get("entity")
                print(f"[APP] Gemini identified Intent: '{intent}', Entity: '{entity}'")

                if intent in ['get_specific_data', 'get_prediction_or_advice']:
                    if not entity:
                        generator = iter(["I need to know which stock you're interested in."])
                    else:
                        ticker_to_use = entity if is_likely_ticker(entity) else (await asyncio.to_thread(stock_api.search_ticker_symbols, entity))[0]['symbol']
                        
                        if intent == 'get_specific_data':
                            generator = proceed_with_intent(intent, ticker_to_use, entity)
                        elif intent == 'get_prediction_or_advice':
                            prediction_data = await asyncio.to_thread(stock_api.get_prediction_data, ticker_to_use)
                            if not prediction_data:
                                generator = iter([f"Sorry, I couldn't gather enough data for {ticker_to_use}."])
                            else:
                                generator = gemini_client.generate_prediction_response(prediction_data, user_message)
                else: 
                    generator = gemini_client.generate_grounded_response(user_message, history)
            
            for chunk in generator:
                full_response_text += chunk
                yield chunk
            
            await asyncio.to_thread(firebase_db.add_message_to_chat, user_id, chat_id, "model", full_response_text)

        except Exception as e:
            print(f"[APP] An error occurred during chat processing: {type(e).__name__} - {e}")
            error_message = "Sorry, an internal error occurred."
            yield error_message
            await asyncio.to_thread(firebase_db.add_message_to_chat, user_id, chat_id, "model", error_message)

    return StreamingResponse(stream_and_save_response(), media_type="text/plain")
    


def save_and_yield(generator, user_id, chat_id, role):
    buffer = []
    for chunk in generator:
        buffer.append(chunk)
        yield chunk
    firebase_db.add_message_to_chat(user_id, chat_id, role, "".join(buffer))
    print(f"[APP] Saved full message to chat {chat_id} for user {user_id}.")


@app.post("/chats", tags=["Chat History"])
async def create_chat_session(payload: NewChatRequest, user: dict = Depends(get_current_user)):
    """Creates a new chat session and returns the new chat ID."""

    print(f"[APP] Creating new chat session for user: {user.get('email')}")
    user_id = user['uid']
    chat_id = firebase_db.create_new_chat(user_id, payload.message)
    firebase_db.add_message_to_chat(user_id, chat_id, "user", payload.message)
    print(f"[APP] Created new chat session with ID: {chat_id} for user {user_id}")
    return {"chat_id": chat_id}

@app.get("/chats", tags=["Chat History"])
async def get_all_chats(user: dict = Depends(get_current_user)):
    """ Gets a list of all chat sessions for the current user """
    print(f"[APP] Fetching chat sessions for user: {user.get('email')}")
    user_id = user['uid']
    chat_list = firebase_db.get_chat_list(user_id)
    return chat_list


@app.get("/chats/{chat_id}", tags=["Chat History"])
async def get_chat_messages(chat_id:str, user:dict = Depends(get_current_user)):
    print(f"[APP] Fetching messages for chat ID: {chat_id} for user: {user.get('email')}")
    """Gets all messages for a specific chat session."""
    user_id = user['uid']
    history = firebase_db.get_chat_history(user_id, chat_id)
    return history

@app.delete("/chats/{chat_id}", tags=["Chat History"])
async def delete_chat(chat_id: str, user: dict = Depends(get_current_user)):
    """Deletes a specific chat session."""
    user_id = user['uid']
    success = firebase_db.delete_chat(user_id, chat_id)
    if success:
        return {"message": "Chat deleted successfully."}
    else:
        raise HTTPException(status_code=404, detail="Chat not found or could not be deleted.")



@app.post("/rag/initiate", tags=["RAG"])
async def rag_initiate(payload: RagInitiateRequest, user: dict = Depends(get_current_user)):
    company_input = payload.company_name
    context = payload.context

    print(f"[APP] RAG Initiate request for: {company_input}")

    # --- FULL DYNAMIC LOGIC (COMMENTED OUT FOR TESTING) ---
    """
    if context.get('awaiting_clarification'):
        ticker = company_input
        matches = await asyncio.to_thread(stock_api.search_ticker_symbols, ticker)
        actual_name = matches[0]['name'] if matches else ticker
    else:
        matches = await asyncio.to_thread(stock_api.search_ticker_symbols, company_input)
        if not matches:
            return JSONResponse(status_code=404, content={"message": f"Sorry, I couldn't find a stock ticker for '{company_input}'."})
        
        if len(matches) > 1:
            return {"response_type": "clarification", "message": f"I found a few potential matches for '{company_input}'.", "choices": matches, "original_intent": "rag_initiate"}
        
        ticker = matches[0]['symbol']
        actual_name = matches[0]['name']
    """
    # --- HARDCODED FOR TESTING ---
    ticker = "AMZN"
    actual_name = "Amazon"
    print(f"[APP] Using hardcoded ticker: {ticker} and name: {actual_name}")
    # --- END OF HARDCODED SECTION ---

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    file_name = f"{actual_name.replace(' ', '_')}_10k.txt"
    file_path = os.path.join(data_dir, file_name)

    document_text = None
    if os.path.exists(file_path):
        print(f"[APP] Found local cache file. Reading from disk.")
        with open(file_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
    else:
        print(f"[APP] No local cache found. Fetching from sec-api.io...")
        document_text = await asyncio.to_thread(stock_api.get_10k_filing_text, ticker)
        if document_text:
            print(f"[APP] Saving fetched document to: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(document_text)

    if not document_text:
        return JSONResponse(status_code=500, content={"message": f"Sorry, I was unable to retrieve the 10-K report for {actual_name}."})

    await rag_pipeline.create_vector_store_from_text(document_text, actual_name)
    
    return {"message": f"The latest 10-K report for {actual_name} is ready. What would you like to know?", "company_name": actual_name}

@app.post("/rag/query", tags=["RAG"])
async def rag_query(payload: RagQueryRequest, user: dict = Depends(get_current_user)):
    company_name = payload.company_name
    question = payload.question
    streaming_response_generator = rag_pipeline.query_rag_pipeline(company_name, question)
    return StreamingResponse(streaming_response_generator, media_type="text/plain")


build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../react-frontend/dist"))

app.mount("/assets", StaticFiles(directory=os.path.join(build_dir, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path:str):
    index_path = os.path.join(build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return JSONResponse(status_code=500, content={"message":"Frontend not found"})

    


