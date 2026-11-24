"""Verified, retryable webhook receipt. No acknowledgement of unprocessed failures."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from entities import WebhookEvent, PaymentOrder, Refund
from integrations.payments.webhook_verifier import verify_razorpay_webhook_signature
from services.reconciliation import process_verified_payment, finalize_refund

router = APIRouter(prefix='/api/webhooks', tags=['Webhooks'])

@router.post('/razorpay')
async def handle_razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    signature = request.headers.get('X-Razorpay-Signature', '')
    valid, _ = verify_razorpay_webhook_signature(raw, signature)
    if not valid:
        raise HTTPException(400, 'Webhook signature verification failed.')
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError()
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(400, 'Malformed JSON object.')
    event_id = request.headers.get('X-Razorpay-Event-Id')
    if not event_id or len(event_id) > 100:
        raise HTTPException(400, 'Missing or invalid X-Razorpay-Event-Id header.')
    event_type = payload.get('event', 'unknown')
    record = db.query(WebhookEvent).filter_by(event_id=event_id).first()
    if not record:
        record = WebhookEvent(event_id=event_id, event_type=event_type, signature_verified=True, payload=payload)
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            record = db.query(WebhookEvent).filter_by(event_id=event_id).one()
    if record.payload != payload:
        raise HTTPException(409, 'Event ID reused with different content.')
    return process_stored_event(db, record, signature)


def process_stored_event(db, record, signature='verified stored webhook'):
    if not record.signature_verified:
        raise HTTPException(400, 'Stored event is not verified.')
    payload, event_id, event_type = record.payload, record.event_id, record.event_type
    try:
        # Lock/CAS event within the same transaction as financial writes.
        claimed = db.execute(update(WebhookEvent).where(WebhookEvent.id == record.id,
            WebhookEvent.is_processed == False).values(is_processed=True)).rowcount
        if not claimed:
            db.rollback()
            return {'status': 'ok', 'duplicate': True}
        if event_type == 'payment.captured':
            entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            if entity.get('status') != 'captured' or not entity.get('id'):
                raise ValueError('Captured payment entity required.')
            order = db.query(PaymentOrder).filter_by(razorpay_order_id=entity.get('order_id')).first()
            if not order:
                raise ValueError('Order not found; event retained for retry.')
            process_verified_payment(db, order, entity['id'], signature, entity.get('method', 'unknown'),
                                     amount_paise=entity.get('amount'), currency=entity.get('currency'))
        elif event_type in ('refund.processed', 'refund.failed', 'refund.created'):
            entity = payload.get('payload', {}).get('refund', {}).get('entity', {})
            refund = db.query(Refund).filter_by(razorpay_refund_id=entity.get('id')).first() if entity.get('id') else None
            if not refund:
                op = entity.get('receipt') or entity.get('notes', {}).get('operation_id')
                refund = db.query(Refund).filter_by(operation_id=op).first() if op else None
            if not refund or entity.get('amount') != refund.amount_paise or entity.get('currency') != 'INR' or entity.get('payment_id') != refund.payment.razorpay_payment_id:
                raise ValueError('Refund does not match reserved operation.')
            refund.razorpay_refund_id = entity['id']
            finalize_refund(db, refund, entity.get('status'))
        record.error_message = None
        db.commit()
        return {'status': 'ok', 'event_id': event_id}
    except Exception as error:
        db.rollback()
        record = db.query(WebhookEvent).filter_by(event_id=event_id).one()
        record.error_message = str(error)[:300]
        db.commit()
        raise HTTPException(409, 'Event retained but not processed. Correct the underlying issue and retry the same event.') from None
