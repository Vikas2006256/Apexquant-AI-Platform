from typing import Dict, Any
from app.agents.base import BaseAgent

class PerformanceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Performance Agent",
            role_description=(
                "You are an institutional performance metrics quant. "
                "Your role is to analyze actual trading account logs: calculate profit factor, "
                "win rates, average hold times, drawdown durations, and evaluate trade expectancy."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "ALL")
        trade_history = inputs.get("trade_history", [])

        if not trade_history:
            return {
                "explanation": "No trade execution history available to evaluate performance metrics.",
                "confidence": 50,
                "data": {"expectancy": 0.0, "total_trades": 0}
            }

        try:
            user_prompt = (
                f"Evaluate this trade execution log:\n{trade_history}\n"
                "Return a JSON mapping profit factor, win rate, expectancy, and behavioral pitfalls."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, trade_history)

    def _run_heuristic(self, ticker: str, trade_history: list) -> Dict[str, Any]:
        wins = 0
        losses = 0
        total_pnl = 0.0
        win_sum = 0.0
        loss_sum = 0.0

        for trade in trade_history:
            pnl = float(trade.get("pnl", 0.0))
            total_pnl += pnl
            if pnl > 0:
                wins += 1
                win_sum += pnl
            elif pnl < 0:
                losses += 1
                loss_sum += abs(pnl)

        total_trades = len(trade_history)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0.0
        
        profit_factor = 0.0
        if loss_sum > 0:
            profit_factor = win_sum / loss_sum
        elif win_sum > 0:
            profit_factor = 999.0 # Infinity surrogate

        avg_win = win_sum / wins if wins > 0 else 0.0
        avg_loss = loss_sum / losses if losses > 0 else 0.0
        
        # Expectancy: (Win% * AvgWin) - (Loss% * AvgLoss)
        expectancy = ((win_rate / 100.0) * avg_win) - (((100 - win_rate) / 100.0) * avg_loss)

        explanation = (
            f"Performance report (Ticker filter: {ticker}): Evaluated {total_trades} executions. "
            f"Win rate is {win_rate:.1f}% and Profit Factor is {profit_factor:.2f}. "
            f"Account expectancy is ${expectancy:.2f} per trade setup."
        )

        return {
            "explanation": explanation,
            "confidence": 90,
            "data": {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "expectancy": expectancy,
                "net_profit": total_pnl
            }
        }
