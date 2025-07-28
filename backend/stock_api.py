# FILE: backend/stock_api.py
# PURPOSE: Handles all communication with the Alpha Vantage API.

import os
import requests
import csv
from dotenv import load_dotenv
import io


load_dotenv()


API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

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
        return [] # Successful search, but no matches found
    except requests.exceptions.RequestException as e:
        print(f"[STOCK API] Network/HTTP Error fetching ticker for {keywords}: {e}")
        return None # Indicates a connection failure



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
        
        # This endpoint returns CSV data, so we need to parse it
        ipo_data = []
        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file)
        for row in reader:
            ipo_data.append(row)
            
        return ipo_data[:10] # Return the top 10 upcoming IPOs
        
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
        "topics": "financial_markets", # Fetch general market news
        "limit": "10", # Get the top 10 articles
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
