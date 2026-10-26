from typing import Dict, Any, List
from app.agents.base import BaseAgent

class PortfolioAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Portfolio Agent",
            role_description=(
                "You are an institutional portfolio construction strategist. "
                "Your role is to analyze asset weights, diversification, correlation risk, "
                "sector exposure, and portfolio beta to optimize risk-adjusted returns."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        portfolio = inputs.get("portfolio_state", {})
        ticker = inputs.get("ticker", "UNKNOWN")

        try:
            user_prompt = (
                f"Evaluate this portfolio state for adding or modifying exposure in {ticker}:\n{portfolio}\n"
                "Return a JSON mapping diversification score, sector weighting balance, correlation risks, and adjustment recommendations."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, portfolio)

    def _run_heuristic(self, ticker: str, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        positions = portfolio.get("positions", [])
        cash = float(portfolio.get("balance", 100000.0))
        total_value = cash + sum(float(pos.get("quantity", 0)) * float(pos.get("current_price", 0)) for pos in positions)

        ticker_weight = 0.0
        # Calculate current weighting of this ticker in portfolio
        for pos in positions:
            if pos.get("ticker") == ticker:
                ticker_weight = (float(pos.get("quantity", 0)) * float(pos.get("current_price", 0))) / total_value if total_value > 0 else 0.0
                break

        diversification = "High"
        num_positions = len(positions)
        if num_positions < 3:
            diversification = "Low"
        elif num_positions <= 7:
            diversification = "Moderate"

        recommendation = "Maintain current weight"
        if ticker_weight > 0.25:
            recommendation = f"Reduce exposure in {ticker} to avoid concentration risk"
        elif ticker_weight == 0 and cash > (total_value * 0.1):
            recommendation = f"Initiate a starter position in {ticker}"

        explanation = (
            f"Portfolio Agent review: Portfolio contains {num_positions} assets with a cash balance of ${cash:.2f}. "
            f"Diversification is {diversification.lower()}. Concentration in {ticker} is at {ticker_weight*100:.1f}%. "
            f"Strategic action: {recommendation}."
        )

        return {
            "explanation": explanation,
            "confidence": 85,
            "data": {
                "ticker": ticker,
                "portfolio_value": total_value,
                "cash_ratio": cash / total_value if total_value > 0 else 1.0,
                "diversification": diversification,
                "ticker_weight": ticker_weight,
                "recommended_action": recommendation
            }
        }
