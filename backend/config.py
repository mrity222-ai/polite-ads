import os
from pathlib import Path

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / '.env', override=False)
APP_ENV = os.environ.get('APP_ENV', 'development')

# Default SQLite database path in backend/data/politiads.db
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "politiads.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

raw_db_url = os.environ.get("DATABASE_URL")
if not raw_db_url:
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
else:
    DATABASE_URL = raw_db_url
    if DATABASE_URL.startswith('sqlite:///') and not DATABASE_URL.startswith('sqlite:////'):
        from sqlalchemy.engine import make_url
        url = make_url(DATABASE_URL)
        if url.database and url.database != ':memory:' and not Path(url.database).is_absolute():
            DATABASE_URL = url.set(database=str((BACKEND_DIR / url.database).resolve())).render_as_string(hide_password=False)

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "24"))
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax")
APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY", "dev_secret_key_change_in_production_32chars")

# Token Encryption Key (Fernet 32 url-safe base64-encoded bytes)
# A default reproducible test key is provided for dev/test mode
ENCRYPTION_KEY = os.environ.get(
    "ENCRYPTION_KEY",
    "k9X2bY1p9R_vQ0wU7oZ_mN5eT3sA1dF4hJ6kL8zC2vM="
)

# Meta Marketing API Configuration
META_APP_ID = os.environ.get("META_APP_ID", "mock_meta_app_1092830")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "mock_meta_secret_abcdef123456")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "mock_meta_access_token_super_admin")
META_GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION", "v19.0")
META_DEFAULT_AD_ACCOUNT_ID = os.environ.get("META_DEFAULT_AD_ACCOUNT_ID", "act_1373171501321455")
META_MOCK_MODE = os.environ.get("META_MOCK_MODE", "true").lower() in ("true", "1", "yes")
META_KILL_SWITCH = os.environ.get("META_KILL_SWITCH", "false").lower() in ("true", "1", "yes")

# Razorpay Payment Gateway Configuration
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_politiads_demo")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "test_secret_key_razorpay_9988")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "whsec_politiads_webhook_test_2026")
RAZORPAY_MOCK_MODE = os.environ.get("RAZORPAY_MOCK_MODE", "true").lower() in ("true", "1", "yes")

if APP_ENV == 'production':
    if not COOKIE_SECURE or COOKIE_SAMESITE not in ('lax', 'strict'):
        raise RuntimeError('Production requires Secure cookies and SameSite lax/strict.')
    if len(APP_SECRET_KEY) < 32 or APP_SECRET_KEY.startswith('dev_'):
        raise RuntimeError('Set a strong production APP_SECRET_KEY.')
    if not os.environ.get('ENCRYPTION_KEY') or ENCRYPTION_KEY == 'k9X2bY1p9R_vQ0wU7oZ_mN5eT3sA1dF4hJ6kL8zC2vM=':
        raise RuntimeError('Set an independent production Fernet key.')
    if not FRONTEND_ORIGIN.startswith('https://'):
        raise RuntimeError('Production FRONTEND_ORIGIN must use HTTPS.')
    if not RAZORPAY_MOCK_MODE and (RAZORPAY_KEY_ID == 'rzp_test_politiads_demo' or RAZORPAY_KEY_SECRET == 'test_secret_key_razorpay_9988' or RAZORPAY_WEBHOOK_SECRET == 'whsec_politiads_webhook_test_2026'):
        raise RuntimeError('Replace default payment credentials before enabling provider mode.')


# Facebook authorization uses a distinct version/configuration from publishing.
META_OAUTH_ENABLED = os.environ.get('META_OAUTH_ENABLED', 'false').lower() in ('true','1','yes')
META_OAUTH_GRAPH_VERSION = os.environ.get('META_OAUTH_GRAPH_VERSION', 'v24.0')
META_OAUTH_REDIRECT_URI = os.environ.get('META_OAUTH_REDIRECT_URI', FRONTEND_ORIGIN.rstrip('/') + '/api/meta/oauth/callback')
META_BUSINESS_CONFIG_ID = os.environ.get('META_BUSINESS_CONFIG_ID', '')
META_FACEBOOK_SCOPES = tuple(x.strip() for x in os.environ.get('META_FACEBOOK_SCOPES', 'pages_show_list,pages_read_engagement,ads_management,ads_read').split(',') if x.strip())
META_INSTAGRAM_SCOPES = tuple(dict.fromkeys((*META_FACEBOOK_SCOPES, 'instagram_basic')))
