

import React from 'react';
import { marked } from 'marked';

function Message({ role, text, choices, original_intent, onClarificationSelect }) {
  const isBot = role === 'model';
  
  const createMarkup = () => {
    return { __html: isBot ? marked.parse(text || '') : `<p>${text}</p>` };
  };

  const handleChoiceClick = (choice) => {
      onClarificationSelect({
          message: choice.symbol,
          context: {
              awaiting_clarification: true,
              original_intent: original_intent
          }
      });
  };

  return (
    <div className={`message ${isBot ? 'bot-message' : 'user-message'}`}>
      <div 
        className="message-content"
        dangerouslySetInnerHTML={createMarkup()}
      >
      </div>
      {choices && (
          <div className="clarification-choices">
              {choices.map(choice => (
                  <button key={choice.symbol} className="clarification-btn" onClick={() => handleChoiceClick(choice)}>
                      <strong>{choice.symbol}</strong> - {choice.name}
                  </button>
              ))}
          </div>
      )}
    </div>
  );
}

export default Message;
