import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(18, 8), nullable=False)
    side = Column(String(10), default="long", nullable=False) # 'long', 'short'
    entry_price = Column(Numeric(18, 4), nullable=False)
    current_price = Column(Numeric(18, 4), nullable=False)
    stop_loss = Column(Numeric(18, 4), nullable=True)
    take_profit = Column(Numeric(18, 4), nullable=True)
    status = Column(String(20), default="open", nullable=False, index=True) # 'open', 'closed'
    pnl = Column(Numeric(18, 4), default=0.0000, nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    portfolio = relationship("Portfolio", back_populates="positions")
    trades = relationship("Trade", back_populates="position")
