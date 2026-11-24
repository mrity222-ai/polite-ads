"""Atomic captures and bounded refunds. Callers own capture transaction commits."""
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from entities import PaymentOrder, Payment, LedgerEntry, Refund, JournalLine, Notification
from integrations.payments.razorpay_client import RazorpayClient


def journal(db, user_id, reference, amount, refund=False):
    # Deposit is a liability, not earned revenue or actual Meta spend.
    debit, credit = ('candidate_credit', 'provider_receivable') if refund else ('provider_receivable', 'candidate_credit')
    db.add_all([
        JournalLine(transaction_id=reference, user_id=user_id, account=debit, debit_paise=amount, credit_paise=0),
        JournalLine(transaction_id=reference, user_id=user_id, account=credit, debit_paise=0, credit_paise=amount),
    ])


def process_verified_payment(db, order, razorpay_payment_id, razorpay_signature='', payment_method='upi', *, amount_paise, currency):
    if type(amount_paise) is not int or amount_paise != order.amount_paise or currency != order.currency:
        raise ValueError('Payment amount or currency does not match the server order.')
    existing = db.query(Payment).filter_by(razorpay_payment_id=razorpay_payment_id).first()
    if existing:
        if existing.order_id != order.id:
            raise ValueError('Payment already belongs to another order.')
        return existing
    claimed = db.execute(update(PaymentOrder).where(PaymentOrder.id == order.id, PaymentOrder.status == 'created').values(status='paid')).rowcount
    if not claimed:
        raise ValueError('Order is already paid or unavailable; no additional credit allowed.')
    payment = Payment(order_id=order.id, user_id=order.user_id, amount_paise=amount_paise, currency=currency,
                      razorpay_payment_id=razorpay_payment_id, razorpay_signature=razorpay_signature,
                      status='captured', payment_method=payment_method)
    db.add(payment)
    db.flush()
    db.add(LedgerEntry(user_id=order.user_id, tx_type='DEPOSIT', amount_paise=amount_paise,
                       platform_cut_paise=0, meta_spend_paise=0, reference_id=payment.id,
                       notes='Customer credit; not platform revenue or confirmed ad spend.'))
    journal(db, order.user_id, payment.id, amount_paise)
    db.add(Notification(user_id=order.user_id, type='payment_success', title='Payment Confirmed',
                        message='Your payment has been captured. Advertising delivery is a separate operation.'))
    db.flush()
    from services.subscriptions import activate
    activate(db, payment, order)
    return payment


def finalize_refund(db, refund, provider_status):
    if provider_status not in ('processed', 'failed') or refund.status in ('processed', 'failed'):
        return
    # Compare-and-set prevents concurrent/replayed completion from adding journal lines twice.
    changed = db.execute(update(Refund).where(Refund.id == refund.id, Refund.status == 'pending').values(status=provider_status)).rowcount
    if not changed:
        return
    if provider_status == 'processed':
        journal(db, refund.user_id, refund.id, refund.amount_paise, refund=True)
        db.add(LedgerEntry(user_id=refund.user_id, tx_type='REFUND', amount_paise=-refund.amount_paise,
                           platform_cut_paise=0, meta_spend_paise=0, reference_id=refund.id, notes='Confirmed refund of customer credit.'))
        from services.subscriptions import revoke_fully_refunded
        revoke_fully_refunded(db, db.get(Payment, refund.payment_id))
    else:
        db.execute(update(Payment).where(Payment.id == refund.payment_id).values(refund_reserved_paise=Payment.refund_reserved_paise-refund.amount_paise))
    db.flush()


def process_refund_request(db, payment_id, amount_paise, reason='Refund', operation_id=None):
    if not operation_id or type(amount_paise) is not int or amount_paise <= 0:
        raise ValueError('A unique operation_id and positive integer refund amount are required.')
    existing = db.query(Refund).filter_by(operation_id=operation_id).first()
    if existing:
        if existing.payment_id != payment_id or existing.amount_paise != amount_paise:
            raise ValueError('Operation ID was already used for a different refund.')
        return existing
    # Conditional UPDATE serializes reservations on both SQLite and PostgreSQL.
    changed = db.execute(update(Payment).where(Payment.id == payment_id, Payment.status == 'captured',
        Payment.refund_reserved_paise + Payment.campaign_reserved_paise + Payment.campaign_consumed_paise + amount_paise <= Payment.amount_paise).values(
        refund_reserved_paise=Payment.refund_reserved_paise+amount_paise)).rowcount
    if not changed:
        db.rollback()
        existing = db.query(Refund).filter_by(operation_id=operation_id, payment_id=payment_id, amount_paise=amount_paise).first()
        if existing:
            return existing
        raise ValueError('Payment missing or refund exceeds remaining refundable balance.')
    payment = db.get(Payment, payment_id)
    refund = Refund(payment_id=payment.id, user_id=payment.user_id, amount_paise=amount_paise,
                    operation_id=operation_id, status='pending', reason=reason)
    db.add(refund)
    try:
        db.commit()  # Reserve before external call. Ambiguous failures stay pending, never blind-retry.
    except IntegrityError:
        db.rollback()
        existing = db.query(Refund).filter_by(operation_id=operation_id).first()
        if existing and existing.payment_id == payment_id and existing.amount_paise == amount_paise:
            return existing
        raise ValueError('Refund operation conflicts with an existing request.') from None
    try:
        response = RazorpayClient().process_refund(payment.razorpay_payment_id, amount_paise, reason, operation_id)
        if response.get('payment_id') != payment.razorpay_payment_id or response.get('amount') != amount_paise:
            raise ValueError('Provider refund response does not match reservation.')
        refund.razorpay_refund_id = response['id']
        finalize_refund(db, refund, response.get('status'))
        db.commit()
    except Exception:
        db.rollback()
        # Reservation deliberately retained. Admin must reconcile with provider before retry/release.
        raise RuntimeError(f'Refund {refund.id} is pending reconciliation; do not create a new request.') from None
    db.refresh(refund)
    return refund
