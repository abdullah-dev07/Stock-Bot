import io
import csv
import time
import requests
from sec_api import QueryApi
from bs4 import BeautifulSoup

from ..config import ALPHA_VANTAGE_API_KEY as API_KEY, SEC_API_KEY
from ..constants import POPULAR_TICKERS
from ..utils.alpha_vantage import fetch as av_fetch

if not API_KEY:
    print("[STOCK] WARNING: ALPHA_VANTAGE_API_KEY not set. Stock data will not be available.")


# ---------------------------------------------------------------------------
# Single-stock endpoints
# ---------------------------------------------------------------------------

def get_stock_quote(ticker):
    """Latest price information for a given ticker."""
    data = av_fetch({"function": "GLOBAL_QUOTE", "symbol": ticker}, f"GLOBAL_QUOTE({ticker})")
    if not data:
        return None
    quote = data.get("Global Quote", {})
    if quote and quote.get("01. symbol", "").upper() == ticker.upper():
        return quote
    return None


def get_company_overview(ticker):
    """Fundamental data and key metrics for a company."""
    data = av_fetch({"function": "OVERVIEW", "symbol": ticker}, f"OVERVIEW({ticker})")
    if not data:
        return None
    if data.get("Symbol", "").upper() == ticker.upper():
        return data
    return None


def get_earnings(ticker):
    """Annual and quarterly earnings (EPS) for a company."""
    return av_fetch({"function": "EARNINGS", "symbol": ticker}, f"EARNINGS({ticker})")


def get_technical_indicator(ticker, function, time_period="60", series_type="close"):
    """Fetch a technical indicator (SMA, RSI, etc.) — returns the latest data point."""
    data = av_fetch(
        {"function": function, "symbol": ticker, "interval": "daily",
         "time_period": time_period, "series_type": series_type},
        f"{function}({ticker})",
    )
    if not data:
        return None
    data_key = f"Technical Analysis: {function}"
    if data_key in data:
        try:
            latest_date = sorted(data[data_key].keys())[-1]
            return data[data_key][latest_date]
        except (KeyError, IndexError):
            return None
    return None


def search_ticker_symbols(keywords):
    """Search for stock tickers — returns up to 5 best matches."""
    data = av_fetch({"function": "SYMBOL_SEARCH", "keywords": keywords.upper()}, "SYMBOL_SEARCH")
    if not data:
        return None
    if "bestMatches" in data:
        return [
            {"symbol": m.get("1. symbol"), "name": m.get("2. name")}
            for m in data["bestMatches"][:5]
        ]
    return []


# ---------------------------------------------------------------------------
# Aggregated / prediction data
# ---------------------------------------------------------------------------

def get_prediction_data(ticker):
    """Gathers fundamental + technical data required for a prediction."""
    if not API_KEY:
        return None
    overview = get_company_overview(ticker)
    if not overview:
        return None
    time.sleep(1)
    rsi_data = get_technical_indicator(ticker, "RSI")
    time.sleep(1)
    quote = get_stock_quote(ticker)
    time.sleep(1)
    sma_50 = get_technical_indicator(ticker, "SMA", time_period="50")
    time.sleep(1)
    sma_200 = get_technical_indicator(ticker, "SMA", time_period="200")

    return {
        "company_name": overview.get("Name", ticker),
        "pe_ratio": overview.get("PERatio", "N/A"),
        "eps": overview.get("EPS", "N/A"),
        "analyst_target_price": overview.get("AnalystTargetPrice", "N/A"),
        "rsi": rsi_data.get("RSI", "N/A") if rsi_data else "N/A",
        "sma_50": sma_50.get("SMA") if sma_50 else "N/A",
        "sma_200": sma_200.get("SMA") if sma_200 else "N/A",
        "current_price": quote.get("05. price", "N/A") if quote else "N/A",
    }


def get_batch_stock_prices(tickers):
    """Fetch prices for multiple tickers with rate-limit delays."""
    if not API_KEY:
        return None
    results = []
    for i, ticker in enumerate(tickers):
        try:
            if i > 0:
                time.sleep(1.5)
            quote_data = get_stock_quote(ticker)
            if quote_data:
                price = quote_data.get("05. price", "0.00")
                change = quote_data.get("09. change", "0.00")
                change_percent = quote_data.get("10. change percent", "0.00%")
                if not change.startswith(('+', '-')):
                    change = f"+{change}" if float(change) >= 0 else change
                if not change_percent.startswith(('+', '-')):
                    change_percent = f"+{change_percent}" if float(change_percent.rstrip('%')) >= 0 else change_percent
                results.append({
                    "symbol": ticker,
                    "price": price,
                    "change": change,
                    "change_percent": change_percent,
                })
        except Exception as e:
            print(f"[STOCK] Error fetching price for {ticker}: {e}")
            continue
    return results if results else None


# ---------------------------------------------------------------------------
# Market-wide endpoints
# ---------------------------------------------------------------------------

def get_market_movers():
    """Top gainers/losers. Tries premium endpoint, falls back to quote-based."""
    data = av_fetch({"function": "TOP_GAINERS_LOSERS"}, "TOP_GAINERS_LOSERS")
    if data:
        def transform(stock):
            return {
                "ticker": stock.get("ticker", stock.get("symbol", "")),
                "price": stock.get("price", "0.00"),
                "change_amount": stock.get("change_amount", "0.00"),
                "change_percentage": stock.get("change_percentage", "0.00%"),
            }
        return {
            "top_gainers": [transform(s) for s in data.get("top_gainers", [])[:5]],
            "top_losers": [transform(s) for s in data.get("top_losers", [])[:5]],
        }
    return _get_movers_from_quotes()


