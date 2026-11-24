# Facebook login and Facebook/Instagram connection setup

Implemented for localhost. This document contains no real credentials. Existing App ID/App Secret values in backend/.env were preserved. No Facebook account consent, advertising publication, payment or live spending was performed during verification.

## Local configuration

Backend reads `backend/.env`. The following public settings have been added/configured:

```dotenv
META_OAUTH_ENABLED=true
META_MOCK_MODE=false
META_APP_ID=<your-existing-meta-app-id>
META_APP_SECRET=<your-existing-meta-app-secret>
META_OAUTH_GRAPH_VERSION=v24.0
META_OAUTH_REDIRECT_URI=http://localhost:5173/api/meta/oauth/callback
META_BUSINESS_CONFIG_ID=
META_FACEBOOK_SCOPES=pages_show_list,pages_read_engagement,ads_management,ads_read
FRONTEND_ORIGIN=http://localhost:5173
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

The real file retains existing secret values, not the placeholders above. `META_OAUTH_GRAPH_VERSION` is a configurable connection API pin; it is separate from legacy publishing `META_GRAPH_VERSION` and is not a claim that the latest Meta version/app configuration has been certified. Confirm the version supported by the actual app when configuring it. Instagram authorization adds `instagram_basic` to the configured connection scopes.

Restart the backend after changing environment values. Start frontend on **http://localhost:5173**, not a different host/port. Use the same browser for authorization start and callback. Vite forwards `/api` to the backend on port 8000.

## Required Meta Dashboard configuration

Adding credentials locally cannot grant provider permissions or approve an app. In the actual Meta app:

1. Configure its Facebook Login product/use case for the intended login and business asset connection flows.
2. Register **exactly** `http://localhost:5173/api/meta/oauth/callback` in the OAuth redirect allowlist used by that app/configuration. Do not use a hash route, port 8000, a trailing slash, or 127.0.0.1 unless both application configuration and the registered callback are changed to match.
3. If the chosen Facebook Login for Business setup requires a configuration ID, enter its ID in `META_BUSINESS_CONFIG_ID`. Keep requested/granted permissions consistent with the configured scopes.
4. Confirm app mode, authorized test/developer accounts, and required permission/access approval for the actual users. These account-specific settings have not been inspected or verified here.
5. Connect only Pages managed by the authorizing account. For this Facebook-based Instagram flow, select an eligible professional Instagram account linked to that Page. Personal Instagram login is not implemented.

Official references (Meta pages may require access/sign-in):
- https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/

No exact approval duration or automatic provider acceptance is promised.

## User flow

- **Continue with Facebook on Login/Register:** browser opens the real Facebook authorization URL. The server exchanges the returned code, verifies token/application/subject, maps an app-scoped Facebook identity, and establishes an HttpOnly app session. No demo credentials are used.
- **Existing email account:** Facebook login never silently takes over an account with the same email. Log in with the existing password first, then explicitly Connect Facebook to link both identities.
- **New Facebook-only account:** may have no provider-supplied email/mobile. It starts as an incomplete candidate profile. Complete required onboarding fields and provide a valid phone when submitting a campaign; no fake phone number is assigned.
- **Connect Facebook:** authorize Page/ad-read permissions and explicitly select an owned Page. Empty Page results are an error/permission state; manual unverified IDs are rejected.
- **Connect Instagram:** after Facebook selection, authorize the additional scope if needed, verify the linked Instagram ID and username, and explicitly select it. It does not become connected merely because a Facebook Page was selected.
- **Disconnect Instagram:** clears Instagram connection only; Facebook remains usable.
- **Disconnect Facebook/all:** clears selected Page, Instagram, encrypted grant/Page tokens and metadata. Pending authorization callbacks become invalid and queued publishing jobs are stopped. It does not delete social accounts, remove the separate Facebook sign-in identity, or pause externally running ads.
- **Remove Meta app permissions:** an authenticated `/api/meta/revoke` operation is available and requires provider confirmation. Meta's signed deauthorization callback also clears grants and revokes relevant old sessions. Local disconnect remains available when the integration kill-switch is on.

## Security and storage

State is random, expires in ten minutes, is stored hashed, is single-use, and is bound to an HttpOnly browser nonce and the initiating app session for connection. Switching app accounts, logout, disconnect, replay or expired requests are rejected. Browser APIs never return user/Page tokens; tokens are encrypted with Fernet. Existing email is not used as proof of account ownership. Callback query parameters are redacted from Uvicorn access logs. Signed deauthorization is verified and replay-protected.

Database revision `8051cdb33264` adds social identities, OAuth attempts, and per-profile Facebook/Instagram metadata. User email/mobile can be nullable for authentic Facebook-only accounts; password registration still requires validated contact fields. The existing database was backed up and upgraded through the copy-first management workflow.

## Domain change later

Set an HTTPS FRONTEND_ORIGIN and matching META_OAUTH_REDIRECT_URI, enable Secure cookies, and update the exact callback in Meta Dashboard. Also configure a public HTTPS deauthorization endpoint `/api/meta/deauthorize`; Meta's server cannot deliver that callback to your localhost. The signed-handler behavior is tested locally, but real callback delivery is not.

## Verification

```powershell
python backend/run_tests.py
python scratch/test_oauth_browser.py
npm run build
python -m alembic check
```

- 33 existing backend regressions and 27 dedicated OAuth tests pass in isolated migrated databases.
- 8 OAuth UI checks pass using a local provider simulator; real Facebook/Instagram domains were blocked during this browser test.
- Real account consent, Meta Dashboard settings/permissions, Graph API acceptance and production deployment remain unverified.
- Live ad publishing is still separately blocked; enabling OAuth does not enable spending.
