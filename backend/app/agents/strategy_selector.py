from typing import Dict, Any
from app.agents.base import BaseAgent

class StrategySelectorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Strategy Selector",
            role_description=(
                "You are an elite quantitative researcher. "
                "Your role is to evaluate market regimes (trending, range, high volatility, low volatility) "
                "and select the optimal strategy (Trend Following, Mean Reversion, Momentum Breakout, or Option Selling)."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        regime = inputs.get("regime", {}) # trend, volatility, volume

        try:
            user_prompt = (
                f"Select the best trading strategy for {ticker} given these conditions:\n{regime}\n"
                "Return a JSON mapping strategy recommendation, entry rules, filter conditions, and conviction rating."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, regime)

    def _run_heuristic(self, ticker: str, regime: Dict[str, Any]) -> Dict[str, Any]:
        trend = regime.get("trend", "Neutral") # Bullish, Bearish, Neutral
        volatility = regime.get("volatility", "Normal") # High, Low, Normal
        volume = regime.get("volume", "Normal") # High, Low, Normal

        strategy = "Range Scalping (Mean Reversion)"
        conviction = "Medium"
        timeframe = "1H / 15m"

        if trend == "Bullish" and volatility == "Normal":
            strategy = "Moving Average Trend-Following"
            conviction = "High"
            timeframe = "Daily / 4H"
        elif trend == "Bearish" and volatility == "Normal":
            strategy = "Short Momentum Breakouts"
            conviction = "High"
            timeframe = "Daily / 4H"
        elif trend == "Neutral" and volatility == "High":
            strategy = "Mean Reversion Bollinger Bands Play"
            conviction = "Medium"
            timeframe = "1H / 30m"
        elif trend == "Bullish" and volatility == "High" and volume == "High":
            strategy = "Institutional Breakout Expansion"
            conviction = "High"
            timeframe = "Daily / 1H"

        explanation = (
            f"Market regime for {ticker} is trending {trend.lower()} with {volatility.lower()} volatility. "
            f"Recommended strategy playbook is '{strategy}' with {conviction.lower()} conviction."
        )

        return {
            "explanation": explanation,
            "confidence": 80,
            "data": {
                "ticker": ticker,
                "strategy": strategy,
                "conviction": conviction,
                "suggested_timeframe": timeframe,
                "rules": {
                    "entry": "Wait for trigger or pullback to indicator reference line",
                    "exit": "Take profit at target or stop loss criteria",
                    "filter": "Avoid trading if spread expands or volume collapses"
                }
            }
        }
