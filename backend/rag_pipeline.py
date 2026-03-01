from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
import os

# Lazy initialization - configure API key when first needed
def _ensure_configured():
    """Ensure genai is configured with API key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[RAG] ERROR: GEMINI_API_KEY not found in environment variables!")
        raise ValueError("GEMINI_API_KEY environment variable is required. Please set it in backend/.env file.")
    # Configure - safe to call multiple times
    genai.configure(api_key=api_key)


vector_store_cache = {}


async def create_vector_store_from_text(document_text, company_name):
    """
    Takes raw text, chunks it, creates embeddings, and stores them in an in-memory vector store.
    """
    print(f"[RAG] Creating vector store for {company_name}...")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=100)
    chunks = text_splitter.split_text(document_text)
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        task_type="SEMANTIC_SIMILARITY"
    )
    
    
    vector_store = await FAISS.afrom_texts(chunks, embedding=embeddings)
    
    vector_store_cache[company_name] = vector_store
    
    print(f"[RAG] Vector store for {company_name} created and cached.")
    return vector_store


def is_question_relevant(question):
    """
    Uses a simple LLM call to check if a user's input is a real question
    or just conversational filler. This remains a synchronous function as it's a short, blocking call.
    """
    print(f"[RAG] Checking relevance of question: '{question}'")
    _ensure_configured()
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Analyze the user's input. Is it a genuine question or command seeking specific information from a financial document? Or is it a simple conversational phrase like "thank you", "okay", "hi", or "sounds good"?

    User Input: "{question}"

    Answer with only the word YES or NO.
    """
    
    try:
        response = model.generate_content(prompt)
        answer = response.text.strip().upper()
        print(f"[RAG] Relevance check response: {answer}")
        return answer == "YES"
    except Exception as e:
        print(f"[RAG] Relevance check failed: {e}")
        return True 

async def query_rag_pipeline(company_name, question):
    """
    Queries the cached vector store for a given company to answer a question.
    """
    print(f"[RAG] Querying RAG pipeline for {company_name} with question: '{question}'")
    
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
    retriever = vector_store.as_retriever(search_kwargs={"k":6})
    
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
            "company_name": lambda x: company_name 
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    async for chunk in rag_chain.astream(question):
        yield chunk
