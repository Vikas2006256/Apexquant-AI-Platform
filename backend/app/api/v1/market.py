from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from app.services.market_data import MarketDataService

router = APIRouter()

@router.get("/ohlcv", response_model=List[Any])
def get_ohlcv(
    ticker: str,
    period: str = Query("60d", description="Historical range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max"),
    interval: str = Query("1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
) -> Any:
    """Fetches historical price candles (OHLCV) for a given symbol."""
    return MarketDataService.get_historical_data(ticker, period, interval)

@router.get("/fundamentals")
def get_fundamentals(ticker: str) -> Any:
    """Fetches key fundamental ratios, market capitalization, and industry labels."""
    return MarketDataService.get_ticker_info(ticker)

@router.get("/news")
def get_news(ticker: str) -> Any:
    """Fetches latest financial news articles linked to the asset symbol."""
    return MarketDataService.get_ticker_news(ticker)

@router.get("/search")
def search_symbols(q: str = Query(..., min_length=1, description="Search query for global stocks, ETFs, indices, cryptos")) -> Any:
    """Searches all global stocks, ETFs, indices, currencies, and cryptocurrencies matching query."""
    return MarketDataService.search_tickers(q)
