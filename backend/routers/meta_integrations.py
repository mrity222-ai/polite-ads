"""OAuth, separate Facebook Page/Instagram selection, and local disconnect."""
import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import config
from database import get_db
from entities import User, UserSession, CandidateProfile, SocialIdentity, OAuthAttempt, PublishingJob, Campaign, AuditEvent
from dependencies import require_active_user, extract_token
from security import hash_token, hash_password, create_session
from security_encryption import encrypt_token, decrypt_token
from integrations.meta.oauth import FacebookOAuth, MetaAuthorizationError

router = APIRouter(tags=['Facebook Login and Meta Connections'])
COOKIE = 'politiads_meta_oauth'
ERRORS = {
 'oauth_disabled':'Facebook authorization is disabled in server configuration.',
 'mock_mode':'Disable Meta mock mode before using real Facebook authorization.',
 'configuration_required':'Configure Meta App ID, App Secret and callback URL on the server.',
 'invalid_callback_url':'Configure a valid HTTPS callback URL (localhost HTTP is development-only).',
 'permissions_required':'Required Facebook/Instagram permissions were not granted. Reconnect and grant access.',
 'authorization_expired':'Facebook authorization expired or was revoked. Reconnect your account.',
 'provider_permissions_or_request':'Meta rejected the request. Check permissions, app review and account access.',
 'provider_unavailable':'Meta could not be reached. Connection was not confirmed; retry later.',
 'account_exists':'This email already has an app account. Log in with your password, then connect Facebook to link it safely.',
 'identity_conflict':'This Facebook identity is already linked to a different app account.',
 'wrong_facebook_account':'Use the same Facebook account that owns the currently selected Page.',
 'invalid_state':'The authorization request expired, was already used, or belongs to a different browser. Start again.',
 'access_denied':'Facebook authorization was cancelled or denied. No connection was created.',
 'inactive_account':'This application account is not active.',
}

