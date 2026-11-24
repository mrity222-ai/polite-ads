import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from media import validated_image
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from database import get_db
from entities import User, CandidateProfile
from models import CandidateProfileResponse, CandidateProfileUpdate
from dependencies import require_active_user

router = APIRouter(prefix="/api/profile", tags=["Candidate Profile & Onboarding"])

def _format_profile_response(profile: CandidateProfile) -> CandidateProfileResponse:
    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        candidate_name=profile.candidate_name,
        contesting_post=profile.contesting_post,
        gaon_ward=profile.gaon_ward,
        area_block=profile.area_block,
        pincode=profile.pincode,
        lat=profile.lat,
        lng=profile.lng,
        accuracy_m=profile.accuracy_m,
        symbol_name=profile.symbol_name,
        custom_symbol_url=profile.custom_symbol_url,
        default_slogan=profile.default_slogan,
        disclaimer_text=profile.disclaimer_text,
        photo_url=profile.photo_url,
        is_meta_connected=profile.is_meta_connected,
        onboarding_completed=profile.onboarding_completed
    )

@router.get("", response_model=CandidateProfileResponse)
def get_candidate_profile(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        # Create a default profile if missing
        profile = CandidateProfile(
            user_id=current_user.id,
            candidate_name=current_user.full_name,
            contesting_post="Ward Councillor / Corporator",
            gaon_ward="Ward 12",
            area_block="Central Block",
            pincode="281306",
            lat="27.4482",
            lng="78.0416",
            accuracy_m=25,
            symbol_name="Car",
            default_slogan="काम किया है, काम करेंगे!",
            disclaimer_text=f"Paid for by {current_user.full_name} Campaign",
            is_meta_connected=False,
            onboarding_completed=False
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return _format_profile_response(profile)

@router.put("", response_model=CandidateProfileResponse)
def update_candidate_profile(
    data: CandidateProfileUpdate,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id, candidate_name=data.candidate_name)
        db.add(profile)

    profile.candidate_name = data.candidate_name
    profile.contesting_post = data.contesting_post
    profile.gaon_ward = data.gaon_ward
    profile.area_block = data.area_block
    profile.pincode = data.pincode
    if data.lat is not None:
        profile.lat = data.lat
    if data.lng is not None:
        profile.lng = data.lng
    if data.accuracy_m is not None:
        profile.accuracy_m = data.accuracy_m
    profile.symbol_name = data.symbol_name
    if data.custom_symbol_url is not None:
        profile.custom_symbol_url = data.custom_symbol_url
    if data.default_slogan is not None:
        profile.default_slogan = data.default_slogan
    if data.disclaimer_text is not None:
        profile.disclaimer_text = data.disclaimer_text
    if data.photo_url is not None:
        profile.photo_url = data.photo_url

    if data.onboarding_completed is not None:
        profile.onboarding_completed = data.onboarding_completed
    db.commit()
    db.refresh(profile)
    return _format_profile_response(profile)

@router.post("/upload-photo")
async def upload_candidate_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    contents = await file.read(5 * 1024 * 1024 + 1)
    data_url = validated_image(contents, file.content_type)

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if profile:
        profile.photo_url = data_url
        db.commit()

    return {"status": "success", "photo_url": data_url}

@router.post("/upload-symbol")
async def upload_custom_symbol(
    file: UploadFile = File(...),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
):
    contents = await file.read(5 * 1024 * 1024 + 1)
    data_url = validated_image(contents, file.content_type)

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if profile:
        profile.custom_symbol_url = data_url
        profile.symbol_name = "Custom Symbol"
        db.commit()

    return {"status": "success", "symbol_url": data_url}
