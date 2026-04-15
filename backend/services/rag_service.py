import os
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from ..config import GEMINI_API_KEY

vector_store_cache = {}


def _ensure_configured():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    genai.configure(api_key=GEMINI_API_KEY)


async def create_vector_store_from_text(document_text, company_name):
    """Chunks text, embeds it, and stores in an in-memory FAISS index."""
    print(f"[RAG] Creating vector store for {company_name}...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=100)
    chunks = text_splitter.split_text(document_text)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        task_type="SEMANTIC_SIMILARITY",
    )

    vector_store = await FAISS.afrom_texts(chunks, embedding=embeddings)
    vector_store_cache[company_name] = vector_store
    print(f"[RAG] Vector store for {company_name} created and cached.")
    return vector_store


def is_question_relevant(question):
    """Quick LLM gate — is this a real question or conversational filler?"""
    _ensure_configured()
    model = genai.GenerativeModel('gemini-pro')
    prompt = (
        f'Analyze the user\'s input. Is it a genuine question seeking specific information '
        f'from a financial document? Or is it conversational filler like "thank you", "okay", "hi"?\n\n'
        f'User Input: "{question}"\n\nAnswer with only YES or NO.'
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip().upper() == "YES"
    except Exception as e:
        print(f"[RAG] Relevance check failed: {e}")
        return True


async def query_rag_pipeline(company_name, question):
    """Async generator — queries the cached vector store and streams the answer."""
    if not is_question_relevant(question):
        _ensure_configured()
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Give an appropriate response based on the user's prompt: {question}"
        response = model.generate_content(prompt)
        yield response.text
        return

    if company_name not in vector_store_cache:
        yield "Sorry, the document for this company has not been processed yet. Please start by providing the company name first."
        return

    vector_store = vector_store_cache[company_name]
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})

    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

    template = """
    You are an expert financial analyst. The user is asking about the 10-K report for {company_name}.
    Answer the following question based ONLY on the provided context from the report.
    If the answer is not found in the context, say "I could not find information on that topic in the provided document."

    Context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

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
