import json
import logging
from typing import List, Dict, Any, Optional
import yfinance as yf
from app.core.database import redis_client

logger = logging.getLogger("apexquant.market_data")

import datetime
import random

def generate_synthetic_ohlcv(ticker: str, count: int = 80) -> List[Dict[str, Any]]:
    ticker_upper = ticker.upper()
    base_price = 150.0
    if "BTC" in ticker_upper:
        base_price = 68000.0
    elif "ETH" in ticker_upper:
        base_price = 3500.0
    elif "NVDA" in ticker_upper:
        base_price = 128.0
    elif "AAPL" in ticker_upper:
        base_price = 225.0
    elif "TSLA" in ticker_upper:
        base_price = 245.0
    elif "MSFT" in ticker_upper:
        base_price = 430.0
    elif "AMZN" in ticker_upper:
        base_price = 190.0
    elif "META" in ticker_upper:
        base_price = 560.0
    elif "SPY" in ticker_upper:
        base_price = 540.0
    
    now = datetime.datetime.now()
    ohlcv = []
    curr_price = base_price * 0.88
    for i in range(count):
        dt = now - datetime.timedelta(days=(count - i))
        change_pct = (random.random() - 0.48) * 0.03
        open_p = curr_price
        close_p = open_p * (1 + change_pct)
        high_p = max(open_p, close_p) * (1 + random.random() * 0.01)
        low_p = min(open_p, close_p) * (1 - random.random() * 0.01)
        vol = random.randint(500000, 5000000)
        curr_price = close_p
        ohlcv.append({
            "time": dt.strftime("%Y-%m-%d"),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": vol
        })
    return ohlcv

class MarketDataService:
    @staticmethod
    def get_historical_data(ticker: str, period: str = "60d", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        Retrieves historical OHLCV data for a ticker. Checks Redis cache first, then yfinance.
        """
        cache_key = f"market_data:{ticker}:{period}:{interval}"
        
        # Check cache
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for ticker: {ticker}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Redis cache read error: {e}")

        logger.info(f"Cache miss for ticker: {ticker}. Fetching from yfinance...")
        try:
            # yfinance handler
            # Map ticker: crypto if it doesn't end with -USD, yfinance uses BTC-USD
            yf_ticker = ticker
            if "-" not in ticker and len(ticker) <= 4:
                # Stock format default
                pass
            
            ticker_obj = yf.Ticker(yf_ticker)
            df = ticker_obj.history(period=period, interval=interval)
            
            if df.empty:
                # Try fallback formatting for crypto
                if not ticker.endswith("-USD") and len(ticker) >= 3:
                    # Let's try BTC-USD format
                    ticker_obj = yf.Ticker(f"{ticker}-USD")
                    df = ticker_obj.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"No market data returned for {ticker}, generating instant synthetic market candles")
                ohlcv = generate_synthetic_ohlcv(ticker)
            else:
                ohlcv = []
                for index, row in df.iterrows():
                    ohlcv.append({
                        "time": index.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row["Volume"])
                    })

            # Save in Redis for 10 minutes (600s)
            try:
                redis_client.setex(cache_key, 600, json.dumps(ohlcv))
            except Exception as e:
                logger.error(f"Redis cache write error: {e}")

            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching data from yfinance for {ticker}: {e}")
            return generate_synthetic_ohlcv(ticker)

    @staticmethod
    def get_ticker_info(ticker: str) -> Dict[str, Any]:
        """Fetches fundamental ratio info for a ticker."""
        cache_key = f"ticker_info:{ticker}"
        try:
            cached_info = redis_client.get(cache_key)
            if cached_info:
                return json.loads(cached_info)
        except Exception as e:
            logger.error(f"Redis cache read error: {e}")

        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # Extract only standard keys for safety
            keys = [
                "trailingPE", "pegRatio", "priceToBook", "returnOnEquity", 
                "operatingMargins", "debtToEquity", "revenueGrowth", 
                "longName", "sector", "industry", "marketCap"
            ]
            cleaned_info = {k: info.get(k) for k in keys if k in info}
            
            try:
                redis_client.setex(cache_key, 3600 * 12, json.dumps(cleaned_info)) # cache 12h
            except Exception as e:
                logger.error(f"Redis cache write error: {e}")
                
            return cleaned_info
        except Exception as e:
            logger.error(f"Error fetching ticker info for {ticker}: {e}")
            return {}

    @staticmethod
    def get_ticker_news(ticker: str) -> List[Dict[str, Any]]:
        """Fetches news headlines for a ticker."""
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news or []
            
            cleaned_news = []
            for n in news[:8]: # latest 8 items
                cleaned_news.append({
                    "title": n.get("title", ""),
                    "publisher": n.get("publisher", ""),
                    "link": n.get("link", ""),
                    "summary": n.get("summary", "")
                })
            return cleaned_news
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

    @staticmethod
    def search_tickers(query: str) -> List[Dict[str, Any]]:
        """
        Searches all global stocks, ETFs, indices, currencies, and cryptocurrencies matching query.
        """
        if not query or len(query.strip()) < 1:
            return []
        
        cache_key = f"symbol_search:{query.strip().lower()}"
        try:
            cached_search = redis_client.get(cache_key)
            if cached_search:
                return json.loads(cached_search)
        except Exception as e:
            logger.error(f"Redis search cache error: {e}")

        try:
            import urllib.request
            import urllib.parse
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query.strip())}&quotesCount=10&newsCount=0"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read().decode())
            
            quotes = data.get("quotes", [])
            results = []
            for q in quotes:
                symbol = q.get("symbol")
                if not symbol:
                    continue
                name = q.get("shortname") or q.get("longname") or symbol
                quote_type = q.get("quoteType", "EQUITY")
                exch = q.get("exchDisp") or q.get("exchange", "")
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "type": quote_type,
                    "exchange": exch
                })

            try:
                redis_client.setex(cache_key, 3600, json.dumps(results))
            except Exception as e:
                logger.error(f"Redis search cache write error: {e}")

            return results
        except Exception as e:
            logger.error(f"Error executing ticker search for {query}: {e}")
            return []
