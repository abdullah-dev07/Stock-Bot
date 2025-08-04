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

    // --- NEW STATE FOR RAG MODE ---
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

    // --- NEW FUNCTION TO START RAG MODE ---
    const startRagAnalysis = () => {
        setIsRagMode(true);
        setRagCompany(null); // Reset company on new analysis
        setHistory(prev => [...prev, {
            role: 'model',
            text: "Which company's 10-K report would you like to analyze? For example: Apple, Microsoft, or NVIDIA.",
            id: Date.now()
        }]);
    };

    // --- REFACTORED MESSAGE HANDLING LOGIC ---
    const handleSendMessage = async (messageText) => {
        setIsLoading(true);

        const newUserMessage = { role: 'user', text: messageText, id: Date.now() };
        setHistory(prev => [...prev, newUserMessage]);

        // --- LOGIC TO HANDLE EITHER RAG OR NORMAL CHAT ---
        if (isRagMode && !ragCompany) {
            // This is the first message in RAG mode: the company name
            await fetchAndProcessRagDocument(messageText);
        } else if (isRagMode && ragCompany) {
            // We are already in a RAG session, so this is a follow-up question
            await askRagQuestion(messageText);
        } else {
            // Normal chat logic
            await handleNormalChat({ message: messageText });
        }

        setIsLoading(false);
    };

    // --- Handles normal chat and predictions ---
    const handleNormalChat = async (payload) => {
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
        }
    };

    // --- NEW FUNCTIONS FOR RAG WORKFLOW ---
    const fetchAndProcessRagDocument = async (companyName) => {
        const token = localStorage.getItem('stockbot_token');
        try {
            const response = await fetch(`${API_BASE_URL}/rag/initiate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ company_name: companyName }),
            });
            const data = await response.json();
            if (response.ok) {
                setRagCompany(companyName); // Lock in the company name for this session
            }
            setHistory(prev => [...prev, { role: 'model', text: data.message, id: Date.now() }]);
        } catch (error) {
            console.error("RAG Initiate Error:", error);
            setHistory(prev => [...prev, { role: 'model', text: "Sorry, I couldn't process that document.", id: Date.now() }]);
        }
    };

    const askRagQuestion = async (question) => {
        const token = localStorage.getItem('stockbot_token');
        try {
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
        } catch (error) {
            console.error("RAG Query Error:", error);
            setHistory(prev => [...prev, { role: 'model', text: "Sorry, I encountered an error answering that question.", id: Date.now() }]);
        }
    };

    return (
        <div className="chat-container">
            <header className="chat-header">
                <h1>Your Stock Bot</h1>
                <div className="header-controls">
                    <button onClick={startRagAnalysis} className="rag-btn">Analyze 10-K Report</button>
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
                        onClarificationSelect={handleNormalChat} // Clarifications always go to normal chat
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
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
}

export default ChatWindow;
