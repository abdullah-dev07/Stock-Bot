import asyncio

from ...services import chat_service, gemini_service
from ...db import chat_repository


class ChatHandler:

    @staticmethod
    async def send_message(user_id: str, chat_id: str, message: str, context: dict):
        """Persist the user message, check for clarification, and build the response.

        Returns:
            (clarification_dict, None) if disambiguation is needed, or
            (None, async_generator) for the streamed model reply.
        """
        history = await asyncio.to_thread(
            chat_repository.get_chat_history, user_id, chat_id
        )
        await asyncio.to_thread(
            chat_repository.add_message_to_chat, user_id, chat_id, "user", message
        )
        clarification = await chat_service.check_clarification_needed(
            message, history, context
        )
        if clarification:
            return clarification, None
        response_gen = chat_service.build_chat_response(
            message, context, history, user_id, chat_id
        )
        return None, response_gen

    @staticmethod
    async def create_session(user_id: str, first_message: str) -> str:
        """Generate a title and create a new chat session. Returns chat_id."""
        title = await asyncio.to_thread(
            gemini_service.generate_chat_title, first_message
        )
        chat_id = await asyncio.to_thread(
            chat_repository.create_new_chat, user_id, title
        )
        return chat_id

    @staticmethod
    async def list_sessions(user_id: str) -> list:
        return await asyncio.to_thread(chat_repository.get_chat_list, user_id)

    @staticmethod
    async def get_messages(user_id: str, chat_id: str) -> list:
        return await asyncio.to_thread(
            chat_repository.get_chat_history, user_id, chat_id
        )

    @staticmethod
    async def delete_session(user_id: str, chat_id: str) -> bool:
        return await asyncio.to_thread(
            chat_repository.delete_chat, user_id, chat_id
        )
