"""Makes the backend importable and gives it a valid environment *before* any
`app.*` module is imported (settings are read at import time)."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "fastapi-todo-backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1:1/none")  # port 1 => refused fast
os.environ.setdefault("JWT_SECRET", "unit-test-secret-unit-test-secret-0123456789")
os.environ.setdefault("ENVIRONMENT", "test")
