import requests
from ..config import ALPHA_VANTAGE_API_KEY as API_KEY, ALPHA_VANTAGE_BASE_URL as BASE_URL


def _check_response(data, label):
    """Check for common Alpha Vantage error/rate-limit payloads."""
    if "Note" in data:
        print(f"[STOCK] API Rate Limit for {label}: {data['Note']}")
        return False
    if "Information" in data:
        print(f"[STOCK] API Information for {label}: {data['Information']}")
        return False
    if "Error Message" in data:
        print(f"[STOCK] API Error for {label}: {data['Error Message']}")
        return False
    return True


def fetch(params, label=None):
    """Make an Alpha Vantage API request with built-in guard and error handling.

    Returns the parsed JSON dict on success, or None on any failure.
    """
    if not API_KEY:
        return None
    full_params = {**params, "apikey": API_KEY}
    tag = label or params.get("function", "UNKNOWN")
    try:
        response = requests.get(BASE_URL, params=full_params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not _check_response(data, tag):
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"[STOCK] Error in {tag}: {e}")
        return None
