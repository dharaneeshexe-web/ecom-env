"""
baseline.py - Gemini-powered agent for the EcommerceReturnEnv.

Usage
-----
  export GEMINI_API_KEY=<your_key>
  python baseline.py [--task easy|medium|hard] [--seed 42] [--verbose]

The agent uses google-generativeai to call Gemini 1.5 Flash.
On API errors or unparseable responses it falls back to a heuristic rule.

NOTE: SYSTEM_PROMPT and heuristic_action are importable from this module
without triggering any API calls or sys.exit — safe for server.py import.
"""

import json
import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from env import EcommerceReturnEnv
from grader import grade
from models import Action
from tasks import TASKS

# -- Importable constants (no side-effects) -----------------------------------

SYSTEM_PROMPT = """You are an AI decision engine for an e-commerce return-management system.
You will receive details about a customer return request and must decide the best action.

Actions:
  0 = approve_full_refund   (best when item is clearly defective / wrong, low fraud risk)
  1 = reject_return         (best when fraud risk is high OR return is outside policy)
  2 = offer_partial_refund  (best for ambiguous cases with moderate risk)

Policy rules:
  - If fraud_risk_score >= 0.55 -> strongly consider reject (1)
  - If days_since_purchase >= 20 -> policy window expired, lean toward reject (1)
  - If return_reason is defective_item or wrong_item_shipped AND fraud_risk < 0.35 -> approve (0)
  - If uncertain -> offer partial refund (2) when available, else reject (1)

Respond with ONLY a JSON object like:
{"action": <0|1|2>, "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}
"""


def heuristic_action(obs) -> Action:
    """Simple rule-based fallback when LLM is unavailable. Safe to call any time."""
    if obs.fraud_risk >= 0.55 or obs.days_since_purchase >= 20:
        return Action(action_type=1, confidence=0.8,
                      reasoning="heuristic: high risk or expired")
    if obs.return_reason in (0, 1, 3) and obs.fraud_risk < 0.35:
        return Action(action_type=0, confidence=0.85,
                      reasoning="heuristic: clear valid reason")
    return Action(action_type=2, confidence=0.6,
                  reasoning="heuristic: ambiguous case")


# -- Internal helpers ---------------------------------------------------------

def _build_prompt(obs_dict: dict, step: int) -> str:
    return (
        SYSTEM_PROMPT
        + f"\n\nStep {step} -- Customer return request:\n"
        + json.dumps(obs_dict, indent=2)
        + "\n\nYour decision:"
    )


def run_episode(task_key: str, seed: int, verbose: bool) -> None:
    # API key checked here, not at module level, so imports never crash the server
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    config  = TASKS[task_key]
    n_steps = config["n_steps"]

    env = EcommerceReturnEnv(config, seed=seed)
    obs = env.reset(seed=seed)

    llm_calls     = 0
    llm_fallbacks = 0
    step          = 0

    print(f"\n{'='*60}")
    print(f"  EcommerceReturn-v1  |  Task: {task_key.upper()}  |  Seed: {seed}")
    print(f"  Steps: {n_steps}  |  Fraud target: {config['fraud_level']*100:.0f}%")
    print(f"{'='*60}\n")

    while not env.done:
        step += 1
        prompt = _build_prompt(obs.to_prompt_dict(), step)

        action: Action
        try:
            response = model.generate_content(prompt)
            raw = response.text.strip()
            if "```" in raw:
                raw = raw.split("```")[1].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
            parsed = json.loads(raw)
            action = Action(
                action_type=int(parsed["action"]),
                confidence=float(parsed.get("confidence", 1.0)),
                reasoning=parsed.get("reasoning", ""),
            )
            llm_calls += 1
        except Exception as exc:
            llm_fallbacks += 1
            llm_calls += 1
            if verbose:
                print(f"  [Step {step}] LLM error ({type(exc).__name__}), using heuristic")
            action = heuristic_action(obs)

        obs, reward, done, info = env.step(action)

        if verbose:
            print(
                f"  [Step {step:3d}] action={action.label:22s} "
                f"reward={reward.value:+7.2f}  conf={action.confidence:.2f}  "
                f"fraud_intercepted={reward.fraud_intercepted}"
            )

        time.sleep(0.3)  # free-tier rate-limit guard

    metrics = env.metrics
    report  = grade(
        metrics=metrics,
        task_difficulty=task_key,
        llm_calls=llm_calls,
        llm_fallbacks=llm_fallbacks,
        seed=seed,
    )

    print(f"\n{'='*60}")
    print("  EPISODE COMPLETE -- GRADE REPORT")
    print(f"{'='*60}")
    print(f"  Task          : {report.task_difficulty}")
    print(f"  Seed          : {report.seed}")
    print(f"  Steps         : {metrics.total_steps}")
    print(f"  Total Profit  : {metrics.profit:+.2f}")
    print(f"  Fraud caught  : {metrics.fraud_intercepted}")
    print(
        f"  Correct decs  : {metrics.correct_decisions}/{metrics.total_steps} "
        f"({100*metrics.correct_decisions/max(1,metrics.total_steps):.1f}%)"
    )
    print(f"\n  -- Sub-scores --")
    print(f"  Profit score        : {report.profit_score:.4f}")
    print(f"  Fraud prev score    : {report.fraud_prevention_score:.4f}")
    print(f"  Decision acc score  : {report.decision_accuracy_score:.4f}")
    print(f"\n  ** FINAL SCORE : {report.score:.4f} **")
    print(f"\n  LLM calls     : {report.llm_calls}  |  Fallbacks: {report.llm_fallbacks}")
    if report.notes:
        print("\n  Notes:")
        for note in report.notes:
            print(f"    * {note}")
    print(f"{'='*60}\n")

    print(json.dumps(report.model_dump(), indent=2))


# -- CLI entry point ----------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini-powered e-commerce return agent")
    parser.add_argument("--task", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    run_episode(args.task, args.seed, args.verbose)
