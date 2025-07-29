// FILE: react-frontend/src/pages/ChatPage.js

import React, { useState, useEffect } from 'react';
import TickerSlider from '../components/Layout/TickerSlider';
import SidePanel from '../components/Layout/SidePanel';
import MarketMovers from '../components/Panels/MarketMovers';
import NewsPanel from '../components/Panels/NewsPanel';
import IpoPanel from '../components/Panels/IpoPanel';
import ChatWindow from '../components/Chat/ChatWindow';

// Define the base URL for your backend API
const API_BASE_URL = 'http://localhost:8000';

function ChatPage() {
  const [tickerData, setTickerData] = useState([]);
  const [marketMovers, setMarketMovers] = useState({ top_gainers: [], top_losers: [] });
  const [news, setNews] = useState([]);
  const [ipos, setIpos] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('stockbot_token');

    const fetchData = async (url) => {
      try {
        // Update fetch call to use the full URL
        const response = await fetch(`${API_BASE_URL}${url}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error(`Failed to fetch ${url}`);
        return await response.json();
      } catch (error) {
        console.error(error);
        // Return a default value that matches the expected data structure
        if (url.includes('movers')) return { top_gainers: [], top_losers: [] };
        return [];
      }
    };

    const fetchInitialData = async () => {
      // No changes needed here; the fetchData helper now handles the full URL
      const [ticker, movers, newsData, ipoData] = await Promise.all([
        fetchData('/ticker-data'),
        fetchData('/market-movers'),
        fetchData('/market-news'),
        fetchData('/ipo-calendar')
      ]);
      setTickerData(ticker);
      setMarketMovers(movers);
      setNews(newsData);
      setIpos(ipoData);
    };

    if (token) {
      fetchInitialData();
    }
  }, []);

  return (
    <>
      <TickerSlider tickerData={tickerData} />
      <div className="main-content-wrapper">
        <SidePanel>
          <MarketMovers movers={marketMovers} />
        </SidePanel>

        <ChatWindow />

        <div className="right-column">
          <SidePanel>
            <NewsPanel news={news} />
          </SidePanel>
          <SidePanel>
            <IpoPanel ipos={ipos} />
          </SidePanel>
        </div>
      </div>
    </>
  );
}

export default ChatPage;