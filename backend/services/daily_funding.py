"""Daily credit reservations and settlement port. No public endpoint can invent provider spend."""
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
import hashlib
from sqlalchemy import update
from fastapi import HTTPException
from entities import (Campaign, CampaignFundingDay, FundReservation, Payment, PaymentOrder,
                      PublishingJob, ProviderSpendRecord, JournalLine, LedgerEntry, AuditEvent)
from services.subscriptions import enforce_limit


def local_day(c, now=None):
    return (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(c.billing_timezone)).date()


def reserve_day(db, c, index, now=None):
    db.flush()
    if not db.execute(update(Campaign).where(Campaign.id == c.id, Campaign.version == c.version,
            Campaign.company_review_status == 'Approved').values(updated_at=datetime.now(timezone.utc))).rowcount:
        raise HTTPException(409, 'Approved campaign version changed before funding.')
    existing = db.query(CampaignFundingDay).filter_by(campaign_id=c.id, campaign_version=c.version, day_index=index).first()
    if existing:
        if existing.status != 'reserved':
            raise HTTPException(409, 'This funding day requires reconciliation or is already closed.')
        return existing
    if not 0 <= index < c.duration_days or c.company_review_status != 'Approved':
        raise HTTPException(409, 'No approved campaign day is eligible for funding.')
    enforce_limit(db, c.owner, c.budget_paise, c.id, aggregate=True)
    billing_date = local_day(c, now)
    if index:
        prior = db.query(CampaignFundingDay).filter_by(campaign_id=c.id, campaign_version=c.version, day_index=index-1).first()
        if not prior or prior.status != 'settled':
            raise HTTPException(409, 'Previous day must have verified final spend and confirmed provider pause before renewal.')
        billing_date = date.fromisoformat(prior.billing_date)+timedelta(days=1)
        if billing_date != local_day(c, now):
            raise HTTPException(409, 'Funding is only permitted for the current billing date; missed days require review.')
    pricing = c.pricing_snapshot
    if not pricing or pricing['customer_daily_paise'] != c.budget_paise:
        raise HTTPException(409, 'Candidate-accepted pricing is required.')
    day = CampaignFundingDay(campaign_id=c.id, campaign_version=c.version, day_index=index,
        billing_date=billing_date.isoformat(), billing_timezone=c.billing_timezone,
        customer_paise=c.budget_paise, meta_paise=pricing['meta_daily_paise'], fee_paise=pricing['company_fee_paise'])
    db.add(day); db.flush()
    remaining = c.budget_paise
    payments = db.query(Payment).join(PaymentOrder).filter(Payment.user_id == c.owner_id,
        Payment.status == 'captured', PaymentOrder.item_type == 'campaign_budget', PaymentOrder.item_id == c.id).order_by(Payment.created_at, Payment.id).all()
    for p in payments:
        available = p.amount_paise-p.refund_reserved_paise-p.campaign_reserved_paise-p.campaign_consumed_paise
        amount = min(remaining, available)
        if amount <= 0:
            continue
        claimed = db.execute(update(Payment).where(Payment.id == p.id,
            Payment.amount_paise-Payment.refund_reserved_paise-Payment.campaign_reserved_paise-Payment.campaign_consumed_paise >= amount)
            .values(campaign_reserved_paise=Payment.campaign_reserved_paise+amount)).rowcount
        if not claimed:
            raise HTTPException(409, 'Funds changed; refresh before reserving again.')
        db.add(FundReservation(campaign_id=c.id, campaign_version=c.version, funding_day_id=day.id,
                               payment_id=p.id, amount_paise=amount))
        remaining -= amount
        if not remaining:
            return day
    raise HTTPException(409, 'Verified campaign funds must cover at least one customer daily budget before approval. No job was queued.')


