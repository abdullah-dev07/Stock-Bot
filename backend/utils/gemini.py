import google.generativeai as genai
from ..config import GEMINI_API_KEY

_configured = False


def configure():
    """Configure the Gemini SDK once. Safe to call multiple times."""
    global _configured
    if _configured:
        return
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    genai.configure(api_key=GEMINI_API_KEY)
    _configured = True


def get_model(name=None):
    """Return a configured GenerativeModel instance."""
    from ..config import GEMINI_FLASH_MODEL
    configure()
    return genai.GenerativeModel(name or GEMINI_FLASH_MODEL)


def format_history(history, max_recent=4):
    """Split history into (older, recent_text) for context compression.

    Returns:
        older: list of older messages (for summarisation), empty if history is short
        recent_text: formatted string of the recent messages
    """
    if len(history) > max_recent:
        older = history[:-max_recent]
        recent = history[-max_recent:]
    else:
        older = []
        recent = history
    recent_text = "\n".join(f"{msg['role']}: {msg['text']}" for msg in recent)
    return older, recent_text
