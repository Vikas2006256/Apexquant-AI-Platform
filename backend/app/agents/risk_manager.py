from typing import Dict, Any
from app.agents.base import BaseAgent

class RiskManager(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Risk Manager",
            role_description=(
                "You are an institutional risk management officer. "
                "Your role is to enforce risk rules, calculate position sizing using Kelly Criterion "
                "or fixed risk models, compute stop loss boundaries, target risk reward ratios (R:R), "
                "and ensure total capital preservation."
            )
        )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ticker = inputs.get("ticker", "UNKNOWN")
        current_price = float(inputs.get("current_price", 100.0))
        atr = float(inputs.get("atr", current_price * 0.02)) # default ATR to 2%
        balance = float(inputs.get("balance", 100000.0))
        user_risk_pct = float(inputs.get("user_risk_pct", 2.0)) # max risk per trade default

        try:
            user_prompt = (
                f"Calculate risk parameters for {ticker} at price {current_price} (ATR: {atr}) "
                f"with capital of {balance} and max risk limit of {user_risk_pct}%:\n"
                "Return a JSON mapping stop loss, targets, position size, risk-reward ratio, and expected value."
            )
            response_str = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=self.role_description + "\nReturn JSON with fields: explanation (str), confidence (int), data (dict)."
            )
            return self.sanitize_json_response(response_str)
        except Exception:
            return self._run_heuristic(ticker, current_price, atr, balance, user_risk_pct)

    def _run_heuristic(self, ticker: str, current_price: float, atr: float, balance: float, user_risk_pct: float) -> Dict[str, Any]:
        # Stop loss at 2 * ATR
        stop_loss_distance = 2 * atr if atr > 0 else current_price * 0.02
        stop_loss = current_price - stop_loss_distance
        
        # Targets: Target 1 (1.5R), Target 2 (2R), Target 3 (3R)
        t1 = current_price + (1.5 * stop_loss_distance)
        t2 = current_price + (2.0 * stop_loss_distance)
        t3 = current_price + (3.0 * stop_loss_distance)

        # Risk Amount in Cash
        risk_cash = balance * (user_risk_pct / 100.0)
        
        # Position Sizing: Risk / Stop Loss Distance
        shares = risk_cash / stop_loss_distance if stop_loss_distance > 0 else 0
        total_position_value = shares * current_price
        
        # Adjust size if position exceeds capital (leveraged check)
        if total_position_value > balance:
            shares = balance / current_price
            total_position_value = balance

        # Expected Value calculation assuming 45% win rate, 2:1 Reward:Risk
        win_rate = 0.45
        avg_win = 2.0 * stop_loss_distance
        avg_loss = stop_loss_distance
        ev = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        ev_ratio = ev / current_price

        explanation = (
            f"Risk parameters determined for {ticker} (entry: {current_price:.2f}). "
            f"Recommended stop loss is {stop_loss:.2f} (2x ATR). Targets set at: "
            f"T1: {t1:.2f}, T2: {t2:.2f}, T3: {t3:.2f}. "
            f"Position sizing permits {shares:.2f} shares (value: ${total_position_value:.2f}) risking {user_risk_pct}% of capital."
        )

        return {
            "explanation": explanation,
            "confidence": 90,
            "data": {
                "ticker": ticker,
                "entry_price": current_price,
                "stop_loss": float(stop_loss),
                "target_1": float(t1),
                "target_2": float(t2),
                "target_3": float(t3),
                "risk_amount_cash": float(risk_cash),
                "shares_to_buy": float(shares),
                "total_position_value": float(total_position_value),
                "risk_reward_ratio": 2.0,
                "expected_value_pct": float(ev_ratio * 100)
            }
        }
