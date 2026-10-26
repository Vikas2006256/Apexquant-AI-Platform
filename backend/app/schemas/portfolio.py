from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class TradeOut(BaseModel):
    id: UUID
    ticker: str
    quantity: float
    price: float
    action: str
    fee: float
    timestamp: datetime

    class Config:
        from_attributes = True

class PositionOut(BaseModel):
    id: UUID
    ticker: str
    quantity: float
    side: str
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    pnl: float
    opened_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = "paper" # 'paper', 'live', 'backtest'
    currency: str = "USD"
    balance: float = Field(100000.0000, ge=0)

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioOut(PortfolioBase):
    id: UUID
    user_id: UUID
    initial_balance: float
    created_at: datetime
    updated_at: datetime
    positions: List[PositionOut] = []
    
    class Config:
        from_attributes = True

class OrderRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    action: str = Field(..., pattern="^(buy|sell)$")
    side: str = Field("long", pattern="^(long|short)$")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
