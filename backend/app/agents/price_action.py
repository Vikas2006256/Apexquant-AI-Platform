from typing import Dict, Any
import numpy as np
from app.agents.base import BaseAgent

class PriceActionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Price Action Agent",
            role_description=(
                "You are an expert price action trader. "
                "Your role is to analyze trend structures, breakout setups, reversals, "
                "compressions (consolidation), expansion phases, and raw candle behaviors."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        ohlcv = inputs.get("ohlcv", [])

        if not ohlcv or len(ohlcv) < 10:
            return {
                "explanation": f"Insufficient data for price action analysis on {ticker}.",
                "confidence": 0,
                "data": {}
            }

        try:
            user_prompt = (
                f"Analyze the price action dynamics for {ticker} using the last 30 periods of OHLCV data:\n{ohlcv[-30:]}\n"
                "Return a JSON summarizing momentum, breakouts, compression vs expansion, and candlestick patterns."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, ohlcv)

    def _run_heuristic(self, ticker: str, ohlcv: list) -> Dict[str, Any]:
        last_n = ohlcv[-15:]
        closes = [x["close"] for x in last_n]
        highs = [x["high"] for x in last_n]
        lows = [x["low"] for x in last_n]
        
        # 1. Calculate candle ranges (high - low)
        ranges = [h - l for h, l in zip(highs, lows)]
        avg_range = sum(ranges) / len(ranges)
        last_range = ranges[-1]
        
        # Compression vs Expansion
        compression_ratio = last_range / avg_range if avg_range > 0 else 1.0
        phase = "Expansion" if compression_ratio > 1.2 else ("Compression" if compression_ratio < 0.8 else "Normal")
        
        # Breakout checks
        breakout = "None"
        resistance_14 = max(highs[:-1])
        support_14 = min(lows[:-1])
        current_close = closes[-1]
        
        if current_close > resistance_14:
            breakout = "Bullish Breakout"
        elif current_close < support_14:
            breakout = "Bearish Breakout"
            
        # Reversal vs Continuation
        # Check if last close goes against previous general direction
        prev_direction = closes[-2] - closes[-6] if len(closes) >= 6 else 0
        last_move = closes[-1] - closes[-2]
        
        market_behavior = "Continuation"
        if prev_direction > 0 and last_move < -avg_range:
            market_behavior = "Potential Reversal Down"
        elif prev_direction < 0 and last_move > avg_range:
            market_behavior = "Potential Reversal Up"
            
        explanation = (
            f"Price action analysis for {ticker} shows the asset is currently in a {phase.lower()} phase. "
            f"A {breakout.lower() if breakout != 'None' else 'no breakout'} is active. "
            f"Recent market dynamics suggest a {market_behavior.lower()} trajectory."
        )

        return {
            "explanation": explanation,
            "confidence": 70,
            "data": {
                "ticker": ticker,
                "market_phase": phase,
                "breakout_status": breakout,
                "behavior": market_behavior,
                "average_range": float(avg_range),
                "last_range": float(last_range)
            }
        }
