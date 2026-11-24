import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from entities import User, Campaign, Review, CandidateProfile
from models import CampaignCreateRequest, CampaignResponse
from dependencies import require_active_user
from services import campaign_review as review_service

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns & Political Ads"])

def _format_campaign_response(c: Campaign, owner: User) -> CampaignResponse:
    profile = owner.profile if owner else None
    c_name = profile.candidate_name if profile else (owner.full_name if owner else "Candidate")
    c_post = profile.contesting_post if profile else "Ward Councillor / Corporator"

    return CampaignResponse(
        duration_days=c.duration_days, billing_timezone=c.billing_timezone,
        version=c.version, approved_version=c.approved_version, pricing_snapshot=c.pricing_snapshot,
        company_review_status=c.company_review_status,
        publishing_job_status=c.publishing_job_status,
        provider_review_status=c.provider_review_status,
        delivery_status=c.delivery_status,
        is_mock=__import__('config').META_MOCK_MODE,
        area=c.area, pincode=c.pincode, whatsapp_phone=c.whatsapp_phone, symbol=c.symbol, photo_url=c.photo_url,
        id=c.id,
        user_id=c.owner_id,
        title=c.title,
        candidate_name=c_name,
        post=c_post,
        budget_daily=round(c.budget_paise / 100.0, 2),
        radius_km=c.radius_km,
        reach=c.reach,
        spent=int(round(c.spent_paise / 100.0)),
        clicks=c.clicks,
        status=('Historical Demo (No Delivery)' if __import__('config').META_MOCK_MODE and 'Live' in c.status else c.status),
        badge=("Simulation only; no confirmed delivery" if __import__("config").META_MOCK_MODE else c.badge),
        template_id=c.template_id,
        slogan=c.slogan,
        submitted_date=c.created_at.strftime("%d %b %Y") if c.created_at else "Today",
        meta_ad_id=c.meta_ad_id
    )

@router.get("", response_model=List[CampaignResponse])
def get_candidate_campaigns(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    # Strict Account Data Isolation: User A only sees User A's campaigns
    campaigns = db.query(Campaign).filter(
        Campaign.owner_id == current_user.id
    ).order_by(Campaign.created_at.desc()).all()

    return [_format_campaign_response(c, current_user) for c in campaigns]

@router.post("/create", response_model=CampaignResponse)
def create_campaign(
    request: CampaignCreateRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()

    budget_paise = review_service.paise(request.budget_daily)
    from services.subscriptions import enforce_limit
    enforce_limit(db, current_user, budget_paise)
    pricing = review_service.quote(db, budget_paise)
    if not request.save_as_draft and request.accepted_pricing != pricing:
        raise HTTPException(409, 'Review and accept the current budget breakdown before submission.')

    # 1. Create Pending Campaign
    new_campaign = Campaign(
        area=request.area, pincode=request.pincode, whatsapp_phone=request.whatsapp_phone,
        symbol=request.symbol, photo_url=request.photo_url,
        owner_id=current_user.id,
        title=request.title,
        slogan=request.slogan,
        budget_paise=budget_paise,
        radius_km=request.radius_km,
        reach=0,
        spent_paise=0,
        clicks=0,
        status="Under Company Review ⏳",
        badge="⏳ Experts Reviewing & Enhancing",
        template_id=request.template_id,
        duration_days=request.duration_days, billing_timezone=request.billing_timezone
    )
    db.add(new_campaign)
    db.flush()

    # 2. Create Review Item
    new_review = Review(
        campaign_id=new_campaign.id,
        original_slogan=request.slogan,
        enhanced_slogan=request.slogan,
        status="Pending Admin Review 🟡",
        correction_note="कंपनी टीम समीक्षा व सुधार करेगी"
    )
    db.add(new_review)

    new_campaign.pricing_snapshot = pricing
    review_service.review_state(db, new_campaign, 'Draft' if request.save_as_draft else 'Pending', 'Company approval required before provider submission.')
    review_service.record(db, new_campaign, current_user, 'draft' if request.save_as_draft else 'submitted')

    db.commit()
    db.refresh(new_campaign)

    return _format_campaign_response(new_campaign, current_user)

@router.post("/{campaign_id}/toggle-status")
def toggle_campaign_status(
    campaign_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    # Verify campaign exists and belongs to current user
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.owner_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found."
        )

    # No provider delivery mutations are simulated as successful live operations.
    if campaign.company_review_status != 'Approved' or campaign.provider_review_status != 'Approved':
        raise HTTPException(409, 'Provider-approved delivery is required. Pending/mock submissions cannot be resumed.')
    raise HTTPException(501, 'Provider delivery controls are not activated; no local-only status change was made.')
