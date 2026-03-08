import os
import requests
import csv
from dotenv import load_dotenv
import io
from sec_api import QueryApi
from bs4 import BeautifulSoup
import time


load_dotenv()

SEC_API_KEY = os.environ.get("SEC_API_KEY")
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Warn if API key is missing
if not API_KEY:
    print("[STOCK API] WARNING: ALPHA_VANTAGE_API_KEY not found in environment variables! Stock data will not be available.")
else:
    print(f"[STOCK API] Alpha Vantage API key loaded (ends with ...{API_KEY[-4:]})")


def _check_api_response(data, function_name):
    """Check for common Alpha Vantage error responses."""
    if "Note" in data:
        print(f"[STOCK API] API Rate Limit Reached for {function_name}: {data['Note']}")
        return False
    if "Information" in data:
        print(f"[STOCK API] API Information for {function_name}: {data['Information']}")
        return False
    if "Error Message" in data:
        print(f"[STOCK API] API Error for {function_name}: {data['Error Message']}")
        return False
    return True


def get_technical_indicator(ticker, function, time_period="60", series_type="close"):
    """
    Generic function to fetch technical indicators like SMA, RSI, etc.
    Returns the most recent data point.
    """
    if not API_KEY:
        print(f"[STOCK API] Skipping {function} - no API key")
        return None

    print(f"\n[STOCK API] calling {function} for ticker: {ticker}")
    params = {
        "function" : function,
        "symbol" : ticker,
        "interval": "daily",
        "time_period": time_period,
        "series_type":series_type,
        "apikey":API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, function):
            return None
        
        data_key = f"Technical Analysis: {function}"
        if data_key in data:
            latest_date = sorted(data[data_key].keys())[-1]
            return data[data_key][latest_date]
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching {function} for {ticker} : {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"[STOCK API] Error parsing {function} data for {ticker}: {e}")
        return None
    

def get_prediction_data(ticker):
    """
    Gathers all fundamental and technical data required for making a prediction.
    """    
    if not API_KEY:
        print(f"[STOCK API] Cannot get prediction data - no API key")
        return None

    print(f"\n[STOCK API] Gathering all prediction data for ticker: '{ticker}")

    overview = get_company_overview(ticker)
    if not overview:
        print(f"Company overview for {ticker} not found using STOCK API")
        return None
    
    time.sleep(1)  # Rate limit delay
    rsi_data = get_technical_indicator(ticker, "RSI")
    time.sleep(1)
    sma_data = get_technical_indicator(ticker, "SMA")

    time.sleep(1)
    quote = get_stock_quote(ticker)

    time.sleep(1)
    sma_50 = get_technical_indicator(ticker, "SMA", time_period="50")
    time.sleep(1)
    sma_200 = get_technical_indicator(ticker, "SMA", time_period="200")

    prediction_payload = {
        "company_name": overview.get("Name", ticker),
        "pe_ratio": overview.get("PERatio", "N/A"),
        "eps": overview.get("EPS", "N/A"),
        "analyst_target_price" : overview.get("AnalystTargetPrice", "N/A"),
        "rsi": rsi_data.get("RSI", "N/A") if rsi_data else "N/A",
        "sma_50": sma_50.get("SMA") if sma_50 else "N/A",
        "sma_200": sma_200.get("SMA") if sma_200 else "N/A",
        "current_price": quote.get("05. price", "N/A") if quote else "N/A"
    }

    return prediction_payload

def search_ticker_symbols(keywords):
    """
    Searches for stock tickers and returns up to 5 best matches.
    Returns None on API/network failure, [] on no results.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot search tickers - no API key")
        return None

    search_term = keywords.upper()
    print(f"\n[STOCK API] Calling search_ticker_symbols with keywords: '{search_term}'")
    
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": search_term,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        print(f"response: {response}")
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, "SYMBOL_SEARCH"):
            return None
        
        if "bestMatches" in data:
            return [
                {"symbol": match.get("1. symbol"), "name": match.get("2. name")} 
                for match in data["bestMatches"][:5]
            ]
        return [] 
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching ticker for {keywords}: {e}")
        return None 



def get_ipo_calendar():
    """
    Fetches the upcoming IPOs for the next 3 months.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot get IPO calendar - no API key")
        return None

    print(f"\n[STOCK API] Calling get_ipo_calendar")
    params = {
        "function": "IPO_CALENDAR",
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        # Check if response looks like an error JSON instead of CSV
        try:
            json_data = response.json()
            if not _check_api_response(json_data, "IPO_CALENDAR"):
                return None
        except ValueError:
            pass  # Not JSON, good - it's CSV data
        
        ipo_data = []
        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Transform CSV columns to match frontend expectations
            # Alpha Vantage CSV columns might vary, so we check multiple possible field names
            transformed_ipo = {
                "symbol": row.get("symbol", row.get("Symbol", row.get("ticker", ""))),
                "name": row.get("name", row.get("Name", row.get("company", ""))),
                "ipoDate": row.get("ipoDate", row.get("IPO Date", row.get("date", row.get("Date", ""))))
            }
            # Only add if we have at least a symbol
            if transformed_ipo["symbol"]:
                ipo_data.append(transformed_ipo)
            
        return ipo_data[:10] 
        
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching IPO calendar: {e}")
        return None
    except Exception as e:
        print(f"[STOCK API] Error parsing IPO calendar CSV: {e}")
        return None



def get_stock_quote(ticker):
    """
    Gets the latest price information for a given ticker.
    Returns None on API/network failure.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot get stock quote - no API key")
        return None

    print(f"\n[STOCK API] Calling get_stock_quote with ticker: '{ticker}'")
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, f"GLOBAL_QUOTE({ticker})"):
            return None

        quote_data = data.get("Global Quote", {})
        if quote_data and quote_data.get("01. symbol") and quote_data.get("01. symbol").upper() == ticker.upper():
            return quote_data
        else:
            print(f"[STOCK API] Warning: Quote data mismatch or empty. Requested {ticker}. Likely a demo key or invalid symbol.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching quote for {ticker}: {e}")
        return None

def get_company_overview(ticker):
    """
    Gets fundamental data and key metrics for a company.
    Returns None on API/network failure.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot get company overview - no API key")
        return None

    print(f"\n[STOCK API] Calling get_company_overview with ticker: '{ticker}'")
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, f"OVERVIEW({ticker})"):
            return None

        if data.get("Symbol") and data.get("Symbol").upper() == ticker.upper():
            return data
        else:
            print(f"[STOCK API] Warning: Overview data mismatch or empty. Requested {ticker}. Likely a demo key or invalid symbol.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching overview for {ticker}: {e}")
        return None

