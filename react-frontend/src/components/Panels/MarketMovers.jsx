// FILE: react-frontend/src/components/Panels/MarketMovers.js

import React from 'react';
import { TrendingUp } from 'lucide-react';

function MarketMovers({ movers }) {
  // Helper function to create a single list item
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

  return (
    <div>
      <h2 className="panel-header"><TrendingUp size={20} /> Market Movers</h2>
      <div className="movers-list">
        {/* FIX: Use optional chaining (?.) to prevent error if movers or top_gainers is undefined */}
        {movers?.top_gainers?.map(stock => createMoverItem(stock, 'gainer'))}
      </div>
      <div className="movers-list" style={{ marginTop: '1rem' }}>
        {/* FIX: Use optional chaining (?.) here as well */}
        {movers?.top_losers?.map(stock => createMoverItem(stock, 'loser'))}
      </div>
    </div>
  );
}

export default MarketMovers;
