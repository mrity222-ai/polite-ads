import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import update

from database import get_db
from entities import (
    User, CandidateProfile, Campaign, Review, SubscriptionPlan,
    PlatformSetting, AuditEvent, PublishingJob, WebhookEvent, Payment, Refund
)
from models import (
    AdminEnhanceAndPushRequest,
    CandidateStatusUpdateRequest,
    CommissionUpdateRequest,
    SubscriptionPlanCreate,
    ApiHealthResponse
)
from dependencies import require_admin
from security import revoke_all_user_sessions
from services.publishing import create_publishing_job, execute_publishing_job
from services.reconciliation import process_refund_request

router = APIRouter(prefix="/api/admin", tags=["Super Admin Boss Suite"])

class ProcessRefundRequest(BaseModel):
    payment_id: str
    amount_inr: Decimal = Field(gt=0, decimal_places=2)
    operation_id: str = Field(min_length=8, max_length=100)
    reason: str = "Admin approved campaign refund"

class KillSwitchRequest(BaseModel):
    enabled: bool

# 1. Ad Review & Quick-Fix Studio
@router.get("/pending-reviews")
def get_pending_review_ads(
    limit: int = Query(25, ge=1, le=50),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    pending_reviews = db.query(Review).filter(
        Review.status.like("%Pending%")
    ).order_by(Review.created_at.desc()).limit(limit).all()

    items = []
    for rev in pending_reviews:
        camp = rev.campaign
        owner = camp.owner if camp else None
        prof = owner.profile if owner else None

        items.append({
            "id": camp.id if camp else rev.campaign_id,
            "review_id": rev.id,
            "candidate_name": prof.candidate_name if prof else (owner.full_name if owner else "Candidate"),
            "post": prof.contesting_post if prof else "Ward Councillor / Corporator",
            "phone": camp.whatsapp_phone or (owner.mobile if owner else ""),
            "area": camp.area or (prof.gaon_ward if prof else "Local Ward"),
            "pincode": camp.pincode or (prof.pincode if prof else ""),
            "budget": round(camp.budget_paise / 100.0, 2) if camp else 500.0,
            "radius": camp.radius_km if camp else 8.0,
            "submitted_date": rev.created_at.strftime("%d %b %Y") if rev.created_at else "Just Now",
            "original_slogan": rev.original_slogan,
            "enhanced_slogan": rev.enhanced_slogan,
            "symbol": camp.symbol or (prof.symbol_name if prof else ""),
            "status": rev.status,
            "correction_note": rev.correction_note or "कंपनी टीम समीक्षा व सुधार करेगी"
        })

    return items

@router.post("/enhance-and-push")
def enhance_and_push_to_meta(request: AdminEnhanceAndPushRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    # Compatibility endpoint uses exactly the same consent, funds and version gate.
    from routers.campaign_reviews import decide
    from models import ReviewDecisionRequest, CampaignCreateRequest
    from services.campaign_review import snapshot
    c = db.get(Campaign, request.ad_id)
    if not c:
        raise HTTPException(404, 'Campaign not found.')
    content = snapshot(c)
    content.update(slogan=request.enhanced_slogan,
                   budget_daily=request.adjusted_budget if request.adjusted_budget is not None else c.budget_paise/100,
                   radius_km=request.adjusted_radius if request.adjusted_radius is not None else c.radius_km)
    result = decide(c.id, ReviewDecisionRequest(expected_version=c.version, action='approve',
                    content=CampaignCreateRequest(**content), note=request.correction_note or ''), admin, db)
    return {**result, 'status': 'success', 'job_status': 'Queued', 'message': 'Company approved; provider confirmation pending.'}

# 2. Candidate Directory & Status Control (Boss Suite)
@router.get("/candidates")
def get_all_candidates(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    candidates = db.query(User).filter(User.role == "candidate").order_by(User.id.asc()).all()
    results = []
    for u in candidates:
        prof = u.profile
        camps = u.campaigns
        total_spend = sum(c.spent_paise for c in camps) / 100.0

        results.append({
            "id": u.id,
            "name": prof.candidate_name if prof else u.full_name,
            "email": u.email,
            "phone": u.mobile,
            "ward": prof.gaon_ward if prof else "Ward 12",
            "pincode": prof.pincode if prof else "",
            "post": prof.contesting_post if prof else "Candidate",
            "symbol": prof.symbol_name if prof else "",
            "lat": prof.lat if prof else "27.4482",
            "lng": prof.lng if prof else "78.0416",
            "plan": "Standard",
            "status": u.status.capitalize(),
            "totalSpend": total_spend,
            "totalAds": len(camps)
        })
    return results

@router.patch("/candidates/{candidate_id}/status")
def update_candidate_status(
    candidate_id: str,
    payload: CandidateStatusUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{candidate_id}' not found."
        )

    old_status = user.status
    new_status = payload.status.lower()

    if new_status not in ("active", "suspended", "pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be Active, Suspended, or Pending."
        )

    user.status = new_status

    revoked_count = 0
    if new_status == "suspended":
        revoked_count = revoke_all_user_sessions(db, user.id)

    audit = AuditEvent(
        actor_id=admin.id,
        target_user_id=user.id,
        action="UPDATE_USER_STATUS",
        details={"old_status": old_status, "new_status": new_status}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "candidate_id": user.id,
        "name": user.full_name,
        "account_status": user.status.capitalize(),
        "new_status": user.status.capitalize(),
        "revoked_sessions": revoked_count,
        "sessions_revoked": new_status == "suspended"
    }

# 3. Profit Engine & Platform Margin
@router.get('/commission')
def get_commission_policy(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from services.campaign_review import policy
    return {**policy(db), 'currency': 'INR'}

@router.post('/commission')
def update_commission_policy(payload: CommissionUpdateRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from routers.campaign_reviews import save_policy
    from models import PricingPolicyRequest
    return save_policy(PricingPolicyRequest(mode='percentage', commission_pct=payload.commission_pct), admin, db)

# 4. Subscription Management
@router.get("/subscriptions")
def get_subscription_plans(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price_paise / 100.0,
            "daily_ad_limit": p.daily_ad_cap_paise / 100.0,
            "badge": p.badge,
            "features": p.features,
            "users_count": 0
        }
        for p in plans
    ]

@router.post("/subscriptions")
def create_subscription_plan(
    payload: SubscriptionPlanCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    price_paise = int(round(payload.price * 100))
    daily_cap_paise = int(round(payload.daily_ad_limit * 100))

    new_plan = SubscriptionPlan(
        id=plan_id,
        name=payload.name,
        price_paise=price_paise,
        daily_ad_cap_paise=daily_cap_paise,
        badge=payload.badge or "Custom",
        features=payload.features,
        is_active=True
    )
    db.add(new_plan)

    audit = AuditEvent(
        actor_id=admin.id,
        action="CREATE_SUBSCRIPTION_PLAN",
        details={"plan_id": plan_id, "name": payload.name}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "plan": {
            "id": plan_id,
            "name": payload.name,
            "price": payload.price,
            "daily_ad_limit": payload.daily_ad_limit,
            "badge": payload.badge or "Custom",
            "features": payload.features,
            "is_active": True,
            "users_count": 0
        }
    }

@router.patch("/subscriptions/{plan_id}/toggle")
def toggle_subscription_plan(
    plan_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")
    
    plan.is_active = not plan.is_active
    audit = AuditEvent(
        actor_id=admin.id,
        action="TOGGLE_SUBSCRIPTION_PLAN",
        details={"plan_id": plan_id, "is_active": plan.is_active}
    )
    db.add(audit)
    db.commit()
    return {"status": "success", "plan_id": plan_id, "is_active": plan.is_active}

@router.delete("/subscriptions/{plan_id}")
def delete_subscription_plan(
    plan_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")
    
    # Soft-delete by marking inactive
    plan.is_active = False
    audit = AuditEvent(
        actor_id=admin.id,
        action="DELETE_SUBSCRIPTION_PLAN",
        details={"plan_id": plan_id}
    )
    db.add(audit)
    db.commit()
    return {"status": "success", "plan_id": plan_id, "message": "Plan deactivated/deleted."}

# 5. API Gateway & Live Health Checks
@router.get("/api-health", response_model=ApiHealthResponse)
def get_api_health(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    kill = db.query(PlatformSetting).filter(PlatformSetting.key == "meta_kill_switch").first()
    is_killed = kill and kill.value.lower() == "true"

    return ApiHealthResponse(
        meta_status="Disabled by kill-switch" if is_killed else ("Mock simulation" if __import__("config").META_MOCK_MODE else "Live publishing unavailable"),
        meta_token_valid=False,
        whatsapp_status="Policy Excluded (Compliant)",
        ai_status="Not integrated",
        token_expires_days=0
    )

@router.post('/api-health/test-meta')
def test_meta_connection(admin: User = Depends(require_admin)):
    return {'status': 'mock' if __import__('config').META_MOCK_MODE else 'unavailable',
            'message': 'This check does not establish a real provider connection.', 'ping_latency_ms': None,
            'meta_graph_version': __import__('config').META_GRAPH_VERSION}

# 6. Payment & Invoices Ledger
@router.get('/finance-summary')
def finance_summary(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func
    from entities import CampaignFundingDay
    days=db.query(CampaignFundingDay).filter_by(status='settled')
    count=days.count()
    return dict(captured_paise=db.query(func.coalesce(func.sum(Payment.amount_paise),0)).filter(Payment.status.in_(['captured','refunded'])).scalar(),
        reserved_paise=db.query(func.coalesce(func.sum(Payment.campaign_reserved_paise),0)).scalar(),
        consumed_paise=db.query(func.coalesce(func.sum(Payment.campaign_consumed_paise),0)).scalar(),
        actual_meta_spend_paise=days.with_entities(func.coalesce(func.sum(CampaignFundingDay.actual_spend_paise),0)).scalar() if count else None,
        earned_company_fee_paise=days.with_entities(func.coalesce(func.sum(CampaignFundingDay.earned_fee_paise),0)).scalar() if count else None,
        settled_days=count)


@router.get("/transactions")
def get_payment_transactions(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
    return [{'id': p.id, 'candidate_name': db.get(User, p.user_id).full_name,
             'reserved_paise': p.campaign_reserved_paise,
             'refund_reserved_paise': p.refund_reserved_paise,
             'refundable_paise': p.amount_paise-p.refund_reserved_paise-p.campaign_reserved_paise-p.campaign_consumed_paise,
             'consumed_paise': p.campaign_consumed_paise,
             'gateway_mock': __import__('config').RAZORPAY_MOCK_MODE,
             'amount': p.amount_paise / 100, 'company_cut': 0, 'meta_payout': 0,
             'status': p.status, 'method': p.payment_method, 'mode': p.payment_method,
             'date': p.created_at.isoformat()} for p in payments]

# 7. Publishing Jobs Inspection & Retry
@router.get("/publishing-jobs")
def get_publishing_jobs(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    jobs = db.query(PublishingJob).order_by(PublishingJob.created_at.desc()).limit(50).all()
    return [
        {
            "id": j.id,
            "campaign_id": j.campaign_id,
            "stage": j.stage,
            "status": j.status,
            "meta_campaign_id": j.meta_campaign_id,
            "meta_ad_id": j.meta_ad_id,
            "error_details": j.error_details,
            "retry_count": j.retry_count,
            "created_at": j.created_at.isoformat()
        }
        for j in jobs
    ]

@router.post("/publishing-jobs/{job_id}/retry")
def retry_publishing_job(
    job_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    job = db.get(PublishingJob, job_id)
    if not job or job.status != 'Failed':
        raise HTTPException(409, 'Only failed jobs can be requeued.')
    from services.publishing import MAX_ATTEMPTS
    if job.attempt_count >= MAX_ATTEMPTS:
        raise HTTPException(409, 'Attempt limit reached. Review provider evidence and create a fresh approved version.')
    campaign = db.get(Campaign, job.campaign_id)
    if not campaign or campaign.company_review_status != 'Approved' or campaign.approved_version != job.campaign_version or campaign.version != job.campaign_version:
        raise HTTPException(409, 'This job no longer refers to the currently approved version.')
    job.status = 'Queued'
    job.next_attempt_at = None
    job.error_details = None
    db.commit()
    return {
        "status": "success",
        "job_id": job.id,
        "job_status": job.status,
        "stage": job.stage,
        "error_details": job.error_details
    }

# 8. Webhook Events Inspector
@router.get("/webhooks")
def get_recent_webhooks(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    events = db.query(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(50).all()
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "signature_verified": e.signature_verified,
            "is_processed": e.is_processed,
            "error_message": e.error_message,
            "created_at": e.created_at.isoformat()
        }
        for e in events
    ]

# 9. Emergency Kill-Switch Control
@router.post("/emergency-kill-switch")
def toggle_emergency_kill_switch(
    req: KillSwitchRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    setting = db.query(PlatformSetting).filter(PlatformSetting.key == "meta_kill_switch").first()
    if not setting:
        setting = PlatformSetting(key="meta_kill_switch", value=str(req.enabled).lower())
        db.add(setting)
    else:
        setting.value = str(req.enabled).lower()

    audit = AuditEvent(
        actor_id=admin.id,
        action="TOGGLE_EMERGENCY_KILL_SWITCH",
        details={"enabled": req.enabled}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "kill_switch_active": req.enabled,
        "message": "Emergency Kill-Switch ACTIVATED. Meta publishing paused." if req.enabled else "Kill-Switch DEACTIVATED. Normal operations resumed."
    }

# 10. Process Refund
@router.post("/refunds/process")
def admin_process_refund(
    req: ProcessRefundRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    amount_paise = int(req.amount_inr * 100)
    try:
        refund = process_refund_request(
        db=db,
        payment_id=req.payment_id,
        amount_paise=amount_paise,
        reason=req.reason,
        operation_id=req.operation_id
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(409, str(error)) from None
    except RuntimeError as error:
        raise HTTPException(502, str(error)) from None
    return {
        "status": "success",
        "refund_id": refund.id,
        "razorpay_refund_id": refund.razorpay_refund_id,
        "amount_inr": refund.amount_paise / 100.0,
        "status_label": refund.status
    }


@router.post('/webhooks/{event_id}/retry')
def retry_verified_webhook(event_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from routers.webhooks import process_stored_event
    record = db.query(WebhookEvent).filter_by(event_id=event_id).first()
    if not record:
        raise HTTPException(404, 'Event not found.')
    return process_stored_event(db, record)
