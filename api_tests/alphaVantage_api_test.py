import requests
import json


# --- Configuration ---
API_KEY = "KLCQOV1OMS6GTGZT"
BASE_URL = "https://www.alphavantage.co/query"

def pretty_print_json(data):
    """Helper function to print JSON data in a readable format."""
    print(json.dumps(data, indent=4))

def test_symbol_search(api_key, keywords="apple"):
    """
    Endpoint 1: Symbol Search (Entity Normalization)
    PURPOSE: Translates a company name into a stock ticker.
    This is Step 3a in your flowchart.
    """
    print(f"--- Testing: Symbol Search for '{keywords}' ---")
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keywords,
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        print("Full API Response:")
        pretty_print_json(data)

        # --- Ticker Extraction Logic ---
        if "bestMatches" in data and data["bestMatches"]:
            best_match = data["bestMatches"][0]
            ticker = best_match.get("1. symbol")
            print(f"\n---> Extracted Ticker: {ticker}")
            return ticker
        else:
            print("\n---> No matches found or unexpected API response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")
        return None


def test_global_quote(api_key, symbol="AAPL"):
    """
    Endpoint 2: Global Quote (Specific Data Lookup)
    PURPOSE: Gets the latest price and trading information for a specific ticker.
    This is for Category 1 questions.
    """
    print(f"\n--- Testing: Global Quote for '{symbol}' ---")
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        pretty_print_json(data)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")


def test_company_overview(api_key, symbol="IBM"):
    """
    Endpoint 3: Company Overview (Analytical Questions)
    PURPOSE: Fetches fundamental data and key metrics for a deeper analysis.
    This is a core part of the "Data-gathering Plan" for Category 2 questions.
    """
    print(f"\n--- Testing: Company Overview for '{symbol}' ---")
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        pretty_print_json(data)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")


def test_news_sentiments(api_key, tickers="IBM"):
    """
    Endpoint 4: News & Sentiments (Analytical Questions)
    PURPOSE: Gathers recent news articles related to a specific stock.
    This is another key part of the "Data-gathering Plan" for Category 2.
    """
    print(f"\n--- Testing: News & Sentiments for '{tickers}' ---")
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": tickers,
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        pretty_print_json(data)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY":
        print("="*50)
        print("ERROR: Please replace 'YOUR_API_KEY' with your actual key.")
        print("You can get a free key from: https://www.alphavantage.co/support/#api-key")
        print("="*50)
    else:
        # Run all the test functions
        test_symbol_search(API_KEY)
        # test_global_quote(API_KEY)
        # test_company_overview(API_KEY)
        # test_news_sentiments(API_KEY)
