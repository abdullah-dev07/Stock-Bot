import React, { useState } from 'react';

function ChatInput({ onSendMessage, isRagMode, onStartRag, onExitRag }) {
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim()) {
            onSendMessage(message);
            setMessage('');
        }
    };

    return (
        <div className="chat-input-area">
            <form onSubmit={handleSubmit}>
                {/* It conditionally renders the correct button based on isRagMode */}
                {isRagMode ? (
                    <button type="button" onClick={onExitRag} className="rag-action-btn exit">
                        Exit Analysis
                    </button>
                ) : (
                    <button type="button" onClick={onStartRag} className="rag-action-btn">
                        Analyze 10-K Reports
                    </button>
                )}

                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Ask about stocks..."
                    autoFocus
                />
                <button type="submit" aria-label="Send message">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </form>
        </div>
    );
}

export default ChatInput;
