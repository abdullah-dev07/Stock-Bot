# FILE: backend/firebase_db.py
# PURPOSE: Handles all interactions with the Firestore database for chat history.

from .firebase_init import db
from datetime import datetime, timezone

def get_chat_list(user_id):
    """Fetches a list of all chat sessions for a given user."""
    try:
        chats_ref = db.collection('users').document(user_id).collection('chats').order_by('createdAt', direction='DESCENDING')
        chats = chats_ref.stream()
        chat_list = [{"id": chat.id, **chat.to_dict()} for chat in chats]
        return chat_list
    except Exception as e:
        print(f"Error fetching chat list for user {user_id}: {e}")
        return []

def get_chat_history(user_id, chat_id):
    """Fetches all messages for a specific chat session."""
    try:
        messages_ref = db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages').order_by('timestamp')
        messages = messages_ref.stream()
        history = [{"id": msg.id, **msg.to_dict()} for msg in messages]
        return history
    except Exception as e:
        print(f"Error fetching messages for chat {chat_id}: {e}")
        return []

def create_new_chat(user_id, first_message_text):
    """Creates a new chat session for a user."""
    try:
        chats_ref = db.collection('users').document(user_id).collection('chats')
        new_chat = {
            "title": first_message_text[:30] + "..." if len(first_message_text) > 30 else first_message_text,
            "createdAt": datetime.now(timezone.utc)
        }
        update_time, chat_ref = chats_ref.add(new_chat)
        return chat_ref.id
    except Exception as e:
        print(f"Error creating new chat for user {user_id}: {e}")
        return None

def add_message_to_chat(user_id, chat_id, role, text):
    """Adds a new message to a specific chat session."""
    try:
        message = {
            "role": role,
            "text": text,
            "timestamp": datetime.now(timezone.utc)
        }
        db.collection('users').document(user_id).collection('chats').document(chat_id).collection('messages').add(message)
    except Exception as e:
        print(f"Error adding message to chat {chat_id}: {e}")

