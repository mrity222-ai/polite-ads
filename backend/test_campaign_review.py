"""Review/finance boundary tests. Isolated migrated database; no provider network."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from test_regressions import Regressions, SessionLocal, app
from entities import Campaign, PublishingJob, Payment, FundReservation, CampaignRevision, User
from services.reconciliation import process_refund_request
from services.publishing import execute_publishing_job
from security import hash_password


class CampaignReviewTests(Regressions):
    def detail(self, campaign):
        response = self.client.get(f'/api/campaigns/{campaign}/review')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def decide(self, campaign, action='save', **kwargs):
        current = self.detail(campaign)
        return self.write(f'/api/admin/review-campaigns/{campaign}',
                          dict(expected_version=current['version'], action=action, **kwargs))

    def resubmit(self, campaign, **kwargs):
        current = self.detail(campaign)
        content = current['content']
        return self.write(f'/api/campaigns/{campaign}/revise',
            {**content, 'expected_version': current['version'], 'accepted_pricing': content['pricing_snapshot'], **kwargs})

    def test_review_no_funds_no_job_or_partial_decision(self):
        campaign = self.campaign(); self.login('admin')
        response = self.decide(campaign, 'approve')
        self.assertEqual(response.status_code, 409, response.text)
        with SessionLocal() as db:
            c = db.get(Campaign, campaign)
            self.assertEqual(c.company_review_status, 'Pending')
            self.assertEqual(c.version, 1)
            self.assertEqual(db.query(PublishingJob).count(), 0)

    def test_review_save_and_decision_history(self):
        campaign = self.campaign(); self.login('admin')
        content = self.detail(campaign)['content']; content['slogan'] = 'Admin edited post content'; content['title'] = 'Updated title'
        response = self.decide(campaign, content=content, note='Checked wording')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()['job_id'])
        self.assertEqual(response.json()['history'][-1]['snapshot']['slogan'], 'Test draft content')
        self.assertEqual(self.decide(campaign, 'changes', note='Please correct the address').status_code, 200)
        self.assertEqual(self.decide(campaign, 'approve').status_code, 409)
        self.login(); self.assertEqual(self.resubmit(campaign, area='Corrected Ward').status_code, 200)
        self.login('admin'); self.assertEqual(self.decide(campaign, 'reject', note='Incorrect eligibility').status_code, 200)
        self.assertEqual(self.decide(campaign, 'approve').status_code, 409)

    def test_review_pricing_override_requires_candidate_consent(self):
        campaign = self.campaign(); self.fund(campaign); self.login('admin')
        self.assertEqual(self.decide(campaign, 'approve', meta_daily_paise=7000).status_code, 409)
        response = self.decide(campaign, 'save', meta_daily_paise=7000)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['company_review_status'], 'Changes Requested')
        self.assertEqual(response.json()['content']['pricing_snapshot']['company_fee_paise'], 43000)
        self.assertEqual(self.decide(campaign, 'save').json()['company_review_status'], 'Changes Requested')
        self.assertEqual(self.decide(campaign, 'approve').status_code, 409)
        self.login(); self.assertEqual(self.resubmit(campaign, accepted_pricing=None).status_code, 409)
        self.assertEqual(self.resubmit(campaign).status_code, 200)
        self.login('admin'); response = self.decide(campaign, 'approve')
        self.assertEqual(response.status_code, 200, response.text)
        with SessionLocal() as db:
            job = db.query(PublishingJob).one()
            self.assertEqual(job.approved_snapshot['pricing_snapshot']['meta_daily_paise'], 7000)

    def test_review_fixed_policy_200_70_and_prospective_changes(self):
        self.login('admin')
        response = self.write('/api/admin/pricing-policy', dict(mode='fixed_meta', meta_daily_paise=7000, commission_pct=20))
        self.assertEqual(response.status_code, 200)
        self.login()
        q = self.client.get('/api/campaigns/pricing-quote?budget_daily=200').json()
        self.assertEqual((q['meta_daily_paise'], q['company_fee_paise']), (7000, 13000))
        campaign = self.campaign(); initial = self.detail(campaign)['content']['pricing_snapshot']
        self.login('admin'); self.write('/api/admin/pricing-policy', dict(mode='fixed_meta', meta_daily_paise=5000))
        self.login(); self.assertEqual(self.detail(campaign)['content']['pricing_snapshot'], initial)
        q = self.client.get('/api/campaigns/pricing-quote?budget_daily=200').json()
        self.assertEqual((q['meta_daily_paise'], q['company_fee_paise']), (5000, 15000))

    def test_review_stale_edit_and_cross_account_denied(self):
        campaign = self.campaign(); first = self.detail(campaign)
        self.assertEqual(self.resubmit(campaign, slogan='New content').status_code, 200)
        response = self.write(f'/api/campaigns/{campaign}/revise', {**first['content'], 'expected_version': 1})
        self.assertEqual(response.status_code, 409)
        self.login('b')
        self.assertEqual(self.client.get(f'/api/campaigns/{campaign}/review').status_code, 404)
        self.assertEqual(self.write('/api/admin/pricing-policy', dict(mode='fixed_meta')).status_code, 403)

    def test_review_supersede_queued_version_releases_funds(self):
        campaign = self.campaign(); self.fund(campaign); self.login('admin')
        result = self.decide(campaign, 'approve'); self.assertEqual(result.status_code, 200, result.text)
        job_id = result.json()['job_id']
        self.login(); self.assertEqual(self.resubmit(campaign, slogan='Candidate revised content').status_code, 200)
        with SessionLocal() as db:
            self.assertEqual(db.get(PublishingJob, job_id).status, 'Cancelled')
            self.assertEqual(db.query(Payment).one().campaign_reserved_paise, 0)
            self.assertEqual(db.query(FundReservation).one().status, 'released')
        self.login('admin'); self.assertEqual(self.decide(campaign, 'approve').status_code, 200)
        with SessionLocal() as db: self.assertEqual(db.query(PublishingJob).count(), 2)

    def test_review_refund_cannot_use_reserved_campaign_funds(self):
        campaign = self.campaign(); self.fund(campaign); self.login('admin')
        self.assertEqual(self.decide(campaign, 'approve').status_code, 200)
        with SessionLocal() as db:
            payment = db.query(Payment).one()
            self.assertEqual(payment.campaign_reserved_paise, 50000)
            with self.assertRaises(ValueError):
                process_refund_request(db, payment.id, 60000, operation_id='reserved_refund_test')

    def test_review_admin_cannot_increase_customer_charge(self):
        campaign = self.campaign(); self.login('admin')
        content = self.detail(campaign)['content']; content['budget_daily'] = 1000
        self.assertEqual(self.decide(campaign, content=content).status_code, 409)

    def test_review_draft_not_in_queue_and_requires_pricing_acceptance(self):
        campaign = self.campaign()
        self.assertEqual(self.resubmit(campaign, save_as_draft=True, accepted_pricing=None).status_code, 200)
        self.login('admin'); queue = self.client.get('/api/admin/review-campaigns?state=All').json()['items']
        self.assertFalse(any(item['id'] == campaign for item in queue))
        self.assertEqual(self.decide(campaign, 'approve').status_code, 409)
        self.login(); self.assertEqual(self.resubmit(campaign, accepted_pricing=None).status_code, 409)
        self.assertEqual(self.resubmit(campaign).status_code, 200)

    def test_review_duplicate_approval_and_worker_version_boundary(self):
        campaign = self.campaign(); self.fund(campaign); self.login('admin')
        version = self.detail(campaign)['version']
        cookie = self.client.cookies.get('politiads_session')
        def approve(_):
            with TestClient(app) as client:
                client.cookies.set('politiads_session', cookie)
                csrf = client.get('/api/auth/csrf').json()['csrf_token']
                return client.post(f'/api/admin/review-campaigns/{campaign}', json=dict(action='approve', expected_version=version), headers={'X-CSRF-Token': csrf}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool: responses = list(pool.map(approve, range(2)))
        self.assertEqual(sorted(responses), [200, 409])
        with SessionLocal() as db:
            self.assertEqual(db.query(PublishingJob).count(), 1)
            c = db.get(Campaign, campaign); c.version += 1; db.commit()
            job = execute_publishing_job(db, db.query(PublishingJob).one().id)
            self.assertEqual(job.status, 'Failed')
            self.assertIn('superseded', job.error_details)

    def test_review_private_admin_username_and_demo_password_block(self):
        with SessionLocal() as db:
            user = db.get(User, 'admin'); user.username = 'super admin'; db.commit()
        r = self.client.post('/api/auth/login', json=dict(login='super admin', password='password123'))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['user']['role'], 'admin')
        with SessionLocal() as db:
            user = db.get(User, 'admin'); user.password_hash = hash_password('admin123'); db.commit()
        self.assertEqual(self.client.post('/api/auth/login', json=dict(login='super admin', password='admin123')).status_code, 401)

    def test_review_release_allows_refund_and_cancels_queue(self):
        campaign = self.campaign(); self.fund(campaign); self.login('admin')
        self.assertEqual(self.decide(campaign, 'approve').status_code, 200)
        current = self.detail(campaign)
        result = self.write(f'/api/admin/review-campaigns/{campaign}/release', dict(action='changes', expected_version=current['version'], note='Return unused funds'))
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['funds']['reserved_paise'], 0)
        with SessionLocal() as db:
            self.assertEqual(db.query(PublishingJob).one().status, 'Cancelled')
            payment = db.query(Payment).one()
            self.assertEqual(process_refund_request(db, payment.id, 100000, operation_id='released_credit_refund').status, 'processed')

    def test_review_invalid_allocation_and_funding_period_rejected(self):
        campaign = self.campaign()
        response = self.write('/api/payments/create-order', dict(item_type='campaign_budget', item_id=campaign, custom_budget_paise=55000))
        self.assertEqual(response.status_code, 422)
        self.login('admin')
        self.assertEqual(self.decide(campaign, meta_daily_paise=60000).status_code, 422)
        self.assertEqual(self.write('/api/admin/pricing-policy', dict(mode='percentage', commission_pct=100)).status_code, 422)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(CampaignReviewTests(name) for name in loader.getTestCaseNames(CampaignReviewTests) if name.startswith('test_review_'))
