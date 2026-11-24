"""Candidate revisions, per-ad company decisions, and prospective pricing settings."""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, defer
from sqlalchemy.orm import Session
from database import get_db
from dependencies import require_active_user, require_admin
from entities import User, Campaign, PlatformSetting, AuditEvent, Notification, CampaignRevision, PublishingJob
from models import CampaignEditRequest, ReviewDecisionRequest, PricingPolicyRequest
from services import campaign_review as service
from services.publishing import create_publishing_job

router = APIRouter(tags=['Campaign review'])


def owned(db, campaign_id, user):
    c = db.get(Campaign, campaign_id)
    if not c or (user.role != 'admin' and c.owner_id != user.id):
        raise HTTPException(404, 'Campaign not found.')
    return c


def detail(db, c):
    from services.daily_funding import funding_summary
    from services.publishing_context import capture
    original = db.query(CampaignRevision).options(defer(CampaignRevision.media_url)).filter_by(campaign_id=c.id).order_by(CampaignRevision.version).first()
    job = db.query(PublishingJob).filter_by(campaign_id=c.id, campaign_version=c.version).first()
    context = (job.approved_snapshot or {}).get('publishing_context') if job else None
    return dict(id=c.id, owner_id=c.owner_id, candidate_name=c.owner.full_name,
                original_submission={**original.snapshot, 'photo_url': None} if original else None,
                publishing_context=context or capture(db, c),
                content=service.snapshot(c), version=c.version, company_review_status=c.company_review_status,
                publishing_job_status=c.publishing_job_status, provider_review_status=c.provider_review_status,
                delivery_status=c.delivery_status, history=service.history(db, c, limit=10), funds=service.funds(db, c),
                funding_days=funding_summary(db, c))


