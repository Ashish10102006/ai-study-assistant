from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
from app.services.supabase_client import verify_user_token


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Extracts user information from Supabase Bearer token if present.
    If no token is provided, returns a guest student context to allow exploring
    study tools and 3D features immediately.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        user = verify_user_token(token)
        if user:
            return user

    # Default Guest Scholar profile for public study queries
    return {
        "id": "student_guest_default",
        "email": "student@studyassistant.ai",
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
