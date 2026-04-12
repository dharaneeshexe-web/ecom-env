"""
grader.py – Deterministic, multi-metric grader for the e-commerce return env.

Scoring formula
───────────────
  score = 0.50 × profit_score
        + 0.30 × fraud_prevention_score
        + 0.20 × decision_accuracy_score

All sub-scores are normalised to [0, 1].
"""

from __future__ import annotations
from models import EpisodeMetrics, GradeReport


# ─── Target thresholds (calibrated against the medium-difficulty task) ───────
PROFIT_TARGET = 300.0      # cumulative profit considered "perfect"
FRAUD_CATCH_RATE_TARGET = 0.80  # fraction of fraudulent requests intercepted


def grade(
    metrics: EpisodeMetrics,
    task_difficulty: str = "medium",
    llm_calls: int = 0,
    llm_fallbacks: int = 0,
    seed: int = 42,
) -> GradeReport:
    """
    Compute a normalised score in [0, 1] from episode metrics.

    Parameters
    ----------
    metrics : EpisodeMetrics
        Populated by the env after episode completion.
    task_difficulty : str
        "easy" | "medium" | "hard"
    llm_calls : int
        Total LLM API calls made during the episode.
    llm_fallbacks : int
        Number of times the agent fell back to a heuristic.
    seed : int
        RNG seed used (for reproducibility tracking).

    Returns
    -------
    GradeReport
    """
    notes: list[str] = []

    # ── difficulty scaling ────────────────────────────────────────────────────
    difficulty_multiplier = {"easy": 0.7, "medium": 1.0, "hard": 2.2}.get(
        task_difficulty, 1.0
    )
    effective_profit_target = PROFIT_TARGET * difficulty_multiplier

    # ── sub-score 1: profit ───────────────────────────────────────────────────
    profit_score = float(
        max(0.0, min(1.0, metrics.profit / effective_profit_target))
    )

    # ── sub-score 2: fraud prevention ────────────────────────────────────────
    # Approx total fraud requests = full_refunds that turned out fraudulent
    total_fraud_encounters = max(
        1,
        metrics.fraud_intercepted + (metrics.full_refunds_approved // 3),
    )
    fraud_catch_rate = metrics.fraud_intercepted / total_fraud_encounters
    fraud_prevention_score = float(
        max(0.0, min(1.0, fraud_catch_rate / FRAUD_CATCH_RATE_TARGET))
    )

    # ── sub-score 3: decision accuracy ───────────────────────────────────────
    total_steps = max(1, metrics.total_steps)
    decision_accuracy_score = float(
        max(0.0, min(1.0, metrics.correct_decisions / total_steps))
    )

    # ── weighted composite ────────────────────────────────────────────────────
    score = (
        0.50 * profit_score
        + 0.30 * fraud_prevention_score
        + 0.20 * decision_accuracy_score
    )
    score = round(float(max(0.0, min(1.0, score))), 4)

    # ── notes ─────────────────────────────────────────────────────────────────
    if llm_fallbacks > llm_calls * 0.3:
        notes.append(
            f"High LLM fallback rate ({llm_fallbacks}/{llm_calls}). "
            "Consider prompt tuning."
        )
    if metrics.profit < 0:
        notes.append("Negative cumulative profit — agent over-approved fraudulent refunds.")
    if fraud_prevention_score < 0.3:
        notes.append("Low fraud interception rate. Review rejection policy.")
    if decision_accuracy_score >= 0.9:
        notes.append("Excellent decision accuracy!")

    return GradeReport(
        task_difficulty=task_difficulty,
        score=score,
        profit_score=round(profit_score, 4),
        fraud_prevention_score=round(fraud_prevention_score, 4),
        decision_accuracy_score=round(decision_accuracy_score, 4),
        episode_metrics=metrics,
        llm_calls=llm_calls,
        llm_fallbacks=llm_fallbacks,
        seed=seed,
        notes=notes,
    )
