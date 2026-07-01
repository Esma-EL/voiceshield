"""Application configuration.

Everything degrades gracefully: with no API keys and no ML deps installed,
the app runs entirely on the heuristic fallbacks so the demo always works.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # CORS: the Next.js dev server.
    frontend_origin: str = "http://localhost:3000"

    # --- Voice anti-spoofing ---
    # HuggingFace/ModelScope model id. If set AND torch+transformers are
    # installed, the real detector is used; otherwise we fall back to the
    # acoustic-feature heuristic.
    spoofing_model_id: str = ""

    # --- Context analysis (LLM) ---
    # Qwen via DashScope. If DASHSCOPE_API_KEY is set AND the dashscope SDK is
    # installed, the LLM analyzes the transcript; otherwise the rule engine runs.
    dashscope_api_key: str = ""
    qwen_model: str = "qwen-plus"

    # --- Verdict thresholds (combined risk 0..1) ---
    risk_amber: float = 0.40
    risk_red: float = 0.65


settings = Settings()
