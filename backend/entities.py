"""
SQLAlchemy Database Entities and Relationships for PolitiAds
Includes Core Models, Decoupled Publishing Jobs, Payment Gateway & Webhooks,
Financial Ledger, Refunds, and In-App Notifications.
"""
import uuid
import sys
from pathlib import Path
from datetime import datetime, timezone

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index, JSON, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid(prefix: str = "") -> str:
    raw = uuid.uuid4().hex
    return f"{prefix}_{raw[:12]}" if prefix else raw

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("usr"))
    full_name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    mobile = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="candidate", nullable=False)  # 'candidate' | 'admin'
    status = Column(String(20), default="active", index=True, nullable=False)  # 'active' | 'suspended' | 'pending'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    profile = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="user", cascade="all, delete-orphan")

class CandidateProfile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("prof"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    candidate_name = Column(String(100), nullable=False)
    contesting_post = Column(String(100), default="Ward Councillor / Corporator", nullable=False)
    gaon_ward = Column(String(100), nullable=False)
    area_block = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    lat = Column(String(30), default="27.4482", nullable=False)
    lng = Column(String(30), default="78.0416", nullable=False)
    accuracy_m = Column(Integer, default=25, nullable=False)
    symbol_name = Column(String(50), default="Car", nullable=False)
    custom_symbol_url = Column(Text, nullable=True)
    default_slogan = Column(Text, nullable=True)
    disclaimer_text = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)
    is_meta_connected = Column(Boolean, default=False, nullable=False)
    meta_connection_status = Column(String(40), default="Not Connected", nullable=False)  # 'Not Connected' | 'Connected & Active' | 'Permission Required' | 'Authorization Expired'
    meta_page_id = Column(String(100), nullable=True)
    meta_page_name = Column(String(150), nullable=True)
    meta_access_token_encrypted = Column(Text, nullable=True)
    meta_facebook_subject = Column(String(100), nullable=True)
    meta_page_token_encrypted = Column(Text, nullable=True)
    meta_scopes = Column(JSON, nullable=True)
    meta_token_expires_at = Column(DateTime, nullable=True)
    meta_verified_at = Column(DateTime, nullable=True)
    meta_connection_generation = Column(Integer, nullable=False, default=0)
    instagram_account_id = Column(String(100), nullable=True)
    instagram_username = Column(String(150), nullable=True)
    is_instagram_connected = Column(Boolean, nullable=False, default=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="profile")

