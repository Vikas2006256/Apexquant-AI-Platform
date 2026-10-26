from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.backtest import Backtest
from app.schemas.backtest import BacktestRequest, BacktestOut
from app.api.deps import get_current_active_user
from app.services.market_data import MarketDataService
from app.services.backtester import BacktestingService

router = APIRouter()

@router.post("/run", response_model=BacktestOut)
def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Runs a historical simulation on a symbol, saving the output reports."""
    # 1. Fetch candles
    ohlcv = MarketDataService.get_historical_data(
        ticker=request.ticker,
        period=request.period,
        interval=request.timeframe
    )
    
    if not ohlcv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to fetch historical market data for {request.ticker} to backtest."
        )

    # 2. Run simulation
    sim_res = BacktestingService.run_backtest(
        ticker=request.ticker,
        strategy_name=request.strategy_name,
        ohlcv=ohlcv,
        initial_balance=request.initial_balance
    )

    if sim_res.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sim_res.get("error", "Backtest failed")
        )

    # 3. Create database entry
    def parse_date(date_str: str) -> datetime:
        if not date_str:
            return datetime.utcnow()
        if len(date_str) == 10:
            return datetime.strptime(date_str, "%Y-%m-%d")
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.fromisoformat(date_str.replace(" ", "T"))

    start_date = parse_date(ohlcv[0]["time"])
    end_date = parse_date(ohlcv[-1]["time"])

    backtest = Backtest(
        user_id=current_user.id,
        strategy_name=request.strategy_name,
        ticker=request.ticker,
        timeframe=request.timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=request.initial_balance,
        final_balance=sim_res["final_balance"],
        total_trades=sim_res["total_trades"],
        winning_trades=sim_res["winning_trades"],
        losing_trades=sim_res["losing_trades"],
        win_rate=sim_res["win_rate"],
        profit_factor=sim_res["profit_factor"],
        max_drawdown=sim_res["max_drawdown"],
        sharpe_ratio=sim_res["sharpe_ratio"],
        sortino_ratio=sim_res["sortino_ratio"],
        status="completed",
        equity_curve=sim_res["equity_curve"],
        metrics={"trades": sim_res["trades"]}
    )
    
    db.add(backtest)
    db.commit()
    db.refresh(backtest)
    return backtest

@router.get("/list", response_model=List[BacktestOut])
def list_backtests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Lists all historical backtest simulations executed by the current user."""
    return db.query(Backtest).filter(Backtest.user_id == current_user.id).order_by(Backtest.created_at.desc()).all()

@router.get("/{backtest_id}", response_model=BacktestOut)
def get_backtest(
    backtest_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieves full details and trade history logs for a specific backtest."""
    backtest = db.query(Backtest).filter(
        Backtest.id == backtest_id,
        Backtest.user_id == current_user.id
    ).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtest
