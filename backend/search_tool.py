# FILE: backend/search_tool.py
# PURPOSE: Handles live internet searches using the Google Custom Search API.

import os
import requests
import json

# --- Configuration ---
# These keys are loaded from the .env file
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID") # Custom Search Engine ID

def perform_search(query):
    """
    Performs a Google search and returns a list of snippets.
    Returns None on failure.
    """
    # print(f"GOOGLE API KEY :{GOOGLE_API_KEY}")
    # print(f"GOOGLE CSI ID :{GOOGLE_CSE_ID}")

    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("[SEARCH] ERROR: GOOGLE_API_KEY or GOOGLE_CSE_ID not set in .env file.")
        return None

    print(f"\n[SEARCH] Performing live search for: '{query}'")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query,
        'num': 3  # Request top 5 results
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()

        # Extract relevant snippets from the search results
        snippets = [item.get('snippet', '') for item in search_results.get('items', [])]
        return snippets

    except requests.exceptions.RequestException as e:
        print(f"[SEARCH] Error performing search: {e}")
        return None
    except Exception as e:
        print(f"[SEARCH] An unexpected error occurred: {e}")
        return None