def aware(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def fail(error):
    raise HTTPException(409, ERRORS.get(error.code, 'Facebook verification failed. Start authorization again.')) from None


def profile_for(db, user):
    profile = db.query(CandidateProfile).filter_by(user_id=user.id).first()
    if not profile:
        raise HTTPException(409, 'Create your candidate profile before connecting accounts.')
    return profile


def check_enabled(db):
    setting = db.get(__import__('entities').PlatformSetting, 'meta_kill_switch')
    if config.META_KILL_SWITCH or (setting and setting.value.lower() == 'true'):
        raise HTTPException(503, 'Meta connection operations are disabled. Local disconnect remains available.')


def required(purpose):
    return set(config.META_INSTAGRAM_SCOPES if purpose == 'instagram' else config.META_FACEBOOK_SCOPES)


def valid_inspection(client, token, purpose=None):
    data = client.inspect_token(token)
    now = datetime.now(timezone.utc).timestamp()
    for name in ('expires_at', 'data_access_expires_at'):
        if data.get(name) and data[name] <= now:
            raise MetaAuthorizationError('authorization_expired')
    if purpose and required(purpose) - set(data.get('scopes', [])):
        raise MetaAuthorizationError('permissions_required')
    return data


def clear_connection(db, profile, target='all'):
    profile.instagram_account_id = None
    profile.instagram_username = None
    profile.is_instagram_connected = False
    profile.meta_connection_generation += 1
    if target != 'instagram':
        profile.meta_access_token_encrypted = None
        profile.meta_page_token_encrypted = None
        profile.meta_page_id = None
        profile.meta_page_name = None
        profile.meta_facebook_subject = None
        profile.meta_scopes = None
        profile.meta_token_expires_at = None
        profile.meta_verified_at = None
        profile.is_meta_connected = False
        profile.meta_connection_status = 'Not Connected'
    # Never stop a worker by changing its claimed state. In-flight actions must check the grant before each step.
    ids = db.query(Campaign.id).filter_by(owner_id=profile.user_id)
    db.query(PublishingJob).filter(PublishingJob.campaign_id.in_(ids), PublishingJob.status == 'Queued').update(
        {'status':'Failed', 'stage':'DISCONNECTED', 'error_details':'Connection disconnected; explicit review required before retry.'}, synchronize_session=False)


def link_identity(db, user_id, subject):
    identity = db.query(SocialIdentity).filter_by(provider='facebook', app_id=config.META_APP_ID, subject=subject).first()
    own = db.query(SocialIdentity).filter_by(provider='facebook', app_id=config.META_APP_ID, user_id=user_id).first()
    if (identity and identity.user_id != user_id) or (own and own.subject != subject):
        raise MetaAuthorizationError('identity_conflict')
    if not identity:
        db.add(SocialIdentity(provider='facebook', app_id=config.META_APP_ID, subject=subject, user_id=user_id))


class StartConnection(BaseModel):
    target: str = Field(default='facebook', pattern='^(facebook|instagram)$')


def start_attempt(request, response, db, purpose, user=None):
    client = FacebookOAuth()
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    try:
        url = client.authorization_url(state, purpose)
    except MetaAuthorizationError as error:
        fail(error)
    if user:
        check_enabled(db)
        profile = profile_for(db, user)
        if purpose == 'instagram' and not profile.is_meta_connected:
            raise HTTPException(409, 'Connect and select your Facebook Page first.')
        # Cancels older authorization attempts, including ones in other browser sessions.
        profile.meta_connection_generation += 1
    db.add(OAuthAttempt(state_hash=hash_token(state), nonce_hash=hash_token(nonce), purpose=purpose,
        user_id=user.id if user else None, session_hash=hash_token(request.state.raw_token) if user else None,
        connection_generation=profile.meta_connection_generation if user else None,
        expires_at=datetime.now(timezone.utc)+timedelta(minutes=10)))
    db.commit()
    response.set_cookie(COOKIE, nonce, httponly=True, secure=config.COOKIE_SECURE, samesite='lax', max_age=600, path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'authorization_url':url}


@router.post('/api/auth/facebook/start')
def facebook_login_start(request: Request, response: Response, db: Session = Depends(get_db)):
    return start_attempt(request, response, db, 'login')


@router.post('/api/meta/oauth/start')
def meta_connect_start(data: StartConnection, request: Request, response: Response,
    user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    return start_attempt(request, response, db, data.target, user)


def callback_redirect(purpose, error=None):
    params = {'purpose':purpose, 'result':'error' if error else 'authorized'}
    if error: params['error'] = error
    response = RedirectResponse(config.FRONTEND_ORIGIN.rstrip('/')+'/#/meta-connect?'+urlencode(params), status_code=303)
    response.delete_cookie(COOKIE, path='/')
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@router.get('/api/meta/oauth/callback')
def oauth_callback(request: Request, state: str = '', code: str = '', error: str = '', db: Session = Depends(get_db)):
    attempt = db.get(OAuthAttempt, hash_token(state)) if state else None
    nonce = request.cookies.get(COOKIE, '')
    if not attempt or not nonce or not hmac.compare_digest(attempt.nonce_hash, hash_token(nonce)) or aware(attempt.expires_at) <= datetime.now(timezone.utc):
        return callback_redirect('login', 'invalid_state')
    claimed = db.execute(update(OAuthAttempt).where(OAuthAttempt.state_hash == attempt.state_hash,
        OAuthAttempt.consumed == False).values(consumed=True)).rowcount
    db.commit()
    if not claimed: return callback_redirect(attempt.purpose, 'invalid_state')
    if error or not code: return callback_redirect(attempt.purpose, 'access_denied')
    try:
        client = FacebookOAuth()
        if attempt.user_id:
            check_enabled(db)
            user = db.get(User, attempt.user_id)
            session = db.query(UserSession).filter_by(token_hash=attempt.session_hash, user_id=attempt.user_id, is_revoked=False).first()
            current_token = extract_token(request)
            if not session or aware(session.expires_at) <= datetime.now(timezone.utc) or (current_token and hash_token(current_token) != attempt.session_hash):
                raise MetaAuthorizationError('invalid_state')
            if not user or user.status != 'active': raise MetaAuthorizationError('inactive_account')
            profile = profile_for(db, user)
            if profile.meta_connection_generation != attempt.connection_generation: raise MetaAuthorizationError('invalid_state')
        exchange = client.exchange_code(code)
        token = exchange.get('access_token')
        if not token: raise MetaAuthorizationError('token_exchange_failed')
        inspection = valid_inspection(client, token, None if attempt.purpose == 'login' else attempt.purpose)
        identity = client.identity(token)
        subject = str(identity['id'])
        if subject != str(inspection.get('user_id')): raise MetaAuthorizationError('invalid_token')
        if attempt.purpose == 'login':
            linked = db.query(SocialIdentity).filter_by(provider='facebook', app_id=config.META_APP_ID, subject=subject).first()
            if linked:
                user = db.get(User, linked.user_id)
            else:
                email = (identity.get('email') or '').strip().lower() or None
                if email and db.query(User).filter_by(email=email).first(): raise MetaAuthorizationError('account_exists')
                user = User(full_name=(identity.get('name') or 'Facebook User')[:100],email=email,mobile=None,
                    password_hash=hash_password(secrets.token_urlsafe(48)),role='candidate',status='active')
                db.add(user); db.flush()
                db.add(CandidateProfile(user_id=user.id,candidate_name=user.full_name,gaon_ward='',area_block='',pincode='',
                    is_meta_connected=False,onboarding_completed=False))
                link_identity(db,user.id,subject)
            if not user or user.status != 'active': raise MetaAuthorizationError('inactive_account')
            db.commit()
            old_token = extract_token(request)
            if old_token:
                db.query(UserSession).filter_by(token_hash=hash_token(old_token)).update({'is_revoked':True})
                db.commit()
            raw_token = create_session(db,user.id,config.SESSION_TTL_HOURS)
            response = callback_redirect('login')
            response.set_cookie('politiads_session',raw_token,httponly=True,secure=config.COOKIE_SECURE,samesite=config.COOKIE_SAMESITE,max_age=config.SESSION_TTL_HOURS*3600,path='/')
            return response
        # Login and asset grants remain separate. Only an authenticated link may attach Facebook to an existing user.
        if attempt.purpose == 'facebook':
            link_identity(db,user.id,subject)
            # A new authorization never inherits a previous account's Page/Instagram selection.
            profile.meta_page_id = profile.meta_page_name = profile.meta_page_token_encrypted = None
            profile.instagram_account_id = profile.instagram_username = None
            profile.is_meta_connected = profile.is_instagram_connected = False
        elif profile.meta_facebook_subject != subject:
            raise MetaAuthorizationError('wrong_facebook_account')
        profile.meta_access_token_encrypted = encrypt_token(token)
        profile.meta_facebook_subject = subject
        profile.meta_scopes = inspection.get('scopes', [])
        expires = inspection.get('expires_at') or (datetime.now(timezone.utc).timestamp()+int(exchange.get('expires_in',3600)))
        profile.meta_token_expires_at = datetime.fromtimestamp(expires,timezone.utc)
        profile.meta_verified_at = datetime.now(timezone.utc)
        profile.meta_connection_status = 'Selection Required' if attempt.purpose == 'facebook' else 'Connected'
        db.commit()
        return callback_redirect(attempt.purpose)
    except MetaAuthorizationError as error:
        db.rollback()
        return callback_redirect(attempt.purpose,error.code if error.code in ERRORS else 'provider_unavailable')
    except IntegrityError:
        db.rollback()
        return callback_redirect(attempt.purpose,'identity_conflict')
    except HTTPException:
        db.rollback()
        return callback_redirect(attempt.purpose,'invalid_state')


def verified_grant(db, profile, target='facebook'):
    check_enabled(db)
    if not profile.meta_access_token_encrypted or not profile.meta_facebook_subject:
        raise HTTPException(409, 'Reconnect Facebook with the authorization button.')
    try:
        token = decrypt_token(profile.meta_access_token_encrypted)
        client = FacebookOAuth()
        inspection = valid_inspection(client,token,target)
        if str(inspection.get('user_id')) != profile.meta_facebook_subject:
            raise MetaAuthorizationError('invalid_token')
        return client,token,inspection
    except MetaAuthorizationError as error:
        fail(error)
    except Exception:
        raise HTTPException(409,'Stored authorization could not be read. Reconnect Facebook.') from None


@router.get('/api/meta/status')
def connection_status(user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    status = profile.meta_connection_status
    valid = False
    error = None
    instagram_valid = False
    if profile.meta_access_token_encrypted and profile.meta_facebook_subject:
        try:
            client,token,inspection = verified_grant(db,profile)
            include_instagram = bool(profile.is_instagram_connected and 'instagram_basic' in inspection.get('scopes', []))
            pages = client.pages(token, include_instagram=include_instagram)
            selected = next((page for page in pages if page.get('id') == profile.meta_page_id and page.get('access_token')), None)
            valid = selected is not None
            if profile.is_meta_connected and not valid:
                status, error = 'Page Access Required', 'The selected Facebook Page is no longer accessible.'
            if profile.is_instagram_connected:
                linked = (selected or {}).get('instagram_business_account') or {}
                instagram_valid = include_instagram and str(linked.get('id')) == str(profile.instagram_account_id)
            else:
                instagram_valid = False
        except MetaAuthorizationError as failure:
            error = ERRORS.get(failure.code, "Provider verification unavailable.")
            status = "Verification Unavailable"
        except HTTPException as failure:
            error = failure.detail
            status = 'Reconnect Required' if failure.status_code == 409 else 'Verification Unavailable'
    facebook = bool(valid and profile.is_meta_connected and profile.meta_page_id and profile.meta_page_token_encrypted)
    instagram = bool(facebook and instagram_valid and profile.instagram_account_id)
    return dict(is_connected=facebook,connection_status=('Connected' if facebook else status),mock=False,
        authorization_present=bool(profile.meta_access_token_encrypted and profile.meta_facebook_subject),
        page_id=profile.meta_page_id if facebook else None,page_name=profile.meta_page_name if facebook else None,
        facebook_connected=facebook,instagram_connected=instagram,
        instagram_account_id=profile.instagram_account_id if instagram else None,
        instagram_username=profile.instagram_username if instagram else None,
        message=error,oauth_enabled=config.META_OAUTH_ENABLED,
        publishing_available=False)


@router.get('/api/meta/assets')
def available_assets(target: str = 'facebook', user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    if target not in ('facebook','instagram'): raise HTTPException(422,'Invalid connection target.')
    profile = profile_for(db,user)
    client,token,_ = verified_grant(db,profile,target)
    try:
        pages=client.pages(token,include_instagram=(target=='instagram'))
    except MetaAuthorizationError as error: fail(error)
    safe=[]
    for page in pages:
        if target=='instagram' and page.get('id') != profile.meta_page_id: continue
        ig=page.get('instagram_business_account') or {}
        safe.append(dict(id=page['id'],name=page.get('name','Facebook Page'),
            instagram_account_id=ig.get('id'),instagram_username=ig.get('username')))
    return {'available_pages':safe,'target':target}


class SelectAsset(BaseModel):
    page_id: str = Field(min_length=1,max_length=100)
    page_name: str | None = None  # Ignored; provider supplies the name.


@router.post('/api/meta/select-page')
def select_page(data: SelectAsset, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    profile=profile_for(db,user)
    client,token,_=verified_grant(db,profile)
    try: pages=client.pages(token)
    except MetaAuthorizationError as error: fail(error)
    selected=next((p for p in pages if p.get('id')==data.page_id),None)
    if not selected or not selected.get('access_token'):
        raise HTTPException(403,'This Page is not available to the authorized account. Reconnect and grant Page access.')
    profile.meta_page_id=selected['id'];profile.meta_page_name=selected.get('name','Facebook Page')
    profile.meta_page_token_encrypted=encrypt_token(selected['access_token'])
    profile.meta_connection_status='Connected';profile.is_meta_connected=True
    profile.instagram_account_id=profile.instagram_username=None;profile.is_instagram_connected=False
    db.commit()
    return {'facebook_connected':True,'page_id':profile.meta_page_id,'page_name':profile.meta_page_name,'instagram_connected':False}


@router.post('/api/meta/instagram/select')
def select_instagram(data: SelectAsset, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    profile=profile_for(db,user)
    if not profile.is_meta_connected or profile.meta_page_id != data.page_id:
        raise HTTPException(409,'Select your Facebook Page before connecting its Instagram account.')
    client,token,_=verified_grant(db,profile,'instagram')
    try:
        pages=client.pages(token,include_instagram=True)
        selected=next((p for p in pages if p.get('id')==data.page_id),None)
        ig=(selected or {}).get('instagram_business_account') or {}
        if not ig.get('id') or not (selected or {}).get('access_token'):
            raise HTTPException(409,'No eligible Instagram professional account is linked to this Page.')
        verified=client.instagram(selected['access_token'],ig['id'])
        if str(verified.get('id')) != str(ig['id']) or not verified.get('username'):
            raise HTTPException(409,'Instagram identity could not be verified.')
    except MetaAuthorizationError as error: fail(error)
    profile.instagram_account_id=str(verified['id']);profile.instagram_username=verified['username'];profile.is_instagram_connected=True
    profile.meta_page_token_encrypted=encrypt_token(selected['access_token'])
    db.commit()
    return {'instagram_connected':True,'instagram_account_id':profile.instagram_account_id,'instagram_username':profile.instagram_username}


class DisconnectRequest(BaseModel):
    target: str = Field(default='all', pattern='^(all|facebook|instagram)$')


@router.post('/api/meta/disconnect')
def disconnect(data: DisconnectRequest = DisconnectRequest(), user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    profile=profile_for(db,user)
    clear_connection(db,profile,data.target);db.commit()
    return {'status':'disconnected','target':data.target,'message':'Disconnected from this app. External accounts/ads were not deleted or paused. Facebook sign-in remains linked.'}


@router.post('/api/meta/revoke')
def revoke_authorization(user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    profile=profile_for(db,user)
    client,token,_=verified_grant(db,profile)
    try: client.revoke(token,profile.meta_facebook_subject)
    except MetaAuthorizationError as error: fail(error)
    clear_connection(db,profile);db.commit()
    return {'status':'revoked','message':'Meta confirmed removal of app permissions; external accounts were not deleted.'}


@router.post('/api/meta/connect')
def legacy_manual_token(user: User = Depends(require_active_user)):
    raise HTTPException(410,'Manual token entry is removed. Use the Facebook authorization button.')


@router.post('/api/meta/deauthorize')
async def deauthorize(request: Request, db: Session = Depends(get_db)):
    form=await request.form();signed=str(form.get('signed_request',''))
    try:
        signature,encoded=signed.split('.',1)
        decode=lambda value: base64.urlsafe_b64decode(value+'='*(-len(value)%4))
        expected=hmac.new(config.META_APP_SECRET.encode(),encoded.encode(),hashlib.sha256).digest()
        if not hmac.compare_digest(decode(signature),expected): raise ValueError()
        payload=json.loads(decode(encoded))
        if not isinstance(payload, dict): raise ValueError()
        if payload.get('algorithm')!='HMAC-SHA256' or not payload.get('user_id'): raise ValueError()
    except (ValueError,TypeError):
        raise HTTPException(400,'Invalid signed deauthorization request.') from None
    issued_at = payload.get('issued_at')
    if type(issued_at) is not int or issued_at <= 0 or issued_at > datetime.now(timezone.utc).timestamp()+300:
        raise HTTPException(400, 'Invalid deauthorization timestamp.')
    event_id = hashlib.sha256(signed.encode()).hexdigest()[:32]
    if db.get(AuditEvent,event_id): return {'status':'ok','duplicate':True}
    event_time = datetime.fromtimestamp(issued_at,timezone.utc) + timedelta(seconds=1)
    subject=str(payload['user_id'])
    profiles=db.query(CandidateProfile).filter_by(meta_facebook_subject=subject).all()
    for profile in profiles:
        if not profile.meta_verified_at or aware(profile.meta_verified_at) <= event_time:
            clear_connection(db,profile)
    identities=db.query(SocialIdentity).filter_by(provider='facebook',app_id=config.META_APP_ID,subject=subject).all()
    for identity in identities:
        db.query(UserSession).filter(UserSession.user_id==identity.user_id,UserSession.created_at<=event_time).update({'is_revoked':True})
    db.add(AuditEvent(id=event_id,action='META_DEAUTHORIZED',details={'provider_subject':subject}))
    try: db.commit()
    except IntegrityError: db.rollback()
    return {'status':'ok'}
