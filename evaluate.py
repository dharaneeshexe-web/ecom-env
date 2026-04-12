import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
import json
import time
import google.generativeai as genai
from env import EcommerceReturnEnv
from models import Action
from tasks import TASKS

# Configure LLM globally
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

SYSTEM_PROMPT = """You are an AI decision engine for e-commerce returns.
Actions:
  0 = approve_full_refund
  1 = reject_return
  2 = offer_partial_refund
  3 = inspect_return (if fraud risk is ambiguous, inspect to get true fraud value)

Policy rules:
  - If fraud_risk >= 0.8 and inspected/obvious → reject (1)
  - If customer_type == 'loyal' and fraud is low → approve (0)
  - If customer_type == 'fraudster' → reject (1)
  - If days_since_purchase >= 30 → reject (1)
  - If ambiguous fraud risk and not inspected → inspect (3)

Output ONLY valid JSON:
{"action": <0|1|2|3>, "reason": "<explanation>"}
"""

def heuristic_action(obs) -> Action:
    """Fallback if LLM fails."""
    if not obs.is_inspected and 0.40 <= obs.fraud_risk <= 0.75:
        return Action(action_type=3, confidence=0.8, reasoning="fallback: uncertain risk, inspecting")
    if obs.fraud_risk >= 0.8 or obs.days_since_purchase >= 30:
        return Action(action_type=1, confidence=0.8, reasoning="fallback: high risk or expired")
    if obs.return_reason in (0, 1, 3) and obs.fraud_risk < 0.35:
        return Action(action_type=0, confidence=0.85, reasoning="fallback: valid reason")
    return Action(action_type=2, confidence=0.6, reasoning="fallback: ambiguous")

def multi_agent_council(obs) -> Action:
    """The 'Council of Nexus' strategy: Fraud vs. Loyalty Agents."""
    if not model:
        return heuristic_action(obs)
    
    obs_json = json.dumps(obs.to_prompt_dict(), indent=2)
    
    # 1. FRAUD SPECIALIST (Pessimistic)
    fraud_prompt = f"ROLE: Pessimistic Risk Auditor. Analyze this transaction for fraud potential. Request: {obs_json}. Output only 'Decision: Reject' or 'Decision: Inspect' with a 1-sentence reason."
    
    # 2. LOYALTY SPECIALIST (Optimistic)
    loyalty_prompt = f"ROLE: Optimistic Customer Success Manager. Focus on LTV (Life Time Value) and satisfaction. Request: {obs_json}. Output only 'Decision: Approve' or 'Decision: Partial' with a 1-sentence reason."
    
    try:
        fraud_opin = model.generate_content(fraud_prompt).text.strip()
        loyalty_opin = model.generate_content(loyalty_prompt).text.strip()
        
        # 3. THE DECIDER AGENT (Synthesis)
        decider_prompt = f"""You are the Master Nexus Decider.
        Transaction: {obs_json}
        Risk Auditor Opinion: {fraud_opin}
        Customer Success Opinion: {loyalty_opin}
        
        Synthesize these and output ONLY a JSON object:
        {{"action": <0|1|2|3>, "confidence": <0.0-1.0>, "reason": "<Synthesis of debate>"}}
        
        Note: If confidence < 0.65, you MAY output action: 4 (Escalate to Human).
        """
        
        res = model.generate_content(decider_prompt).text.strip()
        if "```" in res:
             res = res.split("```")[1].strip()
             if res.startswith("json"):
                 res = res[4:].strip()
        parsed = json.loads(res)
        
        return Action(
            action_type=int(parsed["action"]),
            confidence=float(parsed.get("confidence", 0.9)),
            reasoning=f"COUNCIL DEBATE: {parsed['reason']}"
        )
    except Exception as e:
        return heuristic_action(obs)

def hybrid_agent(obs) -> Action:
    """Enhanced Hybrid Agent with Multi-Agent Council & HITL."""
    # Fast-path optimization
    if obs.fraud_risk > 0.92:
        return Action(action_type=1, confidence=0.99, reasoning="Nexus Shield: Critical Fraud Block")
    
    # Council consultation for moderate/high risk
    if obs.fraud_risk > 0.45 or obs.product_price > 300:
        return multi_agent_council(obs)
    
    # Primary logic
    prompt = SYSTEM_PROMPT + "\n\nRequest:\n" + json.dumps(obs.to_prompt_dict(), indent=2) + "\n\nYour JSON:"
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        parsed = json.loads(raw.replace("```json", "").replace("```", ""))
        
        return Action(
            action_type=int(parsed["action"]),
            confidence=0.9,
            reasoning=parsed.get("reason", "Nexus Decision")
        )
    except:
        return heuristic_action(obs)

def evaluate_all():
    print(f"\n{'='*50}")
    print("🔥 RUNNING EVALUATION SYSTEM (Hybrid Agent)")
    print(f"{'='*50}\n")
    
    from grader import grade
    results = {}
    master_metrics = []

    for task_name in ["easy", "medium", "hard"]:
        env = EcommerceReturnEnv(TASKS[task_name], seed=42)
        obs = env.reset()
        
        while not env.done:
            action = hybrid_agent(obs)
            obs, reward, done, info = env.step(action)
            # Log metrics per step
            master_metrics.append({
                "task": task_name,
                "step": env._step_count,
                "action": action.action_type,
                "reason": action.reasoning,
                "reward_breakdown": reward.breakdown,
                "cumulative_profit": env.metrics.profit
            })
            time.sleep(0.05) # Rate limit protection

        report = grade(env.metrics, task_difficulty=task_name, seed=42)
        results[task_name] = report.score
        
        print(f"Task: {task_name.capitalize():<8} | Score: {report.score:.4f} | Correct Decisions: {env.metrics.correct_decisions}")

    # Save metrics 
    with open("metrics.json", "w") as f:
        json.dump({"summary_scores": results, "logs": master_metrics}, f, indent=2)
        
    print(f"\n✅ All tasks evaluated. Detailed logs saved to 'metrics.json'.")

if __name__ == "__main__":
    evaluate_all()
