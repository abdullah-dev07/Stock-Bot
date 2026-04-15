from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..models.schemas import RagInitiateRequest, RagQueryRequest
from ..services.auth_service import get_current_user
from .handlers.rag_handler import RagHandler

router = APIRouter(tags=["RAG"])


@router.post("/rag/initiate")
async def rag_initiate(payload: RagInitiateRequest, user: dict = Depends(get_current_user)):
    try:
        result = await RagHandler.initiate(payload.company_name, payload.context)
        return result
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/rag/query")
async def rag_query(payload: RagQueryRequest, user: dict = Depends(get_current_user)):
    generator = RagHandler.query(payload.company_name, payload.question)
    return StreamingResponse(generator, media_type="text/plain")
