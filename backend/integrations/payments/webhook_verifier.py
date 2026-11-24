import hmac
import hashlib
from typing import Tuple
from config import RAZORPAY_WEBHOOK_SECRET
from redacting_logger import get_redacted_logger

logger = get_redacted_logger("webhook_verifier")

def verify_razorpay_webhook_signature(
    raw_payload_bytes: bytes,
    signature_header: str
) -> Tuple[bool, str]:
    """
    Validates Razorpay webhook cryptographic signature.
    Matches HMAC-SHA256 of raw bytes with X-Razorpay-Signature header.
    Returns (is_valid: bool, reason: str).
    """
    if not signature_header:
        return False, "Missing X-Razorpay-Signature header."

    secret = RAZORPAY_WEBHOOK_SECRET
    if not secret:
        logger.error("RAZORPAY_WEBHOOK_SECRET is not configured.")
        return False, "Server webhook secret not configured."

    try:
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            raw_payload_bytes,
            hashlib.sha256
        ).hexdigest()

        is_match = hmac.compare_digest(expected_signature, signature_header)
        if is_match:
            return True, "Signature verified."
        else:
            return False, "Cryptographic signature mismatch."
    except Exception as e:
        logger.error(f"Error computing webhook signature: {str(e)}")
        return False, f"Signature evaluation failed: {str(e)}"
