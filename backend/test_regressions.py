"""Regression suite: isolated migrated SQLite, no development DB or external calls.
Run: python -m unittest discover -s backend -p test_regressions.py -v
"""
import os
import sys
import tempfile
import json
import hmac
import hashlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent))
_TEMP = tempfile.TemporaryDirectory(prefix='politiads_regressions_')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_TEMP.name)/'test.db').as_posix()
os.environ['META_MOCK_MODE'] = 'true'
os.environ['RAZORPAY_MOCK_MODE'] = 'true'
os.environ['APP_ENV'] = 'test'
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, func
from fastapi.testclient import TestClient
from PIL import Image
from database import engine, SessionLocal
from entities import Base, User, CandidateProfile, Payment, PaymentOrder, Refund, LedgerEntry, JournalLine, WebhookEvent, Campaign, PublishingJob, Review
from security import hash_password
from config import RAZORPAY_WEBHOOK_SECRET, RAZORPAY_KEY_SECRET
from main import app
from services.reconciliation import process_refund_request
from worker import run_once
from integrations.payments.razorpay_client import RazorpayClient

ROOT = Path(__file__).resolve().parent.parent
class Regressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        command.upgrade(Config(str(ROOT/'alembic.ini')), 'head')
        cls.password_hash = hash_password('password123')

    def setUp(self):
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(delete(table))
        with SessionLocal() as db:
            for name, role, mobile in [('a','candidate','9876543210'),('b','candidate','9876543211'),('admin','admin','9999999999')]:
                user = User(id=name, full_name=name, email=f'{name}@example.com', mobile=mobile, password_hash=self.password_hash, role=role)
                db.add(user)
                db.flush()
                if role == 'candidate':
                    db.add(CandidateProfile(user_id=name, candidate_name=name, gaon_ward='Ward 1', area_block='Block', pincode='281306'))
            db.commit()
        self.client = TestClient(app)
        self.login()

    def tearDown(self):
        self.client.close()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        _TEMP.cleanup()

    def login(self, who='a'):
        response = self.client.post('/api/auth/login', json={'login':f'{who}@example.com','password':'password123'})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def write(self, path, data=None, **kwargs):
        csrf = self.client.get('/api/auth/csrf').json()['csrf_token']
        return self.client.post(path, json=data, headers={'X-CSRF-Token':csrf}, **kwargs)

    def campaign(self):
        response = self.write('/api/campaigns/create', dict(title='Test draft', whatsapp_phone='9876543210', slogan='Test draft content', area='Ward 2', pincode='281306', radius_km=5, budget_daily=500, template_id=1, symbol='Car', accepted_pricing=self.client.get('/api/campaigns/pricing-quote?budget_daily=500').json()))
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['id']

    def fund(self, campaign):
        response=self.write('/api/payments/create-order',dict(item_type='campaign_budget',item_id=campaign,custom_budget_paise=100000))
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(self.webhook(response.json()['razorpay_order_id'],event='fund_'+campaign,payment='pay_'+campaign).status_code,200)

    def order(self):
        response = self.write('/api/payments/create-order',dict(item_type='campaign_budget',item_id=self.campaign(),custom_budget_paise=100000))
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['razorpay_order_id']

    def webhook(self, order, event='evt_test', amount=100000, currency='INR', payment='pay_test', signature=None):
        payload = dict(event='payment.captured',payload={'payment':{'entity':dict(id=payment,order_id=order,amount=amount,currency=currency,status='captured',method='upi')}})
        raw=json.dumps(payload).encode()
        sig=signature or hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(),raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/webhooks/razorpay',content=raw,headers={'X-Razorpay-Signature':sig,'X-Razorpay-Event-Id':event})

    def captured(self):
        order=self.order();self.assertEqual(self.webhook(order).status_code,200)
        with SessionLocal() as db:return db.query(Payment).one().id

    def test_migration_matches_models(self):
        command.check(Config(str(ROOT/'alembic.ini')))

    def test_signup_incomplete_and_no_token_json(self):
        self.client.cookies.clear()
        r=self.client.post('/api/auth/register',json=dict(full_name='New User',mobile='9876543212',email='new@example.com',password='password123',confirm_password='password123',role='admin'))
        self.assertEqual(r.status_code,200,r.text)
        self.assertIsNone(r.json()['access_token'])
        self.assertEqual(r.json()['user']['role'],'candidate')
        profile=self.client.get('/api/profile').json()
        self.assertFalse(profile['onboarding_completed']);self.assertFalse(profile['is_meta_connected'])

    def test_csrf_and_origin(self):
        self.assertEqual(self.client.post('/api/auth/logout').status_code,403)
        self.assertEqual(self.client.post('/api/auth/login',json={'login':'a@example.com','password':'password123'},headers={'Origin':'https://attacker.example'}).status_code,403)
        self.assertEqual(self.write('/api/auth/logout').status_code,200)
        self.assertEqual(self.client.get('/api/auth/me').status_code,401)

    def test_roles_isolation_suspension(self):
        campaign=self.campaign()
        self.assertEqual(self.client.get('/api/admin/candidates').status_code,403)
        self.login('b')
        self.assertNotIn(campaign,[x['id'] for x in self.client.get('/api/campaigns').json()])
        self.assertEqual(self.write(f'/api/campaigns/{campaign}/toggle-status').status_code,404)
        self.login('admin')
        csrf=self.client.get('/api/auth/csrf').json()['csrf_token']
        self.assertEqual(self.client.patch('/api/admin/candidates/a/status',json={'status':'Suspended'},headers={'X-CSRF-Token':csrf}).status_code,200)
        self.client.cookies.clear()
        self.assertEqual(self.client.post('/api/auth/login',json={'login':'a@example.com','password':'password123'}).status_code,403)

    def test_upload_rejects_text_and_inline_bypass(self):
        csrf=self.client.get('/api/auth/csrf').json()['csrf_token']
        r=self.client.post('/api/profile/upload-photo',files={'file':('x.txt',b'not image','text/plain')},headers={'X-CSRF-Token':csrf})
        self.assertEqual(r.status_code,422)
        profile=self.client.get('/api/profile').json();profile['photo_url']='data:image/png;base64,bm90IGltYWdl'
        r=self.client.put('/api/profile',json=profile,headers={'X-CSRF-Token':csrf})
        self.assertEqual(r.status_code,422)

    def test_valid_image(self):
        image=io.BytesIO();Image.new('RGB',(10,10)).save(image,format='PNG')
        csrf=self.client.get('/api/auth/csrf').json()['csrf_token']
        r=self.client.post('/api/profile/upload-photo',files={'file':('x.png',image.getvalue(),'image/png')},headers={'X-CSRF-Token':csrf})
        self.assertEqual(r.status_code,200,r.text)

    def test_campaign_ownership_required_for_order(self):
        self.assertEqual(self.write('/api/payments/create-order',dict(item_type='campaign_budget',item_id='missing',custom_budget_paise=100000)).status_code,404)
        campaign=self.campaign();self.login('b')
        self.assertEqual(self.write('/api/payments/create-order',dict(item_type='campaign_budget',item_id=campaign,custom_budget_paise=100000)).status_code,404)

    def test_wrong_amount_and_currency_no_credit(self):
        order=self.order()
        self.assertEqual(self.webhook(order,amount=1).status_code,409)
        self.assertEqual(self.webhook(order,event='evt_currency',currency='USD').status_code,409)
        with SessionLocal() as db:self.assertEqual(db.query(Payment).count(),0)

    def test_header_event_duplicate_and_atomic_journal(self):
        order=self.order()
        self.assertEqual(self.webhook(order).status_code,200)
        self.assertEqual(self.webhook(order).status_code,200)
        with SessionLocal() as db:
            self.assertEqual(db.query(Payment).count(),1)
            self.assertEqual(db.query(JournalLine).count(),2)
            self.assertEqual(db.query(func.sum(JournalLine.debit_paise-JournalLine.credit_paise)).scalar(),0)
            self.assertEqual(db.query(LedgerEntry).one().meta_spend_paise,0)

    def test_invalid_signature_no_credit(self):
        self.assertFalse(RazorpayClient().verify_payment_signature('x','y','invalid'))
        self.assertEqual(self.webhook(self.order(),signature='invalid').status_code,400)

    def test_atomic_failure_retry_same_event(self):
        order=self.order()
        with patch('services.reconciliation.journal',side_effect=RuntimeError('test failure')):
            self.assertEqual(self.webhook(order).status_code,409)
        with SessionLocal() as db:
            self.assertEqual(db.query(Payment).count(),0)
            self.assertFalse(db.query(WebhookEvent).one().is_processed)
        self.assertEqual(self.webhook(order).status_code,200)

    def test_second_payment_same_order_rejected(self):
        order=self.order();self.webhook(order)
        self.assertEqual(self.webhook(order,event='evt_other',payment='pay_other').status_code,409)

    def test_refund_cumulative_and_idempotent(self):
        payment=self.captured()
        with SessionLocal() as db:
            first=process_refund_request(db,payment,80000,operation_id='operation_one')
            self.assertEqual(first.status,'processed')
            self.assertEqual(process_refund_request(db,payment,80000,operation_id='operation_one').id,first.id)
            with self.assertRaises(ValueError):process_refund_request(db,payment,80000,operation_id='operation_two')
            self.assertEqual(db.query(func.sum(Refund.amount_paise)).scalar(),80000)

    def test_refund_concurrency(self):
        payment=self.captured()
        def refund(index):
            with SessionLocal() as db:
                try:process_refund_request(db,payment,80000,operation_id=f'concurrent_{index}');return True
                except ValueError:return False
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(refund,[1,2]))
        self.assertEqual(sum(results),1)

    def test_refund_timeout_reserves_and_no_repeat(self):
        payment=self.captured()
        with SessionLocal() as db:
            with patch.object(RazorpayClient,'process_refund',side_effect=TimeoutError()):
                with self.assertRaises(RuntimeError):process_refund_request(db,payment,80000,operation_id='timeout_operation')
            pending=process_refund_request(db,payment,80000,operation_id='timeout_operation')
            self.assertEqual(pending.status,'pending')
            with self.assertRaises(ValueError):process_refund_request(db,payment,80000,operation_id='another_operation')

    def test_approval_queue_and_mock_not_live(self):
        campaign=self.campaign();self.fund(campaign);self.login('admin')
        r=self.write('/api/admin/enhance-and-push',dict(ad_id=campaign,enhanced_slogan='Reviewed draft'))
        self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['job_status'],'Queued')
        run_once()
        with SessionLocal() as db:
            c=db.get(Campaign,campaign)
            self.assertNotIn('Live',c.status);self.assertEqual(c.reach,0)
            self.assertEqual(c.delivery_status,'Paused');self.assertEqual(c.provider_review_status,'Not Submitted (Mock)')
        self.assertEqual(self.write('/api/admin/enhance-and-push',dict(ad_id=campaign,enhanced_slogan='Reviewed draft')).status_code,409)

    def test_pending_toggle_blocked(self):
        self.assertEqual(self.write(f'/api/campaigns/{self.campaign()}/toggle-status').status_code,409)

    def test_live_meta_cannot_return_fake_id(self):
        import integrations.meta.client as meta
        with patch.object(meta,'META_MOCK_MODE',False):
            with self.assertRaises(RuntimeError):meta.MetaGraphClient().create_political_campaign('act_1','test','key')

    def test_payment_callback_signature_not_capture_proof(self):
        order=self.order();payment='pay_callback'
        signature=hmac.new(RAZORPAY_KEY_SECRET.encode(),f'{order}|{payment}'.encode(),hashlib.sha256).hexdigest()
        r=self.write('/api/payments/verify',dict(razorpay_order_id=order,razorpay_payment_id=payment,razorpay_signature=signature))
        self.assertEqual(r.status_code,409)
        with SessionLocal() as db:self.assertEqual(db.query(Payment).count(),0)

    def test_onboarding_save_and_restore(self):
        profile=self.client.get('/api/profile').json();profile['onboarding_completed']=True
        csrf=self.client.get('/api/auth/csrf').json()['csrf_token']
        r=self.client.put('/api/profile',json=profile,headers={'X-CSRF-Token':csrf})
        self.assertEqual(r.status_code,200,r.text)
        self.assertTrue(self.client.get('/api/auth/me').json()['onboarding_completed'])

    def test_expired_session(self):
        from entities import UserSession
        from datetime import datetime, timedelta, timezone
        with SessionLocal() as db:
            db.query(UserSession).update({'expires_at': datetime.now(timezone.utc)-timedelta(days=1)})
            db.commit()
        self.assertEqual(self.client.get('/api/auth/me').status_code,401)

    def test_duplicate_registration_and_password_hash(self):
        r=self.client.post('/api/auth/register',json=dict(full_name='Duplicate User',mobile='9876543210',email='a@example.com',password='password123',confirm_password='password123'))
        self.assertEqual(r.status_code,400)
        with SessionLocal() as db:self.assertTrue(db.get(User,'a').password_hash.startswith('$argon2id$'))

    def test_concurrent_payment_events_one_credit(self):
        order=self.order()
        def send(index):
            # Different event receipts for the same provider payment.
            with TestClient(app) as client:
                raw=json.dumps(dict(event='payment.captured',payload={'payment':{'entity':dict(id='pay_concurrent',order_id=order,amount=100000,currency='INR',status='captured')}})).encode()
                signature=hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(),raw,hashlib.sha256).hexdigest()
                return client.post('/api/webhooks/razorpay',content=raw,headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':f'concurrent_{index}'}).status_code
        with ThreadPoolExecutor(2) as pool:self.assertEqual(list(pool.map(send,[1,2])),[200,200])
        with SessionLocal() as db:self.assertEqual(db.query(Payment).count(),1);self.assertEqual(db.query(JournalLine).count(),2)

    def test_journal_append_only(self):
        self.captured()
        with SessionLocal() as db:
            row=db.query(JournalLine).first();row.debit_paise=1
            with self.assertRaises(ValueError):db.commit()
            db.rollback()

    def test_service_records_are_scoped_and_persistent(self):
        response=self.write('/api/surveys/create-poll',dict(question='Test question',options=['One','Two']))
        self.assertEqual(response.status_code,200)
        record=response.json()['poll']['id']
        self.login('b');self.assertEqual(self.client.get('/api/surveys/polls').json(),[])
        self.login('a');self.assertEqual(self.client.get('/api/surveys/polls').json()[0]['id'],record)
        self.assertEqual(self.write('/api/surveys/request-service',dict(service_type='whatsapp_broadcast',candidate_name='Test')).status_code,422)

    def test_page_selection_requires_owned_page(self):
        # Manual browser tokens can no longer establish a connection, even in mock mode.
        self.assertEqual(self.write('/api/meta/select-page',dict(page_id='foreign',page_name='Foreign')).status_code,409)
        self.assertEqual(self.write('/api/meta/connect',dict(access_token='mock_valid_test')).status_code,410)
        self.assertFalse(self.client.get('/api/meta/status').json()['facebook_connected'])

    def test_kill_switch_blocks_worker_without_false_success(self):
        from entities import PlatformSetting
        campaign=self.campaign();self.fund(campaign);self.login('admin')
        self.write('/api/admin/enhance-and-push',dict(ad_id=campaign,enhanced_slogan='Reviewed draft'))
        with SessionLocal() as db:db.add(PlatformSetting(key='meta_kill_switch',value='true'));db.commit()
        run_once()
        with SessionLocal() as db:self.assertEqual(db.query(PublishingJob).one().status,'Failed');self.assertNotIn('Live',db.get(Campaign,campaign).status)

    def test_login_throttle(self):
        from entities import AuditEvent
        with SessionLocal() as db:
            key=hashlib.sha256(b'testclient').hexdigest()[:36]
            db.add_all([AuditEvent(action='AUTH_ATTEMPT',target_user_id=key) for _ in range(20)])
            db.commit()
        self.assertEqual(self.client.post('/api/auth/login',json=dict(login='a@example.com',password='password123')).status_code,429)

    def test_real_payment_adapter_contract_without_network(self):
        import httpx
        import integrations.payments.razorpay_client as module
        calls=[]
        def handler(request):
            calls.append((request.method,request.url.path))
            if request.url.path.endswith('/orders'):
                body=json.loads(request.content);return httpx.Response(200,json=dict(id='order_provider',**body))
            if request.url.path.endswith('/refund'):
                return httpx.Response(200,json=dict(id='rfnd_provider',payment_id='pay_provider',amount=100000,status='pending'))
            return httpx.Response(200,json=dict(id='pay_provider',order_id='order_provider',amount=100000,currency='INR',status='captured'))
        original=httpx.Client
        with patch.object(module,'RAZORPAY_MOCK_MODE',False), patch.object(module.httpx,'Client',side_effect=lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
            client=module.RazorpayClient();client.key_id='test_contract_key';client.key_secret='test_contract_secret'
            self.assertEqual(client.create_order(100000)['id'],'order_provider')
            self.assertEqual(client.fetch_payment('pay_provider')['status'],'captured')
            self.assertEqual(client.process_refund('pay_provider',100000,operation_id='operation_contract')['status'],'pending')
        self.assertEqual(len(calls),3)

    def refund_event(self, refund, payment_id, status, event_id):
        raw=json.dumps(dict(event='refund.'+status,payload={'refund':{'entity':dict(id=refund, payment_id=payment_id, amount=80000,currency='INR',status=status)}})).encode()
        signature=hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(),raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/webhooks/razorpay',content=raw,headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':event_id})

    def test_pending_refund_completion_replay_once(self):
        payment=self.captured()
        with SessionLocal() as db:
            with patch.object(RazorpayClient,'process_refund',return_value=dict(id='rfnd_pending',payment_id='pay_test',amount=80000,status='pending')):
                refund=process_refund_request(db,payment,80000,operation_id='pending_operation')
                self.assertEqual(refund.status,'pending')
        self.assertEqual(self.refund_event('rfnd_pending','pay_test','processed','evt_refund_1').status_code,200)
        self.assertEqual(self.refund_event('rfnd_pending','pay_test','processed','evt_refund_2').status_code,200)
        with SessionLocal() as db:
            self.assertEqual(db.query(JournalLine).count(),4)
            self.assertEqual(db.query(Refund).one().status,'processed')

    def test_failed_refund_releases_reservation(self):
        payment=self.captured()
        with SessionLocal() as db:
            with patch.object(RazorpayClient,'process_refund',return_value=dict(id='rfnd_failed',payment_id='pay_test',amount=80000,status='pending')):
                process_refund_request(db,payment,80000,operation_id='failed_operation')
        self.assertEqual(self.refund_event('rfnd_failed','pay_test','failed','evt_refund_failure').status_code,200)
        with SessionLocal() as db:
            self.assertEqual(db.get(Payment,payment).refund_reserved_paise,0)
            self.assertEqual(db.query(JournalLine).count(),2)

    def test_same_refund_operation_concurrent_no_double_reserve(self):
        payment=self.captured()
        def submit(_):
            with SessionLocal() as db:
                return process_refund_request(db,payment,10000,operation_id='same_operation').id
        with ThreadPoolExecutor(2) as pool:ids=list(pool.map(submit,[1,2]))
        self.assertEqual(ids[0],ids[1])
        with SessionLocal() as db:self.assertEqual(db.get(Payment,payment).refund_reserved_paise,10000)

    def test_production_rejects_unsafe_defaults(self):
        import subprocess
        env=dict(os.environ,APP_ENV='production',COOKIE_SECURE='false')
        result=subprocess.run([sys.executable,'-c','import config'],cwd=ROOT/'backend',env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Production requires Secure cookies',result.stderr)

if __name__ == '__main__': unittest.main(verbosity=2)
