"""OAuth regressions: migrated temporary SQLite and fake provider; no Meta network calls."""
import os,sys,tempfile,json,base64,hmac,hashlib,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit,parse_qs
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
TEMP=tempfile.TemporaryDirectory(prefix='politiads_oauth_tests_')
os.environ.update(DATABASE_URL='sqlite:///'+(Path(TEMP.name)/'oauth.db').as_posix(),APP_ENV='test',META_MOCK_MODE='false',META_OAUTH_ENABLED='true',META_APP_ID='test_app',META_APP_SECRET='test_secret',META_OAUTH_REDIRECT_URI='http://localhost:5173/api/meta/oauth/callback',FRONTEND_ORIGIN='http://localhost:5173')
from sqlalchemy import delete
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from database import engine,SessionLocal
from entities import Base,User,CandidateProfile,SocialIdentity,OAuthAttempt,Campaign,PublishingJob
from security import hash_password
from security_encryption import encrypt_token
from integrations.meta.oauth import FacebookOAuth,MetaAuthorizationError
from main import app
ROOT=Path(__file__).resolve().parent.parent
SCOPES=['public_profile','email','pages_show_list','pages_read_engagement','ads_management','ads_read','instagram_basic']
PAGE=dict(id='page_owned',name='Owned Page',access_token='secret_page_token',instagram_business_account={'id':'ig_owned','username':'owned_ig'})

