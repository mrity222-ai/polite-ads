"""Freeze business inputs; revalidate only credentials/ownership at execution time."""
import math
from datetime import datetime, timezone
import config
from entities import CandidateProfile
from integrations.meta.oauth import FacebookOAuth
from security_encryption import decrypt_token


def capture(db, campaign):
    p = db.query(CandidateProfile).filter_by(user_id=campaign.owner_id).one()
    lat, lng = float(p.lat), float(p.lng)
    if not math.isfinite(lat) or not math.isfinite(lng) or abs(lat) > 90 or abs(lng) > 180:
        raise ValueError('Valid approval coordinates are required.')
    return dict(lat=lat, lng=lng, page_id=p.meta_page_id or ('mock_page_'+campaign.owner_id if config.META_MOCK_MODE else None),
                instagram_id=p.instagram_account_id, facebook_subject=p.meta_facebook_subject,
                connection_generation=p.meta_connection_generation, disclaimer=p.disclaimer_text or '',
                special_ad_categories=['ISSUES_ELECTIONS_POLITICS'], simulation=config.META_MOCK_MODE)


def verify(db, campaign, payload):
    context = payload.get('publishing_context')
    if not context or any(key not in context for key in ('lat', 'lng', 'page_id', 'disclaimer', 'connection_generation')):
        raise ValueError('Complete approved publishing context required; legacy jobs need fresh review.')
    p = db.query(CandidateProfile).filter_by(user_id=campaign.owner_id).one()
    if p.meta_connection_generation != context['connection_generation'] or p.instagram_account_id != context.get('instagram_id'):
        raise ValueError('Approved connection changed; a fresh review is required.')
    current_page = p.meta_page_id or ('mock_page_'+campaign.owner_id if config.META_MOCK_MODE else None)
    if current_page != context['page_id'] or p.meta_facebook_subject != context.get('facebook_subject'):
        raise ValueError('Approved Page/account changed; publishing blocked.')
    if config.META_MOCK_MODE:
        if not context.get('simulation'):
            raise ValueError('A live approved payload cannot be executed in simulation mode.')
        return context
    if context.get('simulation') or not p.is_meta_connected or not p.meta_access_token_encrypted:
        raise ValueError('Verified live connection required.')
    try:
        client = FacebookOAuth()
        token = decrypt_token(p.meta_access_token_encrypted)
        data = client.inspect_token(token)
        now = datetime.now(timezone.utc).timestamp()
        if not data.get('is_valid') or str(data.get('app_id')) != str(config.META_APP_ID) or str(data.get('user_id')) != context['facebook_subject']:
            raise ValueError()
        if any(data.get(key) and data[key] <= now for key in ('expires_at', 'data_access_expires_at')):
            raise ValueError()
        needed = set(config.META_FACEBOOK_SCOPES)
        if context.get('instagram_id'):
            needed.update(config.META_INSTAGRAM_SCOPES)
        if needed - set(data.get('scopes', [])):
            raise ValueError()
        pages = client.pages(token, include_instagram=True)
        selected = next((page for page in pages if str(page['id']) == str(context['page_id'])), None)
        if not selected or not selected.get('access_token'):
            raise ValueError()
        if context.get('instagram_id') and str(selected.get('instagram_business_account', {}).get('id')) != str(context['instagram_id']):
            raise ValueError()
    except Exception:
        raise ValueError('Provider ownership/credential verification failed; reconnect and review again.') from None
    return context
