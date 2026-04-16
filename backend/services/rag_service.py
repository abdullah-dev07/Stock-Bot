import asyncio

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from google.api_core.exceptions import ServiceUnavailable, ResourceExhausted

from ..config import GEMINI_API_KEY, GEMINI_FLASH_MODEL, EMBEDDING_MODEL
from ..utils.gemini import get_model
from ..prompts import rag as prompts
from ..constants import MSG_RAG_NOT_PROCESSED

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]

vector_store_cache = {}


async def create_vector_store_from_text(document_text, company_name):
    """Chunks text, embeds it, and stores in an in-memory FAISS index."""
    print(f"[RAG] Creating vector store for {company_name}...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=100)
    chunks = text_splitter.split_text(document_text)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vector_store = await FAISS.afrom_texts(chunks, embedding=embeddings)
    vector_store_cache[company_name] = vector_store
    print(f"[RAG] Vector store for {company_name} created and cached.")
    return vector_store


def is_question_relevant(question):
    """Quick LLM gate — is this a real question or conversational filler?"""
    model = get_model(GEMINI_FLASH_MODEL)
    try:
        response = model.generate_content(prompts.relevance_check(question))
        return response.text.strip().upper() == "YES"
    except Exception as e:
        print(f"[RAG] Relevance check failed: {e}")
        return True


def _build_rag_chain(vector_store, company_name):
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})
    llm = ChatGoogleGenerativeAI(model=GEMINI_FLASH_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.3)
    prompt = ChatPromptTemplate.from_template(prompts.RAG_CHAIN_TEMPLATE)

    return (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
            "company_name": lambda x: company_name,
        }
        | prompt
        | llm
        | StrOutputParser()
    )


async def query_rag_pipeline(company_name, question):
    """Async generator — queries the cached vector store and streams the answer.
    Retries on transient Gemini 503/429 errors."""
    if not is_question_relevant(question):
        model = get_model(GEMINI_FLASH_MODEL)
        response = model.generate_content(prompts.small_talk_fallback(question))
        yield response.text
        return

    if company_name not in vector_store_cache:
        yield MSG_RAG_NOT_PROCESSED
        return

    rag_chain = _build_rag_chain(vector_store_cache[company_name], company_name)

    for attempt in range(MAX_RETRIES):
        try:
            async for chunk in rag_chain.astream(question):
                yield chunk
            return
        except (ServiceUnavailable, ResourceExhausted) as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"[RAG] Gemini 503/429, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
            else:
                print(f"[RAG] Gemini still unavailable after {MAX_RETRIES} attempts: {e}")
                yield "The AI model is currently experiencing high demand. Please try your question again in a moment."
