"""
Pydantic Schemas for PolitiAds SaaS Platform
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from media import validate_image_reference
import math
import re

# Auth Schemas
class UserRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    mobile: str = Field(pattern=r"^[6-9][0-9]{9}$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

class UserLoginRequest(BaseModel):
    mobile_or_email: Optional[str] = None
    login: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    mobile: str | None
    email: str | None
    role: str
    status: Optional[str] = 'active'
    onboarding_completed: bool = False 

class TokenResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserResponse

# Candidate Onboarding Schemas
class CandidateProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    onboarding_completed: bool | None = None
    candidate_name: str
    contesting_post: str
    gaon_ward: str
    area_block: str
    pincode: str
    lat: Optional[str] = "27.4482"
    lng: Optional[str] = "78.0416"
    accuracy_m: Optional[int] = 25
    symbol_name: str
    custom_symbol_url: Optional[str] = None
    default_slogan: Optional[str] = None
    disclaimer_text: Optional[str] = None
    photo_url: Optional[str] = None

    @field_validator('photo_url', 'custom_symbol_url')
    @classmethod
    def image_reference(cls, value):
        return validate_image_reference(value)

    @field_validator('candidate_name', 'contesting_post', 'gaon_ward', 'area_block', 'symbol_name')
    @classmethod
    def nonempty(cls, value):
        if not value or len(value) > 150:
            raise ValueError('Required field must contain 1–150 characters.')
        return value

    @field_validator('pincode')
    @classmethod
    def valid_pin(cls, value):
        if not re.fullmatch(r'[1-9][0-9]{5}', value):
            raise ValueError('Valid six-digit pincode required.')
        return value

    @field_validator('lat', 'lng')
    @classmethod
    def valid_coordinate(cls, value, info):
        if value is not None:
            number = float(value)
            limit = 90 if info.field_name == 'lat' else 180
            if not math.isfinite(number) or abs(number) > limit:
                raise ValueError('Coordinate out of range.')
        return value

class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    candidate_name: str
    contesting_post: str
    gaon_ward: str
    area_block: str
    pincode: str
    lat: Optional[str]
    lng: Optional[str]
    accuracy_m: Optional[int]
    symbol_name: str
    custom_symbol_url: Optional[str]
    default_slogan: Optional[str]
    disclaimer_text: Optional[str]
    photo_url: Optional[str]
    is_meta_connected: bool
    onboarding_completed: bool

# Campaign / Ad Schemas with Strict Validation
class CampaignCreateRequest(BaseModel):
    duration_days: int = Field(default=1, ge=1, le=365, strict=True)
    billing_timezone: str = Field(default='Asia/Kolkata', pattern='^Asia/Kolkata$')
    save_as_draft: bool = False
    accepted_pricing: dict | None = None
    @field_validator('photo_url')
    @classmethod
    def validate_photo(cls, value):
        return validate_image_reference(value)

    title: str
    whatsapp_phone: str
    slogan: str
    area: str
    pincode: str
    radius_km: float
    budget_daily: float
    template_id: int
    symbol: str
    photo_url: Optional[str] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 2:
            raise ValueError("Campaign Title must be at least 2 non-whitespace characters.")
        return s

    @field_validator('whatsapp_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = re.sub(r'\D', '', v)
        if clean.startswith('91') and len(clean) == 12:
            clean = clean[2:]
        if len(clean) != 10:
            raise ValueError("WhatsApp phone number must be exactly 10 digits.")
        if clean[0] not in '6789':
            raise ValueError("Invalid Indian mobile number. Must start with 6, 7, 8, or 9.")
        return clean

    @field_validator('slogan')
    @classmethod
    def validate_slogan(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 3:
            raise ValueError("Political slogan must be at least 3 non-whitespace characters.")
        return s

    @field_validator('area')
    @classmethod
    def validate_area(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 2:
            raise ValueError("Target Area / Ward must be at least 2 characters.")
        return s

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r'^\d{6}$', clean):
            raise ValueError("Pincode must be exactly 6 digits.")
        return clean

    @field_validator('budget_daily')
    @classmethod
    def validate_budget(cls, v: float) -> float:
        if not math.isfinite(v) or v < 200.0:
            raise ValueError("Daily ad budget must be at least ₹200.")
        return round(float(v), 2)

    @field_validator('radius_km')
    @classmethod
    def validate_radius(cls, v: float) -> float:
        if not (3.0 <= v <= 40.0):
            raise ValueError("Target radius must be between 3 km and 40 km.")
        return round(float(v), 1)

    @field_validator('template_id')
    @classmethod
    def validate_template(cls, v: int) -> int:
        if v not in [1, 2, 3, 4]:
            raise ValueError("Template ID must be one of available templates (1 to 4).")
        return v

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Election symbol must not be empty.")
        return s

class CampaignResponse(BaseModel):
    duration_days: int = 1
    billing_timezone: str = 'Asia/Kolkata'
    version: int = 1
    approved_version: int | None = None
    pricing_snapshot: dict | None = None
    company_review_status: str = "Pending"
    publishing_job_status: str = "Queued"
    provider_review_status: str = "Pending"
    delivery_status: str = "Paused"
    is_mock: bool = True
    area: str | None = None
    pincode: str | None = None
    whatsapp_phone: str | None = None
    symbol: str | None = None
    photo_url: str | None = None
    id: str
    user_id: str
    title: str
    candidate_name: str
    post: str
    budget_daily: float
    radius_km: float
    reach: int
    spent: int
    clicks: int
    status: str
    badge: str
    template_id: int
    slogan: str
    submitted_date: str
    meta_ad_id: Optional[str] = None

# Admin Ad Review & Enhancement Schemas (REVIEW-01 Fix: added adjusted_budget and adjusted_radius)
class AdminEnhanceAndPushRequest(BaseModel):
    ad_id: str
    enhanced_slogan: str
    adjusted_budget: Optional[float] = None
    adjusted_radius: Optional[float] = None
    enhanced_poster_url: Optional[str] = None
    correction_note: Optional[str] = "कंपनी कॉपीराइटिंग टीम द्वारा Meta पर लाइव किया गया"

    @field_validator('ad_id')
    @classmethod
    def validate_ad_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("ad_id must not be empty.")
        return s

    @field_validator('enhanced_slogan')
    @classmethod
    def validate_enhanced_slogan(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 3:
            raise ValueError("Enhanced slogan must be at least 3 non-whitespace characters.")
        return s

    @field_validator('adjusted_budget')
    @classmethod
    def validate_adjusted_budget(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (not math.isfinite(v) or v < 200.0):
            raise ValueError("Adjusted daily budget must be at least ₹200.")
        return v

    @field_validator('adjusted_radius')
    @classmethod
    def validate_adjusted_radius(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (3.0 <= v <= 40.0):
            raise ValueError("Adjusted radius must be between 3 km and 40 km.")
        return v

class SurveyCreateRequest(BaseModel):
    question: str
    options: List[str]

class ServiceRequest(BaseModel):
    service_type: str  # 'whatsapp_broadcast' | 'video_reels' | 'ground_survey'
    candidate_name: str
    mobile: Optional[str] = None
    note: Optional[str] = None

# --- Super Admin Boss Suite Models ---

class CandidateStatusUpdateRequest(BaseModel):
    status: str  # 'Active' | 'Suspended' | 'Pending'

class CommissionUpdateRequest(BaseModel):
    commission_pct: float = Field(ge=0, le=100, allow_inf_nan=False)


class CampaignEditRequest(CampaignCreateRequest):
    expected_version: int = Field(ge=1)


class ReviewDecisionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    action: str = Field(pattern='^(save|changes|reject|approve)$')
    content: CampaignCreateRequest | None = None
    note: str = Field(default='', max_length=2000)
    meta_daily_paise: int | None = Field(default=None, ge=1, strict=True)


class PricingPolicyRequest(BaseModel):
    mode: str = Field(pattern='^(percentage|fixed_meta)$')
    commission_pct: float = Field(default=20, ge=0, le=100, allow_inf_nan=False)
    meta_daily_paise: int = Field(default=7000, ge=1, strict=True)

class SubscriptionPlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    price: float = Field(gt=0, allow_inf_nan=False)
    daily_ad_limit: float = Field(ge=200, allow_inf_nan=False)
    features: List[str]
    badge: Optional[str] = "Custom"

class ApiHealthResponse(BaseModel):
    meta_status: str
    meta_token_valid: bool
    whatsapp_status: str
    ai_status: str
    token_expires_days: int
