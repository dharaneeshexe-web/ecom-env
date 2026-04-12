"""
tasks.py – Task configurations for three difficulty levels.

Each config controls how many steps an episode runs, what fraud prevalence to
inject, and whether to enable partial-refund scenarios.
"""

from typing import Dict, Any

TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "fraud_level": 0.15,
        "n_steps": 50,
        "price_range": (10, 150),
        "partial_refund_enabled": False,
        "description": (
            "Low-fraud environment. The agent mostly encounters legitimate "
            "returns with clear-cut reason codes. Full-refund vs. reject decisions."
        ),
    },
    "medium": {
        "fraud_level": 0.40,
        "n_steps": 75,
        "price_range": (10, 350),
        "partial_refund_enabled": True,
        "description": (
            "Moderate fraud. Mixed return reasons including ambiguous cases. "
            "Partial-refund action is unlocked."
        ),
    },
    "hard": {
        "fraud_level": 0.70,
        "n_steps": 100,
        "price_range": (10, 500),
        "partial_refund_enabled": True,
        "description": (
            "High-fraud environment. Most returns carry elevated fraud risk. "
            "Agent must balance customer satisfaction with loss prevention."
        ),
    },
}
