from typing import Dict, Any
from app.agents.base import BaseAgent

class AIMentor(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AI Mentor",
            role_description=(
                "You are an elite trading performance psychologist and mentor. "
                "Your role is to guide traders through cognitive biases, revenge trading, "
                "FOMO, stress management, and enforce discipline and patience in market execution."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "ALL")
        user_query = inputs.get("user_query", "")
        trade_history = inputs.get("trade_history", [])

        try:
            user_prompt = (
                f"A trader is asking for mentorship regarding {ticker}. Query: '{user_query}'\n"
                f"Recent executions data: {trade_history[-5:]}\n"
                "Return a JSON providing psychological advice, discipline guidelines, and a mentor score."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, user_query, trade_history)

    def _run_heuristic(self, ticker: str, user_query: str, trade_history: list) -> Dict[str, Any]:
        advice = "Focus on sticking to your predefined stop loss levels and maintaining trade journals."
        score = 80
        
        # Analyze potential rules violations
        consecutive_losses = 0
        for trade in reversed(trade_history):
            pnl = float(trade.get("pnl", 0.0))
            if pnl < 0:
                consecutive_losses += 1
            else:
                break
                
        if consecutive_losses >= 3:
            advice = "You have hit a streak of consecutive losses. Step away from the screens to prevent revenge trading. Reduce position size by half on your next trade."
            score = 65
        elif not trade_history:
            advice = "Welcome to your ApexQuant trading journal. Begin by setting a daily loss limit and practicing paper trading to build execution consistency."

        explanation = (
            f"AI Mentor Review for {ticker}: {advice} "
            f"Mentorship rating is {score}/100 based on recent discipline indicators."
        )

        return {
            "explanation": explanation,
            "confidence": 95,
            "data": {
                "ticker": ticker,
                "mentor_score": score,
                "psychology_advice": advice,
                "rules_to_follow": [
                    "Define stop loss before clicking trade button",
                    "Do not override trade execution plans mid-trade",
                    "Limit maximum risk to 2% per setup"
                ]
            }
        }
