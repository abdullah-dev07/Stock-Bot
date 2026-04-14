import { useState, useEffect, useCallback, useRef } from 'react';
import { authFetch } from '../utils/apiClient';

export function useChatSessions(user) {
  const [chatSessions, setChatSessions] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const sessionsRef = useRef([]);

  useEffect(() => {
    sessionsRef.current = chatSessions;
  }, [chatSessions]);

  const fetchSessions = useCallback(async () => {
    try {
      const response = await authFetch('/chats');
      if (response.ok) {
        const data = await response.json();
        setChatSessions(data);
        return data;
      }
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
    }
    return [];
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchSessions().then(data => {
      setActiveChatId(prev => {
        if (prev) return prev;
        return data.length > 0 ? data[0].id : null;
      });
    });
  }, [user, fetchSessions]);

  const createChat = useCallback(async (message) => {
    const response = await authFetch('/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error('Failed to create chat');
    const data = await response.json();

    await fetchSessions();
    return { chatId: data.chat_id };
  }, [fetchSessions]);

  const deleteChat = useCallback(async (chatIdToDelete) => {
    const response = await authFetch(`/chats/${chatIdToDelete}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete chat');

    const current = sessionsRef.current;
    const deletedIndex = current.findIndex(s => s.id === chatIdToDelete);
    const updated = current.filter(s => s.id !== chatIdToDelete);
    setChatSessions(updated);

    if (updated.length > 0) {
      return updated[Math.min(deletedIndex, updated.length - 1)].id;
    }
    return null;
  }, []);

  return {
    chatSessions,
    activeChatId,
    setActiveChatId,
    fetchSessions,
    createChat,
    deleteChat,
  };
}
