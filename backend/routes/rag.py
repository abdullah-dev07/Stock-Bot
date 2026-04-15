import os
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..models.schemas import RagInitiateRequest, RagQueryRequest
from ..services.auth_service import get_current_user
from ..services import rag_service, stock_service
from ..config import DATA_DIR

router = APIRouter(tags=["RAG"])


@router.post("/rag/initiate")
async def rag_initiate(payload: RagInitiateRequest, user: dict = Depends(get_current_user)):
    # Currently hardcoded — to be made dynamic later
    ticker = "AMZN"
    actual_name = "Amazon"

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    file_name = f"{actual_name.replace(' ', '_')}_10k.txt"
    file_path = os.path.join(DATA_DIR, file_name)

    document_text = None
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
    else:
        document_text = await asyncio.to_thread(stock_service.get_10k_filing_text, ticker)
        if document_text:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(document_text)

    if not document_text:
        return JSONResponse(
            status_code=500,
            content={"message": f"Sorry, I was unable to retrieve the 10-K report for {actual_name}."},
        )

    await rag_service.create_vector_store_from_text(document_text, actual_name)
    return {
        "message": f"The latest 10-K report for {actual_name} is ready. What would you like to know?",
        "company_name": actual_name,
    }


@router.post("/rag/query")
async def rag_query(payload: RagQueryRequest, user: dict = Depends(get_current_user)):
    generator = rag_service.query_rag_pipeline(payload.company_name, payload.question)
    return StreamingResponse(generator, media_type="text/plain")
