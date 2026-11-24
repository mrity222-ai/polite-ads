"""Provider calls. Mock mode is explicit; cryptographic checks never have bypasses."""
import hashlib
import hmac
import uuid
from urllib.parse import quote
import httpx
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET, RAZORPAY_MOCK_MODE

class RazorpayClient:
    def __init__(self):
        self.key_id = RAZORPAY_KEY_ID
        self.key_secret = RAZORPAY_KEY_SECRET
        self.webhook_secret = RAZORPAY_WEBHOOK_SECRET

    def _request(self, method, path, payload=None):
        if not self.key_id or not self.key_secret or self.key_id == 'rzp_test_politiads_demo':
            raise RuntimeError('Real Razorpay credentials are required; no synthetic live result is available.')
        with httpx.Client(base_url='https://api.razorpay.com/v1', auth=(self.key_id, self.key_secret), timeout=20) as client:
            response = client.request(method, path, json=payload)
            response.raise_for_status()
            return response.json()

    def create_order(self, amount_paise, currency='INR', receipt=None, notes=None):
        if type(amount_paise) is not int or amount_paise <= 0:
            raise ValueError('Amount must be positive integer paise.')
        data = dict(amount=amount_paise, currency=currency, receipt=receipt or f'rcpt_{uuid.uuid4().hex[:16]}', notes=notes or {})
        if RAZORPAY_MOCK_MODE:
            result = dict(data, id=f'order_mock_{uuid.uuid4().hex[:14]}', status='created')
        else:
            result = self._request('POST', '/orders', data)
        result['key_id'] = self.key_id
        result['mock'] = RAZORPAY_MOCK_MODE
        return result

    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        expected = hmac.new(self.key_secret.encode(), f'{razorpay_order_id}|{razorpay_payment_id}'.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, razorpay_signature or '')

    def fetch_payment(self, payment_id):
        if RAZORPAY_MOCK_MODE:
            raise ValueError('Mock checkout cannot confirm capture. Use a correctly signed test webhook with amount/currency/status.')
        return self._request('GET', '/payments/' + quote(payment_id, safe=''))

    def process_refund(self, payment_id, amount_paise, reason='Refund', operation_id=None):
        if type(amount_paise) is not int or amount_paise <= 0:
            raise ValueError('Refund amount must be positive integer paise.')
        if RAZORPAY_MOCK_MODE:
            return dict(id='rfnd_mock_' + hashlib.sha256((operation_id or uuid.uuid4().hex).encode()).hexdigest()[:20], payment_id=payment_id, amount=amount_paise, currency='INR', status='processed')
        return self._request('POST', '/payments/' + quote(payment_id, safe='') + '/refund', dict(amount=amount_paise, speed='normal', receipt=operation_id, notes={'reason': reason}))
