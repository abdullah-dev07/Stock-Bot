from pydantic import BaseModel


class NewChatRequest(BaseModel):
    message: str


class ChatMessageRequest(BaseModel):
    chat_id: str
    message: str
    context: dict = {}


class RagInitiateRequest(BaseModel):
    company_name: str
    context: dict = {}


class RagQueryRequest(BaseModel):
    company_name: str
    question: str