class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (Index('ix_campaign_review_updated', 'company_review_status', 'updated_at', 'id'),
                      Index('ix_campaign_owner_review', 'owner_id', 'company_review_status'))

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("ad"))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(150), nullable=False)
    slogan = Column(Text, nullable=False)
    budget_paise = Column(Integer, nullable=False)  # stored in paise (₹1 = 100 paise)
    radius_km = Column(Float, nullable=False)
    reach = Column(Integer, default=0, nullable=False)
    spent_paise = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    status = Column(String(40), default="Under Company Review ⏳", index=True, nullable=False)
    badge = Column(String(100), default="⏳ Experts Reviewing & Enhancing", nullable=False)
    template_id = Column(Integer, default=1, nullable=False)
    meta_ad_id = Column(String(100), nullable=True)
    area = Column(String(150), nullable=True)
    pincode = Column(String(10), nullable=True)
    whatsapp_phone = Column(String(20), nullable=True)
    symbol = Column(String(100), nullable=True)
    photo_url = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    approved_version = Column(Integer, nullable=True)
    pricing_snapshot = Column(JSON, nullable=True)
    duration_days = Column(Integer, nullable=False, default=1)
    billing_timezone = Column(String(50), nullable=False, default='Asia/Kolkata')

    # Decoupled Multi-State Status Model
    company_review_status = Column(String(40), default="Pending", index=True, nullable=False)  # 'Pending' | 'Approved' | 'Rejected'
    publishing_job_status = Column(String(40), default="Queued", index=True, nullable=False)   # 'Queued' | 'Processing' | 'Submitted' | 'Failed'
    provider_review_status = Column(String(40), default="Pending", index=True, nullable=False) # 'Pending' | 'Approved' | 'Rejected'
    delivery_status = Column(String(40), default="Paused", index=True, nullable=False)         # 'Paused' | 'Eligible' | 'Delivering' | 'Not Delivering' | 'Completed'

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="campaigns")
    reviews = relationship("Review", back_populates="campaign", cascade="all, delete-orphan")
    publishing_jobs = relationship("PublishingJob", back_populates="campaign", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("rev"))
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_slogan = Column(Text, nullable=False)
    enhanced_slogan = Column(Text, nullable=False)
    status = Column(String(40), default="Pending Admin Review 🟡", index=True, nullable=False)
    correction_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    campaign = relationship("Campaign", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

class PublishingJob(Base):
    __tablename__ = "publishing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("job"))
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    campaign_version = Column(Integer, nullable=False, default=1)
    approved_snapshot = Column(JSON, nullable=True)
    stage = Column(String(50), default="QUEUED", index=True, nullable=False)  # QUEUED, VALIDATING, CREATING_CAMPAIGN, CREATING_ADSET, CREATING_CREATIVE, CREATING_AD, SUBMITTED, FAILED
    status = Column(String(40), default="Queued", index=True, nullable=False)
    idempotency_key = Column(String(64), unique=True, index=True, nullable=False)
    meta_campaign_id = Column(String(100), nullable=True)
    meta_adset_id = Column(String(100), nullable=True)
    meta_creative_id = Column(String(100), nullable=True)
    meta_ad_id = Column(String(100), nullable=True)
    error_details = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    lease_owner = Column(String(64), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    heartbeat_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    campaign = relationship("Campaign", back_populates="publishing_jobs")

class SubscriptionPlan(Base):
    __tablename__ = "plans"

    id = Column(String(50), primary_key=True, default=lambda: generate_uuid("plan"))
    name = Column(String(100), nullable=False)
    price_paise = Column(Integer, nullable=False)
    daily_ad_cap_paise = Column(Integer, nullable=False)
    badge = Column(String(50), default="Popular", nullable=False)
    features = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("order"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    item_type = Column(String(50), nullable=False)  # 'subscription_plan' | 'campaign_budget'
    item_id = Column(String(50), nullable=True)
    amount_paise = Column(Integer, nullable=False)
    campaign_version = Column(Integer, nullable=True)
    pricing_snapshot = Column(JSON, nullable=True)
    plan_snapshot = Column(JSON, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(40), default="created", index=True, nullable=False)  # 'created' | 'paid' | 'failed' | 'cancelled'
    razorpay_order_id = Column(String(100), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="payment_orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("pay"))
    order_id = Column(String(36), ForeignKey("payment_orders.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    razorpay_payment_id = Column(String(100), unique=True, index=True, nullable=False)
    razorpay_signature = Column(String(255), nullable=True)
    status = Column(String(40), default="captured", index=True, nullable=False)  # 'captured' | 'failed' | 'refunded'
    payment_method = Column(String(50), default="upi", nullable=True)  # 'upi' | 'card' | 'netbanking'
    refund_reserved_paise = Column(Integer, default=0, nullable=False)
    campaign_reserved_paise = Column(Integer, default=0, nullable=False)
    campaign_consumed_paise = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("PaymentOrder", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("wh"))
    event_id = Column(String(100), unique=True, index=True, nullable=False)  # Unique provider event ID for idempotency
    event_type = Column(String(100), index=True, nullable=False)
    signature_verified = Column(Boolean, default=False, nullable=False)
    is_processed = Column(Boolean, default=False, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("ledg"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    tx_type = Column(String(50), index=True, nullable=False)  # 'DEPOSIT' | 'PLATFORM_CUT' | 'META_DIRECT_SPEND' | 'REFUND'
    amount_paise = Column(Integer, nullable=False)
    platform_cut_paise = Column(Integer, default=0, nullable=False)
    meta_spend_paise = Column(Integer, default=0, nullable=False)
    reference_id = Column(String(100), index=True, nullable=True)  # payment_id, refund_id, or campaign_id
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="ledger_entries")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("ref"))
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    amount_paise = Column(Integer, nullable=False)
    razorpay_refund_id = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(String(40), default="processed", index=True, nullable=False)  # 'pending' | 'processed' | 'failed'
    reason = Column(Text, nullable=True)
    operation_id = Column(String(100), unique=True, nullable=False, default=lambda: generate_uuid("refund_op"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    payment = relationship("Payment", back_populates="refunds")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("notif"))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(String(50), default="info", nullable=False)  # 'campaign_update' | 'payment_success' | 'review_ready' | 'system'
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    action_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notifications")

class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("sess"))
    token_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 of opaque token
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    is_revoked = Column(Boolean, default=False, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="sessions")

class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("audit"))
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    target_user_id = Column(String(36), index=True, nullable=True)
    action = Column(String(100), index=True, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class JournalLine(Base):
    """Signed debit/credit lines. Historical summary rows are not journal evidence."""
    __tablename__ = "journal_lines"
    __table_args__ = (
        UniqueConstraint('transaction_id', 'account', name='uq_journal_transaction_account'),
        CheckConstraint('(debit_paise > 0 AND credit_paise = 0) OR (credit_paise > 0 AND debit_paise = 0)', name='ck_journal_one_side'),
    )
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("jl"))
    transaction_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    account = Column(String(50), nullable=False)
    debit_paise = Column(Integer, default=0, nullable=False)
    credit_paise = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class ServiceRecord(Base):
    __tablename__ = 'service_records'
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('service'))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    kind = Column(String(30), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SocialIdentity(Base):
    __tablename__ = 'social_identities'
    __table_args__ = (
        UniqueConstraint('provider', 'app_id', 'subject', name='uq_social_subject'),
        UniqueConstraint('provider', 'app_id', 'user_id', name='uq_social_user'),
    )
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('identity'))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = Column(String(30), nullable=False)
    app_id = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class OAuthAttempt(Base):
    __tablename__ = 'oauth_attempts'
    state_hash = Column(String(64), primary_key=True)
    nonce_hash = Column(String(64), nullable=False)
    purpose = Column(String(30), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    session_hash = Column(String(64), nullable=True)
    connection_generation = Column(Integer, nullable=True)
    consumed = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=False)


class CampaignRevision(Base):
    __tablename__ = 'campaign_revisions'
    __table_args__ = (UniqueConstraint('campaign_id', 'version', name='uq_campaign_revision'),)
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('revision'))
    campaign_id = Column(String(36), ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    actor_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    action = Column(String(40), nullable=False)
    snapshot = Column(JSON, nullable=False)
    media_url = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class FundReservation(Base):
    __tablename__ = 'fund_reservations'
    __table_args__ = (UniqueConstraint('funding_day_id', 'payment_id', name='uq_day_fund_payment'),)
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('reserve'))
    campaign_id = Column(String(36), ForeignKey('campaigns.id'), nullable=False, index=True)
    campaign_version = Column(Integer, nullable=False)
    payment_id = Column(String(36), ForeignKey('payments.id'), nullable=False)
    funding_day_id = Column(String(36), ForeignKey('campaign_funding_days.id'), nullable=True, index=True)
    amount_paise = Column(Integer, nullable=False)
    consumed_paise = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default='reserved')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('sub'))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey('payments.id'), nullable=False, unique=True)
    plan_snapshot = Column(JSON, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default='active', index=True)
    source = Column(String(30), nullable=False, default='verified_order')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (Index('ix_subscription_user_status_expiry', 'user_id', 'status', 'expires_at'),)


