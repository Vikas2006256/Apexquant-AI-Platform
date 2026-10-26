from typing import Dict, Any
from app.agents.base import BaseAgent

class MacroeconomicAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Macroeconomic Agent",
            role_description=(
                "You are an expert macroeconomic strategist. "
                "Your role is to assess global economic indicators: GDP, CPI (Inflation), "
                "interest rates, unemployment, and Federal Reserve or other central bank policy statements."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        macro_data = inputs.get("macro", {})

        try:
            user_prompt = (
                f"Evaluate the macroeconomic conditions for trading {ticker} given this economic data:\n{macro_data}\n"
                "Return a JSON mapping interest rate environment, inflation trajectory, Central Bank bias, and liquidity cycle impact."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, macro_data)

    def _run_heuristic(self, ticker: str, macro_data: Dict[str, Any]) -> Dict[str, Any]:
        interest_rate = macro_data.get("interest_rate", 5.25)
        inflation_cpi = macro_data.get("inflation_cpi", 3.0)
        central_bank_stance = macro_data.get("central_bank_stance", "Hawkish") # Hawkish, Dovish, Neutral
        gdp_growth = macro_data.get("gdp_growth", 2.0)

        # Basic Macro Regime Logic
        regime = "Stagflation"
        if gdp_growth > 2.0 and inflation_cpi < 3.0:
            regime = "Expansionary Goldilocks"
        elif gdp_growth < 1.0 and inflation_cpi > 3.5:
            regime = "Stagflationary Contraction"
        elif gdp_growth > 2.0 and inflation_cpi > 4.0:
            regime = "Overheating Reflation"
        elif gdp_growth < 1.0 and inflation_cpi < 2.0:
            regime = "Deflationary Slump"

        liquidity_impact = "Neutral"
        if central_bank_stance == "Dovish" or interest_rate < 3.0:
            liquidity_impact = "Highly Supportive (Easy Money)"
        elif central_bank_stance == "Hawkish" or interest_rate > 4.5:
            liquidity_impact = "Restrictive (Tight Money)"

        explanation = (
            f"Macroeconomic conditions suggest an {regime} regime. "
            f"Central bank stance is {central_bank_stance} with interest rates at {interest_rate:.2f}%. "
            f"Liquidity impact is deemed {liquidity_impact} for risk assets like {ticker}."
        )

        return {
            "explanation": explanation,
            "confidence": 80,
            "data": {
                "ticker": ticker,
                "economic_regime": regime,
                "interest_rate": interest_rate,
                "inflation_cpi": inflation_cpi,
                "central_bank_stance": central_bank_stance,
                "liquidity_impact": liquidity_impact
            }
        }
