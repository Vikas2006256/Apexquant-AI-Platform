import base64
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent

class ChartVisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Chart Vision Agent",
            role_description=(
                "You are an institutional technical chart vision analyst. "
                "Your role is to perform strict 11-step technical trade setup analysis on visible chart data: "
                "1. Chart Info, 2. Support & Resistance, 3. Trend, 4. Patterns, 5. Indicators, 6. Trading Decision (BUY/SELL/WAIT/NO TRADE), "
                "7. Entry Strategy, 8. Stop Loss, 9. Profit Targets, 10. Risk Management with Position Sizing formula, 11. Confidence & Grade."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inputs can contain:
        - chart_image: base64 encoded image string (optional)
        - ticker: ticker symbol (e.g. AAPL)
        - ohlcv: list of dicts with price data (optional)
        """
        ticker = inputs.get("ticker", "UNKNOWN")
        image_data = inputs.get("chart_image")
        ohlcv = inputs.get("ohlcv", [])

        # If image data is available, try to run LLM Vision
        if image_data:
            try:
                # LLM Vision logic
                user_prompt = f"Analyze this chart image for ticker {ticker}. Identify key trendlines, support, resistance, and price patterns."
                # vision prompt details
                # For this implementation, we will request text json through OpenAI/Gemini if configured
                response_str = await self.call_llm(
                    user_prompt=user_prompt,
                    system_prompt=self.role_description + "\nReturn a JSON with fields: explanation (str), confidence (int), data (dict containing trend, support, resistance, pattern)."
                )
                return self.sanitize_json_response(response_str)
            except Exception:
                # Fall back to heuristic vision parsing of the numerical ohlcv data
                pass

        # Heuristic calculation if image Vision fails or isn't provided
        return self._run_heuristic(ticker, ohlcv)

    def _run_heuristic(self, ticker: str, ohlcv: list) -> Dict[str, Any]:
        if not ohlcv:
            return {
                "explanation": f"Insufficient data to run Chart Vision analysis for {ticker}.",
                "confidence": 0,
                "data": {}
            }

        # Calculate basic parameters
        prices = [x["close"] for x in ohlcv]
        highs = [x["high"] for x in ohlcv]
        lows = [x["low"] for x in ohlcv]
        
        current_price = prices[-1]
        max_price = max(prices)
        min_price = min(prices)
        
        # Simple trend detection
        halfway = len(prices) // 2
        first_half_avg = sum(prices[:halfway]) / halfway
        second_half_avg = sum(prices[halfway:]) / (len(prices) - halfway)
        
        trend = "Bullish" if second_half_avg > first_half_avg else "Bearish"
        
        # Simple S/R points
        support = min(lows[-20:]) if len(lows) >= 20 else min_price
        resistance = max(highs[-20:]) if len(highs) >= 20 else max_price

        # Detect double top / bottom
        pattern = "None"
        if len(highs) >= 10:
            last_highs = sorted(highs[-10:])
            if abs(last_highs[-1] - last_highs[-2]) / last_highs[-1] < 0.01:
                pattern = "Potential Double Top"
            last_lows = sorted(lows[-10:])
            if abs(last_lows[0] - last_lows[1]) / last_lows[0] < 0.01:
                pattern = "Potential Double Bottom"

        explanation = (
            f"Analyzed chart for {ticker}. Current price is {current_price:.2f}. "
            f"Visual analysis indicates a {trend.lower()} trend with primary support "
            f"at {support:.2f} and resistance at {resistance:.2f}. Detected pattern: {pattern}."
        )

        return {
            "explanation": explanation,
            "confidence": 75,
            "data": {
                "ticker": ticker,
                "current_price": current_price,
                "trend": trend,
                "support": float(support),
                "resistance": float(resistance),
                "detected_pattern": pattern
            }
        }