def get_earnings(ticker):
    """
    Gets the annual and quarterly earnings (EPS) for a company.
    Returns None on API/network failure.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot get earnings - no API key")
        return None

    print(f"\n[STOCK API] Calling get_earnings with ticker: '{ticker}'")
    params = {
        "function": "EARNINGS",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, f"EARNINGS({ticker})"):
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching earnings for {ticker}: {e}")
        return None


def get_market_movers():
    """Fetches the top 5 US market gainers and losers for the day."""
    if not API_KEY:
        print(f"[STOCK API] Cannot get market movers - no API key")
        return None

    print(f"\n[STOCK API] Calling get_market_movers")
    params = {
        "function": "TOP_GAINERS_LOSERS",
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, "TOP_GAINERS_LOSERS"):
            return None
        
        # Transform Alpha Vantage data to match frontend expectations
        def transform_mover(stock):
            return {
                "ticker": stock.get("ticker", stock.get("symbol", "")),
                "price": stock.get("price", "0.00"),
                "change_amount": stock.get("change_amount", "0.00"),
                "change_percentage": stock.get("change_percentage", "0.00%")
            }
        
        top_gainers = [transform_mover(stock) for stock in data.get("top_gainers", [])[:5]]
        top_losers = [transform_mover(stock) for stock in data.get("top_losers", [])[:5]]
        
        return {
            "top_gainers": top_gainers,
            "top_losers": top_losers
        }
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching market movers: {e}")
        return None


def get_market_news():
    """
    NEW: Fetches the latest general financial news articles.
    """
    if not API_KEY:
        print(f"[STOCK API] Cannot get market news - no API key")
        return None

    print(f"\n[STOCK API] Calling get_market_news")
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets", 
        "limit": "10", 
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not _check_api_response(data, "NEWS_SENTIMENT"):
            return None
        
        return data.get("feed", [])
        
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching market news: {e}")
        return None


def get_10k_filing_text(ticker):
    """
    Fetches and cleans the text of the latest 10-K filing for a given ticker
    using a more robust parsing method to capture all content.
    """
    if not SEC_API_KEY:
        print("[STOCK API] ERROR: SEC_API_KEY not found in environment variables.")
        return None

    print(f"\n[STOCK API] Using sec-api.io to find latest 10-K for ticker: '{ticker}'")
    
    try:
        
        queryApi = QueryApi(api_key=SEC_API_KEY)
        query = {
          "query": f'ticker:"{ticker}" AND formType:"10-K"',
          "from": "0",
          "size": "1",
          "sort": [{ "filedAt": { "order": "desc" } }]
        }
        
        filings = queryApi.get_filings(query)
        
        if not filings['filings']:
            print(f"[STOCK API] No 10-K filings found for {ticker}.")
            return None

        sec_url = filings['filings'][0]['linkToFilingDetails']
        print(f"[STOCK API] Found SEC URL: {sec_url}")

        file_path = sec_url.split("https://www.sec.gov/Archives/edgar/data/")[1]
        download_url = f"https://archive.sec-api.io/{file_path}?token={SEC_API_KEY}"
        print(f"[STOCK API] Constructed Download API URL: {download_url}")
        
        
        headers = {'User-Agent': 'StockBot/1.0 abdullah.muhammad@devsinc.com'}
        response = requests.get(download_url, headers=headers, timeout=60) 
        response.raise_for_status()
        
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        
        
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
        print(f"[STOCK API] Timeout error while fetching 10-K for {ticker}.")
        return None
    except Exception as e:
        print(f"[STOCK API] An error occurred fetching 10-K for {ticker}: {e}")
        return None
