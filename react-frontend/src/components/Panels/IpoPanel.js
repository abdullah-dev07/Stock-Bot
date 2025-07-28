import React from 'react';
import { Rocket } from 'lucide-react'; // Import the icon here

function IpoPanel({ ipos }) {
  return (
    <div id="ipo-panel">
      <h2 className="panel-header"><Rocket size={20} /> Upcoming IPOs</h2>
      <div className="ipo-list">
        {ipos.map((ipo, index) => (
          <div 
            className="ipo-item" 
            key={ipo.symbol}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="ipo-item-header">
              <span className="symbol">{ipo.symbol}</span>
              <span className="date">{ipo.ipoDate}</span>
            </div>
            <div className="name">{ipo.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default IpoPanel;
