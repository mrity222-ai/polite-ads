"""Facebook Login and Page/Instagram discovery. Never returns tokens to the browser."""
import re
import hashlib
import hmac
from urllib.parse import urlencode, urlsplit
import httpx
import config

class MetaAuthorizationError(Exception):
    def __init__(self, code='provider_unavailable'):
        self.code = code
        super().__init__(code)

class FacebookOAuth:
    def __init__(self):
        self.base = 'https://graph.facebook.com/' + config.META_OAUTH_GRAPH_VERSION

    def validate_configuration(self):
        if not config.META_OAUTH_ENABLED:
            raise MetaAuthorizationError('oauth_disabled')
        if config.META_MOCK_MODE:
            raise MetaAuthorizationError('mock_mode')
        if not config.META_APP_ID or config.META_APP_ID.startswith('mock_') or not config.META_APP_SECRET or config.META_APP_SECRET.startswith('mock_'):
            raise MetaAuthorizationError('configuration_required')
        if not re.fullmatch(r'v[0-9]{1,3}\.[0-9]{1,2}', config.META_OAUTH_GRAPH_VERSION):
            raise MetaAuthorizationError('configuration_required')
        uri = urlsplit(config.META_OAUTH_REDIRECT_URI)
        if uri.query or uri.fragment or not uri.netloc or (uri.scheme != 'https' and not (config.APP_ENV != 'production' and uri.scheme == 'http' and uri.hostname in ('localhost', '127.0.0.1'))):
            raise MetaAuthorizationError('invalid_callback_url')

    def authorization_url(self, state, purpose):
        self.validate_configuration()
        scopes = ['public_profile', 'email'] if purpose == 'login' else list(config.META_INSTAGRAM_SCOPES if purpose == 'instagram' else config.META_FACEBOOK_SCOPES)
        params = dict(client_id=config.META_APP_ID, redirect_uri=config.META_OAUTH_REDIRECT_URI,
                      response_type='code', state=state, scope=','.join(scopes))
        if purpose != 'login':
            params['auth_type'] = 'rerequest'
            if config.META_BUSINESS_CONFIG_ID:
                params.update(config_id=config.META_BUSINESS_CONFIG_ID, override_default_response_type='true')
        return 'https://www.facebook.com/' + config.META_OAUTH_GRAPH_VERSION + '/dialog/oauth?' + urlencode(params)

    def _call(self, path, token=None, params=None, method='GET'):
        self.validate_configuration()
        headers = {}
        values = dict(params or {})
        if token:
            headers['Authorization'] = 'Bearer ' + token
            values['appsecret_proof'] = hmac.new(config.META_APP_SECRET.encode(), token.encode(), hashlib.sha256).hexdigest()
        try:
            with httpx.Client(timeout=15, follow_redirects=False) as client:
                response = client.request(method, self.base + path, params=values if method == 'GET' else None,
                                          data=values if method != 'GET' else None, headers=headers)
                payload = response.json()
                if not isinstance(payload, dict):
                    raise MetaAuthorizationError()
                if response.status_code >= 400 or 'error' in payload:
                    code = payload.get('error', {}).get('code')
                    raise MetaAuthorizationError('authorization_expired' if code == 190 else 'provider_permissions_or_request')
                if not isinstance(payload, dict):
                    raise MetaAuthorizationError()
                return payload
        except MetaAuthorizationError:
            raise
        except (httpx.HTTPError, ValueError, TypeError):
            raise MetaAuthorizationError() from None

    def exchange_code(self, code):
        response = self._call('/oauth/access_token', params=dict(client_id=config.META_APP_ID,
            client_secret=config.META_APP_SECRET, redirect_uri=config.META_OAUTH_REDIRECT_URI, code=code), method='POST')
        token = response.get('access_token')
        if not token:
            raise MetaAuthorizationError('token_exchange_failed')
        # A rejected long-lived exchange is not silently treated as a durable connection.
        return self._call('/oauth/access_token', params=dict(grant_type='fb_exchange_token',client_id=config.META_APP_ID,
            client_secret=config.META_APP_SECRET, fb_exchange_token=token), method='POST')

    def inspect_token(self, token):
        data = self._call('/debug_token', params={'input_token':token}, token=config.META_APP_ID+'|'+config.META_APP_SECRET).get('data', {})
        if not data.get('is_valid') or str(data.get('app_id')) != config.META_APP_ID or not data.get('user_id'):
            raise MetaAuthorizationError('invalid_token')
        return data

    def identity(self, token):
        data = self._call('/me', token=token, params={'fields':'id,name,email'})
        if not data.get('id'):
            raise MetaAuthorizationError('identity_missing')
        return data

    def pages(self, token, include_instagram=False):
        fields = 'id,name,tasks,access_token'
        if include_instagram:
            fields += ',instagram_business_account{id,username}'
        pages, after = [], None
        for _ in range(20):
            params = dict(fields=fields, limit=100)
            if after: params['after'] = after
            response = self._call('/me/accounts', token=token, params=params)
            pages.extend(response.get('data', []))
            paging = response.get('paging', {})
            if not paging.get('next'): return pages
            after = paging.get('cursors', {}).get('after')
            if not after: break
        raise MetaAuthorizationError('too_many_pages')

    def instagram(self, page_token, instagram_id):
        return self._call('/' + str(instagram_id), token=page_token, params={'fields':'id,username'})

    def revoke(self, token, subject):
        response = self._call('/' + str(subject) + '/permissions', token=token, method='DELETE')
        if response.get('success') is not True:
            raise MetaAuthorizationError('revocation_unconfirmed')
