from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from ..config import GEMINI_API_KEY, GEMINI_PRO_MODEL, GEMINI_EMBEDDING_MODEL
from ..utils.gemini import get_model
from ..prompts import rag as prompts
from ..constants import MSG_RAG_NOT_PROCESSED

vector_store_cache = {}


async def create_vector_store_from_text(document_text, company_name):
    """Chunks text, embeds it, and stores in an in-memory FAISS index."""
    print(f"[RAG] Creating vector store for {company_name}...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=100)
    chunks = text_splitter.split_text(document_text)

    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
        task_type="SEMANTIC_SIMILARITY",
    )

    vector_store = await FAISS.afrom_texts(chunks, embedding=embeddings)
    vector_store_cache[company_name] = vector_store
    print(f"[RAG] Vector store for {company_name} created and cached.")
    return vector_store


def is_question_relevant(question):
    """Quick LLM gate — is this a real question or conversational filler?"""
    model = get_model(GEMINI_PRO_MODEL)
    try:
        response = model.generate_content(prompts.relevance_check(question))
        return response.text.strip().upper() == "YES"
    except Exception as e:
        print(f"[RAG] Relevance check failed: {e}")
        return True


async def query_rag_pipeline(company_name, question):
    """Async generator — queries the cached vector store and streams the answer."""
    if not is_question_relevant(question):
        model = get_model(GEMINI_PRO_MODEL)
        response = model.generate_content(prompts.small_talk_fallback(question))
        yield response.text
        return

    if company_name not in vector_store_cache:
        yield MSG_RAG_NOT_PROCESSED
        return

    vector_store = vector_store_cache[company_name]
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})

    llm = ChatGoogleGenerativeAI(model=GEMINI_PRO_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.3)
    prompt = ChatPromptTemplate.from_template(prompts.RAG_CHAIN_TEMPLATE)

    rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
            "company_name": lambda x: company_name,
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    async for chunk in rag_chain.astream(question):
        yield chunk