class CampaignFundingDay(Base):
    __tablename__ = 'campaign_funding_days'
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('day'))
    campaign_id = Column(String(36), ForeignKey('campaigns.id'), nullable=False, index=True)
    campaign_version = Column(Integer, nullable=False)
    day_index = Column(Integer, nullable=False)
    billing_date = Column(String(10), nullable=False)
    billing_timezone = Column(String(50), nullable=False)
    customer_paise = Column(Integer, nullable=False)
    meta_paise = Column(Integer, nullable=False)
    fee_paise = Column(Integer, nullable=False)
    actual_spend_paise = Column(Integer, nullable=False, default=0)
    earned_fee_paise = Column(Integer, nullable=False, default=0)
    status = Column(String(40), nullable=False, default='reserved', index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (
        UniqueConstraint('campaign_id', 'campaign_version', 'day_index', name='uq_campaign_funding_day'),
        CheckConstraint('customer_paise > 0 AND meta_paise > 0 AND fee_paise >= 0 AND meta_paise + fee_paise = customer_paise', name='ck_funding_day_split'),
    )


class ProviderSpendRecord(Base):
    __tablename__ = 'provider_spend_records'
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('spend'))
    provider = Column(String(30), nullable=False)
    external_id = Column(String(150), nullable=False)
    funding_day_id = Column(String(36), ForeignKey('campaign_funding_days.id'), nullable=False, unique=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (UniqueConstraint('provider', 'external_id', name='uq_provider_spend_event'),)


class PublishingAttempt(Base):
    __tablename__ = 'publishing_attempts'
    id = Column(String(36), primary_key=True, default=lambda: generate_uuid('attempt'))
    job_id = Column(String(36), ForeignKey('publishing_jobs.id'), nullable=False, index=True)
    lease_owner = Column(String(64), nullable=False, unique=True)
    number = Column(Integer, nullable=False)
    stage = Column(String(50), nullable=False, default='VALIDATING')
    status = Column(String(40), nullable=False, default='Processing')
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)


from sqlalchemy import event
from sqlalchemy.orm import Session as ORMSession
@event.listens_for(ORMSession, 'before_flush')
def append_only_accounting(session, flush_context, instances):
    for record in list(session.dirty) + list(session.deleted):
        if isinstance(record, (LedgerEntry, JournalLine, CampaignRevision, ProviderSpendRecord)):
            raise ValueError('Accounting records are append-only; write a reversal instead.')
