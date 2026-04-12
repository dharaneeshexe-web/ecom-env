"""
models.py – Typed data contracts for the e-commerce return RL environment.

All objects are Pydantic v2 BaseModels so they can be (de)serialised as JSON,
validated at runtime, and exchanged between the env, agents, and grader.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Return-reason catalogue (0-based int codes used internally by the env)
# ---------------------------------------------------------------------------
RETURN_REASON_LABELS = {
    0: "defective_item",
    1: "wrong_item_shipped",
    2: "changed_mind",
    3: "arrived_late",
    4: "better_price_found",
}


# ---------------------------------------------------------------------------
# Core observation / action / reward
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    """State the agent receives at every step."""
    product_price: float = Field(..., ge=0, description="Item price in USD")
    customer_rating: float = Field(..., ge=1, le=5, description="Seller rating 1–5")
    return_reason: int = Field(..., ge=0, le=4, description="Encoded return reason")
    days_since_purchase: int = Field(..., ge=1, le=30, description="Days since order")
    fraud_risk: float = Field(..., ge=0, le=1, description="Fraud probability 0–1")
    order_value_tier: str = Field(
        "medium",
        description="budget | medium | premium"
    )
    customer_type: str = Field(
        "new",
        description="loyal | fraudster | new"
    )
    is_inspected: bool = Field(
        False,
        description="True if previously inspected"
    )
    investigation_report: Optional[str] = Field(
        None,
        description="Detailed text report explaining the fraud anomaly if inspected."
    )

    @property
    def return_reason_label(self) -> str:
        return RETURN_REASON_LABELS.get(self.return_reason, "unknown")

    def to_prompt_dict(self) -> Dict:
        """Human-readable dict for LLM prompt injection."""
        return {
            "product_price_usd": round(self.product_price, 2),
            "customer_rating": round(self.customer_rating, 2),
            "customer_type": self.customer_type,
            "return_reason": self.return_reason_label,
            "days_since_purchase": self.days_since_purchase,
            "fraud_risk_score": round(self.fraud_risk, 3),
            "order_value_tier": self.order_value_tier,
            "is_inspected": self.is_inspected,
            "investigation_report": self.investigation_report
        }


class Action(BaseModel):
    """
    action_type:
        0 = approve_full_refund
        1 = reject_return
        2 = offer_partial_refund
        3 = inspect_return (multi-step action, reveals true fraud status)
    """
    action_type: int = Field(..., ge=0, le=3)
    confidence: float = Field(
        1.0, ge=0, le=1, description="Agent confidence in chosen action"
    )
    reasoning: Optional[str] = Field(
        None, description="Optional chain-of-thought explanation"
    )

    @property
    def label(self) -> str:
        return {
            0: "approve_full_refund", 
            1: "reject_return", 
            2: "offer_partial_refund",
            3: "inspect_return"
        }.get(self.action_type, "unknown")


class Reward(BaseModel):
    """Step-level reward with an auditable breakdown."""
    value: float
    breakdown: Dict[str, float] = Field(default_factory=dict)
    action_label: str = ""
    fraud_intercepted: bool = False


# ---------------------------------------------------------------------------
# Episode & grading summaries
# ---------------------------------------------------------------------------

class EpisodeMetrics(BaseModel):
    """Accumulated metrics over one episode."""
    total_steps: int = 0
    total_reward: float = 0.0
    profit: float = 0.0
    fraud_losses: float = 0.0
    fraud_intercepted: int = 0
    correct_decisions: int = 0
    full_refunds_approved: int = 0
    returns_rejected: int = 0
    partial_refunds: int = 0
    avg_confidence: float = 0.0


class GradeReport(BaseModel):
    """Final structured result returned by the grader."""
    task_difficulty: str
    score: float = Field(..., ge=0, le=1)
    profit_score: float
    fraud_prevention_score: float
    decision_accuracy_score: float
    episode_metrics: EpisodeMetrics
    llm_calls: int
    llm_fallbacks: int
    seed: int
    notes: List[str] = Field(default_factory=list)
