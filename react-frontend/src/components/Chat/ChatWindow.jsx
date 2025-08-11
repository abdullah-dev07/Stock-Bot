// FILE: react-frontend/src/components/Chat/ChatWindow.jsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Message from './Message';
import ChatInput from './ChatInput';
import ChatSidebar from './ChatSidebar';

const API_BASE_URL = 'http://localhost:8000';

function ChatWindow() {
    // --- STATE MANAGEMENT ---
    const [chatSessions, setChatSessions] = useState([]);
    const [activeChatId, setActiveChatId] = useState(null);
    const [history, setHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [user, setUser] = useState(null);
    const [isRagMode, setIsRagMode] = useState(false);
    const [ragCompany, setRagCompany] = useState(null);
    const chatBoxRef = useRef(null);
    const navigate = useNavigate();

    // --- AUTH & USER FETCHING ---
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

    // --- CHAT HISTORY MANAGEMENT ---
    const fetchChatSessions = useCallback(async () => {
        const token = localStorage.getItem('stockbot_token');
        const response = await fetch(`${API_BASE_URL}/chats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            setChatSessions(data);
            if (data.length > 0 && !activeChatId) {
                selectChat(data[0].id);
            } else if (data.length === 0) {
                handleNewChat();
            }
        }
    }, []); // <-- Dependency array is intentionally empty to prevent re-fetching

    useEffect(() => {
        if (user) {
            fetchChatSessions();
        }
    }, [user, fetchChatSessions]);

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
        const token = localStorage.getItem('stockbot_token');
        const response = await fetch(`${API_BASE_URL}/chats/${chatId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        const formattedHistory = data.map(msg => ({ ...msg, id: msg.id || Date.now() }));
        setHistory(formattedHistory);
        setIsLoading(false);
    };

    const handleNewChat = () => {
        setActiveChatId(null);
        setHistory([{ role: 'model', text: "Hello! How can I help you today?", id: Date.now() }]);
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
                if (activeChatId === chatIdToDelete) {
                    handleNewChat();
                }
                fetchChatSessions();
            } else {
                console.error("Failed to delete chat session on the server.");
            }
        } catch (error) {
            console.error("Error deleting chat:", error);
        }
    };

    // --- RAG MODE MANAGEMENT ---
    const startRagAnalysis = () => {
        setIsRagMode(true);
        setRagCompany(null);
        setHistory(prev => [...prev, {
            role: 'model',
            text: "Which company's 10-K report would you like to analyze? For example: Apple, Microsoft, or NVIDIA.",
            id: Date.now()
        }]);
    };

    const exitRagMode = () => {
        setIsRagMode(false);
        setRagCompany(null);
        setHistory(prev => [...prev, {
            role: 'model',
            text: "Exited 10-K analysis mode. You can now ask general questions.",
            id: Date.now()
        }]);
    };

    // --- CORE MESSAGE SENDING LOGIC ---
    const handleSendMessage = async (messageOrPayload) => {
        const isPayloadObject = typeof messageOrPayload === 'object' && messageOrPayload !== null;
        const payload = isPayloadObject ? messageOrPayload : { message: messageOrPayload };
        
        if (!payload.context) {
            const newUserMessage = { role: 'user', text: payload.message, id: Date.now() };
            setHistory(prev => [...prev, newUserMessage]);
        }

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

        if (!currentChatId) {
            const res = await fetch(`${API_BASE_URL}/chats`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ message: payload.message }),
            });
            const data = await res.json();
            currentChatId = data.chat_id;
            setActiveChatId(currentChatId);
            fetchChatSessions();
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
                    const clarificationMessage = { role: 'model', text: data.message, choices: data.choices, original_intent: data.original_intent, id: Date.now() };
                    setHistory(prev => [...prev, clarificationMessage]);
                }
            } else {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let accumulatedText = '';
                const newMessageId = Date.now();
                setHistory(prev => [...prev, { role: 'model', text: '', id: newMessageId }]);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    accumulatedText += decoder.decode(value, { stream: true });
                    setHistory(prev => prev.map(msg => msg.id === newMessageId ? { ...msg, text: accumulatedText } : msg));
                }
            }
        } catch (error) {
            console.error("Chat Error:", error);
            setHistory(prev => [...prev, { role: 'model', text: "Sorry, something went wrong.", id: Date.now() }]);
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
            setHistory(prev => [...prev, { role: 'model', text: "An error occurred during the analysis.", id: Date.now() }]);
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
                    role: 'model', text: data.message, choices: data.choices,
                    original_intent: data.original_intent, id: Date.now()
                };
                setHistory(prev => [...prev, clarificationMessage]);
            } else {
                setRagCompany(data.company_name);
                setHistory(prev => [...prev, { role: 'model', text: data.message, id: Date.now() }]);
            }
        } else {
             setHistory(prev => [...prev, { role: 'model', text: data.message || "An error occurred.", id: Date.now() }]);
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
        const newMessageId = Date.now();
        setHistory(prev => [...prev, { role: 'model', text: '', id: newMessageId }]);
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            accumulatedText += decoder.decode(value, { stream: true });
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
