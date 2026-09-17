import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.config.settings import get_settings

logger = logging.getLogger("ai_study_assistant.supabase")

_supabase_client: Optional[Client] = None


def get_supabase_admin() -> Optional[Client]:
    """Returns an authenticated Supabase client using SUPABASE_URL and SUPABASE_SECRET_KEY."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
        logger.warning("Supabase URL or Secret Key not set.")
        return None

    try:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Supabase JWT token received from frontend client.
    Returns the user dict if valid, or None if invalid.
    """
    if not token:
        return None

    # Strip Bearer if present
    if token.startswith("Bearer "):
        token = token[7:].strip()

    client = get_supabase_admin()
    if not client:
        return None

    try:
        # Verify via Supabase Auth API
        res = client.auth.get_user(jwt=token)
        if res and res.user:
            return {
                "id": str(res.user.id),
                "email": res.user.email,
                "user_metadata": res.user.user_metadata or {}
            }
    except Exception as e:
        logger.warning(f"Supabase token verification failed: {e}")

    return None
