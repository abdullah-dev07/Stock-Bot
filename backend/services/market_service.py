from datetime import datetime, timezone, timedelta

from ..config import CACHE_DURATION_MINUTES
from ..constants import DEFAULT_TICKER_SYMBOLS
from . import stock_service

CACHE = {
    "ticker_data": {"data": None, "timestamp": None},
    "movers_data": {"data": None, "timestamp": None},
    "news_data": {"data": None, "timestamp": None},
    "ipo_data": {"data": None, "timestamp": None},
}


def _is_stale(cache_key):
    ts = CACHE[cache_key]["timestamp"]
    if not ts:
        return True
    return datetime.now(timezone.utc) - ts > timedelta(minutes=CACHE_DURATION_MINUTES)


def get_ticker_data():
    key = "ticker_data"
    if _is_stale(key) or not CACHE[key]["data"]:
        CACHE[key]["data"] = stock_service.get_batch_stock_prices(DEFAULT_TICKER_SYMBOLS)
        CACHE[key]["timestamp"] = datetime.now(timezone.utc)
    return CACHE[key]["data"] or []


def get_market_movers():
    key = "movers_data"
    if _is_stale(key) or not CACHE[key]["data"]:
        movers_data = stock_service.get_market_movers()

        if not movers_data and CACHE["ticker_data"]["data"]:
            ticker_data = CACHE["ticker_data"]["data"]
            sorted_tickers = sorted(
                ticker_data,
                key=lambda x: float(x.get("change", "0").replace("+", "")),
                reverse=True,
            )
            movers_data = {
                "top_gainers": [
                    {
                        "ticker": s["symbol"], "price": s["price"],
                        "change_amount": s["change"],
                        "change_percentage": s.get("change_percent", "0%"),
                    }
                    for s in sorted_tickers
                    if float(s.get("change", "0").replace("+", "")) >= 0
                ][:5],
                "top_losers": [
                    {
                        "ticker": s["symbol"], "price": s["price"],
                        "change_amount": s["change"],
                        "change_percentage": s.get("change_percent", "0%"),
                    }
                    for s in reversed(sorted_tickers)
                    if float(s.get("change", "0").replace("+", "")) < 0
                ][:5],
            }

        CACHE[key]["data"] = movers_data
        CACHE[key]["timestamp"] = datetime.now(timezone.utc)
    return CACHE[key]["data"] or {"top_gainers": [], "top_losers": []}


def get_market_news():
    key = "news_data"
    if _is_stale(key) or not CACHE[key]["data"]:
        CACHE[key]["data"] = stock_service.get_market_news()
        CACHE[key]["timestamp"] = datetime.now(timezone.utc)
    return CACHE[key]["data"] or []


def get_ipo_calendar():
    key = "ipo_data"
    if _is_stale(key) or not CACHE[key]["data"]:
        CACHE[key]["data"] = stock_service.get_ipo_calendar()
        CACHE[key]["timestamp"] = datetime.now(timezone.utc)
    return CACHE[key]["data"] or []
