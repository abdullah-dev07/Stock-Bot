

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Message from './Message';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';

import API_BASE_URL from '../../config';

function ChatWindow() {
    
    const [chatSessions, setChatSessions] = useState([]);
    const [activeChatId, setActiveChatId] = useState(null);
    const [history, setHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [user, setUser] = useState(null);
    const [isRagMode, setIsRagMode] = useState(false);
    const [ragCompany, setRagCompany] = useState(null);
    const chatBoxRef = useRef(null);
    const navigate = useNavigate();

    
    const handleLogout = useCallback(async () => {
        localStorage.removeItem('stockbot_token');
        navigate('/login');
    }, [navigate]);

    useEffect(() => {
        const fetchUser = async () => {
            const token = localStorage.getItem('stockbot_token');
            if (token) {
                try {
                    const response = await fetch(`${API_BASE_URL}/auth/users/me`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) setUser(await response.json());
                    else handleLogout();
                } catch (error) { handleLogout(); }
            } else { navigate('/login'); }
        };
        fetchUser();
    }, [navigate, handleLogout]);

    
    const fetchChatSessions = useCallback(async () => {
        const token = localStorage.getItem('stockbot_token');
        if (!token) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/chats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setChatSessions(data);
                // Only auto-select if no active chat is set and we have chats
                if (data.length > 0 && !activeChatId) {
                    // Select the most recent chat (first in the list)
                    await selectChat(data[0].id);
                } else if (data.length === 0 && !activeChatId) {
                    // Start with empty new chat
                    handleNewChat();
                }
            }
        } catch (error) {
            console.error('Error fetching chat sessions:', error);
        }
    }, []); // Remove activeChatId dependency to prevent loops 

    useEffect(() => {
        if (user) {
            fetchChatSessions();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user]); // Only run when user changes

    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [history]);

    const selectChat = async (chatId) => {
        if (activeChatId === chatId) return;
        setIsLoading(true);
        setActiveChatId(chatId);
        setIsRagMode(false);
        setRagCompany(null);
        
        // Clear current history immediately to prevent mixing
        setHistory([]);
        
        const token = localStorage.getItem('stockbot_token');
        try {
            const response = await fetch(`${API_BASE_URL}/chats/${chatId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                // Format history with proper IDs and ensure proper structure
                const formattedHistory = data.map((msg, index) => ({
                    role: msg.role || 'model',
                    text: msg.text || '',
                    id: msg.id || `msg-${chatId}-${index}`,
                    timestamp: msg.timestamp,
                    choices: msg.choices,
                    original_intent: msg.original_intent
                }));
                // Completely replace history (don't merge)
                setHistory(formattedHistory);
            } else {
                console.error('Failed to load chat history');
                setHistory([]);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            setHistory([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        // Clear active chat and reset state completely
        setActiveChatId(null);
        // Start with empty history - welcome message will be shown when first message is sent
        setHistory([]);
        setIsRagMode(false);
        setRagCompany(null);
    };

    const handleDeleteChat = async (chatIdToDelete) => {
        const token = localStorage.getItem('stockbot_token');
        try {
            const response = await fetch(`${API_BASE_URL}/chats/${chatIdToDelete}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const currentSessions = [...chatSessions];
                const deletedIndex = currentSessions.findIndex(s => s.id === chatIdToDelete);

                const updatedSessions = currentSessions.filter(s => s.id !== chatIdToDelete);
                setChatSessions(updatedSessions);

                if (activeChatId === chatIdToDelete) {
                    if (updatedSessions.length > 0) {
                        const nextIndex = Math.min(deletedIndex, updatedSessions.length - 1);
                        selectChat(updatedSessions[nextIndex].id);
                    } else {
                        handleNewChat();
                    }
                }
            } else {
                console.error("Failed to delete chat session on the server.");
            }
        } catch (error) {
            console.error("Error deleting chat:", error);
        }
    };
    const startRagAnalysis = () => {
        setIsRagMode(true);
        setRagCompany(null);
        // Add RAG mode message to current chat history
        setHistory(prev => [...prev, {
            role: 'model',
            text: "Which company's 10-K report would you like to analyze? For example: Apple, Microsoft, or NVIDIA.",
            id: `rag-start-${Date.now()}`
        }]);
    };

    const exitRagMode = () => {
        setIsRagMode(false);
        setRagCompany(null);
        // Add exit message to current chat history
        setHistory(prev => [...prev, {
            role: 'model',
            text: "Exited 10-K analysis mode. You can now ask general questions.",
            id: `rag-exit-${Date.now()}`
        }]);
    };

    
    const handleSendMessage = async (messageOrPayload) => {
        const isPayloadObject = typeof messageOrPayload === 'object' && messageOrPayload !== null;
        const payload = isPayloadObject ? messageOrPayload : { message: messageOrPayload };

        // Don't add user message here - let handleNormalChat or handleRagChat handle it
        // This prevents duplicate messages when switching contexts

        const intent = payload.context?.original_intent;
        if (isRagMode || intent === 'rag_initiate') {
            await handleRagChat(payload);
        } else {
            await handleNormalChat(payload);
        }
    };

    const handleNormalChat = async (payload) => {
        setIsLoading(true);
        const token = localStorage.getItem('stockbot_token');
        let currentChatId = activeChatId;

        // Create new chat if needed
        if (!currentChatId) {
            try {
                const res = await fetch(`${API_BASE_URL}/chats`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ message: payload.message }),
                });
                if (!res.ok) throw new Error('Failed to create chat');
                
                const data = await res.json();
                currentChatId = data.chat_id;
                
                // Update active chat and add to sessions list
                setActiveChatId(currentChatId);
                
                // Fetch updated chat list to get the new chat with title
                const chatsRes = await fetch(`${API_BASE_URL}/chats`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (chatsRes.ok) {
                    const chatsData = await chatsRes.json();
                    setChatSessions(chatsData);
                }
                
                // Clear history and start fresh for new chat
                setHistory([]);
            } catch (error) {
                console.error("Error creating new chat:", error);
                setIsLoading(false);
                return;
            }
        }

        // Add user message to history (only if not already added)
        if (!payload.context?.awaiting_clarification) {
            const userMessage = { role: 'user', text: payload.message, id: `user-${currentChatId}-${Date.now()}` };
            setHistory(prev => {
                // Prevent duplicates - check if same message was just added (within last 2 seconds)
                const recentDuplicate = prev.some(msg => 
                    msg.text === payload.message && 
                    msg.role === 'user' && 
                    msg.id && msg.id.startsWith(`user-${currentChatId}-`)
                );
                if (recentDuplicate) {
                    return prev;
                }
                return [...prev, userMessage];
            });
        }

        const fullPayload = { ...payload, chat_id: currentChatId };

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(fullPayload),
            });
            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (data.response_type === 'clarification') {
                    const clarificationMessage = { 
                        role: 'model', 
                        text: data.message, 
                        choices: data.choices, 
                        original_intent: data.original_intent, 
                        id: `clarification-${Date.now()}` 
                    };
                    setHistory(prev => [...prev, clarificationMessage]);
                }
            } else {
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let accumulatedText = '';
                const newMessageId = `model-${currentChatId}-${Date.now()}`;
                
                // Add placeholder for streaming message
                setHistory(prev => [...prev, { role: 'model', text: '', id: newMessageId }]);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    accumulatedText += decoder.decode(value, { stream: true });
                    // Update only the specific message being streamed
                    setHistory(prev => prev.map(msg => 
                        msg.id === newMessageId ? { ...msg, text: accumulatedText } : msg
                    ));
                }
            }
        } catch (error) {
            console.error("Chat Error:", error);
            setHistory(prev => [...prev, { 
                role: 'model', 
                text: "Sorry, something went wrong.", 
                id: `error-${Date.now()}` 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRagChat = async (payload) => {
        setIsLoading(true);
        try {
            if (!ragCompany || payload.context?.original_intent === 'rag_initiate') {
                await fetchAndProcessRagDocument(payload);
            } else {
                await askRagQuestion(payload.message);
            }
        } catch (error) {
            console.error("RAG Chat Error:", error);
            setHistory(prev => [...prev, { 
                role: 'model', 
                text: "An error occurred during the analysis.", 
                id: `rag-error-${Date.now()}` 
            }]);
            exitRagMode();
        } finally {
            setIsLoading(false);
        }
    };

    const fetchAndProcessRagDocument = async (payload) => {
        const token = localStorage.getItem('stockbot_token');
        const body = {
            company_name: payload.message,
            context: payload.context || {}
        };
        const response = await fetch(`${API_BASE_URL}/rag/initiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(body),
        });
        const data = await response.json();
        if (response.ok) {
            if (data.response_type === 'clarification') {
                const clarificationMessage = {
                    role: 'model', 
                    text: data.message, 
                    choices: data.choices,
                    original_intent: data.original_intent, 
                    id: `rag-clarification-${Date.now()}`
                };
                setHistory(prev => [...prev, clarificationMessage]);
            } else {
                setRagCompany(data.company_name);
                setHistory(prev => [...prev, { 
                    role: 'model', 
                    text: data.message, 
                    id: `rag-init-${Date.now()}` 
                }]);
            }
        } else {
            setHistory(prev => [...prev, { 
                role: 'model', 
                text: data.message || "An error occurred.", 
                id: `rag-error-${Date.now()}` 
            }]);
            exitRagMode();
        }
    };

    const askRagQuestion = async (question) => {
        const token = localStorage.getItem('stockbot_token');
        const response = await fetch(`${API_BASE_URL}/rag/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ company_name: ragCompany, question: question }),
        });
        if (!response.ok) throw new Error(`RAG query failed: ${response.statusText}`);
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = '';
        const newMessageId = `rag-response-${Date.now()}`;
        
        // Add placeholder for streaming message
        setHistory(prev => [...prev, { role: 'model', text: '', id: newMessageId }]);
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            accumulatedText += decoder.decode(value, { stream: true });
            // Update only the specific message being streamed
            setHistory(prev => prev.map(msg =>
                msg.id === newMessageId ? { ...msg, text: accumulatedText } : msg
            ));
        }
    };

    return (
        <div className="full-page-chat-wrapper">
            <ChatSidebar
                sessions={chatSessions}
                activeChatId={activeChatId}
                onSelectChat={selectChat}
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
