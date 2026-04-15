# ---------------------------------------------------------------------------
# Ticker lists
# ---------------------------------------------------------------------------
DEFAULT_TICKER_SYMBOLS = ["AAPL", "NVDA", "GOOGL", "MSFT"]
POPULAR_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD"]

# ---------------------------------------------------------------------------
# Disclaimers
# ---------------------------------------------------------------------------
FINANCIAL_DISCLAIMER = (
    "This is not financial advice. Please do your own research "
    "or consult with a professional financial advisor."
)
PREDICTION_DISCLAIMER = (
    "This is a prediction based on available data and not financial advice. "
    "Stock markets are volatile, and past performance is not indicative of future results. "
    "Always do your own research."
)

# ---------------------------------------------------------------------------
# User-facing messages (use .format() for dynamic values)
# ---------------------------------------------------------------------------
MSG_INTERNAL_ERROR = "Sorry, an internal error occurred."
MSG_GENERATION_ERROR = "Sorry, an error occurred while generating the response."
MSG_PREDICTION_ERROR = "Sorry, an error occurred while generating the prediction."
MSG_NO_PRICE_DATA = "Sorry, I couldn't retrieve valid price data for {ticker}."
MSG_NO_PREDICTION_DATA = "Sorry, I couldn't gather enough data for {ticker}."
MSG_NEED_STOCK_NAME = "I need to know which stock you're interested in."
MSG_CLARIFICATION = "I found a few potential matches for '{entity}'."
MSG_QUOTE_FALLBACK = "Based on the latest data for {company}, I couldn't retrieve the information."
MSG_RAG_NOT_PROCESSED = (
    "Sorry, the document for this company has not been processed yet. "
    "Please start by providing the company name first."
)
MSG_UNKNOWN_REQUEST = "I'm not sure how to proceed with that request."
