import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class AgentAnalysisLog(Base):
    __tablename__ = "agent_analysis_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), default="1D", nullable=False)
    confidence_score = Column(Integer, nullable=False) # 0 to 100
    trade_grade = Column(String(5), nullable=False) # 'A+', 'A', 'B', 'C', 'Avoid'
    agent_responses = Column(JSON, nullable=False) # Combined responses of all 15 agents
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="agent_logs")
