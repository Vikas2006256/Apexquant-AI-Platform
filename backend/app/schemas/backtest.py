from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class BacktestRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    strategy_name: str = Field("ema_crossover", description="EMA Crossover, RSI Reversion or BB Breakout")
    timeframe: str = "1D"
    period: str = "1y" # yfinance periods: 1mo, 3mo, 6mo, 1y, 2y, 5y
    initial_balance: float = Field(100000.00, ge=100)

class BacktestOut(BaseModel):
    id: UUID
    user_id: UUID
    strategy_name: str
    ticker: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    status: str
    equity_curve: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
