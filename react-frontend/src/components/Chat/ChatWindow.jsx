// FILE: react-frontend/src/components/Chat/ChatWindow.js

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Message from './Message';
import ChatInput from './ChatInput';

// It's good practice to define the base URL as a constant.
const API_BASE_URL = 'http://localhost:8000';

function ChatWindow() {
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
            // Use the API_BASE_URL constant for consistency
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
                    handleLogout(); // Log out on fetch error
                }
            } else {
                navigate('/login'); // Redirect if no token
            }
        };
        fetchUser();
    }, [navigate, handleLogout]);

    // Scrolls the chat box to the bottom whenever the history changes
    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [history]);

    // --- SIMPLIFIED AND UNIFIED MESSAGE HANDLING LOGIC ---
    const handleSendMessage = async (messageOrPayload) => {
        // Determine the payload. It can be a simple string from the input
        // or an object with context from a clarification button.
        const isPayloadObject = typeof messageOrPayload === 'object' && messageOrPayload !== null;
        const payload = isPayloadObject ? messageOrPayload : { message: messageOrPayload };

        // Start loading indicator
        setIsLoading(true);

        // Add the user's message to history ONLY if it's a new message,
        // not a clarification selection (which doesn't need to be echoed).
        if (!payload.context) {
            const newUserMessage = {
                role: 'user',
                text: payload.message,
                id: Date.now()
            };
            setHistory(prev => [...prev, newUserMessage]);
        }

        // We send the entire history (minus the initial greeting) to the backend for context.
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
                        role: 'model',
                        text: data.message,
                        choices: data.choices,
                        original_intent: data.original_intent,
                        id: Date.now()
                    };
                    setHistory(prev => [...prev, clarificationMessage]);
                }
            } else {
                // Handle the text stream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let accumulatedText = '';
                const newMessageId = Date.now();

                // Add a placeholder for the streaming message
                setHistory(prev => [...prev, { role: 'model', text: '', id: newMessageId }]);

                // Process each chunk as it arrives
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    accumulatedText += decoder.decode(value, { stream: true });
                    
                    // Directly update the history with the latest accumulated text
                    setHistory(prev => prev.map(msg =>
                        msg.id === newMessageId
                            ? { ...msg, text: accumulatedText }
                            : msg
                    ));
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
            // Stop loading indicator after everything is done
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
                        // Pass the handler directly. It can handle the payload object.
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
            {/* Pass the handler directly. It can handle the text string. */}
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
}

export default ChatWindow;
