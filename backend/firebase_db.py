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
        # Include the document ID in the message object
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
            "title": first_message_text[:35] + "..." if len(first_message_text) > 35 else first_message_text,
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


def delete_chat(user_id, chat_id):
    """Deletes a specific chat session for a given user."""
    try:
        chat_ref = db.collection('users').document(user_id).collection('chats').document(chat_id)
        messages_ref = chat_ref.collection('messages')
        docs = messages_ref.stream()
        for doc in docs:
            doc.reference.delete()
        chat_ref.delete()                                                                               
        print(f"Chat {chat_id} deleted successfully for user {user_id}.")                                                                                                                                                                   
        return True                                                                                                                                                     
    except Exception as e:
        print(f"Error deleting chat {chat_id} for user {user_id}: {e}")
        return False