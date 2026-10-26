from typing import Dict, Any
from app.agents.base import BaseAgent

class ExecutionPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Execution Planner",
            role_description=(
                "You are an institutional execution trader. "
                "Your role is to formulate high-efficiency execution schedules: "
                "TWAP, VWAP, limit placements, order routing, and analyze bid-ask spreads to minimize slippage."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        execution_req = inputs.get("execution_request", {}) # target quantity, current spread

        try:
            user_prompt = (
                f"Design an execution plan for {ticker} given these targets:\n{execution_req}\n"
                "Return a JSON mapping execution type (market/limit/TWAP/VWAP), order splits, route channels, and spread risk."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, execution_req)

    def _run_heuristic(self, ticker: str, req: Dict[str, Any]) -> Dict[str, Any]:
        shares = float(req.get("quantity", 1000.0))
        spread = float(req.get("spread", 0.05)) # bid-ask spread
        daily_vol = float(req.get("average_daily_volume", 500000.0))

        # Check impact ratio
        impact_pct = (shares / daily_vol) * 100 if daily_vol > 0 else 0.0
        
        exec_type = "Limit Orders"
        notes = "Split into 3 lots and use limit buy grids."
        
        if impact_pct > 1.0:
            exec_type = "TWAP (Time Weighted Average Price)"
            notes = "Execute in hourly tranches over the next 4 hours to avoid market disruption."
        elif spread > 0.5:
            exec_type = "Post-Only Limit Orders"
            notes = "High spread detected. Never use market orders; wait for fill on book."
        elif impact_pct < 0.1 and spread < 0.05:
            exec_type = "Market Order"
            notes = "Minimal impact and narrow spread; direct entry approved."

        explanation = (
            f"Execution plan created for {ticker} (Order size: {shares} shares). "
            f"Using {exec_type} mechanism. Impact ratio is {impact_pct:.2f}% of daily volume. "
            f"Action instructions: {notes}"
        )

        return {
            "explanation": explanation,
            "confidence": 85,
            "data": {
                "ticker": ticker,
                "execution_type": exec_type,
                "order_instructions": notes,
                "estimated_impact_pct": impact_pct,
                "order_size": shares
            }
        }
