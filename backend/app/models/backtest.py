import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Integer, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    ticker = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    initial_balance = Column(Numeric(18, 4), nullable=False)
    final_balance = Column(Numeric(18, 4), nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Numeric(5, 2), default=0.00, nullable=False)
    profit_factor = Column(Numeric(10, 2), default=0.00, nullable=False)
    max_drawdown = Column(Numeric(5, 2), default=0.00, nullable=False)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    sortino_ratio = Column(Numeric(10, 4), nullable=True)
    status = Column(String(20), default="pending", nullable=False) # 'pending', 'running', 'completed', 'failed'
    equity_curve = Column(JSON, default=list, nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="backtests")
