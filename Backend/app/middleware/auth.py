import re
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
from app.services.supabase_client import verify_user_token


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_guest_id: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extracts user information from Supabase Bearer token if present.
    If no token is provided, returns an isolated guest student profile
    keyed to their unique browser/device ID (x_guest_id) so multiple
    visitors do not see each other's uploaded materials or chats.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        user = verify_user_token(token)
        if user:
            return user

    # Sanitize and validate client guest ID or fallback token identity
    guest_id = "guest_default"
    if x_guest_id and isinstance(x_guest_id, str):
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', x_guest_id.strip())[:64]
        if cleaned:
            guest_id = cleaned if cleaned.startswith("guest_") else f"guest_{cleaned}"
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', token)[:64]
        if cleaned:
            guest_id = f"user_{cleaned}"

    return {
        "id": guest_id,
        "email": f"{guest_id}@guest.studyassistant.ai",
        "is_guest": True,
        "user_metadata": {"full_name": "Scholar Guest"}
    }


async def require_auth(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Enforces that an authenticated Supabase user token is present.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to your student account."
        )

    token = authorization.split(" ")[1].strip()
    user = verify_user_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again."
        )

    return user
