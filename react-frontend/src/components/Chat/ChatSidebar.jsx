import React from 'react';

function ChatSidebar({ sessions, activeChatId, onSelectChat, onNewChat, onDeleteChat }) {
    
    const handleDelete = (e, sessionId) => {
        e.stopPropagation(); // Prevents the chat from being selected when clicking delete
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
                        {/* --- NEW DELETE BUTTON --- */}
                        <button className="delete-chat-btn" onClick={(e) => handleDelete(e, session.id)}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ChatSidebar;
