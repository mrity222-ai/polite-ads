import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from database import get_db
from entities import User, CandidateProfile
from models import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from security import hash_password, verify_password, create_session, revoke_session
from dependencies import get_current_user, require_active_user, extract_token
from config import COOKIE_SECURE, COOKIE_SAMESITE, SESSION_TTL_HOURS

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(request: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    # Check if user with same email or mobile already exists
    clean_email = request.email.strip().lower()
    clean_mobile = request.mobile.strip()
    existing = db.query(User).filter(
        or_(User.email == clean_email, User.mobile == clean_mobile)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this mobile or email already exists."
        )

    # Hash password with Argon2id
    pwd_hash = hash_password(request.password)

    new_user = User(
        full_name=request.full_name.strip(),
        email=clean_email,
        mobile=clean_mobile,
        password_hash=pwd_hash,
        role="candidate",
        status="active"
    )
    db.add(new_user)
    db.flush()

    # Create linked profile
    new_profile = CandidateProfile(
        user_id=new_user.id,
        candidate_name=new_user.full_name,
        contesting_post="Ward Councillor / Corporator",
        gaon_ward="Ward 12",
        area_block="Central Block",
        pincode="281306",
        lat="27.4482",
        lng="78.0416",
        accuracy_m=25,
        symbol_name="Car",
        default_slogan="काम किया है, काम करेंगे - वार्ड को नंबर 1 बनाएंगे!",
        disclaimer_text=f"Paid for by: {new_user.full_name} Campaign",
        is_meta_connected=False,
        onboarding_completed=False
    )
    db.add(new_profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, 'User with this mobile or email already exists.') from None

    # Create session token and set cookie
    raw_token = create_session(db, new_user.id, ttl_hours=SESSION_TTL_HOURS)
    response.set_cookie(
        key="politiads_session",
        value=raw_token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return TokenResponse(
        access_token=None,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            full_name=new_user.full_name,
            mobile=new_user.mobile,
            email=new_user.email,
            role=new_user.role,
            onboarding_completed=False,
            status=new_user.status
        )
    )

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    login_id = (request.login or request.mobile_or_email or "").strip().lower()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number or email is required."
        )

    user = db.query(User).filter(
        or_(User.email == login_id, User.mobile == login_id, User.username == login_id)
    ).first()

    if not user or (user.role == 'admin' and request.password in ('admin123', 'secret123', 'candidate123')) or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number, email, or password."
        )

    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended by administration. Please contact platform support."
        )

    # Create session token and set cookie
    raw_token = create_session(db, user.id, ttl_hours=SESSION_TTL_HOURS)
    response.set_cookie(
        key="politiads_session",
        value=raw_token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return TokenResponse(
        access_token=None,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            mobile=user.mobile,
            email=user.email,
            role=user.role,
            onboarding_completed=bool(user.profile and user.profile.onboarding_completed),
            status=user.status
        )
    )

@router.post("/super-admin/login", response_model=TokenResponse)
def super_admin_login(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    login_id = (request.login or request.mobile_or_email or "").strip().lower()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email, mobile number, or username is required."
        )

    user = db.query(User).filter(
        or_(User.email == login_id, User.mobile == login_id, User.username == login_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials."
        )

    # STRICT ISOLATION: Reject candidates attempting to log in via Super Admin portal
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This portal is strictly for Super Administrators only. Candidates must log in via the candidate portal."
        )

    if (user.role == 'admin' and request.password in ('admin123', 'secret123', 'candidate123')) or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials."
        )

    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your administrator account has been suspended. Please contact platform operations."
        )

    # Create session token and set cookie
    raw_token = create_session(db, user.id, ttl_hours=SESSION_TTL_HOURS)
    response.set_cookie(
        key="politiads_session",
        value=raw_token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return TokenResponse(
        access_token=None,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            mobile=user.mobile,
            email=user.email,
            role=user.role,
            onboarding_completed=False,
            status=user.status
        )
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(require_active_user)):
    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        mobile=current_user.mobile,
        email=current_user.email,
        role=current_user.role,
        onboarding_completed=bool(current_user.profile and current_user.profile.onboarding_completed),
        status=current_user.status
    )

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = extract_token(request)
    if token:
        revoke_session(db, token)
    response.delete_cookie("politiads_session")
    return {"status": "success", "message": "Logged out successfully"}


@router.get('/csrf')
def get_csrf(request: Request, current_user: User = Depends(require_active_user)):
    from security_guards import csrf_token
    return {'csrf_token': csrf_token(request.state.raw_token)}
