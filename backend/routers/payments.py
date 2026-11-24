import httpx
import sys
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_db
from dependencies import require_active_user
from entities import User, PaymentOrder, Payment, SubscriptionPlan, Campaign
from integrations.payments.razorpay_client import RazorpayClient
from services.reconciliation import process_verified_payment
from services.subscriptions import catalog_snapshot
from redacting_logger import get_redacted_logger

logger = get_redacted_logger("payments_router")
router = APIRouter(prefix="/api/payments", tags=["Payments"])

class CreateOrderRequest(BaseModel):
    item_type: str = Field(..., pattern="^(subscription_plan|campaign_budget)$")
    item_id: str
    custom_budget_paise: int | None = Field(default=None, strict=True)

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    payment_method: str = "upi"

@router.post("/create-order")
def create_payment_order(
    req: CreateOrderRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Creates a payment order on Razorpay and records in payment_orders table.
    Enforces server-side amount calculation in integer paise.
    """
    amount_paise = 0

    if req.item_type == "subscription_plan":
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == req.item_id).first()
        if not plan or not plan.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {req.item_id} not found.")
        amount_paise = plan.price_paise
    elif req.item_type == "campaign_budget":
        campaign = db.query(Campaign).filter_by(id=req.item_id, owner_id=current_user.id).first()
        if not campaign:
            raise HTTPException(404, "Campaign not found.")
        from services.subscriptions import enforce_limit
        enforce_limit(db, current_user, campaign.budget_paise, campaign.id)
        if campaign.company_review_status in ('Draft', 'Rejected', 'Changes Requested') or not campaign.pricing_snapshot:
            raise HTTPException(409, 'Submit the ad and accept its pricing before paying.')
        if not req.custom_budget_paise or req.custom_budget_paise < 20000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Minimum budget deposit is ₹200 (20,000 paise).")
        amount_paise = req.custom_budget_paise
        if amount_paise % campaign.budget_paise or amount_paise > campaign.budget_paise * 365:
            raise HTTPException(422, 'Campaign funding must cover 1–365 whole customer daily budgets.')

    client = RazorpayClient()
    try:
        gateway_order = client.create_order(
            amount_paise=amount_paise,
            currency="INR",
            notes={"user_id": current_user.id, "item_type": req.item_type, "item_id": req.item_id}
        )
    except (RuntimeError, httpx.HTTPError):
        raise HTTPException(502, 'Provider order creation was not confirmed. No local payment was credited.') from None

    if gateway_order.get('amount') != amount_paise or gateway_order.get('currency') != 'INR':
        raise HTTPException(502, 'Provider order response did not match requested amount/currency.')
    db_order = PaymentOrder(
        user_id=current_user.id,
        item_type=req.item_type,
        item_id=req.item_id,
        amount_paise=amount_paise,
        campaign_version=campaign.version if req.item_type == 'campaign_budget' else None,
        pricing_snapshot=campaign.pricing_snapshot if req.item_type == 'campaign_budget' else None,
        plan_snapshot=catalog_snapshot(plan) if req.item_type == 'subscription_plan' else None,
        currency="INR",
        status="created",
        razorpay_order_id=gateway_order["id"]
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return {
        "order_id": db_order.id,
        "razorpay_order_id": gateway_order["id"],
        "amount_paise": amount_paise,
        "amount_inr": amount_paise / 100.0,
        "currency": "INR",
        "mock": gateway_order.get("mock", False),
        "pricing_snapshot": db_order.pricing_snapshot,
        "key_id": gateway_order["key_id"],
        "user_name": current_user.full_name,
        "user_email": current_user.email,
        "user_mobile": current_user.mobile
    }

@router.post("/verify")
def verify_payment_and_capture(
    req: VerifyPaymentRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verifies Razorpay checkout signature and captures payment into immutable ledger.
    """
    db_order = db.query(PaymentOrder).filter(
        PaymentOrder.razorpay_order_id == req.razorpay_order_id,
        PaymentOrder.user_id == current_user.id
    ).first()

    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching order record not found.")

    client = RazorpayClient()
    is_valid = client.verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature
    )

    if not is_valid:
        logger.warning(f"Signature verification failed for order {req.razorpay_order_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cryptographic payment signature mismatch.")

    try:
        entity = client.fetch_payment(req.razorpay_payment_id)
        if entity.get('order_id') != req.razorpay_order_id or entity.get('status') != 'captured':
            raise ValueError('Provider has not confirmed capture for this order.')
        payment = process_verified_payment(
        db=db,
        order=db_order,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
        payment_method=entity.get('method', 'unknown'),
        amount_paise=entity.get('amount'), currency=entity.get('currency')
        )
        db.commit()
    except httpx.HTTPError:
        db.rollback()
        raise HTTPException(502, 'Provider capture verification failed; no local credit was recorded.') from None
    except (ValueError, RuntimeError) as error:
        db.rollback()
        raise HTTPException(409, str(error)) from None

    return {
        "status": "success",
        "payment_id": payment.id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "amount_inr": payment.amount_paise / 100.0,
        "order_status": db_order.status
    }

@router.get("/history")
def get_user_payment_history(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns user payment transactions.
    """
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "amount_inr": p.amount_paise / 100.0,
            "status": p.status,
            "method": p.payment_method,
            "created_at": p.created_at.isoformat()
        }
        for p in payments
    ]
