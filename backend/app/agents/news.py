from typing import Dict, Any, List
from app.agents.base import BaseAgent

class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="News Agent",
            role_description=(
                "You are an institutional financial news researcher. "
                "Your role is to analyze current headlines, press releases, corporate filings, "
                "and classify events as Bullish, Bearish, or Neutral, explaining the market impact."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        news_items = inputs.get("news", [])

        if not news_items:
            return {
                "explanation": f"No recent news articles found for {ticker}.",
                "confidence": 50,
                "data": {"impact": "Neutral", "sentiment_score": 0.0}
            }

        try:
            user_prompt = (
                f"Analyze this news stream for {ticker}:\n{news_items}\n"
                "Return a JSON evaluating the news sentiment (Bullish/Bearish/Neutral), an aggregate sentiment score (-1 to +1), and key impact explanation."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, news_items)

    def _run_heuristic(self, ticker: str, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        bullish_keywords = ["beat", "buy", "growth", "jump", "surge", "acquisition", "upgrade", "approved", "positive", "exceeds"]
        bearish_keywords = ["miss", "sell", "decline", "fall", "drop", "lawsuit", "investigation", "downgrade", "debt", "negative", "warns"]

        score = 0.0
        analyzed = []
        for item in news_items:
            title = item.get("title", "").lower()
            summary = item.get("summary", "").lower() or item.get("publisher", "").lower()
            text = f"{title} {summary}"
            
            item_score = 0.0
            for w in bullish_keywords:
                if w in text:
                    item_score += 0.2
            for w in bearish_keywords:
                if w in text:
                    item_score -= 0.2
            
            # Clamp item score
            item_score = max(-1.0, min(1.0, item_score))
            score += item_score
            
            sentiment = "Neutral"
            if item_score > 0.1:
                sentiment = "Bullish"
            elif item_score < -0.1:
                sentiment = "Bearish"
                
            analyzed.append({
                "headline": item.get("title"),
                "sentiment": sentiment,
                "score": round(item_score, 2)
            })

        avg_score = score / len(news_items) if news_items else 0.0
        avg_score = max(-1.0, min(1.0, avg_score))
        
        impact = "Neutral"
        if avg_score > 0.15:
            impact = "Bullish"
        elif avg_score < -0.15:
            impact = "Bearish"

        explanation = (
            f"News analysis for {ticker} indicates a {impact.lower()} sentiment. "
            f"Evaluated {len(news_items)} news headlines with an average sentiment score of {avg_score:.2f}."
        )

        return {
            "explanation": explanation,
            "confidence": 70,
            "data": {
                "ticker": ticker,
                "impact": impact,
                "sentiment_score": float(avg_score),
                "articles": analyzed
            }
        }
