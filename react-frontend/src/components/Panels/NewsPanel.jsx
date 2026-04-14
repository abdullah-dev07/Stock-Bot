import React from 'react';
import { Newspaper } from 'lucide-react';
import './NewsPanel.css';

function NewsPanel({ news }) {
  const hasNews = news && news.length > 0;
  const articlesToDisplay = hasNews ? news.slice(0, 10) : [];

  return (
    <div id="news-panel">
      <h2 className="panel-header"><Newspaper size={20} /> Latest News</h2>
      <div className="news-list">
        {hasNews ? (
          articlesToDisplay.map((article, index) => (
            <a 
              href={article.url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="news-item" 
              key={index}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="news-item-title">{article.title}</div>
              <div className="news-item-summary">{article.summary || article.source || ''}</div>
            </a>
          ))
        ) : (
          <p style={{ padding: '0.5rem', color: '#666', fontSize: '0.9rem' }}>No news available</p>
        )}
      </div>
    </div>
  );
}

export default NewsPanel;