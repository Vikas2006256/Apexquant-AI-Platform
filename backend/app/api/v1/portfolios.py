from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.schemas.portfolio import PortfolioCreate, PortfolioOut, OrderRequest, TradeOut
from app.api.deps import get_current_active_user
from app.services.paper_trading import PaperTradingService

router = APIRouter()

@router.get("/", response_model=List[PortfolioOut])
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Lists all portfolios associated with the current user."""
    return db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()

@router.post("/", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_in: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Creates a new portfolio for paper trading or tracking."""
    new_portfolio = Portfolio(
        user_id=current_user.id,
        name=portfolio_in.name,
        type=portfolio_in.type,
        currency=portfolio_in.currency,
        balance=portfolio_in.balance,
        initial_balance=portfolio_in.balance
    )
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio

@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieves full details of a specific portfolio, updating positions 
    with real-time prices and executing triggered stops.
    """
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    # Trigger automated pricing updates and stop-out executions
    PaperTradingService.update_portfolio_positions(db, str(portfolio_id))
    db.refresh(portfolio)
    return portfolio

@router.post("/{portfolio_id}/order", response_model=TradeOut)
def place_portfolio_order(
    portfolio_id: UUID,
    order_in: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Places a new buy/sell order inside a portfolio."""
    # Ensure portfolio belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    # Execute order
    trade = PaperTradingService.place_order(
        db=db,
        portfolio_id=str(portfolio_id),
        ticker=order_in.ticker,
        quantity=order_in.quantity,
        action=order_in.action,
        side=order_in.side,
        stop_loss=order_in.stop_loss,
        take_profit=order_in.take_profit
    )
    return trade

@router.get("/{portfolio_id}/trades", response_model=List[TradeOut])
def get_portfolio_trades(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieves full trade history for a specific portfolio."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    return db.query(Trade).filter(Trade.portfolio_id == portfolio_id).order_by(Trade.timestamp.desc()).all()
