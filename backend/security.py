"""
Security and Session Utilities for PolitiAds
Argon2id Password Hashing & Opaque Token Session Management
"""
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy.orm import Session
try:
    from entities import UserSession
except ImportError:
    from backend.entities import UserSession

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return ph.hash(plain_password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifies a password against an Argon2id hash."""
    try:
        return ph.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception:
        return False

def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of an opaque session token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_session(db: Session, user_id: str, ttl_hours: int = 24) -> str:
    """
    Creates a secure opaque session token, stores only its SHA-256 hash in the database,
    and returns the raw token to be set in an HttpOnly cookie.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

    session_record = UserSession(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        is_revoked=False
    )
    db.add(session_record)
    db.commit()

    return raw_token

def revoke_session(db: Session, raw_token: str) -> bool:
    """Revokes a specific session by token."""
    th = hash_token(raw_token)
    session = db.query(UserSession).filter(UserSession.token_hash == th).first()
    if session:
        session.is_revoked = True
        db.commit()
        return True
    return False

def revoke_all_user_sessions(db: Session, user_id: str) -> int:
    """Revokes all active sessions for a user (used upon suspension or security events)."""
    count = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()
    return count
