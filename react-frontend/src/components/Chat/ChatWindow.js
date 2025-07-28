// FILE: react-frontend/src/components/Chat/ChatWindow.js

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Message from './Message';
import ChatInput from './ChatInput'; // Make sure this path is correct

const API_BASE_URL = 'http://localhost:8000';

function ChatWindow() {
    const streamStateRef = useRef({ text: '', id: null });
    const [history, setHistory] = useState([
        { role: 'model', text: "Hello! How can I help you today?", id: Date.now() }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const [user, setUser] = useState(null);
    const chatBoxRef = useRef(null);
    const navigate = useNavigate();

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

    // Updated function with correct loading logic
    const handleSendMessage = async (messageText) => {
        // 1. Turn loading ON at the very beginning.
        setIsLoading(true);

        const payload = { message: messageText, history: history.slice(1) }; // Pass previous history
        
        const newUserMessage = {
            role: 'user',
            text: messageText,
            id: Date.now()
        };
        setHistory(prev => [...prev, newUserMessage]);

        const token = localStorage.getItem('stockbot_token');

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);

            const responseContentType = response.headers.get("content-type");
            if (responseContentType && responseContentType.includes("application/json")) {
                const data = await response.json();
                if (data.response_type === 'clarification') {
                    const clarificationMessage = {
                        role: 'model',
                        text: data.message,
                        choices: data.choices,
                        original_intent: data.original_intent,
                        id: Date.now()
                    };
                    setHistory(prev => [...prev, clarificationMessage]);
                }
            } else { // Handle the text stream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                const newMessageId = Date.now();
                streamStateRef.current = { text: '', id: newMessageId };

                // Add placeholder for the bot's response
                setHistory(prev => [...prev, {
                    role: 'model',
                    text: '',
                    id: newMessageId
                }]);

                const updateStreamingMessage = () => {
                    setHistory(prev => {
                        const newHistory = [...prev];
                        const lastMessage = newHistory[newHistory.length - 1];
                        if (lastMessage && lastMessage.id === streamStateRef.current.id) {
                            lastMessage.text = streamStateRef.current.text;
                        }
                        return newHistory;
                    });
                };

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    streamStateRef.current.text += decoder.decode(value, { stream: true });
                    updateStreamingMessage();
                }
            }
        } catch (error) {
            console.error("Chat Error:", error);
            setHistory(prev => [...prev, {
                role: 'model',
                text: "Sorry, something went wrong. Please try again.",
                id: Date.now()
            }]);
        } finally {
            // 2. Turn loading OFF at the very end, after everything is finished.
            setIsLoading(false);
        }
    };

    return (
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
                        onClarificationSelect={(clarificationPayload) => handleSendMessage(clarificationPayload.message)}
                    />
                ))}
                {/* This loading indicator will now correctly display for the whole duration */}
                {isLoading && (
                    <div className="message bot-message">
                        <div className="message-content typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
            </div>
            {/* The ChatInput component sends only the message text */}
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
}

export default ChatWindow;