// FILE: react-frontend/src/components/Chat/ChatWindow.jsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Message from './Message';
import ChatInput from './ChatInput';

const API_BASE_URL = 'http://localhost:8000';

function ChatWindow() {
    const [history, setHistory] = useState([
        { role: 'model', text: "Hello! How can I help you today?", id: Date.now() }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const [user, setUser] = useState(null);
    const chatBoxRef = useRef(null);
    const navigate = useNavigate();

    const [isRagMode, setIsRagMode] = useState(false);
    const [ragCompany, setRagCompany] = useState(null);

    const handleLogout = useCallback(async () => {
        localStorage.removeItem('stockbot_token');
        try {
            await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST' });
        } catch (error) {
            console.error("Logout request failed:", error);
        }
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
                    if (response.ok) {
                        const userData = await response.json();
                        setUser(userData);
                    } else {
                        handleLogout();
                    }
                } catch (error) {
                    console.error("Failed to fetch user data:", error);
                    handleLogout();
                }
            } else {
                navigate('/login');
            }
        };
        fetchUser();
    }, [navigate, handleLogout]);

    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [history]);


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
        const fullPayload = { ...payload, history: history.slice(1) };
        const token = localStorage.getItem('stockbot_token');

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
                        role: 'model', text: data.message, choices: data.choices,
                        original_intent: data.original_intent, id: Date.now()
                    };
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
                    setHistory(prev => prev.map(msg =>
                        msg.id === newMessageId ? { ...msg, text: accumulatedText } : msg
                    ));
                }
            }
        } catch (error) {
            console.error("Chat Error:", error);
            setHistory(prev => [...prev, {
                role: 'model', text: "Sorry, something went wrong. Please try again.", id: Date.now()
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
        <div className="chat-container">
            <header className="chat-header">
                <h1>Your Stock Bot</h1>
                <div className="header-controls">
                    {/* Button is now removed from here */}
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
            {/* --- FIX: Pass the RAG state and functions to ChatInput --- */}
            <ChatInput 
                onSendMessage={handleSendMessage} 
                isRagMode={isRagMode}
                onStartRag={startRagAnalysis}
                onExitRag={exitRagMode}
            />
        </div>
    );
}

export default ChatWindow;
