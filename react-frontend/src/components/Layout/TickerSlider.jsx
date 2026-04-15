

import React from 'react';
import '../../styles/TickerSlider.css';

function TickerSlider({ tickerData }) {
  
  
  const getChangeClass = (change) => {
    const changeValue = parseFloat(change);
    return changeValue >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className="ticker-slider-container">
      <div className="ticker-track">
        {}
        {tickerData.map((stock, index) => (
          <div className="ticker-item" key={index}>
            <span className="symbol">{stock.symbol}</span>
            <span className="price">${parseFloat(stock.price).toFixed(2)}</span>
            <span className={`change ${getChangeClass(stock.change)}`}>
              {}
              {parseFloat(stock.change) >= 0 ? '+' : ''}
              {parseFloat(stock.change).toFixed(2)} ({stock.change_percent})
            </span>
          </div>
        ))}
        {}
        {tickerData.map((stock, index) => (
            <div className="ticker-item" key={`duplicate-${index}`}>
                <span className="symbol">{stock.symbol}</span>
                <span className="price">${parseFloat(stock.price).toFixed(2)}</span>
                <span className={`change ${getChangeClass(stock.change)}`}>
                {parseFloat(stock.change) >= 0 ? '+' : ''}
                {parseFloat(stock.change).toFixed(2)} ({stock.change_percent})
                </span>
            </div>
        ))}
      </div>
    </div>
  );
}

export default TickerSlider;
