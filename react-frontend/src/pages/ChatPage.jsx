

import React, { useState, useEffect } from 'react';
import TickerSlider from '../components/Layout/TickerSlider';
import SidePanel from '../components/Layout/SidePanel';
import MarketMovers from '../components/Panels/MarketMovers';
import NewsPanel from '../components/Panels/NewsPanel';
import IpoPanel from '../components/Panels/IpoPanel';
import ChatWindow from '../components/Chat/ChatWindow';


import API_BASE_URL from '../config';

function ChatPage() {
  const [tickerData, setTickerData] = useState([]);
  const [marketMovers, setMarketMovers] = useState({ top_gainers: [], top_losers: [] });
  const [news, setNews] = useState([]);
  const [ipos, setIpos] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('stockbot_token');

    const fetchData = async (url, defaultValue) => {
      try {
        console.log(`[ChatPage] Fetching ${API_BASE_URL}${url}`);
        const response = await fetch(`${API_BASE_URL}${url}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) {
          console.error(`[ChatPage] Failed to fetch ${url}: ${response.status} ${response.statusText}`);
          return defaultValue;
        }
        const data = await response.json();
        console.log(`[ChatPage] Received data for ${url}:`, data ? 'OK' : 'empty');
        return data;
      } catch (error) {
        console.error(`[ChatPage] Error fetching ${url}:`, error);
        return defaultValue;
      }
    };

    const fetchInitialData = async () => {
      // Fetch data sequentially to avoid overwhelming the backend API rate limits
      // The backend caches results, so subsequent loads will be fast
      console.log('[ChatPage] Starting data fetch...');
      
      // Fetch ticker data first (this is the slowest due to multiple API calls)
      const ticker = await fetchData('/ticker-data', []);
      setTickerData(ticker);
      
      // Then fetch the rest in parallel (these are single API calls each)
      const [movers, newsData, ipoData] = await Promise.all([
        fetchData('/market-movers', { top_gainers: [], top_losers: [] }),
        fetchData('/market-news', []),
        fetchData('/ipo-calendar', [])
      ]);
      
      setMarketMovers(movers);
      setNews(newsData);
      setIpos(ipoData);
      
      console.log('[ChatPage] All data fetched.');
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