def _get_movers_from_quotes():
    """Fallback: fetch quotes for popular stocks and sort by change%."""
    popular_tickers = POPULAR_TICKERS
    quotes = []
    for i, ticker in enumerate(popular_tickers):
        if i > 0:
            time.sleep(1.5)
        try:
            q = get_stock_quote(ticker)
            if q:
                pct_str = q.get("10. change percent", "0%").rstrip('%')
                try:
                    pct = float(pct_str)
                except ValueError:
                    pct = 0.0
                quotes.append({
                    "ticker": ticker,
                    "price": q.get("05. price", "0.00"),
                    "change_amount": q.get("09. change", "0.00"),
                    "change_percentage": f"{pct:.2f}%",
                    "_sort": pct,
                })
        except Exception as e:
            print(f"[STOCK] Error in fallback mover fetch for {ticker}: {e}")
    if not quotes:
        return None
    sorted_q = sorted(quotes, key=lambda x: x["_sort"], reverse=True)
    for q in sorted_q:
        q.pop("_sort", None)
    gainers = [q for q in sorted_q if float(q["change_amount"]) >= 0][:5]
    losers = [q for q in reversed(sorted_q) if float(q["change_amount"]) < 0][:5]
    return {"top_gainers": gainers, "top_losers": losers}


def get_market_news():
    """Financial news — tries Alpha Vantage premium, falls back to RSS."""
    data = av_fetch(
        {"function": "NEWS_SENTIMENT", "topics": "financial_markets", "limit": "10"},
        "NEWS_SENTIMENT",
    )
    if data:
        return data.get("feed", [])
    return _get_news_from_rss()


def _get_news_from_rss():
    """Fallback: Google News RSS feed."""
    import xml.etree.ElementTree as ET
    rss_url = "https://news.google.com/rss/search?q=stock+market+finance&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(rss_url, timeout=15, headers={"User-Agent": "StockBot/1.0"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        articles = []
        for item in root.findall('.//item')[:10]:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            source = item.find('source')
            summary_parts = []
            if source is not None and source.text:
                summary_parts.append(f"Source: {source.text}")
            if pub_date is not None and pub_date.text:
                summary_parts.append(pub_date.text)
            articles.append({
                "title": title.text if title is not None else "Untitled",
                "url": link.text if link is not None else "#",
                "summary": " | ".join(summary_parts) if summary_parts else "Financial news",
                "source": source.text if source is not None else "Google News",
            })
        return articles
    except Exception as e:
        print(f"[STOCK] Error fetching RSS news: {e}")
        return None


def get_ipo_calendar():
    """Upcoming IPOs for the next 3 months."""
    if not API_KEY:
        return None
    # IPO endpoint returns CSV, so we can't use av_fetch (which expects JSON)
    from ..config import ALPHA_VANTAGE_BASE_URL as BASE_URL
    params = {"function": "IPO_CALENDAR", "apikey": API_KEY}
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        try:
            json_data = response.json()
            for key in ("Note", "Information", "Error Message"):
                if key in json_data:
                    print(f"[STOCK] IPO_CALENDAR {key}: {json_data[key]}")
                    return None
        except ValueError:
            pass  # Not JSON — it's CSV, which is expected
        ipo_data = []
        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file)
        for row in reader:
            entry = {
                "symbol": row.get("symbol", row.get("Symbol", row.get("ticker", ""))),
                "name": row.get("name", row.get("Name", row.get("company", ""))),
                "ipoDate": row.get("ipoDate", row.get("IPO Date", row.get("date", row.get("Date", "")))),
            }
            if entry["symbol"]:
                ipo_data.append(entry)
        return ipo_data[:10]
    except Exception as e:
        print(f"[STOCK] Error fetching IPO calendar: {e}")
        return None


def get_10k_filing_text(ticker):
    """Fetches and cleans the text of the latest 10-K filing via sec-api.io."""
    if not SEC_API_KEY:
        print("[STOCK] ERROR: SEC_API_KEY not set.")
        return None
    try:
        queryApi = QueryApi(api_key=SEC_API_KEY)
        query = {
            "query": f'ticker:"{ticker}" AND formType:"10-K"',
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        filings = queryApi.get_filings(query)
        if not filings['filings']:
            return None
        sec_url = filings['filings'][0]['linkToFilingDetails']
        file_path = sec_url.split("https://www.sec.gov/Archives/edgar/data/")[1]
        download_url = f"https://archive.sec-api.io/{file_path}?token={SEC_API_KEY}"
        headers = {"User-Agent": "StockBot/1.0 contact@stockbot.app"}
        response = requests.get(download_url, headers=headers, timeout=60)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        markdown_tables = []
        for table in soup.find_all('table'):
            table_str = ""
            for row in table.find_all('tr'):
                row_text = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                table_str += " | ".join(row_text) + "\n"
            placeholder = f"---TABLE_PLACEHOLDER_{len(markdown_tables)}---"
            markdown_tables.append(table_str)
            table.replace_with(placeholder)

        clean_text = soup.get_text(separator='\n', strip=True)
        for i, table_md in enumerate(markdown_tables):
            clean_text = clean_text.replace(f"---TABLE_PLACEHOLDER_{i}---", f"\n\n{table_md}\n\n")
        return clean_text
    except requests.exceptions.Timeout:
        print(f"[STOCK] Timeout fetching 10-K for {ticker}.")
        return None
    except Exception as e:
        print(f"[STOCK] Error fetching 10-K for {ticker}: {e}")
        return None
