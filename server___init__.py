# Re-export app so `uvicorn server:app` continues to work alongside
# the multi-mode `python -m server.app` entrypoint.
from server.app import app, main  # noqa: F401

__all__ = ["app", "main"]
