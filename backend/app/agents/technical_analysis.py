import pandas as pd
import numpy as np
from typing import Dict, Any
from app.agents.base import BaseAgent

class TechnicalAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Technical Analysis Agent",
            role_description=(
                "You are an elite technical analysis quant agent. "
                "Your role is to evaluate technical indicators: MACD, RSI, EMAs, SMAs, "
                "ATR, Bollinger Bands, and Stochastic indicators to determine market direction."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        ohlcv = inputs.get("ohlcv", [])
        
        # Calculate technical indicators
        ta_data = self._calculate_indicators(ohlcv)
        if not ta_data:
            return {
                "explanation": f"Insufficient data for technical analysis on {ticker}.",
                "confidence": 0,
                "data": {}
            }

        # Try to use LLM for synthesis
        try:
            user_prompt = (
                f"Synthesize this technical indicator data for {ticker}:\n{ta_data}\n"
                "Return a JSON summarizing technical trend, momentum, volatility, and indicator states."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            # Heuristic synthesis
            return self._run_heuristic(ticker, ta_data)

    def _calculate_indicators(self, ohlcv: list) -> Dict[str, Any]:
        if len(ohlcv) < 20:
            return {}

        df = pd.DataFrame(ohlcv)
        
        # 1. SMAs & EMAs
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
        df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
        
        # 2. RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["rsi"] = df["rsi"].fillna(50)
        
        # 3. Bollinger Bands
        df["bb_mid"] = df["sma_20"]
        df["bb_std"] = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_mid"] + (2 * df["bb_std"])
        df["bb_lower"] = df["bb_mid"] - (2 * df["bb_std"])
        
        # 4. ATR
        high_low = df["high"] - df["low"]
        high_cp = (df["high"] - df["close"].shift(1)).abs()
        low_cp = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=14).mean().fillna(0)

        # 5. MACD
        df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        last_row = df.iloc[-1]
        
        return {
            "close": float(last_row["close"]),
            "sma_20": float(last_row["sma_20"]) if not pd.isna(last_row["sma_20"]) else None,
            "ema_20": float(last_row["ema_20"]) if not pd.isna(last_row["ema_20"]) else None,
            "ema_50": float(last_row["ema_50"]) if not pd.isna(last_row["ema_50"]) else None,
            "rsi": float(last_row["rsi"]),
            "bb_upper": float(last_row["bb_upper"]) if not pd.isna(last_row["bb_upper"]) else None,
            "bb_lower": float(last_row["bb_lower"]) if not pd.isna(last_row["bb_lower"]) else None,
            "macd": float(last_row["macd"]) if not pd.isna(last_row["macd"]) else None,
            "macd_signal": float(last_row["signal"]) if not pd.isna(last_row["signal"]) else None,
            "atr": float(last_row["atr"])
        }

    def _run_heuristic(self, ticker: str, ta_data: Dict[str, Any]) -> Dict[str, Any]:
        rsi = ta_data["rsi"]
        macd = ta_data.get("macd")
        signal = ta_data.get("macd_signal")
        close = ta_data["close"]
        ema_20 = ta_data.get("ema_20")
        ema_50 = ta_data.get("ema_50")
        
        rsi_signal = "Neutral"
        if rsi > 70:
            rsi_signal = "Overbought"
        elif rsi < 30:
            rsi_signal = "Oversold"

        trend = "Neutral"
        if ema_20 and ema_50:
            if ema_20 > ema_50 and close > ema_20:
                trend = "Bullish"
            elif ema_20 < ema_50 and close < ema_20:
                trend = "Bearish"

        macd_signal = "Neutral"
        if macd and signal:
            macd_signal = "Bullish Crossover" if macd > signal else "Bearish Crossover"

        explanation = (
            f"Technical indicators for {ticker} show a {trend.lower()} trend state. "
            f"RSI is at {rsi:.2f} ({rsi_signal}). MACD displays a {macd_signal.lower()}. "
            f"Close is {close:.2f} relative to EMA20 of {ema_20:.2f}."
        )

        rating = "Hold"
        if trend == "Bullish" and macd_signal == "Bullish Crossover" and rsi < 65:
            rating = "Buy"
        elif trend == "Bearish" and macd_signal == "Bearish Crossover" and rsi > 35:
            rating = "Sell"

        return {
            "explanation": explanation,
            "confidence": 80,
            "data": {
                "ticker": ticker,
                "indicators": ta_data,
                "trend_status": trend,
                "rsi_status": rsi_signal,
                "macd_status": macd_signal,
                "rating": rating
            }
        }
