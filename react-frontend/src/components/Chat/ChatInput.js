import React, { useState } from 'react';
import { Send } from 'lucide-react';

function ChatInput({ onSendMessage }) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <div className="chat-input-area">
      <form onSubmit={handleSubmit}>
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask about a stock..." 
          autoComplete="off"
        />
        <button type="submit"><Send color="white" /></button>
      </form>
    </div>
  );
}

export default ChatInput;
