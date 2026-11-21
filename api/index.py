"""Vercel serverless entry point for the Genopedia API.

Vercel's Python runtime serves the module-level FastAPI ``app`` from files
under /api. The repository root is added so the ``genopedia`` package imports
without installation. When DATABASE_URL points at a real database, pending
Alembic migrations are applied once at cold start so a fresh deployment is
immediately usable; failures are logged and left to surface via /health.
"""

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _run_migrations() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url or database_url.startswith("sqlite"):
        return
    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        command.upgrade(cfg, "head")
        print("alembic upgrade head: ok")
    except Exception:  # noqa: BLE001 - cold start must not hard-crash
        print("alembic upgrade head failed:")
        traceback.print_exc()


_run_migrations()

from genopedia.api.app import app  # noqa: E402,F401
