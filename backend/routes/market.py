from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..services.auth_service import get_current_user
from .handlers.market_handler import MarketHandler

router = APIRouter(tags=["Market Data"])


@router.get("/ticker-data")
def get_ticker_data(user: dict = Depends(get_current_user)):
    return JSONResponse(content=MarketHandler.get_ticker_data())


@router.get("/market-movers")
def get_market_movers(user: dict = Depends(get_current_user)):
    return JSONResponse(content=MarketHandler.get_movers())


@router.get("/market-news")
def get_market_news(user: dict = Depends(get_current_user)):
    return JSONResponse(content=MarketHandler.get_news())


@router.get("/ipo-calendar")
def get_ipo_calendar(user: dict = Depends(get_current_user)):
    return JSONResponse(content=MarketHandler.get_ipo_calendar())
