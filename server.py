"""
server.py — FastAPI server for EcommerceReturn-v1 (OpenEnv-compliant).

Run:
    uvicorn server:app --host 0.0.0.0 --port 7860
    python server.py

Environment variables:
    API_BASE_URL   LLM endpoint    (default: https://router.huggingface.co/v1)
    MODEL_NAME     Model id        (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       API key
"""

import os
import json
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

from env import EcommerceReturnEnv
from tasks import TASKS
from models import Action
from baseline import SYSTEM_PROMPT, heuristic_action
from audit_gen import generate_audit_pdf

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="EcommerceReturn-v1 API",
    description="OpenEnv-compliant environment for e-commerce return decisions.",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# LLM client (OpenAI-compatible, optional)
# ---------------------------------------------------------------------------

_api_key = (
    os.getenv("HF_TOKEN")
    or os.getenv("API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
_api_base = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
_model    = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")

_llm_client: Optional[OpenAI] = None
if _api_key:
    try:
        _llm_client = OpenAI(base_url=_api_base, api_key=_api_key)
    except Exception as exc:
        print(f"[WARN] OpenAI client init failed: {exc}")


def _llm_action(obs) -> Optional[Action]:
    """Ask the LLM for an action; returns None on any failure."""
    if _llm_client is None:
        return None
    try:
        obs_dict = obs.model_dump()
        completion = _llm_client.chat.completions.create(
            model=_model,
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
        print(f"[DEBUG] LLM error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Global environment state
# ---------------------------------------------------------------------------

class EnvState:
    def __init__(self):
        self.env = EcommerceReturnEnv(TASKS["medium"], seed=42)
        self.obs = self.env.reset(seed=42)
        self.history = []
        self.profit_history = [{"step": 0, "profit": 0}]


state = EnvState()


class StepRequest(BaseModel):
    action_type: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/reset")
def reset_env():
    """Reset environment to a clean, deterministic state (seed=42)."""
    state.env = EcommerceReturnEnv(TASKS["medium"], seed=42)
    state.obs = state.env.reset(seed=42)
    state.history = []
    state.profit_history = [{"step": 0, "profit": 0}]
    return get_state()


@app.get("/state")
def get_state():
    return {
        "observation":    state.obs.model_dump(),
        "metrics":        state.env.metrics.model_dump(),
        "done":           state.env.done,
        "history":        state.history[-5:],
        "profit_history": state.profit_history,
        "step_count":     state.env._step_count,
    }


@app.post("/step")
def step_env(req: StepRequest):
    if state.env.done:
        raise HTTPException(status_code=400, detail="Episode finished.")
    action = Action(
        action_type=req.action_type,
        confidence=1.0,
        reasoning="Manual override",
    )
    return _apply_action(action)


@app.post("/agent_step")
def agent_step():
    """Hybrid agent (LLM + rules) picks the next action."""
    if state.env.done:
        raise HTTPException(status_code=400, detail="Episode finished.")
    action = _llm_action(state.obs)
    if action is None:
        action = heuristic_action(state.obs)
        action.reasoning = "(heuristic fallback) " + action.reasoning
    return _apply_action(action)


@app.get("/download_audit")
def download_audit():
    if not state.history:
        raise HTTPException(status_code=400, detail="No decisions made yet.")
    last = state.history[-1]
    obs = {
        "product_price":       last["price"],
        "customer_type":       "new",
        "fraud_risk":          0.0,
        "return_reason_label": str(last["reason"]),
        "days_since_purchase": 5,
    }
    act = {"action_label": last["action"], "reasoning": last["reasoning"]}
    rew = {"value": last["reward"], "fraud_intercepted": last["fraud_intercepted"]}
    path = generate_audit_pdf(obs, act, rew)
    return FileResponse(path, media_type="application/pdf", filename="nexus_audit.pdf")


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _apply_action(action: Action):
    prev_obs = state.obs.model_dump()
    obs, reward, done, info = state.env.step(action)
    state.obs = obs

    label = {0: "Approved", 1: "Rejected", 2: "Partial Refund", 3: "Inspected"}.get(
        action.action_type, "Unknown"
    )
    state.history.append({
        "id":                int(time.time() * 1000),
        "action":            label,
        "price":             prev_obs["product_price"],
        "reason":            prev_obs["return_reason"],
        "reward":            reward.value,
        "fraud_intercepted": reward.fraud_intercepted,
        "reasoning":         action.reasoning,
    })
    state.profit_history.append({
        "step":   state.env._step_count,
        "profit": state.env.metrics.profit,
    })
    return get_state()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
