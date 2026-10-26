from typing import Dict, Any
from app.agents.base import BaseAgent

class BacktestingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Backtesting Agent",
            role_description=(
                "You are an expert backtesting system auditor. "
                "Your role is to evaluate backtest runs: equity curves, maximum drawdowns, "
                "win rates, transaction slippage effects, and identify indicators of overfitting."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        backtest_results = inputs.get("backtest_results", {})

        if not backtest_results:
            return {
                "explanation": f"No backtest results available to audit for {ticker}.",
                "confidence": 0,
                "data": {}
            }

        try:
            user_prompt = (
                f"Audit these backtesting metrics for strategy on {ticker}:\n{backtest_results}\n"
                "Return a JSON mapping performance grade, curve stability, drawdown risk, and slippage decay score."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, backtest_results)

    def _run_heuristic(self, ticker: str, results: Dict[str, Any]) -> Dict[str, Any]:
        win_rate = results.get("win_rate", 0.0) # percentage
        sharpe = results.get("sharpe_ratio", 0.0)
        drawdown = results.get("max_drawdown", 0.0) # percentage
        trades = results.get("total_trades", 0)

        # Review backtest validity
        overfit_risk = "Low"
        if sharpe > 3.0 and trades < 50:
            overfit_risk = "High (Sample size too small)"
        elif sharpe > 4.5:
            overfit_risk = "Very High (Looks like look-ahead bias)"

        grade = "D"
        if trades >= 30:
            if sharpe >= 1.5 and drawdown < 15:
                grade = "A"
            elif sharpe >= 1.0 and drawdown < 20:
                grade = "B"
            elif sharpe >= 0.5 and drawdown < 30:
                grade = "C"

        explanation = (
            f"Backtest audit for {ticker} strategy: Grade {grade} assigned. "
            f"Sharpe ratio is {sharpe:.2f} with a max drawdown of {drawdown:.2f}% across {trades} trades. "
            f"Overfitting / curve-fitting risk is flagged as {overfit_risk.lower()}."
        )

        return {
            "explanation": explanation,
            "confidence": 85,
            "data": {
                "ticker": ticker,
                "grade": grade,
                "sharpe_ratio": sharpe,
                "max_drawdown": drawdown,
                "total_trades": trades,
                "overfitting_risk": overfit_risk,
                "curve_stability": "Steady" if drawdown < 10 else "Volatile"
            }
        }
