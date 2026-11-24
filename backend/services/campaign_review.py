"""Versioned company moderation and explicit, immutable pricing quotes (integer paise)."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import defer
from entities import (Campaign, CampaignRevision, Review, PublishingJob, PlatformSetting,
                      AuditEvent, Payment, PaymentOrder)

FIELDS = ('title', 'slogan', 'area', 'pincode', 'whatsapp_phone', 'radius_km', 'template_id', 'symbol', 'photo_url', 'duration_days', 'billing_timezone')


def paise(value):
    return int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def policy(db):
    setting = db.get(PlatformSetting, 'campaign_pricing_policy')
    if setting:
        return json.loads(setting.value)
    legacy = db.get(PlatformSetting, 'company_commission_pct')
    return dict(mode='percentage', commission_pct=float(legacy.value) if legacy else 20,
                meta_daily_paise=7000, policy_version='initial')


def quote(db, gross, selected_policy=None, meta_override=None):
    rule = selected_policy or policy(db)
    fee = int((Decimal(gross) * Decimal(str(rule['commission_pct'])) / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    meta = meta_override if meta_override is not None else (rule['meta_daily_paise'] if rule['mode'] == 'fixed_meta' else gross - fee)
    if type(meta) is not int or not 0 < meta <= gross:
        raise HTTPException(422, 'Meta allocation must be positive and cannot exceed the customer daily total.')
    return dict(customer_daily_paise=gross, meta_daily_paise=meta, company_fee_paise=gross-meta,
                fee_recognition_rule='proportional_verified_final_meta_spend',
                policy_version=rule['policy_version'], mode='campaign_override' if meta_override is not None else rule['mode'],
                commission_pct=round((gross-meta)*100/gross, 4))


def snapshot(c):
    return {**{field: getattr(c, field) for field in FIELDS}, 'budget_daily': c.budget_paise/100,
            'pricing_snapshot': c.pricing_snapshot, 'version': c.version}


def record(db, c, actor, action, note='', before=None):
    content = snapshot(c)
    media = content.pop('photo_url', None)
    content.update(photo_url=None, has_image=bool(media))
    db.add(CampaignRevision(campaign_id=c.id, version=c.version, actor_id=actor.id,
                            action=action, snapshot=content, media_url=media, note=note))
    db.add(AuditEvent(actor_id=actor.id, target_user_id=c.owner_id, action='CAMPAIGN_'+action.upper(),
                      details={'campaign_id': c.id, 'version': c.version, 'before': before, 'after': snapshot(c), 'note': note}))


def lock_version(db, c, expected):
    if not db.execute(update(Campaign).where(Campaign.id == c.id, Campaign.version == expected)
                      .values(version=expected+1)).rowcount:
        db.rollback()
        raise HTTPException(409, 'This ad changed. Refresh and review its latest version.')
    db.refresh(c)


def cancel_unsubmitted(db, c):
    if c.delivery_status == 'Delivering' or db.query(PublishingJob).filter(
            PublishingJob.campaign_id == c.id, PublishingJob.status.in_(['Processing', 'Submitted', 'Reconciliation Required'])).first():
        raise HTTPException(409, 'Provider submission is in progress or recorded. Confirm provider pause/cancellation before editing this campaign.')
    db.execute(update(PublishingJob).where(PublishingJob.campaign_id == c.id,
        PublishingJob.status.in_(['Queued', 'Failed'])).values(status='Cancelled', stage='SUPERSEDED'))
    release(db, c.id)


def release(db, campaign_id):
    from services.daily_funding import release_unsubmitted
    return release_unsubmitted(db, campaign_id)


def reserve(db, c):
    from services.daily_funding import reserve_day
    return reserve_day(db, c, 0)


def apply_content(c, payload):
    for field in FIELDS:
        setattr(c, field, getattr(payload, field))
    c.budget_paise = paise(payload.budget_daily)


def review_state(db, c, state, note, actor=None):
    c.company_review_status = state
    c.status = {'Draft': 'Draft', 'Pending': 'Under Company Review', 'Changes Requested': 'Changes Requested',
                'Rejected': 'Company Rejected', 'Approved': 'Company Approved'}[state]
    c.badge = note[:100] or c.status
    rev = db.query(Review).filter_by(campaign_id=c.id).order_by(Review.created_at.desc()).first()
    if not rev:
        rev = Review(campaign_id=c.id, original_slogan=c.slogan, enhanced_slogan=c.slogan)
        db.add(rev)
    rev.enhanced_slogan = c.slogan
    rev.status = 'Pending Admin Review' if state == 'Pending' else state
    rev.correction_note = note
    if actor:
        rev.reviewer_id = actor.id
        rev.reviewed_at = datetime.now(timezone.utc)
    if state != 'Approved':
        c.approved_version = None
        c.publishing_job_status = 'Not Queued'


def history(db, c, limit=10, before_version=None):
    query = db.query(CampaignRevision).options(defer(CampaignRevision.media_url)).filter_by(campaign_id=c.id)
    if before_version is not None:
        query = query.filter(CampaignRevision.version < before_version)
    return [dict(version=r.version, action=r.action, actor_id=r.actor_id,
                 snapshot={**r.snapshot, 'photo_url': None, 'has_image': bool(r.snapshot.get('has_image') or r.snapshot.get('photo_url'))},
                 note=r.note, created_at=r.created_at.isoformat()) for r in query
            .order_by(CampaignRevision.version.desc()).limit(limit)]


def funds(db, c):
    rows = db.query(Payment).join(PaymentOrder).filter(PaymentOrder.item_type == 'campaign_budget',
            PaymentOrder.item_id == c.id, Payment.user_id == c.owner_id, Payment.status == 'captured').all()
    return dict(available_paise=sum(p.amount_paise-p.refund_reserved_paise-p.campaign_reserved_paise-p.campaign_consumed_paise for p in rows),
                reserved_paise=sum(p.campaign_reserved_paise for p in rows),
                consumed_paise=sum(p.campaign_consumed_paise for p in rows),
                required_daily_paise=c.budget_paise)