class OAuthTests(unittest.TestCase):
 original_inspector = FacebookOAuth.inspect_token
 @classmethod
 def setUpClass(cls):
  command.upgrade(Config(str(ROOT/'alembic.ini')),'head');cls.pwd=hash_password('password123')
 def setUp(self):
  with engine.begin() as connection:
   for table in reversed(Base.metadata.sorted_tables):connection.execute(delete(table))
  with SessionLocal() as db:
   for name in ('a','b'):
    db.add(User(id=name,full_name=name,email=name+'@example.com',mobile='987654321'+('0' if name=='a' else '1'),password_hash=self.pwd,role='candidate',status='active'));db.flush()
    db.add(CandidateProfile(user_id=name,candidate_name=name,gaon_ward='Ward',area_block='Block',pincode='281306'))
   db.commit()
  self.client=TestClient(app,follow_redirects=False)
  self.patches=[patch.object(FacebookOAuth,'exchange_code',return_value={'access_token':'secret_user_token','expires_in':3600}),
   patch.object(FacebookOAuth,'inspect_token',return_value={'is_valid':True,'app_id':'test_app','user_id':'fb_subject','scopes':SCOPES,'expires_at':int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())}),
   patch.object(FacebookOAuth,'identity',return_value={'id':'fb_subject','name':'Actual Facebook User','email':'facebook@example.com'}),
   patch.object(FacebookOAuth,'pages',return_value=[PAGE]),
   patch.object(FacebookOAuth,'instagram',return_value={'id':'ig_owned','username':'owned_ig'})]
  for item in self.patches:item.start();self.addCleanup(item.stop)
  self.addCleanup(self.client.close)
 @classmethod
 def tearDownClass(cls):engine.dispose();TEMP.cleanup()
 def login(self,user='a'):
  response=self.client.post('/api/auth/login',json={'login':user+'@example.com','password':'password123'})
  self.assertEqual(response.status_code,200,response.text)
 def post(self,path,body=None):
  token=self.client.get('/api/auth/csrf').json()['csrf_token']
  return self.client.post(path,json=body,headers={'X-CSRF-Token':token})
 def start(self,purpose='login'):
  response=self.client.post('/api/auth/facebook/start') if purpose=='login' else self.post('/api/meta/oauth/start',{'target':purpose})
  self.assertEqual(response.status_code,200,response.text)
  url=response.json()['authorization_url'];query=parse_qs(urlsplit(url).query)
  self.assertNotIn('client_secret',query)
  self.assertEqual(query['response_type'],['code'])
  return query['state'][0]
 def callback(self,state,**params):return self.client.get('/api/meta/oauth/callback',params={'state':state,'code':'provider_authorization_code',**params})
 def connect(self):
  state=self.start('facebook');response=self.callback(state)
  self.assertNotIn('error=',response.headers['location'])
  response=self.post('/api/meta/select-page',{'page_id':'page_owned'})
  self.assertEqual(response.status_code,200,response.text)

 def test_real_login_creates_own_identity_not_demo(self):
  result=self.callback(self.start())
  self.assertEqual(result.status_code,303,result.text)
  user=self.client.get('/api/auth/me').json()
  self.assertEqual(user['full_name'],'Actual Facebook User');self.assertNotEqual(user['id'],'a');self.assertIsNone(user['mobile'])
  self.assertFalse(user['onboarding_completed'])
  with SessionLocal() as db:self.assertEqual(db.query(SocialIdentity).count(),1)
 def test_repeat_login_uses_same_identity(self):
  self.callback(self.start());first=self.client.get('/api/auth/me').json()['id']
  self.client.cookies.clear();self.callback(self.start())
  self.assertEqual(self.client.get('/api/auth/me').json()['id'],first)
 def test_existing_email_never_auto_links(self):
  with patch.object(FacebookOAuth,'identity',return_value={'id':'fb_subject','name':'Someone','email':'a@example.com'}):
   response=self.callback(self.start())
  self.assertIn('account_exists',response.headers['location']);self.assertEqual(self.client.get('/api/auth/me').status_code,401)
 def test_state_must_be_bound_to_same_browser(self):
  state=self.start();self.client.cookies.delete('politiads_meta_oauth')
  self.assertIn('invalid_state',self.callback(state).headers['location'])
 def test_state_single_use(self):
  state=self.start();self.callback(state)
  self.assertIn('invalid_state',self.callback(state).headers['location'])
 def test_expired_state(self):
  state=self.start()
  with SessionLocal() as db:db.query(OAuthAttempt).update({'expires_at':datetime.now(timezone.utc)-timedelta(minutes=1)});db.commit()
  self.assertIn('invalid_state',self.callback(state).headers['location'])
 def test_cancelled_consent(self):
  response=self.callback(self.start(),error='access_denied')
  self.assertIn('access_denied',response.headers['location'])
  with SessionLocal() as db:self.assertEqual(db.query(SocialIdentity).count(),0)
 def test_connect_requires_app_session_and_csrf(self):
  self.assertEqual(self.client.post('/api/meta/oauth/start',json={'target':'facebook'}).status_code,401)
  self.login();self.assertEqual(self.client.post('/api/meta/oauth/start',json={'target':'facebook'}).status_code,403)
 def test_connection_page_list_has_no_tokens(self):
  self.login();self.connect()
  response=self.client.get('/api/meta/assets')
  self.assertEqual(response.status_code,200,response.text);self.assertIn('available_pages',response.json())
  self.assertNotIn('secret_user_token',response.text);self.assertNotIn('secret_page_token',response.text)
  status=self.client.get('/api/meta/status').json()
  self.assertTrue(status['facebook_connected']);self.assertFalse(status['instagram_connected'])
 def test_page_selection_empty_results_never_accept_manual_id(self):
  self.login();self.connect()
  with patch.object(FacebookOAuth,'pages',return_value=[]):
   self.assertEqual(self.post('/api/meta/select-page',{'page_id':'unverified'}).status_code,403)
 def test_instagram_separate_verified_connection(self):
  self.login();self.connect();self.callback(self.start('instagram'))
  response=self.post('/api/meta/instagram/select',{'page_id':'page_owned'})
  self.assertEqual(response.status_code,200,response.text)
  status=self.client.get('/api/meta/status').json();self.assertTrue(status['instagram_connected']);self.assertEqual(status['instagram_username'],'owned_ig')
 def test_instagram_requires_page_and_eligible_account(self):
  self.login();self.assertEqual(self.post('/api/meta/oauth/start',{'target':'instagram'}).status_code,409)
  self.connect()
  with patch.object(FacebookOAuth,'pages',return_value=[{'id':'page_owned','name':'Page','access_token':'secret'}]):
   self.assertEqual(self.post('/api/meta/instagram/select',{'page_id':'page_owned'}).status_code,409)
 def test_disconnect_instagram_retains_facebook(self):
  self.login();self.connect();self.callback(self.start('instagram'));self.post('/api/meta/instagram/select',{'page_id':'page_owned'})
  self.assertEqual(self.post('/api/meta/disconnect',{'target':'instagram'}).status_code,200)
  status=self.client.get('/api/meta/status').json();self.assertTrue(status['facebook_connected']);self.assertFalse(status['instagram_connected'])
 def test_disconnect_clears_page_tokens_and_blocks_stale_callback(self):
  self.login();self.connect();state=self.start('facebook')
  self.post('/api/meta/disconnect',{'target':'all'})
  self.assertIn('invalid_state',self.callback(state).headers['location'])
  with SessionLocal() as db:
   p=db.query(CandidateProfile).filter_by(user_id='a').one()
   self.assertIsNone(p.meta_page_id);self.assertIsNone(p.meta_access_token_encrypted);self.assertIsNone(p.meta_page_token_encrypted);self.assertFalse(p.is_instagram_connected)
 def test_disconnect_available_when_kill_switch_active(self):
  from entities import PlatformSetting
  self.login();self.connect()
  with SessionLocal() as db:db.add(PlatformSetting(key='meta_kill_switch',value='true'));db.commit()
  self.assertEqual(self.post('/api/meta/disconnect',{'target':'all'}).status_code,200)
 def test_missing_permissions_no_connection(self):
  self.login();state=self.start('facebook')
  with patch.object(FacebookOAuth,'inspect_token',return_value={'user_id':'fb_subject','scopes':['public_profile']}):
   self.assertIn('permissions_required',self.callback(state).headers['location'])
  self.assertFalse(self.client.get('/api/meta/status').json()['facebook_connected'])
 def test_changed_app_session_rejects_connection_callback(self):
  self.login();state=self.start('facebook');self.login('b')
  self.assertIn('invalid_state',self.callback(state).headers['location'])
 def test_instagram_wrong_facebook_account_rejected(self):
  self.login();self.connect();state=self.start('instagram')
  with patch.object(FacebookOAuth,'inspect_token',return_value={'user_id':'someone_else','scopes':SCOPES}),patch.object(FacebookOAuth,'identity',return_value={'id':'someone_else'}):
   self.assertIn('wrong_facebook_account',self.callback(state).headers['location'])
 def test_unlink_does_not_delete_facebook_login_identity(self):
  self.login();self.connect();self.post('/api/meta/disconnect',{'target':'facebook'})
  self.client.cookies.clear();self.callback(self.start())
  self.assertEqual(self.client.get('/api/auth/me').json()['id'],'a')
 def test_signed_deauthorization_and_forgery(self):
  self.login();self.connect()
  payload=base64.urlsafe_b64encode(json.dumps({'algorithm':'HMAC-SHA256','user_id':'fb_subject','issued_at':int(datetime.now(timezone.utc).timestamp())}).encode()).decode().rstrip('=')
  signature=base64.urlsafe_b64encode(hmac.new(b'test_secret',payload.encode(),hashlib.sha256).digest()).decode().rstrip('=')
  self.assertEqual(self.client.post('/api/meta/deauthorize',data={'signed_request':'invalid.'+payload}).status_code,400)
  self.assertEqual(self.client.post('/api/meta/deauthorize',data={'signed_request':signature+'.'+payload}).status_code,200)
  self.assertEqual(self.client.get('/api/auth/me').status_code,401)
 def test_manual_token_endpoint_removed(self):
  self.login();self.assertEqual(self.post('/api/meta/connect',{'access_token':'manual'}).status_code,410)
 def test_http_contract_no_real_network(self):
  import httpx
  seen=[]
  def handler(request):
   seen.append(request)
   if request.url.path.endswith('/me/accounts'):return httpx.Response(200,json={'data':[PAGE]})
   if request.url.path.endswith('/ig_owned'):return httpx.Response(200,json={'id':'ig_owned','username':'owned_ig'})
   return httpx.Response(200,json={'id':'fb_subject','name':'Test'})
  original=httpx.Client
  with patch('integrations.meta.oauth.httpx.Client',side_effect=lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs)):
   client=FacebookOAuth();self.assertEqual(client.pages('token',True)[0]['id'],'page_owned');self.assertEqual(client.instagram('page_token','ig_owned')['username'],'owned_ig')
  self.assertTrue(all('Authorization' in request.headers for request in seen))
 def test_callback_access_log_redacted(self):
  import logging
  from redacting_logger import OAuthAccessLogFilter
  record=logging.LogRecord('test',20,'',0,'%s %s %s %s %s',('peer','GET','/api/meta/oauth/callback?code=secret&state=state','1.1',303),None)
  OAuthAccessLogFilter().filter(record)
  self.assertNotIn('code=secret',record.getMessage())

 def test_replayed_deauthorization_does_not_remove_new_connection(self):
  self.login();self.connect()
  payload=base64.urlsafe_b64encode(json.dumps({'algorithm':'HMAC-SHA256','user_id':'fb_subject','issued_at':int(datetime.now(timezone.utc).timestamp())}).encode()).decode().rstrip('=')
  signature=base64.urlsafe_b64encode(hmac.new(b'test_secret',payload.encode(),hashlib.sha256).digest()).decode().rstrip('=')
  signed=signature+'.'+payload
  self.assertEqual(self.client.post('/api/meta/deauthorize',data={'signed_request':signed}).status_code,200)
  self.login();self.connect()
  self.assertTrue(self.client.post('/api/meta/deauthorize',data={'signed_request':signed}).json()['duplicate'])
  self.assertTrue(self.client.get('/api/meta/status').json()['facebook_connected'])

 def test_facebook_identity_cannot_link_to_two_app_users(self):
  self.login();self.connect();self.login('b');state=self.start('facebook')
  self.assertIn('identity_conflict',self.callback(state).headers['location'])
  with SessionLocal() as db:self.assertEqual(db.query(SocialIdentity).one().user_id,'a')
 def test_logged_out_connection_callback_rejected_before_provider_call(self):
  self.login();state=self.start('facebook');self.post('/api/auth/logout')
  with patch.object(FacebookOAuth,'exchange_code') as exchange:
   self.assertIn('invalid_state',self.callback(state).headers['location']);exchange.assert_not_called()
 def test_provider_token_from_wrong_application_rejected(self):
  # Exercise the real inspection method rather than the fixture inspector.
  with patch.object(FacebookOAuth,'_call',return_value={'data':{'is_valid':True,'app_id':'another_app','user_id':'subject'}}):
   from integrations.meta import oauth
   original = type(self).original_inspector
   with self.assertRaises(MetaAuthorizationError):original(FacebookOAuth(),'token')

if __name__=='__main__':unittest.main(verbosity=2)
