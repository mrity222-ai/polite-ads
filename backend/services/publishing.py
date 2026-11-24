"""Leased, version-bound publishing. Live provider writes remain unavailable."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import update, or_
from entities import Campaign, PublishingJob, PublishingAttempt, PlatformSetting, CampaignFundingDay
from integrations.meta.client import MetaGraphClient
from config import META_MOCK_MODE, META_KILL_SWITCH
from services import publishing_context
from services.subscriptions import enforce_limit

LEASE_SECONDS = 90
MAX_ATTEMPTS = 3


class LostLease(RuntimeError):
    pass


class RetryablePublishingError(RuntimeError):
    """Only for provider-confirmed safe retry or side-effect-free transient operations."""


def now_utc():
    return datetime.now(timezone.utc)


def create_publishing_job(db, campaign_id, commit=True):
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.company_review_status != 'Approved' or campaign.approved_version != campaign.version:
        raise ValueError('Current company-approved version required.')
    existing = db.query(PublishingJob).filter_by(campaign_id=campaign_id, campaign_version=campaign.version).first()
    if existing:
        return existing
    from services.campaign_review import snapshot
    payload = snapshot(campaign)
    payload['publishing_context'] = publishing_context.capture(db, campaign)
    day = db.query(CampaignFundingDay).filter_by(campaign_id=campaign_id, campaign_version=campaign.version, day_index=0).one()
    payload['start_billing_date'] = day.billing_date
    job = PublishingJob(campaign_id=campaign_id, campaign_version=campaign.version, approved_snapshot=payload,
                        idempotency_key=hashlib.sha256(f'{campaign_id}:{campaign.version}'.encode()).hexdigest())
    db.add(job)
    campaign.publishing_job_status = 'Queued'
    campaign.status = 'Publishing Queued'
    campaign.badge = 'Company approved; provider submission pending'
    db.flush()
    if commit:
        db.commit()
    return job


def heartbeat(db, job_id, owner, stage=None):
    now = now_utc()
    values = dict(heartbeat_at=now, lease_expires_at=now+timedelta(seconds=LEASE_SECONDS))
    if stage:
        values['stage'] = stage
    if not db.execute(update(PublishingJob).where(PublishingJob.id==job_id, PublishingJob.status=='Processing',
            PublishingJob.lease_owner==owner, PublishingJob.lease_expires_at>now).values(**values).execution_options(synchronize_session=False)).rowcount:
        db.rollback()
        raise LostLease('Publishing lease lost; provider evidence requires reconciliation.')
    attempt = db.query(PublishingAttempt).filter_by(lease_owner=owner).one()
    if stage:
        attempt.stage = stage
    db.commit()


def recover_expired(db, now=None):
    now = now or now_utc()
    rows = db.query(PublishingJob).filter(PublishingJob.status=='Processing',
        or_(PublishingJob.lease_expires_at<=now, PublishingJob.lease_expires_at.is_(None))).limit(100).all()
    for job in rows:
        status = ('Queued' if job.attempt_count < MAX_ATTEMPTS else 'Needs Attention') if META_MOCK_MODE else 'Reconciliation Required'
        changed = db.execute(update(PublishingJob).where(PublishingJob.id==job.id, PublishingJob.status=='Processing',
            or_(PublishingJob.lease_expires_at<=now, PublishingJob.lease_expires_at.is_(None))).values(
            status=status, lease_owner=None, lease_expires_at=None, next_attempt_at=now+timedelta(seconds=2),
            error_details='Worker lease expired; '+('safe simulation recovery' if META_MOCK_MODE else 'provider reconciliation required')).execution_options(synchronize_session=False)).rowcount
        if changed:
            db.execute(update(PublishingAttempt).where(PublishingAttempt.job_id==job.id,
                PublishingAttempt.status=='Processing').values(status='Interrupted', finished_at=now))
            c = db.get(Campaign, job.campaign_id)
            if c:
                c.publishing_job_status=status
                if status=='Reconciliation Required':
                    c.delivery_status='Reconciliation Required'
    db.commit()
    return len(rows)


def execute_publishing_job(db, job_id):
    owner = uuid.uuid4().hex
    now = now_utc()
    claimed = db.execute(update(PublishingJob).where(PublishingJob.id==job_id, PublishingJob.status=='Queued',
        PublishingJob.attempt_count<MAX_ATTEMPTS,
        or_(PublishingJob.next_attempt_at.is_(None), PublishingJob.next_attempt_at<=now)).values(
        status='Processing', stage='VALIDATING', lease_owner=owner, heartbeat_at=now,
        lease_expires_at=now+timedelta(seconds=LEASE_SECONDS), attempt_count=PublishingJob.attempt_count+1).execution_options(synchronize_session=False)).rowcount
    if not claimed:
        db.rollback()
        return db.get(PublishingJob, job_id)
    db.flush()
    job = db.get(PublishingJob, job_id); db.refresh(job)
    db.add(PublishingAttempt(job_id=job.id, lease_owner=owner, number=job.attempt_count))
    db.commit()
    campaign = db.get(Campaign, job.campaign_id)
    try:
        kill = db.get(PlatformSetting, 'meta_kill_switch')
        if META_KILL_SWITCH or (kill and kill.value.lower()=='true'):
            raise ValueError('Publishing disabled by kill-switch.')
        if not campaign or campaign.version!=job.campaign_version or campaign.approved_version!=job.campaign_version:
            raise ValueError('Approved version was superseded; publishing blocked.')
        if not job.approved_snapshot or not job.approved_snapshot.get('publishing_context'):
            raise ValueError('Complete approved snapshot required; legacy job needs fresh review.')
        if not META_MOCK_MODE:
            raise ValueError('Live Meta publishing blocked: provider implementation/approval not available.')
        if campaign.company_review_status!='Approved' or campaign.owner.status!='active':
            raise ValueError('Active owner and company approval required.')
        enforce_limit(db, campaign.owner, campaign.budget_paise, campaign.id, aggregate=True)
        context = publishing_context.verify(db, campaign, job.approved_snapshot)
        from services.daily_funding import local_day
        day = db.query(CampaignFundingDay).filter_by(campaign_id=campaign.id, campaign_version=job.campaign_version,
            billing_date=local_day(campaign).isoformat(), status='reserved').first()
        if not day:
            raise ValueError('Current billing day requires verified reserved funds and reconciliation.')
        payload = job.approved_snapshot
        client = MetaGraphClient()
        stages = [
            ('meta_campaign_id', lambda: client.create_political_campaign('mock_account', payload['title'], job.idempotency_key)),
            ('meta_adset_id', lambda: client.create_adset('mock_account', job.meta_campaign_id, payload['title'],
                payload['pricing_snapshot']['meta_daily_paise'], context['lat'], context['lng'], payload['radius_km'])),
            ('meta_creative_id', lambda: client.create_ad_creative('mock_account', context['page_id'], payload['title'],
                payload['slogan'], context['disclaimer'], payload['photo_url'])),
            ('meta_ad_id', lambda: client.create_ad('mock_account', job.meta_adset_id, job.meta_creative_id, payload['title'])),
        ]
        campaign.publishing_job_status='Processing'
        for field, create in stages:
            if not getattr(job, field):
                heartbeat(db, job.id, owner, field.upper())
                if campaign.owner.status != 'active' or campaign.version != job.campaign_version:
                    raise ValueError('Account or campaign version changed during publishing.')
                publishing_context.verify(db, campaign, payload)
                response = create()
                heartbeat(db, job.id, owner)
                setattr(job, field, response['id']); db.commit()
        heartbeat(db, job.id, owner)
        publishing_context.verify(db, campaign, payload)
        job.status='Submitted'; job.stage='MOCK_SUBMITTED'; job.error_details=None
        campaign.meta_ad_id=job.meta_ad_id; campaign.publishing_job_status='Submitted'
        campaign.provider_review_status='Not Submitted (Mock)'; campaign.delivery_status='Paused'
        campaign.status='Mock Submitted (Paused)'; campaign.badge='Simulation only; no Meta publication'
        attempt=db.query(PublishingAttempt).filter_by(lease_owner=owner).one()
        attempt.status='Submitted'; attempt.finished_at=now_utc()
        job.lease_owner=None; job.lease_expires_at=None
        db.commit()
    except LostLease:
        db.rollback()  # A stale owner must never overwrite the new owner's state.
    except Exception as error:
        db.rollback()
        job=db.get(PublishingJob, job_id); db.refresh(job)
        if job.lease_owner!=owner or job.status!='Processing':
            return job
        retry=isinstance(error, RetryablePublishingError) and job.attempt_count<MAX_ATTEMPTS
        status='Queued' if retry else ('Needs Attention' if isinstance(error, RetryablePublishingError) else 'Failed')
        if not META_MOCK_MODE and job.stage!='VALIDATING':
            status='Reconciliation Required'
        job.status=status; job.error_details=str(error)[:300]; job.retry_count+=1
        job.next_attempt_at=now_utc()+timedelta(seconds=2**job.attempt_count) if retry else None
        job.lease_owner=None; job.lease_expires_at=None
        attempt=db.query(PublishingAttempt).filter_by(lease_owner=owner).one()
        attempt.status=status; attempt.error=job.error_details; attempt.finished_at=now_utc()
        if campaign:
            campaign=db.get(Campaign, campaign.id)
            campaign.publishing_job_status=status; campaign.status='Publishing '+status
            campaign.badge='Submission requires attention'
            if status=='Reconciliation Required':campaign.delivery_status=status
        db.commit()
    return db.get(PublishingJob, job_id)