@router.get('/api/campaigns/pricing-quote')
def pricing_quote(budget_daily: float = Query(ge=200, le=10000000, allow_inf_nan=False),
                  user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    return service.quote(db, service.paise(budget_daily))


@router.get('/api/campaigns/{campaign_id}/review')
def campaign_detail(campaign_id: str, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    return detail(db, owned(db, campaign_id, user))


@router.post('/api/campaigns/{campaign_id}/revise')
def revise(campaign_id: str, req: CampaignEditRequest, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    c = owned(db, campaign_id, user)
    if c.owner_id != user.id:
        raise HTTPException(403, 'Use the admin review editor for another account.')
    from services.subscriptions import enforce_limit
    enforce_limit(db, user, service.paise(req.budget_daily), c.id)
    before = service.snapshot(c)
    service.cancel_unsubmitted(db, c)
    service.lock_version(db, c, req.expected_version)
    pricing = c.pricing_snapshot if c.pricing_snapshot and c.pricing_snapshot['customer_daily_paise'] == service.paise(req.budget_daily) else service.quote(db, service.paise(req.budget_daily))
    if not req.save_as_draft and req.accepted_pricing != pricing:
        raise HTTPException(409, 'Accept the current budget breakdown before submitting.')
    service.apply_content(c, req)
    c.pricing_snapshot = pricing
    service.review_state(db, c, 'Draft' if req.save_as_draft else 'Pending', 'Saved by candidate; company approval required.')
    service.record(db, c, user, 'draft' if req.save_as_draft else 'submitted', before=before)
    db.commit()
    return detail(db, c)


@router.get('/api/admin/review-campaigns')
def review_queue(state: str = 'Pending', page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
                 search: str = Query('', max_length=100), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = db.query(Campaign).options(joinedload(Campaign.owner), defer(Campaign.photo_url), defer(Campaign.slogan)).filter(Campaign.company_review_status != 'Draft')
    if state != 'All':
        query = query.filter(Campaign.company_review_status == state)
    if search.strip():
        term = '%'+search.strip().replace('%', '\\%').replace('_', '\\_')+'%'
        query = query.join(User, Campaign.owner_id == User.id).filter(or_(Campaign.title.ilike(term, escape='\\'), User.full_name.ilike(term, escape='\\'), Campaign.id.ilike(term, escape='\\')))
    total = query.count()
    rows = query.order_by(Campaign.updated_at.desc(), Campaign.id).offset((page-1)*page_size).limit(page_size).all()
    return dict(items=[dict(id=c.id, version=c.version, candidate_name=c.owner.full_name, title=c.title,
        company_review_status=c.company_review_status, publishing_job_status=c.publishing_job_status,
        delivery_status=c.delivery_status, budget_daily=c.budget_paise/100, updated_at=c.updated_at.isoformat()) for c in rows],
        total=total, page=page, page_size=page_size, has_more=page*page_size<total)


@router.get('/api/campaigns/{campaign_id}/history')
def campaign_history(campaign_id: str, before_version: int | None = Query(None, ge=1),
                     page_size: int = Query(10, ge=1, le=50), user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    c = owned(db, campaign_id, user)
    items = service.history(db, c, limit=page_size, before_version=before_version)
    return dict(items=items, next_before_version=items[-1]['version'] if len(items)==page_size else None)


@router.post('/api/admin/review-campaigns/{campaign_id}')
def decide(campaign_id: str, req: ReviewDecisionRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = owned(db, campaign_id, admin)
    if req.action == 'approve' and c.owner.status != 'active':
        raise HTTPException(409, 'An active candidate account is required before approval.')
    if c.company_review_status not in ('Pending', 'Changes Requested'):
        raise HTTPException(409, 'Only submitted ads awaiting a decision can be reviewed.')
    if req.action in ('changes', 'reject') and not req.note.strip():
        raise HTTPException(422, 'A reason is required.')
    before = service.snapshot(c)
    service.cancel_unsubmitted(db, c)
    service.lock_version(db, c, req.expected_version)
    if req.content:
        if req.content.duration_days > c.duration_days:
            raise HTTPException(409, 'Longer campaign duration requires candidate resubmission and consent.')
        if service.paise(req.content.budget_daily) > before['budget_daily']*100:
            raise HTTPException(409, 'A higher customer budget requires candidate resubmission and consent.')
        service.apply_content(c, req.content)
    old_pricing = c.pricing_snapshot
    if not old_pricing:
        # Legacy campaigns require candidate pricing consent before first approval.
        c.pricing_snapshot = service.quote(db, c.budget_paise, meta_override=req.meta_daily_paise)
    elif req.meta_daily_paise is not None or old_pricing['customer_daily_paise'] != c.budget_paise:
        c.pricing_snapshot = service.quote(db, c.budget_paise, meta_override=req.meta_daily_paise)
    pricing_changed = old_pricing != c.pricing_snapshot
    if req.action == 'approve' and pricing_changed:
        raise HTTPException(409, 'Save changed pricing and request candidate consent before approval.')
    # Save with altered pricing automatically requests explicit candidate acceptance.
    state = 'Changes Requested' if pricing_changed and req.action != 'reject' else {'save': 'Pending', 'changes': 'Changes Requested', 'reject': 'Rejected', 'approve': 'Approved'}[req.action]
    if req.action == 'save' and c.company_review_status == 'Changes Requested':
        state = 'Changes Requested'
    if req.action == 'approve' and c.company_review_status != 'Pending':
        raise HTTPException(409, 'Candidate resubmission is required before approval.')
    service.review_state(db, c, state, req.note, admin)
    job = None
    if state == 'Approved':
        from services.subscriptions import enforce_limit
        enforce_limit(db, c.owner, c.budget_paise, c.id, aggregate=True)
        c.approved_version = c.version
        service.reserve(db, c)
        job = create_publishing_job(db, c.id, commit=False)
    service.record(db, c, admin, req.action, req.note, before)
    db.add(Notification(user_id=c.owner_id, type='campaign_update', title='Ad review updated',
        message=f'{c.title}: {state}. {req.note}'[:2000]))
    db.commit()
    return {**detail(db, c), 'job_id': job.id if job else None}


@router.get('/api/campaigns/{campaign_id}/history/{version}/media')
def revision_media(campaign_id: str, version: int, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    c = owned(db, campaign_id, user)
    row = db.query(CampaignRevision).filter_by(campaign_id=c.id, version=version).first()
    if not row:
        raise HTTPException(404, 'Revision not found.')
    return dict(photo_url=row.media_url or row.snapshot.get('photo_url'))


@router.post('/api/admin/review-campaigns/{campaign_id}/release')
def release_campaign(campaign_id: str, req: ReviewDecisionRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = owned(db, campaign_id, admin)
    if c.company_review_status != 'Approved' or not req.note.strip():
        raise HTTPException(409, 'An approved campaign and a release reason are required.')
    before = service.snapshot(c)
    service.cancel_unsubmitted(db, c)
    service.lock_version(db, c, req.expected_version)
    service.review_state(db, c, 'Changes Requested', req.note, admin)
    service.record(db, c, admin, 'funds_released', req.note, before)
    db.add(Notification(user_id=c.owner_id, type='campaign_update', title='Campaign returned for changes', message=req.note))
    db.commit()
    return detail(db, c)


@router.get('/api/admin/pricing-policy')
def get_policy(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.policy(db)


@router.post('/api/admin/pricing-policy')
def save_policy(req: PricingPolicyRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if req.mode == 'percentage' and req.commission_pct >= 100:
        raise HTTPException(422, 'A positive Meta allocation is required; company fee must be below 100%.')
    value = {**req.model_dump(), 'policy_version': uuid.uuid4().hex}
    row = db.get(PlatformSetting, 'campaign_pricing_policy')
    if row:
        row.value = json.dumps(value)
    else:
        db.add(PlatformSetting(key='campaign_pricing_policy', value=json.dumps(value)))
    db.add(AuditEvent(actor_id=admin.id, action='PRICING_POLICY_UPDATED', details=value))
    db.commit()
    return value
