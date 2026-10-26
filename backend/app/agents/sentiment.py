from typing import Dict, Any
from app.agents.base import BaseAgent

class SentimentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Sentiment Agent",
            role_description=(
                "You are an expert market sentiment analyst. "
                "Your role is to assess market crowd psychology: Fear & Greed Index, "
                "Put/Call Ratio (PCR), retail positioning metrics (social sentiment), and order book imbalances."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        sentiment_data = inputs.get("sentiment_data", {})

        try:
            user_prompt = (
                f"Evaluate the market sentiment for {ticker} with this information:\n{sentiment_data}\n"
                "Return a JSON mapping crowd sentiment, fear & greed state, retail positioning bias, and market mood."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, sentiment_data)

    def _run_heuristic(self, ticker: str, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        # Heuristics for sentiment
        fear_greed = sentiment_data.get("fear_greed_index", 50) # 0 to 100
        pcr = sentiment_data.get("put_call_ratio", 1.0) # PCR: >1 bearish, <1 bullish
        social_score = sentiment_data.get("social_score", 0.0) # -1.0 to 1.0

        fg_state = "Neutral"
        if fear_greed > 75:
            fg_state = "Extreme Greed"
        elif fear_greed > 55:
            fg_state = "Greed"
        elif fear_greed < 25:
            fg_state = "Extreme Fear"
        elif fear_greed < 45:
            fg_state = "Fear"

        crowd_bias = "Neutral"
        if pcr < 0.75 and social_score > 0.2:
            crowd_bias = "Bullish"
        elif pcr > 1.2 and social_score < -0.2:
            crowd_bias = "Bearish"

        explanation = (
            f"Sentiment analysis for {ticker} shows {fg_state} (Fear & Greed Index: {fear_greed}). "
            f"Options PCR is at {pcr:.2f}, indicating a {crowd_bias.lower()} positioning bias. "
            f"Social media sentiment index score is {social_score:.2f}."
        )

        return {
            "explanation": explanation,
            "confidence": 75,
            "data": {
                "ticker": ticker,
                "fear_greed": fear_greed,
                "fear_greed_state": fg_state,
                "put_call_ratio": pcr,
                "social_sentiment": social_score,
                "crowd_bias": crowd_bias
            }
        }
