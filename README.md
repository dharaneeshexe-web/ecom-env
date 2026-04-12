---
title: Ecommerce Return Agent
emoji: 🛒
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🛒 EcommerceReturn-v1

> **OpenEnv-compliant RL environment for automating e-commerce return decisions with an LLM agent.**

[![OpenEnv 1.0](https://img.shields.io/badge/OpenEnv-1.0-blue)](openenv.yaml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)](requirements.txt)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](Dockerfile)

---

## 🎯 Environment Overview

`EcommerceReturn-v1` simulates a real-world e-commerce return desk. An AI agent receives a return request — containing product price, customer history, fraud risk score, return reason, and elapsed days — and must decide the optimal action to balance customer satisfaction against fraud prevention and financial loss.

All LLM calls use an **OpenAI-compatible API** client, driven by `HF_TOKEN` and `API_BASE_URL`, making the environment compatible with any Hugging Face inference endpoint or OpenAI-compatible provider.

---

## 📦 Observation Space

| Field | Type | Range | Description |
|---|---|---|---|
| `product_price` | float | 10–500 USD | Item value |
| `customer_rating` | float | 1–5 | Historical customer rating |
| `return_reason` | int | 0–4 | Encoded return reason (see labels below) |
| `days_since_purchase` | int | 1–30 | Days elapsed since order |
| `fraud_risk` | float | 0–1 | Computed fraud probability score |
| `order_value_tier` | str | budget/medium/premium | Price bucket |
| `customer_type` | str | new/loyal/fraudster | Customer segment |
| `is_inspected` | bool | — | Whether manual inspection was triggered |

**Return reason labels:** `0=defective_item`, `1=wrong_item_shipped`, `2=changed_mind`, `3=arrived_late`, `4=better_price_found`

---

## ⚡ Action Space

| ID | Label | Policy |
|---|---|---|
| 0 | `approve_full_refund` | Best for valid, low-risk returns |
| 1 | `reject_return` | Use for fraud suspects or policy violations |
| 2 | `offer_partial_refund` | Safe hedge for ambiguous cases |
| 3 | `inspect_return` | Multi-step: reveals true fraud status (costs −5) |

---

## 🎯 Tasks

| Task | Fraud Level | Steps | Price Range | Partial Refund |
|---|---|---|---|---|
| `easy` | 15% | 50 | $10–$150 | ❌ |
| `medium` | 40% | 75 | $10–$350 | ✅ |
| `hard` | 70% | 100 | $10–$500 | ✅ |

Difficulty increases fraud prevalence, episode length, and financial stakes.

---

## 📊 Reward Function

| Scenario | Reward |
|---|---|
| Approve valid return (low fraud, good reason) | +8 to +15 (loyalty bonus) |
| Approve fraudulent return | −65% of price |
| Reject fraud or expired policy | +10% of price |
| Reject valid return (wrong decision) | −4 to −8 |
| Offer partial refund | +4 (−20% of price if fraud) |
| Inspect return | −5 (investigation cost) |

---

## 📈 Grader (Score 0.0–1.0)

| Metric | Weight |
|---|---|
| Net profit (normalized) | 50% |
| Fraud interception rate | 30% |
| Decision accuracy vs. optimal heuristic | 20% |

---

## 🚀 Setup & Running

### Prerequisites

```bash
pip install -r requirements.txt
```

### Environment Variables

```bash
export HF_TOKEN=your_huggingface_token_here
export API_BASE_URL=https://router.huggingface.co/v1   # any OpenAI-compatible endpoint
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct            # any supported model
```

> If `HF_TOKEN` is not set, `inference.py` automatically falls back to a deterministic heuristic agent and still produces valid scores.

### Run Inference (Baseline)

```bash
python inference.py
```

Runs all 3 tasks (easy → medium → hard) and emits structured `[START]` / `[STEP]` / `[END]` logs per the OpenEnv spec.

**Example output:**
```
[START] task=easy env=EcommerceReturn-v1 model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=approve_full_refund reward=8.00 done=false error=null
...
[END] success=true steps=50 score=0.712 rewards=8.00,-3.20,...
```

### Run the API Server

```bash
# Multi-mode entrypoint (recommended)
python -m server.app

# Or via uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t ecommerce-return-v1 .

docker run -p 7860:7860 \
  -e HF_TOKEN=your_token \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  ecommerce-return-v1
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/reset` | Reset environment (deterministic seed=42) |
| GET | `/state` | Current observation + metrics |
| POST | `/step` | Manual action `{"action_type": 0–3}` |
| POST | `/agent_step` | LLM agent picks the next action |
| GET | `/download_audit` | Download PDF audit of last decision |

---

## 📁 Project Structure

```
├── inference.py        # OpenEnv baseline script (root, required)
├── env.py              # EcommerceReturnEnv — reset/step/state/close
├── models.py           # Pydantic models: Observation, Action, Reward
├── tasks.py            # Task configs: easy / medium / hard
├── grader.py           # Normalized score function (0.0–1.0)
├── baseline.py         # Heuristic agent + SYSTEM_PROMPT
├── server.py           # Root shim → server/app.py
├── server/
│   ├── __init__.py     # Re-exports app for uvicorn server:app
│   └── app.py          # FastAPI application + main() entrypoint
├── openenv.yaml        # OpenEnv metadata and deployment config
├── Dockerfile          # Container build definition
└── requirements.txt    # Python dependencies
```

---

## 📄 License

MIT License.
