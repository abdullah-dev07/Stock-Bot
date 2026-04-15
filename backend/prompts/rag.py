"""All prompt templates used by rag_service."""


def relevance_check(question: str) -> str:
    return (
        f'Analyze the user\'s input. Is it a genuine question seeking specific information '
        f'from a financial document? Or is it conversational filler like "thank you", "okay", "hi"?\n\n'
        f'User Input: "{question}"\n\nAnswer with only YES or NO.'
    )


def small_talk_fallback(question: str) -> str:
    return f"Give an appropriate response based on the user's prompt: {question}"


RAG_CHAIN_TEMPLATE = """You are an expert financial analyst. The user is asking about the 10-K report for {company_name}.
Answer the following question based ONLY on the provided context from the report.
If the answer is not found in the context, say "I could not find information on that topic in the provided document."

Context:
{context}

Question: {question}
"""
