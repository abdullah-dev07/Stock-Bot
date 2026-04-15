import React from 'react';
import { Rocket } from 'lucide-react';
import '../../styles/IpoPanel.css';

function IpoPanel({ ipos }) {
  // Add safety check for empty or undefined data
  if (!ipos || ipos.length === 0) {
    return (
      <div id="ipo-panel">
        <h2 className="panel-header"><Rocket size={20} /> Upcoming IPOs</h2>
        <div className="ipo-list">
          <p style={{ padding: '1rem', color: '#666', fontSize: '0.9rem' }}>No IPO data available</p>
        </div>
      </div>
    );
  }

  return (
    <div id="ipo-panel">
      <h2 className="panel-header"><Rocket size={20} /> Upcoming IPOs</h2>
      <div className="ipo-list">
        {ipos.map((ipo, index) => (
          <div 
            className="ipo-item" 
            key={ipo.symbol || index}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="ipo-item-header">
              <span className="symbol">{ipo.symbol || 'N/A'}</span>
              <span className="date">{ipo.ipoDate || 'TBD'}</span>
            </div>
            <div className="name">{ipo.name || 'Unknown Company'}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default IpoPanel;
