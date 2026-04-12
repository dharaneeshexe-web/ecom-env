import unittest
from env import EcommerceReturnEnv
from tasks import TASKS
from models import Action
from grader import grade

class TestGrader(unittest.TestCase):
    def test_perfect_agent(self):
        """Reference case: The perfect agent should score near 1.0."""
        env = EcommerceReturnEnv(TASKS["medium"], seed=10)
        obs = env.reset()
        while not env.done:
            opt = env._optimal_action(env.current_request)
            obs, rew, done, info = env.step(Action(action_type=opt, reasoning="perfect reference"))
            
        report = grade(env.metrics, "medium", seed=10)
        print(f"Perfect agent score: {report.score}")
        self.assertGreater(report.score, 0.85, "Perfect agent should score extremely high.")

    def test_null_agent(self):
        """Reference case: The null agent (always reject) should score poorly."""
        env = EcommerceReturnEnv(TASKS["medium"], seed=10)
        obs = env.reset()
        while not env.done:
            # Null agent blindly approves everything (massive fraud loss)
            obs, rew, done, info = env.step(Action(action_type=0, reasoning="null reference"))
            
        report = grade(env.metrics, "medium", seed=10)
        print(f"Null agent score: {report.score}")
        self.assertLess(report.score, 0.40, "Null agent should score very poorly.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
