"""
env.py – OpenEnv-compliant EcommerceReturnEnv.

Implements the full OpenEnv interface:
  • reset(seed) → Observation
  • step(action) → (Observation, Reward, done, info)
  • render()
  • close()
  • task_config property

Reward design
─────────────
Action 0 – approve_full_refund
    If fraud_risk < 0.4  and  return_reason ∈ {defective, wrong_item, arrived_late}
        reward = +8   (correct approval: good customer service, low risk)
    Else if fraud_risk >= 0.4
        reward = -price * 0.65  (fraudulent refund absorbed as loss)
    Else
        reward = -price * 0.15  (marginal case: money-back but low risk)

Action 1 – reject_return
    If fraud_risk >= 0.5  or  days_since_purchase >= 20
        reward = +price * 0.10  (correct rejection: prevented loss)
    Else
        reward = -5            (wrong rejection: customer satisfaction hit)

Action 2 – offer_partial_refund  (only available when task.partial_refund_enabled)
    reward = +4  always (compromise, safe middle ground)
    If partial_refund_enabled == False → treated as reject (action 1 fallback)
"""

import numpy as np
from typing import Tuple, Any, Dict

from models import Observation, Action, Reward, EpisodeMetrics


class EcommerceReturnEnv:
    """
    OpenEnv-style environment for e-commerce return decision making.

    Parameters
    ----------
    config : dict
        One of the task configs from tasks.py (easy / medium / hard).
    seed : int
        RNG seed for reproducibility.
    """

    # OpenEnv metadata
    ENV_ID = "EcommerceReturn-v1"
    OPENENV_VERSION = "1.0"

    def __init__(self, config: Dict[str, Any], seed: int = 42):
        self.config = config
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self._metrics = EpisodeMetrics()
        self._step_count = 0
        self._done = False
        self.current_request: Dict = {}
        self.reset(seed=seed)

    # ------------------------------------------------------------------
    # OpenEnv API
    # ------------------------------------------------------------------

    def reset(self, seed: int | None = None) -> Observation:
        """Reset environment state and metrics. Returns initial observation."""
        if seed is not None:
            self.seed = seed
            self.rng = np.random.default_rng(seed)
        self._metrics = EpisodeMetrics()
        self._step_count = 0
        self._done = False
        self.current_request = self._generate_request()
        return self._make_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """
        Apply action to current state.

        Returns
        -------
        observation : Observation
            Next state.
        reward : Reward
            Step reward with breakdown dict.
        done : bool
            True when episode is complete.
        info : dict
            Diagnostic info.
        """
        if self._done:
            raise RuntimeError("Episode finished. Call reset() before stepping again.")

        r = self.current_request

        if action.action_type == 3:  # Inspect Multi-step
            # Reveal true fraud status & report
            if not r["is_inspected"]:
                r["is_inspected"] = True
                r["fraud"] = 1.0 if r["is_fraud_injected"] else 0.0
                r["investigation_report"] = "Network analysis reveals cross-regional IP match & duplicate card" if r["is_fraud_injected"] else "Customer history verified clean via manual review."
                reward_value, breakdown, fraud_intercepted = -5.0, {"inspection_cost": -5.0}, False
            else:
                reward_value, breakdown, fraud_intercepted = -2.0, {"redundant_inspection": -2.0}, False
            
            # Metric update
            self._metrics.total_steps += 1
            self._metrics.total_reward += reward_value
            self._metrics.profit += reward_value
        else:
            # Standard terminal action for this request
            reward_value, breakdown, fraud_intercepted = self._compute_reward(action, r)

            # Update metrics
            self._metrics.total_steps += 1
            self._metrics.total_reward += reward_value
            self._metrics.profit += reward_value
            if fraud_intercepted:
                self._metrics.fraud_intercepted += 1
            if action.action_type == 0:
                self._metrics.full_refunds_approved += 1
            elif action.action_type == 1:
                self._metrics.returns_rejected += 1
            else:
                self._metrics.partial_refunds += 1

            optimal = self._optimal_action(r)
            if action.action_type == optimal:
                self._metrics.correct_decisions += 1

            # Only step forward in the data if the action was terminal (not inspect)
            self._step_count += 1
            self.current_request = self._generate_request()

        n_steps = self.config.get("n_steps", 50)
        self._done = self._step_count >= n_steps

        # Use new state after potential transition
        obs = self._make_observation()

        reward = Reward(
            value=reward_value,
            breakdown=breakdown,
            action_label=action.label,
            fraud_intercepted=fraud_intercepted,
        )
        info = {
            "step": self._step_count,
            "done": self._done,
            "optimal_action": self._optimal_action(self.current_request) if not self._done else None,
        }
        return obs, reward, self._done, info

    def render(self) -> str:
        """Return a human-readable summary of current state."""
        r = self.current_request
        lines = [
            f"=== EcommerceReturnEnv | Step {self._step_count} ===",
            f"  Price        : ${r['price']:.2f}",
            f"  Rating       : {r['rating']:.1f}/5",
            f"  Customer Type: {r['customer_type']}",
            f"  Return reason: {r['reason_label']} ({r['reason']})",
            f"  Days elapsed : {r['days']}",
            f"  Fraud risk   : {r['fraud']:.3f} {'(INSPECTED)' if r['is_inspected'] else ''}",
            f"  Tier         : {r['tier']}",
            f"  Metrics      : profit={self._metrics.profit:.1f}  "
            f"fraud_intercepted={self._metrics.fraud_intercepted}  "
        ]
        return "\n".join(lines)

    def state(self) -> Observation:
        """Return the current environment state (required by OpenEnv spec)."""
        return self._make_observation()

    def close(self):
        """Release any resources."""
        pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def task_config(self) -> Dict[str, Any]:
        return self.config

    @property
    def metrics(self) -> EpisodeMetrics:
        self._metrics.total_steps = self._step_count
        return self._metrics

    @property
    def done(self) -> bool:
        return self._done

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_observation(self) -> Observation:
        r = self.current_request
        return Observation(
            product_price=r["price"],
            customer_rating=r["rating"],
            return_reason=r["reason"],
            days_since_purchase=r["days"],
            fraud_risk=r["fraud"],
            order_value_tier=r["tier"],
            customer_type=r["customer_type"],
            is_inspected=r["is_inspected"],
            investigation_report=r.get("investigation_report")
        )

    def _generate_request(self) -> Dict:
        lo, hi = self.config.get("price_range", (10, 500))
        price = float(self.rng.uniform(lo, hi))
        fraud_level = self.config.get("fraud_level", 0.3)

        # 1. Base Fraud Roll
        is_fraud = self.rng.random() < fraud_level

        # 2. Determine Customer Type (loyal, fraudster, new)
        cust_roll = self.rng.random()
        if cust_roll < 0.2:
            customer_type = "loyal"
            if is_fraud and self.rng.random() < 0.9: 
                # Loyal customers rarely commit fraud
                is_fraud = False
        elif cust_roll > 0.85:
            customer_type = "fraudster"
            if not is_fraud and self.rng.random() < 0.8:
                # Fraudsters usually commit fraud
                is_fraud = True
        else:
            customer_type = "new"

        # 3. Assign observable fraud_risk
        if is_fraud:
            # High risk score, but loyal appears safer, fraudster appears obviously bad
            if customer_type == "loyal":
                fraud = float(self.rng.uniform(0.40, 0.60))
            elif customer_type == "fraudster":
                fraud = float(self.rng.uniform(0.70, 0.99))
            else:
                fraud = float(self.rng.uniform(0.55, 0.85))
        else:
            if customer_type == "loyal":
                fraud = float(self.rng.uniform(0.0, 0.20))
            else:
                fraud = float(self.rng.uniform(0.10, 0.45))

        reason = int(self.rng.integers(0, 5))
        days = int(self.rng.integers(1, 31))
        rating = float(self.rng.uniform(1, 5))
        if customer_type == "loyal": rating = float(self.rng.uniform(4, 5))

        if price < 60:
            tier = "budget"
        elif price < 200:
            tier = "medium"
        else:
            tier = "premium"

        from models import RETURN_REASON_LABELS
        return {
            "price": price,
            "rating": rating,
            "reason": reason,
            "reason_label": RETURN_REASON_LABELS.get(reason, "unknown"),
            "days": days,
            "fraud": fraud,
            "tier": tier,
            "is_fraud_injected": is_fraud,
            "customer_type": customer_type,
            "is_inspected": False
        }

    def _compute_reward(
        self, action: Action, r: Dict
    ) -> Tuple[float, Dict[str, float], bool]:
        # Underlying truth matters for reward, even if they didn't inspect
        fraud = 1.0 if r["is_fraud_injected"] else 0.0
        price = r["price"]
        reason = r["reason"]
        days = r["days"]
        customer_type = r["customer_type"]
        partial_ok = self.config.get("partial_refund_enabled", False)

        fraud_intercepted = False
        breakdown: Dict[str, float] = {}

        if action.action_type == 2 and not partial_ok:
            effective_action = 1
        else:
            effective_action = action.action_type

        # Happy customer bonus scalar
        cs_bonus = 15.0 if customer_type == "loyal" else 8.0

        if effective_action == 0:  # approve full refund
            if fraud == 1.0:
                val = -(price * 0.65)
                breakdown["fraud_loss"] = val
            elif reason in (0, 1, 3):
                val = cs_bonus
                breakdown["customer_happy"] = val
            else:
                val = -(price * 0.12)
                breakdown["marginal_refund"] = val

        elif effective_action == 1:  # reject
            if fraud == 1.0 or days >= 30:
                val = price * 0.10
                breakdown["rejection_gain"] = val
                if fraud == 1.0:
                    fraud_intercepted = True
                    breakdown["fraud_intercepted"] = val
            else:
                val = -8.0 if customer_type == "loyal" else -4.0
                breakdown["wrong_rejection_penalty"] = val

        else:  # offer partial refund (action 2)
            val = 4.0
            breakdown["partial_settlement"] = val
            if fraud == 1.0:
                loss = -(price * 0.20)
                val += loss
                breakdown["partial_fraud_loss"] = loss

        return float(val), breakdown, fraud_intercepted

    def _optimal_action(self, r: Dict) -> int:
        """Heuristic optimal action for accuracy measurement."""
        # Note: if it's uncertain and not inspected, optimal is 3
        fraud_val = r["fraud"]
        is_fraud = r["is_fraud_injected"]
        days = r["days"]
        reason = r["reason"]
        partial_ok = self.config.get("partial_refund_enabled", False)

        if not r["is_inspected"]:
            # If uncertain, we should inspect
            if 0.40 <= fraud_val <= 0.75:
                return 3

        # After inspection, or if it was obvious
        if is_fraud or days >= 30:
            return 1  # reject
        if reason in (0, 1, 3) and not is_fraud:
            return 0  # approve
        if partial_ok:
            return 2  # partial
        return 1  # default reject
