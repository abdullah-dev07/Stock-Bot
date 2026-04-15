import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from ..models.schemas import NewChatRequest, ChatMessageRequest
from ..services.auth_service import get_current_user
from ..services import chat_service, gemini_service
from ..db import chat_repository

router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat(payload: ChatMessageRequest, user: dict = Depends(get_current_user)):
    user_id = user['uid']
    chat_id = payload.chat_id

    history = await asyncio.to_thread(chat_repository.get_chat_history, user_id, chat_id)
    await asyncio.to_thread(
        chat_repository.add_message_to_chat, user_id, chat_id, "user", payload.message
    )

    clarification = await chat_service.check_clarification_needed(
        payload.message, history, payload.context
    )
    if clarification:
        return JSONResponse(content=clarification)

    response_gen = chat_service.build_chat_response(
        payload.message, payload.context, history, user_id, chat_id
    )
    return StreamingResponse(response_gen, media_type="text/plain")


@router.post("/chats")
async def create_chat_session(payload: NewChatRequest, user: dict = Depends(get_current_user)):
    user_id = user['uid']
    title = await asyncio.to_thread(gemini_service.generate_chat_title, payload.message)
    chat_id = await asyncio.to_thread(chat_repository.create_new_chat, user_id, title)
    return {"chat_id": chat_id}


@router.get("/chats")
async def get_all_chats(user: dict = Depends(get_current_user)):
    user_id = user['uid']
    return await asyncio.to_thread(chat_repository.get_chat_list, user_id)


@router.get("/chats/{chat_id}")
async def get_chat_messages(chat_id: str, user: dict = Depends(get_current_user)):
    user_id = user['uid']
    return await asyncio.to_thread(chat_repository.get_chat_history, user_id, chat_id)


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user: dict = Depends(get_current_user)):
    user_id = user['uid']
    success = await asyncio.to_thread(chat_repository.delete_chat, user_id, chat_id)
    if success:
        return {"message": "Chat deleted successfully."}
    raise HTTPException(status_code=404, detail="Chat not found or could not be deleted.")
