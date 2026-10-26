from typing import Dict, Any, List
from app.agents.base import BaseAgent

class SMCAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Smart Money Concepts Agent",
            role_description=(
                "You are an expert institutional trader specializing in Smart Money Concepts (SMC). "
                "Your role is to map out market structures, detecting Order Blocks, Fair Value Gaps (FVG), "
                "Liquidity Sweeps, Break of Structure (BOS), and Change of Character (CHOCH)."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        ohlcv = inputs.get("ohlcv", [])

        if not ohlcv or len(ohlcv) < 15:
            return {
                "explanation": f"Insufficient data for SMC analysis on {ticker}.",
                "confidence": 0,
                "data": {}
            }

        try:
            user_prompt = (
                f"Analyze the market structure for {ticker} using SMC with the following data:\n{ohlcv[-20:]}\n"
                "Return a JSON mapping Order Blocks, FVGs, BOS/CHOCH levels, and premium/discount zones."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, ohlcv)

    def _run_heuristic(self, ticker: str, ohlcv: list) -> Dict[str, Any]:
        # Detect Fair Value Gaps (FVG)
        # Bullish FVG: Low of candle i > High of candle i-2
        # Bearish FVG: High of candle i < Low of candle i-2
        fvgs = []
        for i in range(2, len(ohlcv)):
            c1 = ohlcv[i-2]
            c2 = ohlcv[i-1]
            c3 = ohlcv[i]
            
            # Bullish FVG
            if c3["low"] > c1["high"]:
                fvgs.append({
                    "type": "Bullish FVG",
                    "top": float(c3["low"]),
                    "bottom": float(c1["high"]),
                    "index": i-1
                })
            # Bearish FVG
            elif c3["high"] < c1["low"]:
                fvgs.append({
                    "type": "Bearish FVG",
                    "top": float(c1["low"]),
                    "bottom": float(c3["high"]),
                    "index": i-1
                })

        # Order Blocks (OB)
        # Bullish OB: Last down-candle before a strong impulse up (e.g. 3 consecutive up-candles)
        order_blocks = []
        for i in range(1, len(ohlcv) - 3):
            c_prev = ohlcv[i]
            c1 = ohlcv[i+1]
            c2 = ohlcv[i+2]
            c3 = ohlcv[i+3]
            
            if c_prev["close"] < c_prev["open"]: # Down candle
                if c1["close"] > c1["open"] and c2["close"] > c2["open"] and c3["close"] > c3["open"]:
                    if c3["close"] > c_prev["open"]: # impulse
                        order_blocks.append({
                            "type": "Bullish OB",
                            "high": float(c_prev["high"]),
                            "low": float(c_prev["low"]),
                            "price": float(c_prev["close"]),
                            "index": i
                        })
            elif c_prev["close"] > c_prev["open"]: # Up candle
                if c1["close"] < c1["open"] and c2["close"] < c2["open"] and c3["close"] < c3["open"]:
                    if c3["close"] < c_prev["open"]: # impulse
                        order_blocks.append({
                            "type": "Bearish OB",
                            "high": float(c_prev["high"]),
                            "low": float(c_prev["low"]),
                            "price": float(c_prev["close"]),
                            "index": i
                        })

        # BOS/CHOCH Detection
        bos = "None"
        recent_highs = [x["high"] for x in ohlcv[-10:-1]]
        recent_lows = [x["low"] for x in ohlcv[-10:-1]]
        highest_high = max(recent_highs) if recent_highs else 0
        lowest_low = min(recent_lows) if recent_lows else 0
        
        current_close = ohlcv[-1]["close"]
        if current_close > highest_high:
            bos = "Bullish BOS"
        elif current_close < lowest_low:
            bos = "Bearish BOS"

        explanation = (
            f"SMC structural mapping for {ticker} shows: "
            f"Detected {len(fvgs)} FVGs and {len(order_blocks)} Order Blocks. "
            f"Current structure shift is {bos.lower() if bos != 'None' else 'Neutral'}."
        )

        return {
            "explanation": explanation,
            "confidence": 75,
            "data": {
                "ticker": ticker,
                "fvgs": fvgs[-3:] if fvgs else [], # return latest 3
                "order_blocks": order_blocks[-2:] if order_blocks else [],
                "market_structure_shift": bos
            }
        }
