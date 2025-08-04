# FILE: backend/rag_pipeline.py
# PURPOSE: Contains all logic for the Retrieval-Augmented Generation pipeline.

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# This dictionary will act as a simple, temporary cache for our vector stores
# In a real production app, you might use something more robust like Redis
vector_store_cache = {}

def create_vector_store_from_text(document_text, company_name):
    """
    Takes raw text, chunks it, creates embeddings, and stores them in an in-memory vector store.
    """
    print(f"[RAG] Creating vector store for {company_name}...")
    
    # 1. Chunk the document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = text_splitter.split_text(document_text)
    
    # 2. Select embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # 3. Create the vector store using FAISS
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    # 4. Cache the vector store for subsequent questions
    vector_store_cache[company_name] = vector_store
    
    print(f"[RAG] Vector store for {company_name} created and cached.")
    return vector_store

def query_rag_pipeline(company_name, question):
    """
    Queries the cached vector store for a given company to answer a question.
    """
    print(f"[RAG] Querying RAG pipeline for {company_name} with question: '{question}'")
    
    # 1. Check if the vector store is in our cache
    if company_name not in vector_store_cache:
        # This is a fallback, ideally the store should be created by the /initiate endpoint
        return "Sorry, the document for this company has not been processed yet. Please start by providing the company name first."

    vector_store = vector_store_cache[company_name]
    retriever = vector_store.as_retriever()
    
    # 2. Select the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, stream=True)
    
    # 3. Create the prompt template
    template = """
    You are an expert financial analyst. Answer the following question based ONLY on the provided context from the company's 10-K report.
    If the answer is not found in the context, say "I could not find information on that topic in the provided document."

    Context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # 4. Create and run the RAG chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # The chain will stream the response
    return rag_chain.stream(question)
