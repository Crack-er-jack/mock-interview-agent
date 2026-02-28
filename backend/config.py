"""Application configuration — loads from .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ── LLM settings ────────────────────────────────────────────
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL: str = os.getenv(
    "LLM_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# ── Sandbox settings ────────────────────────────────────────
SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "10"))
MAX_CODE_LENGTH: int = int(os.getenv("MAX_CODE_LENGTH", "5000"))

# ── Testing settings ────────────────────────────────────────
QUICK_TEST_MODE: bool = os.getenv("QUICK_TEST_MODE", "false").lower() == "true"
