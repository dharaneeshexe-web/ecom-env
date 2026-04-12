#!/usr/bin/env python3
"""
inference.py -- OpenEnv-compliant inference script for EcommerceReturn-v1.

STDOUT FORMAT (required):
    [START] task=<task> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Env vars:
    API_BASE_URL   LLM endpoint   (default: https://router.huggingface.co/v1)
    MODEL_NAME     Model id       (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       API key        (or API_KEY / OPENAI_API_KEY)
"""

import os
import sys
import json
import time
from typing import List, Optional

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from openai import OpenAI

from env import EcommerceReturnEnv
from models import Action
from tasks import TASKS
from grader import grade

# -- Config -------------------------------------------------------------------
API_KEY = (
    os.getenv("HF_TOKEN")
    or os.getenv("API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "EcommerceReturn-v1"
SEED         = 42
SUCCESS_SCORE_THRESHOLD = 0.40

SYSTEM_PROMPT = (
    "You are an AI decision engine for e-commerce return requests.\n\n"
    "Actions available:\n"
    "  0 = approve_full_refund\n"
    "  1 = reject_return\n"
    "  2 = offer_partial_refund\n"
    "  3 = inspect_return\n\n"
    "Policy guidelines:\n"
    "  - fraud_risk >= 0.8 or customer_type == 'fraudster' -> reject (1)\n"
    "  - days_since_purchase >= 30 -> reject (1)\n"
    "  - customer_type == 'loyal' AND fraud_risk < 0.3 -> approve (0)\n"
    "  - ambiguous fraud (0.4 to 0.75) AND not inspected -> inspect (3)\n"
    "  - return_reason in [defective_item, wrong_item_shipped] AND fraud_risk < 0.35 -> approve (0)\n"
    "  - otherwise -> offer_partial_refund (2)\n\n"
    "Output ONLY valid JSON with no markdown fences:\n"
    '{"action": <0|1|2|3>, "confidence": <0.0-1.0>, "reason": "<brief explanation>"}'
)


# -- Logging helpers ----------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool,
             error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float,
            rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# -- Agent --------------------------------------------------------------------

def heuristic_action(obs) -> Action:
    """Rule-based fallback used when the LLM is unavailable or errors."""
    if not obs.is_inspected and 0.40 <= obs.fraud_risk <= 0.75:
        return Action(action_type=3, confidence=0.8,
                      reasoning="uncertain risk - inspect first")
    if obs.fraud_risk >= 0.8 or obs.days_since_purchase >= 30:
        return Action(action_type=1, confidence=0.9,
                      reasoning="high risk or policy expired")
    if obs.return_reason in (0, 1, 3) and obs.fraud_risk < 0.35:
        return Action(action_type=0, confidence=0.85,
                      reasoning="valid reason and low fraud risk")
    return Action(action_type=2, confidence=0.6,
                  reasoning="ambiguous case - partial refund")


def llm_action(client: OpenAI, obs) -> Optional[Action]:
    """Ask the LLM; return None on any error so caller falls back to heuristics."""
    try:
        obs_dict = (
            obs.to_prompt_dict() if hasattr(obs, "to_prompt_dict")
            else obs.model_dump()
        )
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": json.dumps(obs_dict, indent=2)},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        raw = (completion.choices[0].message.content or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return Action(
            action_type=int(parsed["action"]),
            confidence=float(parsed.get("confidence", 0.9)),
            reasoning=parsed.get("reason", "LLM decision"),
        )
    except Exception as exc:
        print(f"[DEBUG] LLM error: {exc}", flush=True)
        return None


# -- Episode runner -----------------------------------------------------------

def run_task(client: Optional[OpenAI], task_name: str) -> None:
    """Run one full episode for task_name and emit [START]/[STEP]*/[END]."""
    config = TASKS[task_name]
    env    = EcommerceReturnEnv(config, seed=SEED)
    obs    = env.reset(seed=SEED)

    rewards: List[float] = []
    steps_taken   = 0
    llm_calls     = 0
    llm_fallbacks = 0
    score         = 0.0
    success       = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        for step in range(1, config["n_steps"] + 1):
            if env.done:
                break

            error  = None
            action = None

            if client is not None:
                action = llm_action(client, obs)
                llm_calls += 1

            if action is None:
                action = heuristic_action(obs)
                llm_fallbacks += 1
                if client is not None:
                    error = "llm_fallback"

            obs, reward, done, _ = env.step(action)
            rewards.append(reward.value)
            steps_taken = step

            log_step(step=step, action=action.label,
                     reward=reward.value, done=done, error=error)

            if done:
                break

            # Light rate-limit guard
            if client is not None and llm_calls % 10 == 0:
                time.sleep(1.0)

        report  = grade(
            metrics=env.metrics,
            task_difficulty=task_name,
            llm_calls=llm_calls,
            llm_fallbacks=llm_fallbacks,
            seed=SEED,
        )
        score   = report.score
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error in task={task_name}: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# -- Entry point --------------------------------------------------------------

def main() -> None:
    client: Optional[OpenAI] = None

    if API_KEY:
        try:
            client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
            print(
                f"[DEBUG] LLM ready -- model={MODEL_NAME} base={API_BASE_URL}",
                flush=True,
            )
        except Exception as exc:
            print(f"[DEBUG] OpenAI client init failed: {exc}", flush=True)
    else:
        print(
            "[DEBUG] No API key found (HF_TOKEN / API_KEY / OPENAI_API_KEY). "
            "Running heuristic-only baseline.",
            flush=True,
        )

    for task_name in ["easy", "medium", "hard"]:
        run_task(client, task_name)


if __name__ == "__main__":
    main()
