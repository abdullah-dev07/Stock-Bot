import React, { useState, useEffect } from 'react';
import TickerSlider from '../components/Layout/TickerSlider';
import SidePanel from '../components/Layout/SidePanel';
import MarketMovers from '../components/Panels/MarketMovers';
import NewsPanel from '../components/Panels/NewsPanel';
import IpoPanel from '../components/Panels/IpoPanel';
import ChatWindow from '../components/Chat/ChatWindow';
import { authFetch } from '../utils/apiClient';
import '../styles/ChatPage.css';

function ChatPage() {
  const [tickerData, setTickerData] = useState([]);
  const [marketMovers, setMarketMovers] = useState({ top_gainers: [], top_losers: [] });
  const [news, setNews] = useState([]);
  const [ipos, setIpos] = useState([]);

  useEffect(() => {
    const fetchData = async (url, defaultValue) => {
      try {
        const response = await authFetch(url);
        if (!response.ok) return defaultValue;
        return await response.json();
      } catch {
        return defaultValue;
      }
    };

    const fetchInitialData = async () => {
      const ticker = await fetchData('/ticker-data', []);
      setTickerData(ticker);

      const [movers, newsData, ipoData] = await Promise.all([
        fetchData('/market-movers', { top_gainers: [], top_losers: [] }),
        fetchData('/market-news', []),
        fetchData('/ipo-calendar', [])
      ]);

      setMarketMovers(movers);
      setNews(newsData);
      setIpos(ipoData);
    };

    fetchInitialData();
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
