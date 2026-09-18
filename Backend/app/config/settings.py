import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

import tempfile

# Ensure .env is loaded from Backend/.env
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
env_file_path = backend_dir / ".env"

if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path, override=False)


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_JWKS_URL: str = os.getenv("SUPABASE_JWKS_URL", "")

    # AI & Search Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Application Settings
    APP_URL: str = os.getenv("APP_URL", "http://localhost:5173")
    API_PORT: int = int(os.getenv("PORT", "8000"))
    API_HOST: str = os.getenv("HOST", "0.0.0.0")
    UPLOAD_DIR: Path = Path(tempfile.gettempdir()) / "uploads" if (os.getenv("VERCEL") or not os.access(str(backend_dir), os.W_OK)) else backend_dir / "uploads"
    MAX_FILE_SIZE_MB: int = 25

    # AI Model Settings - configured with verified, high-performance Google Gemini models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro"
    ]

    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    def get_safe_status(self) -> dict:
        """Returns safe configuration diagnostics without revealing any secret values."""
        return {
            "supabase_configured": bool(self.SUPABASE_URL and self.SUPABASE_SECRET_KEY),
            "supabase_url": self.SUPABASE_URL.split("//")[-1].split(".")[0] + ".supabase.co" if self.SUPABASE_URL else None,
            "gemini_configured": bool(self.GEMINI_API_KEY),
            "tavily_configured": bool(self.TAVILY_API_KEY),
            "model": self.GEMINI_MODEL,
            "uploads_ready": self.UPLOAD_DIR.exists()
        }


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return settings
