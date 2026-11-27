"""
Vercel Serverless Entrypoint for the FastAPI Backend.

Mounts the existing modular FastAPI application (`backend/app/main.py`) at
`/api/index` so all `/api/*`, `/docs`, `/openapi.json`, and `/health` routes
execute seamlessly on Vercel under the same global domain as the Vite SPA.
"""

import os
import sys

# Ensure `backend/` is on sys.path so `from app.X import Y` resolves cleanly
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_dir = os.path.join(_repo_root, "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Default to fast surrogate NLI mode on Vercel serverless unless explicitly overridden
os.environ.setdefault("OFFLINE_MODE", "1")

from app.main import app  # noqa: E402
from app.database.seed_data import seed_database  # noqa: E402

# Cold-start idempotent seeding (Vercel serverless functions may skip lifespan hooks)
try:
    seed_database()
except Exception as exc:  # pragma: no cover
    print(f"[Vercel Startup Warning] Database seeding skipped/failed: {exc}")
