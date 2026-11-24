"""
FastAPI Authentication, Account Isolation, and Role-Based Access Control Dependencies
"""
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
try:
    from database import get_db
    from entities import User, UserSession
    from security import hash_token
except ImportError:
    from backend.database import get_db
    from backend.entities import User, UserSession
    from backend.security import hash_token

def extract_token(request: Request) -> str | None:
    """Extracts session token from HttpOnly cookie or Authorization Bearer header."""
    cookie_token = request.cookies.get("politiads_session")
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Validates session token from cookie/header against database session record.
    Returns authenticated User entity or raises HTTP 401 Unauthorized.
    """
    token = extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing session cookie or Bearer token."
        )

    th = hash_token(token)
    now = datetime.now(timezone.utc)

    session_record = db.query(UserSession).filter(
        UserSession.token_hash == th,
        UserSession.is_revoked == False
    ).first()

    if not session_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked session."
        )

    # Check expiration (handling timezone-aware vs naive)
    exp = session_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if exp <= now:
        session_record.is_revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again."
        )

    user = db.query(User).filter(User.id == session_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this session no longer exists."
        )

    request.state.user = user
    request.state.raw_token = token
    return user

def require_active_user(user: User = Depends(get_current_user)) -> User:
    """
    Enforces that the user account is active.
    If suspended, raises HTTP 403 Forbidden.
    """
    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended by administration. Please contact platform support."
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account status is '{user.status}'. Active status required."
        )

    return user

def require_admin(user: User = Depends(require_active_user)) -> User:
    """
    Enforces that the user has admin privileges.
    If candidate, raises HTTP 403 Forbidden.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access privileges required."
        )

    return user
