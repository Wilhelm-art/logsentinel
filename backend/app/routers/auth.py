"""
LogSentinel — Auth Router
Validates requests from NextAuth-authenticated frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from jose import jwt, JWTError

from app.config import settings

router = APIRouter()


async def verify_auth_token(
    authorization: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
) -> str:
    """
    Dependency that validates the user's identity.
    
    In production with NextAuth, the frontend sends the session token.
    For MVP, we accept the X-User-Email header from the Next.js proxy
    which is set after NextAuth validates the session server-side.
    """
    email = None

    # Try JWT from Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        try:
            if settings.AUTH_SECRET:
                payload = jwt.decode(
                    token, settings.AUTH_SECRET, algorithms=["HS256"]
                )
                email = payload.get("email", "").lower()
        except JWTError:
            pass

    # Fallback: trust X-User-Email from internal Next.js proxy
    if not email and x_user_email:
        email = x_user_email.strip().lower()

    if not email:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check allowlist
    allowed = settings.allowed_emails_set
    if allowed and email not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. {email} is not in the allowed users list.",
        )

    return email


@router.get("/me")
async def get_current_user(email: str = Depends(verify_auth_token)):
    """Returns the authenticated user's email."""
    return {"email": email, "authorized": True}
