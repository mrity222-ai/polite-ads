"""
PolitiAds SaaS - Main FastAPI Backend Application
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from config import FRONTEND_ORIGIN
    from database import init_db
    from seed import seed_database
    from routers import (
        auth, profile, campaigns, admin, surveys,
        meta_integrations, payments, webhooks, notifications, billing
    )
except ImportError:
    from backend.config import FRONTEND_ORIGIN
    from backend.database import init_db
    from backend.seed import seed_database
    from backend.routers import (
        auth, profile, campaigns, admin, surveys,
        meta_integrations, payments, webhooks, notifications, billing
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema and demo data are explicit management operations, never startup side effects.
    from database import engine
    from sqlalchemy import inspect
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    cfg = Config(str(BACKEND_DIR.parent / 'alembic.ini'))
    expected = ScriptDirectory.from_config(cfg).get_current_head()
    with engine.connect() as connection:
        revision = MigrationContext.configure(connection).get_current_revision()
    if revision != expected:
        raise RuntimeError('Database migration required: run python -m alembic upgrade head before startup.')
    if APP_ENV == 'production':
        from database import SessionLocal
        from entities import User
        from security import verify_password
        with SessionLocal() as db:
            for user in db.query(User).filter_by(status='active'):
                if any(verify_password(password, user.password_hash) for password in ('admin123', 'secret123', 'candidate123')):
                    raise RuntimeError('Disable/reset seeded demo credentials before production startup.')
    yield

app = FastAPI(
    title="PolitiAds Backend API",
    description="Backend API Suite for Indian Political Ads, Candidate Onboarding, Meta Ad Moderation & Quick-Fix Engine",
    version="2.0.0",
    lifespan=lifespan
)

# Allowed CORS origins
allowed_origins = [
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
from config import APP_ENV
allowed_origins = [FRONTEND_ORIGIN] if APP_ENV == "production" else list(set(filter(None, allowed_origins)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from security_guards import security_guard
import logging
from redacting_logger import OAuthAccessLogFilter
logging.getLogger("uvicorn.access").addFilter(OAuthAccessLogFilter())
app.middleware("http")(security_guard)

# Register All Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(campaigns.router)
app.include_router(admin.router)
app.include_router(surveys.router)
app.include_router(meta_integrations.router)
app.include_router(payments.router)
app.include_router(webhooks.router)
app.include_router(notifications.router)
app.include_router(billing.router)
from routers import campaign_reviews
app.include_router(campaign_reviews.router)

@app.get("/")
def root_health_check():
    return {
        "platform": "PolitiAds SaaS API",
        "status": "online",
        "version": "2.0.0",
        "meta_graph_api": "Mock mode" if __import__("config").META_MOCK_MODE else "Live publishing unavailable",
        "payments_gateway": "Mock mode" if __import__("config").RAZORPAY_MOCK_MODE else "Provider mode (credentials required)",
        "whatsapp_policy": "Excluded (Compliant)",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
