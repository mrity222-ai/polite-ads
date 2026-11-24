import logging
import re

SENSITIVE_PATTERNS = [
    # Bearer tokens
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), r"\1[REDACTED]"),
    # Access tokens and secrets
    (re.compile(r"((?:token|secret|api_key|password|key_secret)\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-\.]{8,}(['\"]?)", re.IGNORECASE), r"\1[REDACTED]\2"),
    # Credit/Debit Card numbers
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[REDACTED_CARD]"),
    # Webhook signature strings
    (re.compile(r"((?:signature|x-razorpay-signature)\s*[:=]\s*['\"]?)[a-zA-Z0-9]{32,}(['\"]?)", re.IGNORECASE), r"\1[REDACTED_SIGNATURE]\2"),
]

class RedactingFormatter(logging.Formatter):
    """
    Custom logging formatter that strips API tokens, secrets,
    and sensitive payment parameters before writing to console/file.
    """
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern, replacement in SENSITIVE_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

def get_redacted_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class OAuthAccessLogFilter(logging.Filter):
    """Prevent authorization codes/state/signed requests from reaching Uvicorn access logs."""
    def filter(self, record):
        if isinstance(record.args, tuple):
            values = list(record.args)
            for index, value in enumerate(values):
                if isinstance(value, str) and '/api/meta/oauth/callback' in value:
                    values[index] = value.split('?')[0] + '?[oauth-parameters-redacted]'
            record.args = tuple(values)
        return True
