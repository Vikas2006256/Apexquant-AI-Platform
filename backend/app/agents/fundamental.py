from typing import Dict, Any
from app.agents.base import BaseAgent

class FundamentalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Fundamental Analysis Agent",
            role_description=(
                "You are a professional fundamental research analyst. "
                "Your role is to analyze corporate balance sheets, revenue growth, EPS, "
                "operating margins, debt levels, ROE, ROCE, P/E, P/B, and PEG valuation ratios."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        info = inputs.get("fundamental_info", {})

        if not info:
            return {
                "explanation": f"No fundamental financials data available for {ticker}.",
                "confidence": 0,
                "data": {}
            }

        try:
            user_prompt = (
                f"Evaluate the fundamental health of {ticker} given these metrics:\n{info}\n"
                "Return a JSON mapping valuation, growth, margins, debt profile, and overall financial grade."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, info)

    def _run_heuristic(self, ticker: str, info: Dict[str, Any]) -> Dict[str, Any]:
        # Extract fields safely
        pe = info.get("trailingPE")
        peg = info.get("pegRatio")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        margin = info.get("operatingMargins")
        debt_to_equity = info.get("debtToEquity")
        rev_growth = info.get("revenueGrowth")

        valuation_verdict = "Fair Value"
        if pe:
            if pe < 15:
                valuation_verdict = "Undervalued"
            elif pe > 30:
                valuation_verdict = "Overvalued"

        profitability = "Moderate"
        if roe and roe > 0.15:
            profitability = "High"
        elif roe and roe < 0.05:
            profitability = "Low"

        risk_level = "Low"
        if debt_to_equity and debt_to_equity > 150:
            risk_level = "High"

        grade = "B"
        if valuation_verdict == "Undervalued" and profitability == "High" and risk_level == "Low":
            grade = "A"
        elif valuation_verdict == "Overvalued" or risk_level == "High":
            grade = "C"

        explanation = (
            f"Fundamental analysis for {ticker} shows an overall grade of {grade}. "
            f"The asset appears {valuation_verdict.lower()} (P/E: {pe or 'N/A'}, PEG: {peg or 'N/A'}). "
            f"Profitability is {profitability.lower()} (ROE: {f'{roe*100:.1f}%' if roe else 'N/A'}, Operating Margin: {f'{margin*100:.1f}%' if margin else 'N/A'}). "
            f"Debt-to-equity risk profile is {risk_level.lower()}."
        )

        return {
            "explanation": explanation,
            "confidence": 80,
            "data": {
                "ticker": ticker,
                "grade": grade,
                "valuation": valuation_verdict,
                "profitability": profitability,
                "risk_level": risk_level,
                "metrics": {
                    "pe": pe,
                    "peg": peg,
                    "pb": pb,
                    "roe": roe,
                    "operating_margin": margin,
                    "debt_to_equity": debt_to_equity,
                    "revenue_growth": rev_growth
                }
            }
        }
