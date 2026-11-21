"""Vercel serverless entry point for the Genopedia API.

Vercel's Python runtime serves the module-level FastAPI ``app`` from files
under /api. The repository root is added so the ``genopedia`` package imports
without installation. Database migrations run out-of-band with
``alembic upgrade head`` against the production DATABASE_URL (see
docs/api-deployment.md); the app refuses to start in production against SQLite.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genopedia.api.app import app  # noqa: E402,F401
