from __future__ import annotations

from pathlib import Path
import sys


BACKEND_PATH = Path(__file__).resolve().parents[1] / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.main import app  # noqa: E402
