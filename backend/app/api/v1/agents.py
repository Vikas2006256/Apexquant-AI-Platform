from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.models.agent_log import AgentAnalysisLog
from app.schemas.agent_analysis import AnalysisRequest
from app.api.deps import get_current_active_user
from app.services.market_data import MarketDataService
from app.agents.multi_agent import MultiAgentOrchestrator

router = APIRouter()
orchestrator = MultiAgentOrchestrator()

@router.post("/analyze")
async def run_agent_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Runs a 15-agent consensus research report on a symbol."""
    # 1. Fetch market feeds
    ohlcv = MarketDataService.get_historical_data(request.ticker, request.period, request.interval)
    if not ohlcv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to fetch market candles for {request.ticker}."
        )

    fundamental_info = MarketDataService.get_ticker_info(request.ticker)
    news = MarketDataService.get_ticker_news(request.ticker)

    # 2. Build portfolio states if portfolio_id provided
    portfolio_state = {}
    trade_history = []
    balance = float(current_user.risk_limit_pct) * 1000 # baseline sizing proxy
    
    if request.portfolio_id:
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == request.portfolio_id,
            Portfolio.user_id == current_user.id
        ).first()
        if portfolio:
            balance = float(portfolio.balance)
            positions = db.query(Position).filter(Position.portfolio_id == portfolio.id, Position.status == "open").all()
            trades = db.query(Trade).filter(Trade.portfolio_id == portfolio.id).all()
            
            portfolio_state = {
                "balance": balance,
                "positions": [
                    {
                        "ticker": p.ticker,
                        "quantity": float(p.quantity),
                        "entry_price": float(p.entry_price),
                        "current_price": float(p.current_price),
                        "side": p.side
                    } for p in positions
                ]
            }
            trade_history = [
                {
                    "ticker": t.ticker,
                    "quantity": float(t.quantity),
                    "price": float(t.price),
                    "action": t.action,
                    "pnl": float(t.pnl) if hasattr(t, 'pnl') and t.pnl else 0.0
                } for t in trades
            ]

    # Combine all parameters into inputs
    inputs = {
        "ticker": request.ticker,
        "ohlcv": ohlcv,
        "fundamental_info": fundamental_info,
        "news": news,
        "portfolio_state": portfolio_state,
        "trade_history": trade_history,
        "balance": balance,
        "user_risk_pct": float(current_user.risk_limit_pct),
        "chart_image": request.chart_image,
        "user_query": request.user_query,
        "spread": 0.02, # estimate spread
        "average_daily_volume": 1500000.0,
        "sentiment_data": {
            "fear_greed_index": 52,
            "put_call_ratio": 0.88,
            "social_score": 0.15
        },
        "macro": {
            "interest_rate": 5.25,
            "inflation_cpi": 2.9,
            "central_bank_stance": "Neutral",
            "gdp_growth": 2.4
        }
    }

    # 3. Execute agents
    report = await orchestrator.analyze(inputs)

    # 4. Log report to DB
    conf_str = report.get("Confidence", {}).get("Confidence Score", "50%").replace("%", "")
    try:
        confidence_score_int = int(conf_str)
    except Exception:
        confidence_score_int = 50

    trade_grade_str = report.get("Confidence", {}).get("Trade Grade", "Avoid")
    
    agent_log = AgentAnalysisLog(
        user_id=current_user.id,
        ticker=request.ticker,
        timeframe=request.interval,
        confidence_score=confidence_score_int,
        trade_grade=trade_grade_str,
        agent_responses=report
    )
    db.add(agent_log)
    db.commit()
    db.refresh(agent_log)

    return report
