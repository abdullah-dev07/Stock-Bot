import React from 'react';
import { Newspaper } from 'lucide-react'; 

function NewsPanel({ news }) {
  const articlesToDisplay = news.slice(0, 10);

  return (
    <div id="news-panel">
      <h2 className="panel-header"><Newspaper size={20} /> Latest News</h2>
      <div className="news-list">
        {articlesToDisplay.map((article, index) => (
          <a 
            href={article.url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="news-item" 
            key={index}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="news-item-title">{article.title}</div>
            <div className="news-item-summary">{article.summary}</div>
          </a>
        ))}
      </div>
    </div>
  );
}

export default NewsPanel;