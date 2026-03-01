

import React from 'react';
import { TrendingUp } from 'lucide-react';

function MarketMovers({ movers }) {
  
  const createMoverItem = (stock, type) => {
    const changePercent = parseFloat(stock.change_percentage.replace('%', '')).toFixed(2);
    const isPositive = type === 'gainer';

    return (
      <div className={`mover-item ${type}`} key={stock.ticker}>
        <div className="mover-item-header">
          <span className="symbol">{stock.ticker}</span>
          <span className="price">${parseFloat(stock.price).toFixed(2)}</span>
        </div>
        <div className="mover-item-details">
          <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? '+' : ''}{stock.change_amount}
          </span>
          <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? '+' : ''}{changePercent}%
          </span>
        </div>
      </div>
    );
  };

  // Safety check for empty data
  const hasGainers = movers?.top_gainers && movers.top_gainers.length > 0;
  const hasLosers = movers?.top_losers && movers.top_losers.length > 0;

  return (
    <div>
      <h2 className="panel-header"><TrendingUp size={20} /> Market Movers</h2>
      <div className="movers-list">
        {hasGainers ? (
          movers.top_gainers.map(stock => createMoverItem(stock, 'gainer'))
        ) : (
          <p style={{ padding: '0.5rem', color: '#666', fontSize: '0.9rem' }}>No gainers data</p>
        )}
      </div>
      <div className="movers-list" style={{ marginTop: '1rem' }}>
        {hasLosers ? (
          movers.top_losers.map(stock => createMoverItem(stock, 'loser'))
        ) : (
          <p style={{ padding: '0.5rem', color: '#666', fontSize: '0.9rem' }}>No losers data</p>
        )}
      </div>
    </div>
  );
}

export default MarketMovers;
