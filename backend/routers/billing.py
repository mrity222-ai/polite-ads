import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_db
from dependencies import require_active_user
from entities import User, CandidateProfile, SubscriptionPlan, Payment, PaymentOrder, Campaign

router = APIRouter(tags=["Billing & Plans"])

# ========================================================
# 1. Public Endpoint: Plans Catalog
# ========================================================
@router.get("/api/plans")
def get_public_plans(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Public catalog of all active subscription packages created by Super Admin.
    Synchronized across Landing Page, Candidate Billing, and Super Admin.
    """
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price_paise.asc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price_paise / 100.0,
            "price_paise": p.price_paise,
            "daily_ad_limit": p.daily_ad_cap_paise / 100.0,
            "badge": p.badge,
            "features": p.features or [],
            "is_active": p.is_active
        }
        for p in plans
    ]

# ========================================================
# 2. Candidate Endpoint: Active Subscription & Demo Status
# ========================================================
@router.get("/api/billing/subscription-status")
def get_candidate_subscription_status(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns current active package, demo privileges, validity, and available packages.
    """
    from services.subscriptions import entitlement, catalog_snapshot, utc
    access = entitlement(db, current_user)
    snap = access['snapshot'] or {}
    plans = [catalog_snapshot(p) for p in db.query(SubscriptionPlan).filter_by(is_active=True).order_by(SubscriptionPlan.price_paise)]
    plans_list = [dict(id=p['id'], name=p['name'], price=p['price_paise']/100,
        daily_ad_limit=p['daily_ad_cap_paise']/100, badge=p['badge'], features=p['features'], is_active=True) for p in plans]
    return dict(is_demo=access['is_demo'], status=('Active Demo Package' if access['is_demo'] else 'Active (Subscribed)') if access['status']=='active' else access['status'].replace('_',' ').title(),
        entitlement_status=access['status'], subscription_id=access['subscription_id'],
        plan_id=snap.get('id'), plan_name=snap.get('name', 'No active entitlement'), price=snap.get('price_paise',0)/100,
        daily_ad_limit=snap.get('daily_ad_cap_paise',0)/100, badge=snap.get('badge','Inactive'), features=snap.get('features',[]),
        activated_at=access['starts_at'].isoformat(), expires_at=access['expires_at'].isoformat(),
        days_remaining=max(0,(access['expires_at']-utc()).days), available_plans=plans_list,
        renewal_rule='New verified purchase replaces access immediately for 30 days; unused time is not carried forward.',
        partial_refund_rule='Partial refunds do not change entitlement; a fully processed refund revokes that purchase.')

# ========================================================
# 3. Candidate Endpoint: Detailed Invoices & Tax Receipts
# ========================================================
@router.get("/api/billing/invoices")
def get_candidate_invoices(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns itemized invoices for all captured candidate payments.
    Includes GST tax breakdown, SAC code 998371, and printable details.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    candidate_name = profile.candidate_name if profile else current_user.full_name
    ward_info = f"{profile.gaon_ward}, {profile.area_block} (PIN: {profile.pincode})" if profile else "Ward Constituency"

    invoices = []
    for pay in payments:
        order = db.query(PaymentOrder).filter(PaymentOrder.id == pay.order_id).first()
        
        # Determine human-readable description
        desc = "Campaign Ad Budget Top-up"
        item_type = order.item_type if order else "campaign_budget"
        
        if order and order.item_type == "subscription_plan":
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == order.item_id).first()
            desc = f"Subscription: {plan.name}" if plan else "Election Campaign Subscription"
        elif order and order.item_type == "campaign_budget" and order.item_id:
            camp = db.query(Campaign).filter(Campaign.id == order.item_id).first()
            if camp:
                desc = f"Ad Budget: {camp.title}"

        amount_inr = pay.amount_paise / 100.0
        subtotal_inr = amount_inr
        gst_inr = 0.0
        cgst_inr = round(gst_inr / 2.0, 2)
        sgst_inr = round(gst_inr / 2.0, 2)

        raw_id = pay.id.replace("pay_", "")
        inv_no = f"INV-{pay.created_at.strftime('%Y')}-{raw_id[-6:].upper()}"

        invoices.append({
            "id": pay.id,
            "invoice_number": inv_no,
            "date": pay.created_at.strftime("%d %b %Y, %I:%M %p"),
            "iso_date": pay.created_at.isoformat(),
            "item_type": item_type,
            "description": desc,
            "amount_inr": amount_inr,
            "subtotal_inr": subtotal_inr,
            "gst_inr": gst_inr,
            "cgst_inr": cgst_inr,
            "sgst_inr": sgst_inr,
            "payment_method": (pay.payment_method or "upi").upper(),
            "status": "Paid" if pay.status == "captured" else pay.status.capitalize(),
            "razorpay_payment_id": pay.razorpay_payment_id,
            "candidate_name": candidate_name,
            "candidate_email": current_user.email,
            "candidate_phone": current_user.mobile,
            "ward_info": ward_info,
            "sac_code": None,
            "document_type": "payment_receipt",
            "pricing_snapshot": order.pricing_snapshot if order else None,
            "reserved_paise": pay.campaign_reserved_paise,
            "refund_reserved_paise": pay.refund_reserved_paise,
            "company_name": "Maeaco Technologies Private Limited",
            "platform_url": "politiads.maeaco.com"
        })

    return invoices