def release_unsubmitted(db, campaign_id):
    rows = db.query(FundReservation).filter_by(campaign_id=campaign_id, status='reserved').all()
    days = db.query(CampaignFundingDay).filter_by(campaign_id=campaign_id).all()
    if any(d.status in ('reconciliation_required', 'settlement_pending') for d in days):
        raise HTTPException(409, 'Provider reconciliation is required before releasing these funds.')
    for row in rows:
        if db.execute(update(FundReservation).where(FundReservation.id == row.id, FundReservation.status == 'reserved')
                      .values(status='released')).rowcount:
            db.execute(update(Payment).where(Payment.id == row.payment_id).values(
                campaign_reserved_paise=Payment.campaign_reserved_paise-row.amount_paise))
    for day in days:
        if day.status == 'reserved':
            day.status = 'released'


@dataclass(frozen=True)
class VerifiedSpendConfirmation:
    """Trusted adapter output, never request JSON. Adapter must verify provider evidence first."""
    external_id: str
    funding_day_id: str
    meta_ad_id: str
    amount_paise: int
    currency: str
    period_start: str
    period_end: str
    provider_pause_confirmed: bool
    final: bool


def settle_verified_day(db, report: VerifiedSpendConfirmation, now=None):
    if not isinstance(report, VerifiedSpendConfirmation):
        raise ValueError('Trusted provider adapter confirmation required.')
    payload = asdict(report)
    prior = db.query(ProviderSpendRecord).filter_by(provider='meta', external_id=report.external_id).first()
    if prior:
        if prior.payload != payload:
            raise ValueError('Provider report ID was reused with different content.')
        return db.get(CampaignFundingDay, prior.funding_day_id)
    day = db.get(CampaignFundingDay, report.funding_day_id)
    if not day:
        raise ValueError('Funding day not found.')
    c = db.get(Campaign, day.campaign_id)
    db.execute(update(Campaign).where(Campaign.id == c.id).values(updated_at=datetime.now(timezone.utc)))
    db.refresh(c)
    prior = db.query(ProviderSpendRecord).filter_by(provider='meta', external_id=report.external_id).first()
    if prior:
        if prior.payload != payload:
            raise ValueError('Provider report ID was reused with different content.')
        return db.get(CampaignFundingDay, prior.funding_day_id)
    start = datetime.combine(date.fromisoformat(day.billing_date), datetime.min.time(), ZoneInfo(day.billing_timezone)).astimezone(timezone.utc)
    end = start+timedelta(days=1)
    clock = now or datetime.now(timezone.utc)
    if (not isinstance(report.external_id, str) or not 1 <= len(report.external_id) <= 150 or not c.meta_ad_id or report.meta_ad_id != c.meta_ad_id or
        report.currency != 'INR' or type(report.amount_paise) is not int or report.amount_paise < 0 or
        report.period_start != start.isoformat() or report.period_end != end.isoformat() or clock < end or
        not report.final or not report.provider_pause_confirmed):
        raise ValueError('Final period, matching ad/currency, and verified provider pause are required; funds stay reserved.')
    if report.amount_paise > day.meta_paise:
        event_id = 'over_'+hashlib.sha256(report.external_id.encode()).hexdigest()[:30]
        evidence = db.get(AuditEvent, event_id)
        if evidence and evidence.details != payload:
            raise ValueError('Provider evidence ID was reused with different content.')
        if not evidence:
            db.add(AuditEvent(id=event_id, target_user_id=c.owner_id,
                action='PROVIDER_OVERSPEND_RECONCILIATION_REQUIRED', details=payload))
        day.status = 'reconciliation_required'
        c.delivery_status = 'Reconciliation Required'
        return day  # No invented release, fee or negative balance on overspend.
    claimed = db.execute(update(CampaignFundingDay).where(CampaignFundingDay.id == day.id,
        CampaignFundingDay.status.in_(['reserved', 'reconciliation_required'])).values(status='settlement_pending')).rowcount
    if not claimed:
        raise ValueError('Funding day already closed or unavailable.')
    fee = int((Decimal(day.fee_paise)*report.amount_paise/day.meta_paise).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    consumed = report.amount_paise+fee
    rows = db.query(FundReservation).filter_by(funding_day_id=day.id, status='reserved').order_by(FundReservation.id).all()
    if sum(r.amount_paise for r in rows) != day.customer_paise:
        raise ValueError('Reservation evidence does not match the funding day.')
    remaining = consumed
    for row in rows:
        used = min(remaining, row.amount_paise)
        db.execute(update(Payment).where(Payment.id == row.payment_id).values(
            campaign_reserved_paise=Payment.campaign_reserved_paise-row.amount_paise,
            campaign_consumed_paise=Payment.campaign_consumed_paise+used))
        row.status = 'settled'; row.consumed_paise = used
        remaining -= used
    db.add(ProviderSpendRecord(provider='meta', external_id=report.external_id, funding_day_id=day.id, payload=payload))
    reference = 'day:'+day.id
    if consumed:
        db.add(JournalLine(transaction_id=reference, user_id=c.owner_id, account='candidate_credit', debit_paise=consumed, credit_paise=0))
        for account, amount, kind in [('meta_payable', report.amount_paise, 'META_DIRECT_SPEND'), ('service_revenue', fee, 'PLATFORM_CUT')]:
            if amount:
                db.add(JournalLine(transaction_id=reference, user_id=c.owner_id, account=account, debit_paise=0, credit_paise=amount))
                db.add(LedgerEntry(user_id=c.owner_id, tx_type=kind, amount_paise=-amount,
                    platform_cut_paise=amount if kind=='PLATFORM_CUT' else 0,
                    meta_spend_paise=amount if kind=='META_DIRECT_SPEND' else 0, reference_id=reference,
                    notes='Verified final provider report '+report.external_id))
    day.actual_spend_paise = report.amount_paise; day.earned_fee_paise = fee; day.status = 'settled'
    c.spent_paise += report.amount_paise
    c.delivery_status = 'Completed' if day.day_index+1 == c.duration_days else 'Paused'
    db.flush()
    return day


def funding_summary(db, c):
    rows = db.query(CampaignFundingDay).filter_by(campaign_id=c.id).order_by(CampaignFundingDay.created_at.desc()).limit(366).all()
    return [dict(id=d.id, version=d.campaign_version, day_index=d.day_index, billing_date=d.billing_date,
        billing_timezone=d.billing_timezone, status=d.status, customer_paise=d.customer_paise,
        meta_paise=d.meta_paise, fee_paise=d.fee_paise, actual_spend_paise=d.actual_spend_paise,
        earned_fee_paise=d.earned_fee_paise) for d in rows]


def renew_due_campaigns(db, now=None):
    """Closed days can fund the next current day; unknown delivery never releases credit."""
    cursor = ''
    while True:
        candidates = db.query(Campaign).filter(Campaign.company_review_status=='Approved',
            Campaign.delivery_status!='Completed', Campaign.id>cursor).order_by(Campaign.id).limit(100).all()
        if not candidates:
            break
        cursor = candidates[-1].id
        for c in candidates:
            renew_campaign_day(db, c, now)
        db.commit()


def renew_campaign_day(db, c, now=None):
    if not db.execute(update(Campaign).where(Campaign.id==c.id, Campaign.version==c.version,
            Campaign.company_review_status=='Approved').values(updated_at=datetime.now(timezone.utc))).rowcount:
        return
    db.refresh(c)
    day = db.query(CampaignFundingDay).filter_by(campaign_id=c.id, campaign_version=c.version).order_by(CampaignFundingDay.day_index.desc()).first()
    if not day or date.fromisoformat(day.billing_date) >= local_day(c, now):
        return
    if day.status != 'settled':
        job = db.query(PublishingJob).filter_by(campaign_id=c.id, campaign_version=c.version).first()
        if job and job.status in ('Queued', 'Failed', 'Needs Attention') and not any((job.meta_campaign_id, job.meta_adset_id, job.meta_creative_id, job.meta_ad_id)):
            c.delivery_status = 'Funding Required'
            return  # No provider submission; admin can cancel/review and release this hold.
        day.status = 'reconciliation_required'; c.delivery_status = 'Reconciliation Required'
        return
    if day.day_index+1 < c.duration_days:
        try:
            with db.begin_nested():
                reserve_day(db, c, day.day_index+1, now)
            c.delivery_status = 'Paused'  # Funding never asserts provider resumption.
        except HTTPException:
            c.delivery_status = 'Funding Required'
