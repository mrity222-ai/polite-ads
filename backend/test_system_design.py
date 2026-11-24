"""Business invariants: isolated SQLite and deterministic provider contracts only."""
import unittest
import uuid
from datetime import datetime,timedelta,timezone,date
from zoneinfo import ZoneInfo
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from sqlalchemy import func
from test_campaign_review import CampaignReviewTests
from test_regressions import SessionLocal
from entities import (SubscriptionPlan,Subscription,Payment,Campaign,CampaignFundingDay,FundReservation,
                      PublishingJob,PublishingAttempt,ProviderSpendRecord,JournalLine,CandidateProfile,CampaignRevision,User)
from services.reconciliation import process_refund_request
from services.daily_funding import reserve_day,settle_verified_day,VerifiedSpendConfirmation,renew_due_campaigns
from services.publishing import execute_publishing_job,recover_expired,heartbeat,LostLease,RetryablePublishingError,MAX_ATTEMPTS
from integrations.meta.client import MetaGraphClient
from worker import run_once
import os
import subprocess
import sys
import sqlite3
import tempfile
import json
import io
import base64
from PIL import Image
from pathlib import Path
from contextlib import closing


class SystemDesignTests(CampaignReviewTests):
    def purchase(self,cap=50000):
        pid='plan_'+uuid.uuid4().hex[:12]
        with SessionLocal() as db:
            db.add(SubscriptionPlan(id=pid,name='Purchased plan',price_paise=100000,daily_ad_cap_paise=cap,features=['Saved feature']))
            db.commit()
        order=self.write('/api/payments/create-order',dict(item_type='subscription_plan',item_id=pid))
        self.assertEqual(order.status_code,200,order.text)
        self.assertEqual(self.webhook(order.json()['razorpay_order_id'],event='evt_'+pid,payment='pay_'+pid).status_code,200)
        with SessionLocal() as db:
            sub=db.query(Subscription).filter(Subscription.plan_snapshot['id'].as_string()==pid).one()
            return sub.id,sub.payment_id,pid

    def prepared(self,duration=1,publish=False):
        campaign=self.campaign()
        if duration!=1:self.assertEqual(self.resubmit(campaign,duration_days=duration).status_code,200)
        self.fund(campaign);self.login('admin')
        response=self.decide(campaign,'approve');self.assertEqual(response.status_code,200,response.text)
        if publish:run_once()
        return campaign,response.json()['job_id']

    def report(self,db,campaign,amount=20000,event='report_one'):
        day=db.query(CampaignFundingDay).filter_by(campaign_id=campaign,day_index=0).one()
        c=db.get(Campaign,campaign)
        start=datetime.combine(date.fromisoformat(day.billing_date),datetime.min.time(),ZoneInfo(day.billing_timezone)).astimezone(timezone.utc)
        end=start+timedelta(days=1)
        return VerifiedSpendConfirmation(event,day.id,c.meta_ad_id,amount,'INR',start.isoformat(),end.isoformat(),True,True),end+timedelta(seconds=1)

    def test_design_expired_subscription_is_inactive(self):
        campaign=self.campaign()
        sub,_,_=self.purchase()
        with SessionLocal() as db:
            db.get(Subscription,sub).expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
        result=self.client.get('/api/billing/subscription-status').json()
        self.assertEqual(result['entitlement_status'],'expired');self.assertEqual(result['daily_ad_limit'],0)
        response=self.write('/api/campaigns/create',dict(title='Denied',whatsapp_phone='9876543210',slogan='Test content',area='Ward',pincode='281306',radius_km=5,budget_daily=200,template_id=1,symbol='Car'))
        self.assertEqual(response.status_code,409)
        self.assertEqual(self.write('/api/payments/create-order',dict(item_type='campaign_budget',item_id=campaign,custom_budget_paise=50000)).status_code,409)

    def test_design_partial_then_full_refund_revokes_entitlement(self):
        _,payment,_=self.purchase()
        with SessionLocal() as db:process_refund_request(db,payment,40000,operation_id='partial_subscription')
        self.assertEqual(self.client.get('/api/billing/subscription-status').json()['entitlement_status'],'active')
        with SessionLocal() as db:process_refund_request(db,payment,60000,operation_id='full_subscription')
        result=self.client.get('/api/billing/subscription-status').json()
        self.assertEqual(result['entitlement_status'],'revoked')
        with SessionLocal() as db:self.assertEqual(db.get(Payment,payment).status,'refunded')

    def test_design_plan_snapshot_survives_catalog_edits(self):
        _,_,plan=self.purchase()
        with SessionLocal() as db:
            p=db.get(SubscriptionPlan,plan);p.name='Changed catalog';p.price_paise=900000;p.daily_ad_cap_paise=999999;p.features=['Other feature'];db.commit()
        result=self.client.get('/api/billing/subscription-status').json()
        self.assertEqual(result['plan_name'],'Purchased plan');self.assertEqual(result['price'],1000)
        self.assertEqual(result['daily_ad_limit'],500);self.assertEqual(result['features'],['Saved feature'])

    def test_design_renewal_replaces_access_and_refund_does_not_resurrect_old(self):
        old,_,_=self.purchase();new,payment,_=self.purchase(cap=90000)
        with SessionLocal() as db:
            self.assertEqual(db.get(Subscription,old).status,'superseded')
            self.assertEqual(db.get(Subscription,new).status,'active')
            process_refund_request(db,payment,100000,operation_id='renewal_refund')
        self.assertEqual(self.client.get('/api/billing/subscription-status').json()['entitlement_status'],'revoked')

    def test_design_plan_limit_at_create_edit_approval(self):
        campaign=self.campaign();self.fund(campaign)
        self.purchase(cap=20000)
        self.assertEqual(self.resubmit(campaign).status_code,409)
        self.login('admin');self.assertEqual(self.decide(campaign,'approve').status_code,409)
        self.login()
        payload=self.detail(campaign)['content'];payload['accepted_pricing']=payload['pricing_snapshot']
        self.assertEqual(self.write('/api/campaigns/create',payload).status_code,409)

    def test_design_aggregate_limit_prevents_parallel_campaign_bypass(self):
        first=self.campaign();self.fund(first);second=self.campaign();self.fund(second);self.login('admin')
        self.assertEqual(self.decide(first,'approve').status_code,200)
        self.assertEqual(self.decide(second,'approve').status_code,409)
        with SessionLocal() as db:self.assertEqual(db.query(PublishingJob).count(),1)

    def test_design_concurrent_approvals_share_one_owner_limit(self):
        from fastapi.testclient import TestClient
        from test_regressions import app
        first=self.campaign();self.fund(first);second=self.campaign();self.fund(second);self.login('admin')
        cookie=self.client.cookies.get('politiads_session')
        def approve(campaign):
            with TestClient(app) as client:
                client.cookies.set('politiads_session',cookie)
                csrf=client.get('/api/auth/csrf').json()['csrf_token']
                return client.post(f'/api/admin/review-campaigns/{campaign}',json=dict(action='approve',expected_version=1),headers={'X-CSRF-Token':csrf}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(approve,[first,second]))
        self.assertEqual(sorted(results),[200,409])
        with SessionLocal() as db:self.assertEqual(db.query(PublishingJob).count(),1)

    def test_design_approval_payload_ignores_later_profile_location_and_disclaimer(self):
        campaign,job=self.prepared()
        with SessionLocal() as db:
            payload=db.get(PublishingJob,job).approved_snapshot
            p=db.query(CandidateProfile).filter_by(user_id='a').one();p.lat='11';p.lng='22';p.disclaimer_text='Changed after approval';db.commit()
        with patch.object(MetaGraphClient,'create_adset',return_value={'id':'mock_adset'}) as adset,patch.object(MetaGraphClient,'create_ad_creative',return_value={'id':'mock_creative'}) as creative:
            run_once()
            self.assertEqual(adset.call_args.args[4:6],(payload['publishing_context']['lat'],payload['publishing_context']['lng']))
            self.assertEqual(creative.call_args.args[4],payload['publishing_context']['disclaimer'])
        with SessionLocal() as db:self.assertEqual(db.get(PublishingJob,job).status,'Submitted')

    def test_design_connection_change_blocks_approved_job(self):
        _,job=self.prepared()
        with SessionLocal() as db:
            p=db.query(CandidateProfile).filter_by(user_id='a').one();p.meta_connection_generation+=1;db.commit()
        run_once()
        with SessionLocal() as db:
            self.assertEqual(db.get(PublishingJob,job).status,'Failed');self.assertIn('connection changed',db.get(PublishingJob,job).error_details)

    def test_design_live_preflight_rechecks_owned_page_and_permissions(self):
        import config
        from services import publishing_context
        from security_encryption import encrypt_token
        campaign=self.campaign()
        with SessionLocal() as db:
            p=db.query(CandidateProfile).filter_by(user_id='a').one()
            p.meta_page_id='owned_page';p.meta_facebook_subject='fb_subject';p.is_meta_connected=True
            p.meta_access_token_encrypted=encrypt_token('test_only_token');db.commit()
            c=db.get(Campaign,campaign)
            with patch.object(config,'META_MOCK_MODE',False),patch.object(publishing_context,'FacebookOAuth') as adapter:
                context=publishing_context.capture(db,c)
                adapter.return_value.inspect_token.return_value=dict(is_valid=True,app_id=config.META_APP_ID,user_id='fb_subject',scopes=config.META_FACEBOOK_SCOPES)
                adapter.return_value.pages.return_value=[]
                with self.assertRaises(ValueError):publishing_context.verify(db,c,dict(publishing_context=context))
                adapter.return_value.pages.return_value=[{'id':'owned_page','access_token':'test_only_page_token'}]
                self.assertEqual(publishing_context.verify(db,c,dict(publishing_context=context)),context)
                adapter.return_value.inspect_token.return_value['scopes']=[]
                with self.assertRaises(ValueError):publishing_context.verify(db,c,dict(publishing_context=context))

    def test_design_daily_settlement_balances_and_unused_credit_is_refundable(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign)
            day=settle_verified_day(db,report,clock);db.commit()
            self.assertEqual((day.actual_spend_paise,day.earned_fee_paise),(20000,5000))
            p=db.query(Payment).one();self.assertEqual((p.campaign_reserved_paise,p.campaign_consumed_paise),(0,25000))
            self.assertEqual(db.query(func.sum(JournalLine.debit_paise)).scalar(),db.query(func.sum(JournalLine.credit_paise)).scalar())
            process_refund_request(db,p.id,75000,operation_id='unused_credit_refund')
            with self.assertRaises(ValueError):process_refund_request(db,p.id,1,operation_id='spent_credit_refund')
        summary=self.client.get('/api/admin/finance-summary').json()
        self.assertEqual(summary['actual_meta_spend_paise'],20000)
        self.assertEqual(summary['earned_company_fee_paise'],5000)

    def test_design_duplicate_report_does_not_double_charge(self):
        campaign,_=self.prepared(publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign)
            settle_verified_day(db,report,clock);db.commit()
            settle_verified_day(db,report,clock);db.commit()
            self.assertEqual(db.query(ProviderSpendRecord).count(),1)
            self.assertEqual(db.query(Payment).one().campaign_consumed_paise,25000)

    def test_design_unknown_delivery_or_overspend_never_releases_funds(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign,amount=50000)
            day=settle_verified_day(db,report,clock);db.commit()
            self.assertEqual(day.status,'reconciliation_required')
            self.assertEqual(db.query(Payment).one().campaign_reserved_paise,50000)
            self.assertEqual(db.query(ProviderSpendRecord).count(),0)
            with self.assertRaises(ValueError):settle_verified_day(db,{'amount_paise':1},clock)

    def test_design_next_day_requires_final_settlement_and_current_date(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign)
            c=db.get(Campaign,campaign)
            with self.assertRaises(HTTPException):reserve_day(db,c,1,clock)
            db.rollback()
            settle_verified_day(db,report,clock);db.commit()
            next_day=reserve_day(db,c,1,clock);db.commit()
            self.assertEqual(next_day.day_index,1)
            self.assertEqual(db.query(Payment).one().campaign_reserved_paise,50000)
            self.assertEqual(c.delivery_status,'Paused')

    def test_design_scheduler_keeps_unknown_days_reserved(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            _,clock=self.report(db,campaign)
            renew_due_campaigns(db,clock)
            self.assertEqual(db.query(CampaignFundingDay).one().status,'reconciliation_required')
            self.assertEqual(db.query(Payment).one().campaign_reserved_paise,50000)
            self.assertEqual(db.get(Campaign,campaign).delivery_status,'Reconciliation Required')

    def test_design_expired_unsubmitted_day_can_be_returned_for_review(self):
        campaign,_=self.prepared()
        with SessionLocal() as db:
            day=db.query(CampaignFundingDay).one()
            day.billing_date=(date.fromisoformat(day.billing_date)-timedelta(days=1)).isoformat();db.commit()
            renew_due_campaigns(db)
            self.assertEqual(db.get(Campaign,campaign).delivery_status,'Funding Required')
        current=self.detail(campaign)
        result=self.write(f'/api/admin/review-campaigns/{campaign}/release',dict(expected_version=current['version'],action='changes',note='Unsubmitted day expired'))
        self.assertEqual(result.status_code,200,result.text)

    def test_design_next_day_insufficient_funds_blocks_funding(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign,amount=40000)
            settle_verified_day(db,report,clock);db.commit()
            p=db.query(Payment).one();process_refund_request(db,p.id,50000,operation_id='unused_next_day')
            renew_due_campaigns(db,clock)
            self.assertEqual(db.get(Campaign,campaign).delivery_status,'Funding Required')
            self.assertEqual(db.query(CampaignFundingDay).count(),1)

    def test_design_suspended_owner_cannot_reserve_next_day(self):
        campaign,_=self.prepared(duration=2,publish=True)
        with SessionLocal() as db:
            report,clock=self.report(db,campaign)
            settle_verified_day(db,report,clock);db.commit()
            db.get(User,'a').status='suspended';db.commit()
            renew_due_campaigns(db,clock)
            self.assertEqual(db.get(Campaign,campaign).delivery_status,'Funding Required')
            self.assertEqual(db.query(CampaignFundingDay).count(),1)
            self.assertEqual(db.query(Payment).one().campaign_reserved_paise,0)

    def test_design_worker_expired_mock_lease_recovers_but_live_needs_reconciliation(self):
        _,jid=self.prepared()
        with SessionLocal() as db:
            job=db.get(PublishingJob,jid);job.status='Processing';job.lease_owner='dead_worker';job.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
            recover_expired(db)
            self.assertEqual(db.get(PublishingJob,jid).status,'Queued')
            job=db.get(PublishingJob,jid);job.status='Processing';job.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
            with patch('services.publishing.META_MOCK_MODE',False):recover_expired(db)
            self.assertEqual(db.get(PublishingJob,jid).status,'Reconciliation Required')

    def test_design_stale_worker_cannot_renew_other_owner_lease(self):
        _,jid=self.prepared()
        with SessionLocal() as db:
            job=db.get(PublishingJob,jid);job.status='Processing';job.lease_owner='current_worker';job.lease_expires_at=datetime.now(timezone.utc)+timedelta(minutes=2);db.commit()
            with self.assertRaises(LostLease):heartbeat(db,jid,'stale_worker')
            self.assertEqual(db.get(PublishingJob,jid).lease_owner,'current_worker')

    def test_design_safe_transient_retries_are_bounded(self):
        _,jid=self.prepared()
        with patch.object(MetaGraphClient,'create_political_campaign',side_effect=RetryablePublishingError('Safe retry')):
            for _ in range(MAX_ATTEMPTS):
                with SessionLocal() as db:
                    job=db.get(PublishingJob,jid);job.next_attempt_at=None;db.commit();execute_publishing_job(db,jid)
        with SessionLocal() as db:
            self.assertEqual(db.get(PublishingJob,jid).status,'Needs Attention')
            self.assertEqual(db.query(PublishingAttempt).count(),MAX_ATTEMPTS)

    def test_design_admin_queue_and_history_are_bounded(self):
        campaign=self.campaign()
        for _ in range(12):self.assertEqual(self.resubmit(campaign).status_code,200)
        for _ in range(11):self.campaign()
        self.login('admin')
        response=self.client.get('/api/admin/review-campaigns?page_size=5').json()
        self.assertEqual((len(response['items']),response['total']),(5,12))
        self.assertNotIn('content',response['items'][0]);self.assertNotIn('history',response['items'][0])
        detail=self.detail(campaign);self.assertEqual(len(detail['history']),10)
        older=self.client.get(f'/api/campaigns/{campaign}/history?before_version='+str(detail['history'][-1]['version'])).json()
        self.assertEqual(len(older['items']),3)
        self.assertEqual(detail['original_submission']['version'],1)
        result=self.client.get('/api/admin/review-campaigns?search=definitely_missing').json()
        self.assertEqual(result['total'],0)

    def test_design_revision_media_is_scoped_and_loaded_separately(self):
        campaign=self.campaign()
        buffer=io.BytesIO();Image.new('RGB',(64,64),(20,90,40)).save(buffer,format='PNG')
        media='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
        self.assertEqual(self.resubmit(campaign,photo_url=media).status_code,200)
        content=self.detail(campaign)
        self.assertTrue(content['history'][0]['snapshot']['has_image'])
        self.assertIsNone(content['history'][0]['snapshot']['photo_url'])
        self.assertTrue(self.client.get(f'/api/campaigns/{campaign}/history/2/media').json()['photo_url'].startswith('data:image/'))
        self.assertEqual(self.client.get(f'/api/campaigns/{campaign}/history/1/media').status_code,200)
        self.login('b')
        self.assertEqual(self.client.get(f'/api/campaigns/{campaign}/history/1/media').status_code,404)

    def test_design_legacy_migration_does_not_invent_paid_entitlements(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='legacy_entitlements_') as tmp:
            path=Path(tmp)/'old.db'
            env=dict(os.environ,DATABASE_URL='sqlite:///'+path.as_posix())
            subprocess.run([sys.executable,'-m','alembic','upgrade','697c642caf16'],cwd=root,env=env,check=True,capture_output=True)
            timestamp=(datetime.now(timezone.utc)-timedelta(days=45)).replace(tzinfo=None).isoformat(' ')
            with closing(sqlite3.connect(path)) as db:
                db.execute("INSERT INTO users (id,full_name,email,password_hash,role,status,created_at,updated_at) VALUES ('legacy','Legacy','legacy@example.com','unused','candidate','active',?,?)",(timestamp,timestamp))
                db.execute("INSERT INTO payment_orders (id,user_id,item_type,item_id,amount_paise,currency,status,created_at,updated_at) VALUES ('order_old','legacy','subscription_plan','old_plan',100000,'INR','paid',?,?)",(timestamp,timestamp))
                db.execute("INSERT INTO payments (id,order_id,user_id,amount_paise,currency,razorpay_payment_id,status,refund_reserved_paise,campaign_reserved_paise,created_at) VALUES ('payment_old','order_old','legacy',100000,'INR','provider_old','captured',0,0,?)",(timestamp,))
                db.execute("INSERT INTO campaigns (id,owner_id,title,slogan,budget_paise,radius_km,reach,spent_paise,clicks,status,badge,template_id,company_review_status,publishing_job_status,provider_review_status,delivery_status,created_at,updated_at,version) VALUES ('legacy_ad','legacy','Old','Old caption',50000,5,0,0,0,'Under Company Review','',1,'Pending','Not Queued','Pending','Paused',?,?,1)",(timestamp,timestamp))
                snapshot=json.dumps(dict(title='Old',slogan='Old caption',photo_url='https://example.invalid/saved.png'))
                db.execute("INSERT INTO campaign_revisions (id,campaign_id,version,actor_id,action,snapshot,created_at) VALUES ('legacy_revision','legacy_ad',1,'legacy','submitted',?,?)",(snapshot,timestamp))
                db.commit()
            subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root,env=env,check=True,capture_output=True)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('SELECT status,source FROM subscriptions').fetchone(),('review_required','legacy_unverified'))
                self.assertEqual(db.execute('SELECT count(*) FROM payments').fetchone()[0],1)
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
                snapshot,media=db.execute('SELECT snapshot,media_url FROM campaign_revisions').fetchone()
                self.assertIsNone(json.loads(snapshot)['photo_url'])
                self.assertEqual(media,'https://example.invalid/saved.png')


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(SystemDesignTests(name) for name in loader.getTestCaseNames(SystemDesignTests) if name.startswith('test_design_'))
