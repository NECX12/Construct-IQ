import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _get_setting(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is not None:
        return value

    try:
        import streamlit as st

        return st.secrets.get(name, default)
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    ai_provider: str = _get_setting("AI_PROVIDER", "none").strip().lower()
    model_name: str = _get_setting("MODEL_NAME", "gemini-2.5-flash").strip()
    gemini_api_key: str = _get_setting("GEMINI_API_KEY", "").strip()
    max_upload_size_mb: int = int(_get_setting("MAX_UPLOAD_SIZE_MB", "100"))
    default_currency: str = _get_setting("DEFAULT_CURRENCY", "NGN").strip().upper()


settings = Settings()