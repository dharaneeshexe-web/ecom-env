import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import time
from env import EcommerceReturnEnv
from tasks import TASKS
from evaluate import hybrid_agent

def run_demo():
    print("\n🚀 Starting LIVE DEMO of Hybrid E-commerce Agent")
    print("========================================================\n")
    
    env = EcommerceReturnEnv(TASKS["medium"], seed=101)
    obs = env.reset()
    
    for _ in range(10):  # 10 steps for a clean presentation
        print("-" * 60)
        print(f"📦 REQUEST [Step {env._step_count+1}]:")
        print(f"   Item value: ${obs.product_price:.2f} | Reason: {obs.return_reason_label}")
        print(f"   Customer: {obs.customer_type.upper()} | Current Fraud Risk: {obs.fraud_risk:.2f}")
        
        if obs.is_inspected:
             print("   Status: INSPECTED")
             
        # AI Engine decides
        time.sleep(1.0) # simulate thinking
        action = hybrid_agent(obs)
        
        print("\n🧠 AGENT DECISION:")
        print(f"   => Action Code : {action.action_type} ({action.label})")
        print(f"   => Explanation : {action.reasoning}")
        
        # Apply step to environment
        obs, reward, done, info = env.step(action)
        
        print("\n💰 OUTCOME:")
        print(f"   => Reward    : {reward.value:+.2f} USD")
        print(f"   => Breakdown : {reward.breakdown}")
        
        time.sleep(2.0)
        
    print("\n🏁 Demo completed. Check your metrics or start full UI!")

if __name__ == "__main__":
    run_demo()
