from .firebase_init import db
from datetime import datetime, timezone


def get_chat_list(user_id):
    """Fetches a list of all chat sessions for a given user."""
    try:
        chats_ref = (
            db.collection('users')
            .document(user_id)
            .collection('chats')
            .order_by('createdAt', direction='DESCENDING')
        )
        chats = chats_ref.stream()
        return [{"id": chat.id, **chat.to_dict()} for chat in chats]
    except Exception as e:
        print(f"Error fetching chat list for user {user_id}: {e}")
        return []


def get_chat_history(user_id, chat_id):
    """Fetches all messages for a specific chat session."""
    try:
        messages_ref = (
            db.collection('users')
            .document(user_id)
            .collection('chats')
            .document(chat_id)
            .collection('messages')
            .order_by('timestamp')
        )
        messages = messages_ref.stream()
        return [{"id": msg.id, **msg.to_dict()} for msg in messages]
    except Exception as e:
        print(f"Error fetching messages for chat {chat_id}: {e}")
        return []


def create_new_chat(user_id, title):
    """Creates a new chat session with a pre-generated title."""
    try:
        chats_ref = (
            db.collection('users')
            .document(user_id)
            .collection('chats')
        )
        new_chat = {
            "title": title,
            "createdAt": datetime.now(timezone.utc),
        }
        _update_time, chat_ref = chats_ref.add(new_chat)
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
            "timestamp": datetime.now(timezone.utc),
        }
        (
            db.collection('users')
            .document(user_id)
            .collection('chats')
            .document(chat_id)
            .collection('messages')
            .add(message)
        )
    except Exception as e:
        print(f"Error adding message to chat {chat_id}: {e}")


def delete_chat(user_id, chat_id):
    """Deletes a specific chat session and all its messages."""
    try:
        chat_ref = (
            db.collection('users')
            .document(user_id)
            .collection('chats')
            .document(chat_id)
        )
        messages_ref = chat_ref.collection('messages')
        for doc in messages_ref.stream():
            doc.reference.delete()
        chat_ref.delete()
        print(f"Chat {chat_id} deleted successfully for user {user_id}.")
        return True
    except Exception as e:
        print(f"Error deleting chat {chat_id} for user {user_id}: {e}")
        return False
