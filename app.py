"""
server/app.py — OpenEnv multi-mode deployment entry point.
Imports and re-exports the FastAPI app from the root server.py.
"""
import sys
import os

# Ensure root project directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app  # noqa: F401 — re-export for openenv multi-mode

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
