"""All prompt templates used by gemini_service."""

from ..constants import PREDICTION_DISCLAIMER, FINANCIAL_DISCLAIMER


def chat_title(message_text: str) -> str:
    return (
        f'Generate a concise title, not more than 5 words, for the following message:\n\n'
        f'Message: "{message_text}"\n\n'
        f'The title should be short, descriptive, and capture the essence of the message.\n\nTitle:'
    )


def conversation_summary(history_text: str) -> str:
    return (
        f"Concisely summarize the key points of the following conversation "
        f"into a single paragraph. This summary will be used as context for an ongoing chat.\n\n"
        f"Conversation:\n{history_text}"
    )


def intent_classification(context_summary: str, history_text: str, user_prompt: str) -> str:
    return f"""You are an intent classifier for a stock-focused assistant. Your goal is to categorize the user's LATEST query into one of the following intents.

INTENT TYPES:
- 'get_specific_data': The user is asking for CURRENT, real-time stock data (price, open, close, volume, etc.) for a single company.
- 'get_qualitative_analysis': The user is asking for an explanation of PAST events, reasoning, or trends.
- 'get_prediction_or_advice': The user is asking for a FUTURE prediction, forecast, opinion, or advice about a stock.
- 'general_knowledge': The user is asking about general financial concepts (e.g., "What is a dividend?")

Return only a JSON object with:
- "intent": one of the four intent values above
- "entity": company name or stock ticker mentioned, or null

{context_summary}

RECENT CONVERSATION:
{history_text}

LAST User Query: "{user_prompt}"

JSON Output:
"""


def prediction_analysis(prediction_data: dict, user_prompt: str) -> str:
    return f"""You are an expert financial analyst. Your task is to provide a stock price prediction based ONLY on the recently fetched technical and fundamental data.

**User's Original Question:** "{user_prompt}"

**Analyze the following data for {prediction_data.get('company_name', 'this company')}:**
- P/E Ratio: {prediction_data.get('pe_ratio', 'N/A')}
- Earnings Per Share (EPS): {prediction_data.get('eps', 'N/A')}
- 12-Month Analyst Target Price: {prediction_data.get('analyst_target_price', 'N/A')}
- Current Stock Price: {prediction_data.get('current_price', 'N/A')}
- Relative Strength Index (RSI): {prediction_data.get('rsi', 'N/A')}
- 50-Day Simple Moving Average (SMA): {prediction_data.get('sma_50', 'N/A')}
- 200-Day Simple Moving Average (SMA): {prediction_data.get('sma_200', 'N/A')}

Provide your analysis in markdown format. Conclude with: "{PREDICTION_DISCLAIMER}"
"""


def grounded_response(summary_section: str, history_text: str, user_prompt: str) -> str:
    return f"""{summary_section}RECENT CONVERSATION:
{history_text}

{user_prompt}

IMPORTANT: If this query asks for any form of financial suggestion or advice, conclude your response with: '{FINANCIAL_DISCLAIMER}'
"""


def quote_response(company: str, quote_json: str) -> str:
    return (
        f"A user asked for the stock price of {company}.\n"
        f'Using the latest market data below, formulate a friendly and clear response starting with, "Based on the latest data,".\n'
        f"Data: {quote_json}"
    )
