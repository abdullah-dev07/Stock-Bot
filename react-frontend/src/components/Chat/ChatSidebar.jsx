import React from 'react';

function ChatSidebar({ sessions, activeChatId, onSelectChat, onNewChat }) {
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
                        {session.title}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ChatSidebar;
