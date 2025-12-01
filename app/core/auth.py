import os
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# Supabase JWT Secret (should be in env vars)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"

# Auth mode: "required", "optional", or "disabled"
# Set AUTH_MODE=disabled for local development, AUTH_MODE=required for production
AUTH_MODE = os.getenv("AUTH_MODE", "optional").lower()

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Verifies the JWT token from Supabase.
    
    Behavior based on AUTH_MODE:
    - "disabled": Always returns None, no authentication required
    - "optional": Returns user if valid token provided, None otherwise
    - "required": Requires valid token, raises 401 if missing/invalid
    """
    # If auth is disabled, skip validation entirely
    if AUTH_MODE == "disabled":
        return None
    
    # No credentials provided
    if credentials is None:
        if AUTH_MODE == "required":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None  # optional mode, no token = anonymous user
    
    token = credentials.credentials
    
    if not SUPABASE_JWT_SECRET:
        if AUTH_MODE == "required":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: Missing JWT Secret"
            )
        # In optional mode without secret configured, treat as anonymous
        return None

    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], audience="authenticated")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        if AUTH_MODE == "required":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None  # optional mode, invalid token = treat as anonymous


def require_auth(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency that strictly requires authentication.
    Use this for sensitive endpoints that always need auth regardless of AUTH_MODE.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this endpoint",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_user_id(user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Optional[str]:
    """
    Extract user ID from the authenticated user payload.
    Returns None if no user is authenticated.
    """
    if user is None:
        return None
    return user.get("sub")  # Supabase uses 'sub' claim for user ID
