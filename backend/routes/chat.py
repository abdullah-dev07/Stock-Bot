from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from ..models.schemas import NewChatRequest, ChatMessageRequest
from ..services.auth_service import get_current_user
from .handlers.chat_handler import ChatHandler

router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat(payload: ChatMessageRequest, user: dict = Depends(get_current_user)):
    clarification, response_gen = await ChatHandler.send_message(
        user['uid'], payload.chat_id, payload.message, payload.context
    )
    if clarification:
        return JSONResponse(content=clarification)
    return StreamingResponse(response_gen, media_type="text/plain")


@router.post("/chats")
async def create_chat_session(payload: NewChatRequest, user: dict = Depends(get_current_user)):
    chat_id = await ChatHandler.create_session(user['uid'], payload.message)
    return {"chat_id": chat_id}


@router.get("/chats")
async def get_all_chats(user: dict = Depends(get_current_user)):
    return await ChatHandler.list_sessions(user['uid'])


@router.get("/chats/{chat_id}")
async def get_chat_messages(chat_id: str, user: dict = Depends(get_current_user)):
    return await ChatHandler.get_messages(user['uid'], chat_id)


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user: dict = Depends(get_current_user)):
    success = await ChatHandler.delete_session(user['uid'], chat_id)
    if success:
        return {"message": "Chat deleted successfully."}
    raise HTTPException(status_code=404, detail="Chat not found or could not be deleted.")
