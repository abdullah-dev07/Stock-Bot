import React, { useState, useEffect, useRef } from 'react';
import Message from './Message';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';
import { useAuth } from '../../hooks/useAuth';
import { useChatSessions } from '../../hooks/useChatSessions';
import { authFetch } from '../../utils/apiClient';
import { readStreamResponse } from '../../utils/streamReader';
import './ChatWindow.css';

function ChatWindow() {
  const { user, handleLogout } = useAuth();
  const {
    chatSessions, activeChatId, setActiveChatId,
    createChat, deleteChat,
  } = useChatSessions(user);

  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRagMode, setIsRagMode] = useState(false);
  const [ragCompany, setRagCompany] = useState(null);
  const chatBoxRef = useRef(null);

  useEffect(() => {
    if (!activeChatId) {
      setHistory([]);
      return;
    }

    let cancelled = false;
    const loadMessages = async () => {
      setIsLoading(true);
      setIsRagMode(false);
      setRagCompany(null);
      setHistory([]);
      try {
        const response = await authFetch(`/chats/${activeChatId}`);
        if (response.ok && !cancelled) {
          const data = await response.json();
          setHistory(data.map((msg, index) => ({
            role: msg.role || 'model',
            text: msg.text || '',
            id: msg.id || `msg-${activeChatId}-${index}`,
            timestamp: msg.timestamp,
            choices: msg.choices,
            original_intent: msg.original_intent,
          })));
        } else if (!cancelled) {
          setHistory([]);
        }
      } catch {
        if (!cancelled) setHistory([]);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };
    loadMessages();
    return () => { cancelled = true; };
  }, [activeChatId]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [history]);

  const handleNewChat = () => {
    setActiveChatId(null);
    setHistory([]);
    setIsRagMode(false);
    setRagCompany(null);
  };

  const handleDeleteChat = async (chatIdToDelete) => {
    try {
      const nextChatId = await deleteChat(chatIdToDelete);
      if (activeChatId === chatIdToDelete) {
        if (nextChatId) {
          setActiveChatId(nextChatId);
        } else {
          handleNewChat();
        }
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  const startRagAnalysis = () => {
    setIsRagMode(true);
    setRagCompany(null);
    setHistory(prev => [...prev, {
      role: 'model',
      text: "Which company's 10-K report would you like to analyze? For example: Apple, Microsoft, or NVIDIA.",
      id: `rag-start-${Date.now()}`,
    }]);
  };

  const exitRagMode = () => {
    setIsRagMode(false);
    setRagCompany(null);
    setHistory(prev => [...prev, {
      role: 'model',
      text: 'Exited 10-K analysis mode. You can now ask general questions.',
      id: `rag-exit-${Date.now()}`,
    }]);
  };

  const handleSendMessage = async (messageOrPayload) => {
    const isPayloadObject = typeof messageOrPayload === 'object' && messageOrPayload !== null;
    const payload = isPayloadObject ? messageOrPayload : { message: messageOrPayload };

    const intent = payload.context?.original_intent;
    if (isRagMode || intent === 'rag_initiate') {
      await handleRagChat(payload);
    } else {
      await handleNormalChat(payload);
    }
  };

  const handleNormalChat = async (payload) => {
    setIsLoading(true);
    let currentChatId = activeChatId;

    if (!currentChatId) {
      try {
        const result = await createChat(payload.message);
        currentChatId = result.chatId;
        setActiveChatId(currentChatId);
        setHistory([]);
      } catch {
        setIsLoading(false);
        return;
      }
    }

    if (!payload.context?.awaiting_clarification) {
      const userMessage = { role: 'user', text: payload.message, id: `user-${currentChatId}-${Date.now()}` };
      setHistory(prev => {
        const recentDuplicate = prev.some(msg =>
          msg.text === payload.message && msg.role === 'user' &&
          msg.id?.startsWith(`user-${currentChatId}-`)
        );
        return recentDuplicate ? prev : [...prev, userMessage];
      });
    }

    try {
      const response = await authFetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, chat_id: currentChatId }),
      });
      if (!response.ok) throw new Error('Network response was not ok');

      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const data = await response.json();
        if (data.response_type === 'clarification') {
          setHistory(prev => [...prev, {
            role: 'model', text: data.message, choices: data.choices,
            original_intent: data.original_intent, id: `clarification-${Date.now()}`,
          }]);
        }
      } else {
        await readStreamResponse(response, `model-${currentChatId}-${Date.now()}`, setHistory);
      }
    } catch {
      setHistory(prev => [...prev, {
        role: 'model', text: 'Sorry, something went wrong.', id: `error-${Date.now()}`,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRagChat = async (payload) => {
    setIsLoading(true);
    try {
      if (!ragCompany || payload.context?.original_intent === 'rag_initiate') {
        const body = { company_name: payload.message, context: payload.context || {} };
        const response = await authFetch('/rag/initiate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await response.json();
        if (response.ok) {
          if (data.response_type === 'clarification') {
            setHistory(prev => [...prev, {
              role: 'model', text: data.message, choices: data.choices,
              original_intent: data.original_intent, id: `rag-clarification-${Date.now()}`,
            }]);
          } else {
            setRagCompany(data.company_name);
            setHistory(prev => [...prev, {
              role: 'model', text: data.message, id: `rag-init-${Date.now()}`,
            }]);
          }
        } else {
          setHistory(prev => [...prev, {
            role: 'model', text: data.message || 'An error occurred.', id: `rag-error-${Date.now()}`,
          }]);
          exitRagMode();
        }
      } else {
        const response = await authFetch('/rag/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ company_name: ragCompany, question: payload.message }),
        });
        if (!response.ok) throw new Error('RAG query failed');
        await readStreamResponse(response, `rag-response-${Date.now()}`, setHistory);
      }
    } catch {
      setHistory(prev => [...prev, {
        role: 'model', text: 'An error occurred during the analysis.', id: `rag-error-${Date.now()}`,
      }]);
      exitRagMode();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="full-page-chat-wrapper">
      <ChatSidebar
        sessions={chatSessions}
        activeChatId={activeChatId}
        onSelectChat={setActiveChatId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />
      <div className="chat-container">
        <header className="chat-header">
          <h1>Your Stock Bot</h1>
          <div className="header-controls">
            <span>Welcome, {user ? user.email : '...'}</span>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </header>
        <div className="chat-box" ref={chatBoxRef}>
          {history.map((msg) => (
            <Message
              key={msg.id}
              role={msg.role}
              text={msg.text}
              choices={msg.choices}
              original_intent={msg.original_intent}
              onClarificationSelect={handleSendMessage}
            />
          ))}
          {isLoading && (
            <div className="message bot-message">
              <div className="message-content typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
        </div>
        <ChatInput
          onSendMessage={handleSendMessage}
          isRagMode={isRagMode}
          onStartRag={startRagAnalysis}
          onExitRag={exitRagMode}
        />
      </div>
    </div>
  );
}

export default ChatWindow;
