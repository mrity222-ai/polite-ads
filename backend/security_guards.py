"""Browser CSRF protection and persistent per-client login throttling."""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from fastapi.responses import JSONResponse
from sqlalchemy import select
from database import SessionLocal
from entities import AuditEvent
from config import APP_SECRET_KEY, FRONTEND_ORIGIN, APP_ENV


def csrf_token(session_token):
    return hmac.new(APP_SECRET_KEY.encode(), ('csrf:' + session_token).encode(), hashlib.sha256).hexdigest()


async def security_guard(request, call_next):
    unsafe = request.method not in ('GET', 'HEAD', 'OPTIONS')
    if unsafe and request.url.path not in ('/api/webhooks/razorpay', '/api/meta/deauthorize'):
        origin = request.headers.get('origin')
        allowed = {FRONTEND_ORIGIN}
        if APP_ENV != 'production':
            allowed.update({'http://localhost:5173', 'http://127.0.0.1:5173'})
        if origin and origin not in allowed:
            return JSONResponse({'detail': 'Untrusted request origin.'}, status_code=403)
        cookie = request.cookies.get('politiads_session')
        # Login/registration authenticate credentials, but still reject foreign origins.
        if cookie and request.url.path not in ('/api/auth/login', '/api/auth/register', '/api/auth/facebook/start'):
            if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), csrf_token(cookie)):
                return JSONResponse({'detail': 'Missing or invalid CSRF token.'}, status_code=403)
    if request.method == 'POST' and request.url.path in ('/api/auth/login', '/api/auth/register', '/api/auth/facebook/start'):
        # Direct peer address only: never trust a client-supplied forwarding header.
        peer = request.client.host if request.client else 'unknown'
        key = hashlib.sha256(peer.encode()).hexdigest()[:36]
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        with SessionLocal() as db:
            recent = db.query(AuditEvent).filter(AuditEvent.action == 'AUTH_ATTEMPT',
                AuditEvent.target_user_id == key, AuditEvent.created_at >= cutoff).count()
            if recent >= 20:
                return JSONResponse({'detail': 'Too many authentication attempts. Try again in five minutes.'}, status_code=429)
            db.add(AuditEvent(action='AUTH_ATTEMPT', target_user_id=key))
            db.commit()
    return await call_next(request)
