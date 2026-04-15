from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .config import (
    CORS_ORIGINS, BUILD_DIR,
    ALPHA_VANTAGE_API_KEY, GEMINI_API_KEY, SEC_API_KEY,
    FIREBASE_WEB_API_KEY,
)
from .db import firebase_init
from .routes import auth, chat, market, rag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(market.router)
app.include_router(rag.router)


# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return JSONResponse(content={
        "status": "running",
        "config": {
            "ALPHA_VANTAGE_API_KEY": "set" if ALPHA_VANTAGE_API_KEY else "MISSING",
            "GEMINI_API_KEY": "set" if GEMINI_API_KEY else "MISSING",
            "SEC_API_KEY": "set" if SEC_API_KEY else "MISSING",
            "FIREBASE_WEB_API_KEY": "set" if FIREBASE_WEB_API_KEY else "MISSING",
            "FIREBASE_ADMIN": "connected" if firebase_init.db else "NOT CONNECTED",
            "CORS_ORIGINS": "*",
        },
    })


# ── Static SPA serving (production) ─────────────────────────────────────
assets_dir = os.path.join(BUILD_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    index_path = os.path.join(BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        status_code=404,
        content={"message": "Frontend not found. In development, use Vite on http://localhost:5173"},
    )
