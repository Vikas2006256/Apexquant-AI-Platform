from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    period: str = "60d"
    interval: str = "1d"
    chart_image: Optional[str] = Field(None, description="Base64 encoded chart image string for Vision Agent evaluation")
    user_query: Optional[str] = "Provide general trading decision review"
    portfolio_id: Optional[UUID] = None
