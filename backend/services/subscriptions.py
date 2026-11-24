"""Purchased entitlements are independent of mutable catalog rows and payment display state."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import update, func
from fastapi import HTTPException
from entities import Subscription, User, Campaign, Refund


def utc(value=None):
    value = value or datetime.now(timezone.utc)
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def catalog_snapshot(plan):
    return dict(id=plan.id, name=plan.name, price_paise=plan.price_paise,
                daily_ad_cap_paise=plan.daily_ad_cap_paise, features=list(plan.features or []),
                badge=plan.badge, duration_days=30, renewal_rule='replace_immediately_30_days')


def activate(db, payment, order):
    if order.item_type != 'subscription_plan' or db.query(Subscription).filter_by(payment_id=payment.id).first():
        return
    # Serializes competing purchases and approval-limit checks for this owner.
    db.execute(update(User).where(User.id == payment.user_id).values(updated_at=datetime.now(timezone.utc)))
    now = utc(payment.created_at)
    snap = order.plan_snapshot
    if snap:
        db.execute(update(Subscription).where(Subscription.user_id == payment.user_id,
            Subscription.status == 'active').values(status='superseded'))
    db.add(Subscription(user_id=payment.user_id, payment_id=payment.id, plan_snapshot=snap,
        starts_at=now, expires_at=now+timedelta(days=30), status='active' if snap else 'review_required',
        source='verified_order' if snap else 'legacy_unverified'))


def revoke_fully_refunded(db, payment):
    total = db.query(func.coalesce(func.sum(Refund.amount_paise), 0)).filter_by(
        payment_id=payment.id, status='processed').scalar()
    if total >= payment.amount_paise:
        payment.status = 'refunded'
        db.execute(update(Subscription).where(Subscription.payment_id == payment.id).values(status='revoked'))


def entitlement(db, user, now=None):
    now = utc(now)
    rows = db.query(Subscription).filter_by(user_id=user.id).order_by(Subscription.starts_at.desc(), Subscription.id.desc()).all()
    active = next((s for s in rows if s.status == 'active' and utc(s.starts_at) <= now < utc(s.expires_at)), None)
    if active and active.plan_snapshot:
        return dict(status='active', is_demo=False, subscription_id=active.id, snapshot=active.plan_snapshot,
                    starts_at=utc(active.starts_at), expires_at=utc(active.expires_at))
    if rows:
        last = rows[0]
        status = 'expired' if last.status == 'active' and now >= utc(last.expires_at) else last.status
        return dict(status=status, is_demo=False, subscription_id=last.id, snapshot=None,
                    starts_at=utc(last.starts_at), expires_at=utc(last.expires_at))
    end = utc(user.created_at)+timedelta(days=30)
    return dict(status='active' if now < end else 'expired', is_demo=True, subscription_id=None,
                snapshot=dict(id='demo_plan', name='Local Trial', price_paise=0, daily_ad_cap_paise=50000,
                              features=['Local draft preparation and company review'], badge='Trial') if now < end else None,
                starts_at=utc(user.created_at), expires_at=end)


def enforce_limit(db, user, budget_paise, campaign_id=None, aggregate=False):
    if aggregate:
        db.execute(update(User).where(User.id == user.id).values(updated_at=datetime.now(timezone.utc)))
        db.refresh(user)
    if user.status != 'active':
        raise HTTPException(409, 'An active candidate account is required for campaign entitlement and funding.')
    access = entitlement(db, user)
    if access['status'] != 'active' or not access['snapshot']:
        raise HTTPException(409, 'An active subscription or trial entitlement is required. Expired, refunded or unverified plans cannot fund delivery.')
    cap = access['snapshot']['daily_ad_cap_paise']
    total = budget_paise
    if aggregate:
        total += db.query(func.coalesce(func.sum(Campaign.budget_paise), 0)).filter(
            Campaign.owner_id == user.id, Campaign.company_review_status == 'Approved',
            Campaign.delivery_status != 'Completed', Campaign.id != (campaign_id or '')).scalar()
    if total > cap:
        raise HTTPException(409, f'Plan daily limit is ₹{cap/100:g}; the requested approved daily total exceeds it.')
    return access
