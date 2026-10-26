from typing import Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.services.market_data import MarketDataService

class PaperTradingService:
    @staticmethod
    def place_order(
        db: Session,
        portfolio_id: Any,
        ticker: str,
        quantity: float,
        action: str, # 'buy', 'sell'
        side: str = "long", # 'long', 'short'
        stop_loss: float = None,
        take_profit: float = None
    ) -> Trade:
        """
        Executes a paper order: verifies cash balance, creates transaction record, and opens or updates positions.
        """
        import uuid
        if isinstance(portfolio_id, str):
            try:
                portfolio_uuid = uuid.UUID(portfolio_id)
            except Exception:
                portfolio_uuid = portfolio_id
        else:
            portfolio_uuid = portfolio_id

        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_uuid).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Fetch current price with fallbacks
        ohlcv = MarketDataService.get_historical_data(ticker, period="1d", interval="1m")
        if not ohlcv:
            ohlcv = MarketDataService.get_historical_data(ticker, period="5d", interval="1d")
        if not ohlcv:
            ohlcv = MarketDataService.get_historical_data(ticker, period="60d", interval="1d")
        
        current_price = 0.0
        if ohlcv and len(ohlcv) > 0:
            current_price = float(ohlcv[-1]["close"])
        else:
            info = MarketDataService.get_ticker_info(ticker)
            if info and info.get("regularMarketPrice"):
                current_price = float(info["regularMarketPrice"])
            elif info and info.get("previousClose"):
                current_price = float(info["previousClose"])

        if current_price <= 0:
            raise HTTPException(status_code=400, detail=f"Market price for {ticker} is not available")
            
        order_cost = quantity * current_price
        fee = order_cost * 0.001

        # Validate Stop Loss and Take Profit sanity for Long / Short positions
        if stop_loss:
            if side == "long" and float(stop_loss) >= current_price:
                stop_loss = None # Invalid SL above entry price for long
            elif side == "short" and float(stop_loss) <= current_price:
                stop_loss = None
        if take_profit:
            if side == "long" and float(take_profit) <= current_price:
                take_profit = None # Invalid TP below entry price for long
            elif side == "short" and float(take_profit) >= current_price:
                take_profit = None

        if action == "buy":
            # Check cash balance
            if portfolio.balance < (order_cost + fee):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient balance. Required: ${(order_cost + fee):.2f}, Available: ${portfolio.balance:.2f}"
                )
            
            # Deduct cash
            portfolio.balance = float(portfolio.balance) - (order_cost + fee)
            
            # Find existing open position
            position = db.query(Position).filter(
                Position.portfolio_id == portfolio_uuid,
                Position.ticker == ticker,
                Position.status == "open"
            ).first()
            
            if position:
                if position.side == "long":
                    # Average up/down entry price
                    total_qty = float(position.quantity) + quantity
                    total_cost = (float(position.quantity) * float(position.entry_price)) + order_cost
                    position.entry_price = total_cost / total_qty
                    position.quantity = total_qty
                    position.current_price = current_price
                    if stop_loss: position.stop_loss = stop_loss
                    if take_profit: position.take_profit = take_profit
                else:
                    # Closing existing short position
                    close_qty = min(float(position.quantity), quantity)
                    realized_pnl = (float(position.entry_price) - current_price) * close_qty
                    portfolio.balance = float(portfolio.balance) + (close_qty * current_price) + realized_pnl - fee
                    position.quantity = float(position.quantity) - close_qty
                    if position.quantity <= 0:
                        position.status = "closed"
                        position.closed_at = datetime.utcnow()
            else:
                # Open new long position
                position = Position(
                    portfolio_id=portfolio_uuid,
                    ticker=ticker,
                    quantity=quantity,
                    side=side or "long",
                    entry_price=current_price,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    status="open"
                )
                db.add(position)
                db.flush() # populated position.id

            trade = Trade(
                portfolio_id=portfolio_uuid,
                position_id=position.id,
                ticker=ticker,
                quantity=quantity,
                price=current_price,
                action="buy",
                fee=fee
            )
            db.add(trade)
            db.commit()
            return trade

        elif action == "sell":
            # Check if open position exists
            position = db.query(Position).filter(
                Position.portfolio_id == portfolio_uuid,
                Position.ticker == ticker,
                Position.status == "open"
            ).first()
            
            if position:
                # Selling existing position (long or short)
                close_qty = min(float(position.quantity), quantity)
                revenue = (close_qty * current_price) - fee
                portfolio.balance = float(portfolio.balance) + revenue
                
                pnl_factor = 1 if position.side == "long" else -1
                realized_pnl = (current_price - float(position.entry_price)) * close_qty * pnl_factor
                
                position.quantity = float(position.quantity) - close_qty
                position.current_price = current_price
                
                if position.quantity <= 0:
                    position.status = "closed"
                    position.closed_at = datetime.utcnow()
                    position.pnl = float(position.pnl) + realized_pnl
                
                trade = Trade(
                    portfolio_id=portfolio_uuid,
                    position_id=position.id,
                    ticker=ticker,
                    quantity=close_qty,
                    price=current_price,
                    action="sell",
                    fee=fee
                )
                db.add(trade)
                db.commit()
                return trade
            else:
                # Open new short position if no open long position exists
                margin_required = order_cost * 0.2 + fee # 20% margin
                if portfolio.balance < margin_required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient margin balance to open Short position for {ticker}. Required: ${margin_required:.2f}"
                    )
                
                portfolio.balance = float(portfolio.balance) - margin_required
                position = Position(
                    portfolio_id=portfolio_uuid,
                    ticker=ticker,
                    quantity=quantity,
                    side="short",
                    entry_price=current_price,
                    current_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    status="open"
                )
                db.add(position)
                db.flush()

                trade = Trade(
                    portfolio_id=portfolio_uuid,
                    position_id=position.id,
                    ticker=ticker,
                    quantity=quantity,
                    price=current_price,
                    action="sell",
                    fee=fee
                )
                db.add(trade)
                db.commit()
                return trade

    @staticmethod
    def update_portfolio_positions(db: Session, portfolio_id: Any) -> None:
        """
        Iterates over all open positions in a portfolio:
        1. Updates their current market price.
        2. Computes current unrealized PnL.
        3. Evaluates and executes automated exit triggers (Stop Loss, Take Profit).
        """
        import uuid
        if isinstance(portfolio_id, str):
            try:
                portfolio_uuid = uuid.UUID(portfolio_id)
            except Exception:
                portfolio_uuid = portfolio_id
        else:
            portfolio_uuid = portfolio_id

        open_positions = db.query(Position).filter(
            Position.portfolio_id == portfolio_uuid,
            Position.status == "open"
        ).all()
        
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_uuid).first()
        if not portfolio:
            return

        for pos in open_positions:
            # Fetch latest price
            ohlcv = MarketDataService.get_historical_data(pos.ticker, period="1d", interval="1m")
            if not ohlcv:
                ohlcv = MarketDataService.get_historical_data(pos.ticker, period="5d", interval="1d")
                
            if not ohlcv:
                continue
                
            current_price = float(ohlcv[-1]["close"])
            pos.current_price = current_price
            
            # Recalculate PnL
            pnl_factor = 1 if pos.side == "long" else -1
            pos.pnl = (current_price - float(pos.entry_price)) * float(pos.quantity) * pnl_factor
            
            # Check Stop Loss / Take Profit triggers
            sl_triggered = False
            tp_triggered = False
            
            if pos.side == "long":
                if pos.stop_loss and current_price <= float(pos.stop_loss):
                    sl_triggered = True
                elif pos.take_profit and current_price >= float(pos.take_profit):
                    tp_triggered = True
            elif pos.side == "short":
                if pos.stop_loss and current_price >= float(pos.stop_loss):
                    sl_triggered = True
                elif pos.take_profit and current_price <= float(pos.take_profit):
                    tp_triggered = True

            if sl_triggered or tp_triggered:
                # Trigger liquidation order
                qty = float(pos.quantity)
                revenue = qty * current_price
                fee = revenue * 0.001
                
                portfolio.balance = float(portfolio.balance) + (revenue - fee)
                pos.quantity = 0.0
                pos.status = "closed"
                pos.closed_at = datetime.utcnow()
                pos.pnl = (current_price - float(pos.entry_price)) * qty * pnl_factor - fee
                
                trade = Trade(
                    portfolio_id=portfolio_uuid,
                    position_id=pos.id,
                    ticker=pos.ticker,
                    quantity=qty,
                    price=current_price,
                    action="stop_limit_exit",
                    fee=fee
                )
                db.add(trade)
                
        db.commit()
