// FILE: react-frontend/src/components/Layout/TickerSlider.js

import React from 'react';

// This is a "presentational" component. Its only job is to receive data (props)
// and display it. It doesn't have its own state.
function TickerSlider({ tickerData }) {
  
  // Helper to determine the class for styling (green for positive, red for negative)
  const getChangeClass = (change) => {
    const changeValue = parseFloat(change);
    return changeValue >= 0 ? 'positive' : 'negative';
  };

  return (
    <div className="ticker-slider-container">
      <div className="ticker-track">
        {/* We map over the tickerData array passed down from App.js */}
        {tickerData.map((stock, index) => (
          <div className="ticker-item" key={index}>
            <span className="symbol">{stock.symbol}</span>
            <span className="price">${parseFloat(stock.price).toFixed(2)}</span>
            <span className={`change ${getChangeClass(stock.change)}`}>
              {/* Add a '+' sign if the change is positive */}
              {parseFloat(stock.change) >= 0 ? '+' : ''}
              {parseFloat(stock.change).toFixed(2)} ({stock.change_percent})
            </span>
          </div>
        ))}
        {/* We duplicate the data to create a seamless scrolling animation */}
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
