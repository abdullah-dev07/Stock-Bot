import React from 'react';

function ChatSidebar({ sessions, activeChatId, onSelectChat, onNewChat, onDeleteChat }) {
    
    const handleDelete = (e, sessionId) => {
        e.stopPropagation(); 
        if (window.confirm('Are you sure you want to delete this chat?')) {
            onDeleteChat(sessionId);
        }
    };

    return (
        <div className="chat-sidebar">
            <button className="new-chat-btn" onClick={onNewChat}>
                + New Chat
            </button>
            <div className="chat-list">
                {sessions.map(session => (
                    <div
                        key={session.id}
                        className={`chat-session-item ${session.id === activeChatId ? 'active' : ''}`}
                        onClick={() => onSelectChat(session.id)}
                    >
                        <span className="chat-session-title">{session.title}</span>
                        {}
                        <button className="delete-chat-btn" onClick={(e) => handleDelete(e, session.id)}>
                            <svg xmlns="http:
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ChatSidebar;
