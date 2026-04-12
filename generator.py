import json
import random

def generate_procedural_environment():
    """Generates procedural configurations for OpenEnv scaling."""
    print("Generating procedural task config...")
    diff_level = random.choice(["easy", "medium", "hard"])
    
    fraud = {"easy": 0.1, "medium": 0.3, "hard": 0.7}[diff_level]
    fraud += random.uniform(-0.05, 0.05)
    
    tasks = {
        "generated_task": {
            "n_steps": random.randint(30, 200),
            "price_range": [random.randint(5, 50), random.randint(200, 1000)],
            "fraud_level": round(min(0.95, max(0.01, fraud)), 2),
            "partial_refund_enabled": random.choice([True, False]),
            "description": f"Procedurally generated task based on {diff_level} template."
        }
    }
    
    with open("tasks_generated.json", "w") as f:
        json.dump(tasks, f, indent=2)
        
    print(f"Saved 'tasks_generated.json' successfully.\nDetails:\n{json.dumps(tasks, indent=2)}")

if __name__ == "__main__":
    generate_procedural_environment()
