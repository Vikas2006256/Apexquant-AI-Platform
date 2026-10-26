import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from app.services.market_data import MarketDataService

class BacktestingService:
    @staticmethod
    def run_backtest(
        ticker: str,
        strategy_name: str,
        ohlcv: List[Dict[str, Any]],
        initial_balance: float = 100000.0,
        slippage_pct: float = 0.0005, # 0.05%
        fee_pct: float = 0.001 # 0.1%
    ) -> Dict[str, Any]:
        """
        Runs a historical backtest simulation.
        Supported strategies: 'ema_crossover', 'rsi_reversion', 'bb_breakout'
        """
        if len(ohlcv) < 30:
            return {
                "status": "failed",
                "error": "Insufficient candles to run simulation. Need at least 30 periods."
            }

        df = pd.DataFrame(ohlcv)
        
        # Precompute indicators
        # 1. EMAs
        df["ema_fast"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=21, adjust=False).mean()
        
        # 2. RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["rsi"] = df["rsi"].fillna(50)

        # 3. Bollinger Bands
        df["bb_mid"] = df["close"].rolling(window=20).mean()
        df["bb_std"] = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_mid"] + (2 * df["bb_std"])
        df["bb_lower"] = df["bb_mid"] - (2 * df["bb_std"])

        balance = initial_balance
        position = 0.0 # shares
        entry_price = 0.0
        trades = []
        equity_curve = []

        # Start simulation loop
        for i in range(25, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            close_price = float(row["close"])
            date_str = str(row["time"])
            
            # Check strategy triggers
            buy_signal = False
            sell_signal = False

            if strategy_name == "ema_crossover":
                if prev_row["ema_fast"] <= prev_row["ema_slow"] and row["ema_fast"] > row["ema_slow"]:
                    buy_signal = True
                elif prev_row["ema_fast"] >= prev_row["ema_slow"] and row["ema_fast"] < row["ema_slow"]:
                    sell_signal = True
            elif strategy_name == "rsi_reversion":
                if row["rsi"] < 30 and position == 0:
                    buy_signal = True
                elif row["rsi"] > 70 and position > 0:
                    sell_signal = True
            elif strategy_name == "bb_breakout":
                if prev_row["close"] <= prev_row["bb_upper"] and row["close"] > row["bb_upper"] and position == 0:
                    buy_signal = True
                elif prev_row["close"] >= prev_row["bb_mid"] and row["close"] < row["bb_mid"] and position > 0:
                    sell_signal = True
            else:
                # Default fallback crossover
                if prev_row["ema_fast"] <= prev_row["ema_slow"] and row["ema_fast"] > row["ema_slow"]:
                    buy_signal = True
                elif prev_row["ema_fast"] >= prev_row["ema_slow"] and row["ema_fast"] < row["ema_slow"]:
                    sell_signal = True

            # Execution Logic
            if buy_signal and position == 0:
                # Buy maximum possible shares
                execution_price = close_price * (1 + slippage_pct)
                fee = balance * fee_pct
                net_capital = balance - fee
                position = net_capital / execution_price
                entry_price = execution_price
                balance = 0.0
                trades.append({
                    "action": "buy",
                    "price": execution_price,
                    "quantity": position,
                    "fee": fee,
                    "time": date_str
                })
            elif sell_signal and position > 0:
                # Sell all shares
                execution_price = close_price * (1 - slippage_pct)
                gross_value = position * execution_price
                fee = gross_value * fee_pct
                balance = gross_value - fee
                pnl = (execution_price - entry_price) * position - (fee + trades[-1]["fee"])
                trades.append({
                    "action": "sell",
                    "price": execution_price,
                    "quantity": position,
                    "fee": fee,
                    "pnl": pnl,
                    "time": date_str
                })
                position = 0.0
                entry_price = 0.0

            # Calculate current equity
            current_equity = balance + (position * close_price if position > 0 else 0.0)
            equity_curve.append({
                "time": date_str,
                "balance": current_equity
            })

        # Final close out of position
        if position > 0:
            final_row = df.iloc[-1]
            close_price = float(final_row["close"])
            execution_price = close_price * (1 - slippage_pct)
            gross_value = position * execution_price
            fee = gross_value * fee_pct
            balance = gross_value - fee
            pnl = (execution_price - entry_price) * position - (fee + trades[-1]["fee"])
            trades.append({
                "action": "sell_closeout",
                "price": execution_price,
                "quantity": position,
                "fee": fee,
                "pnl": pnl,
                "time": str(final_row["time"])
            })
            position = 0.0

        # Calculate metrics
        pnl_trades = [t["pnl"] for t in trades if "pnl" in t]
        total_trades = len(pnl_trades)
        winning_trades = len([p for p in pnl_trades if p > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        gross_profits = sum([p for p in pnl_trades if p > 0])
        gross_losses = sum([abs(p) for p in pnl_trades if p < 0])
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else (99.0 if gross_profits > 0 else 1.0)
        
        # Maximum Drawdown
        equity_series = pd.Series([eq["balance"] for eq in equity_curve])
        cum_max = equity_series.cummax()
        drawdown_series = (equity_series - cum_max) / cum_max * 100
        max_drawdown = drawdown_series.min() if not drawdown_series.empty else 0.0

        # Sharpe / Sortino Ratio calculation
        returns = equity_series.pct_change().dropna()
        risk_free_rate = 0.02 / 252 # Daily RFR assuming 2% annual
        excess_returns = returns - risk_free_rate
        
        sharpe = 0.0
        if not excess_returns.empty and excess_returns.std() > 0:
            sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

        negative_returns = excess_returns[excess_returns < 0]
        sortino = 0.0
        if not negative_returns.empty and negative_returns.std() > 0:
            sortino = (excess_returns.mean() / negative_returns.std()) * np.sqrt(252)

        return {
            "status": "completed",
            "initial_balance": initial_balance,
            "final_balance": balance,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": float(round(win_rate, 2)),
            "profit_factor": float(round(profit_factor, 2)),
            "max_drawdown": float(round(abs(max_drawdown), 2)),
            "sharpe_ratio": float(round(sharpe, 4)),
            "sortino_ratio": float(round(sortino, 4)),
            "equity_curve": equity_curve,
            "trades": trades
        }
