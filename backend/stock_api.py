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


def get_technical_indicator(ticker, function, time_period="60", series_type="close"):
    """
    Generic function to fetch technical indicators like SMA, RSI, etc.
    Returns the most recent data point.
    """

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
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API limited reached for {function} : {data['Note']}")
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
    print(f"\n[STOCK API] Gathering all prediction data for ticker: '{ticker}")

    overview = get_company_overview(ticker)
    if not overview:
        print(f"Company overview for {ticker} not found using STOCK API")
        return None
    
    rsi_data = get_technical_indicator(ticker, "RSI")
    sma_data = get_technical_indicator(ticker, "SMA")

    quote = get_stock_quote(ticker)

    prediction_payload = {
        "company_name": overview.get("Name", ticker),
        "pe_ratio": overview.get("PERatio", "N/A"),
        "eps": overview.get("EPS", "N/A"),
        "analyst_target_price" : overview.get("AnalystTargetPrice", "N/A"),
        "rsi": rsi_data.get("RSI", "N/A") if rsi_data else "N//A",
        "sma_50": get_technical_indicator(ticker, "SMA", time_period="50").get("SMA") if get_technical_indicator(ticker, "SMA", time_period="50") else "N/A",
        "sma_200": get_technical_indicator(ticker, "SMA", time_period="200").get("SMA") if get_technical_indicator(ticker, "SMA", time_period="200") else "N/A",
        "current_price": quote.get("05. price", "N/A") if quote else "N/A"
    }

    return prediction_payload

def search_ticker_symbols(keywords):
    """
    Searches for stock tickers and returns up to 5 best matches.
    Returns None on API/network failure, [] on no results.
    """
    search_term = keywords.upper()
    print(f"\n[STOCK API] Calling search_ticker_symbols with keywords: '{search_term}'")
    
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": search_term,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        print(f"response: {response}")
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
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
    NEW: Fetches the upcoming IPOs for the next 3 months.
    """
    print(f"\n[STOCK API] Calling get_ipo_calendar")
    params = {
        "function": "IPO_CALENDAR",
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        
        ipo_data = []
        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file)
        for row in reader:
            ipo_data.append(row)
            
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
    print(f"\n[STOCK API] Calling get_stock_quote with ticker: '{ticker}'")
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
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
    print(f"\n[STOCK API] Calling get_company_overview with ticker: '{ticker}'")
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
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
    print(f"\n[STOCK API] Calling get_earnings with ticker: '{ticker}'")
    params = {
        "function": "EARNINGS",
        "symbol": ticker,
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching earnings for {ticker}: {e}")
        return None


def get_market_movers():
    """Fetches the top 5 US market gainers and losers for the day."""
    print(f"\n[STOCK API] Calling get_market_movers")
    params = {
        "function": "TOP_GAINERS_LOSERS",
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
            return None
        
        return {
            "top_gainers": data.get("top_gainers", [])[:5],
            "top_losers": data.get("top_losers", [])[:5]
        }
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching market movers: {e}")
        return None


def get_market_news():
    """
    NEW: Fetches the latest general financial news articles.
    """
    print(f"\n[STOCK API] Calling get_market_news")
    params = {
        "function": "NEWS_SENTIMENT",
        "topics": "financial_markets", 
        "limit": "10", 
        "apikey": API_KEY,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data:
            print(f"[STOCK API] API Limit Reached: {data['Note']}")
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
