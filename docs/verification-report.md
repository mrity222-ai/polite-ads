# Verification report — 27 October 2026

## Executed checks

| Check | Result | Scope |
| --- | --- | --- |
| Backend regression suite | 33/33 passed | Isolated SQLite created through real Alembic migrations; no external provider calls. |
| Clean-environment verification | Passed | New Windows/Python 3.14 virtual environment, locked dependencies installed, all 33 tests passed. |
| Headless browser regression | Passed | 11 reported checks: candidate login/dashboard render, refresh restore, signup, onboarding save/restore, draft submission via Vite+CSRF, mobile dashboard width, admin hub, admin approval/queue, worker mock/paused result, failed/successful logout, and no uncaught JS exceptions. |
| Source lint | Passed, zero warnings | `npm run lint` checks `src`; historical scratch JSX fragments excluded from source lint. |
| Production frontend build | Passed | Bundle compilation; not evidence of live service operations. |
| Python compilation | Passed | Backend syntax compilation. |
| Fresh migrations and Alembic model comparison | Passed | No new upgrade operations detected. |
| Existing development database migration | Passed | Backup and trial-copy upgrade first; original upgraded to b9bdaf69e9fe. Old table row counts unchanged; zero FK violations. |

## Regression coverage

The maintained `backend/test_regressions.py` covers bad signatures (including the old `invalid` bypass), amount/currency mismatch, header event IDs, duplicate/concurrent captures, atomic failure/retry, one capture per order, bounded/idempotent/concurrent refunds, timeout reservation, balanced append-only journal lines, ownership/RBAC/suspension, expiry/logout, CSRF/origin checks, login throttling, image/inline-upload validation, queued publishing, kill-switch, mock/live boundaries, provider page ownership, onboarding restoration, persistent owner-scoped ancillary records, and Razorpay HTTP contract tests with MockTransport.

## Limits

- No real Meta publication, provider approval, merchant payment/refund, or settlement was performed.
- Razorpay network calls were intercepted by a test transport; this is not provider sandbox acceptance.
- Live Meta write/status-control implementation remains unavailable and fails closed.
- PostgreSQL, a full mobile device matrix, real GPS permission scenarios, and exhaustive keyboard/accessibility verification were not executed.
- Browser checks use the existing Selenium/Chrome installation; the clean backend environment check does not install a browser.
- This is application verification, not an independent penetration-test or compliance certification.

Historical 35/11/10-check claims have been superseded. Their scripts remain archived for review; compatibility commands run the same maintained suite and must not be added together as separate test counts.


## Facebook/Instagram OAuth update

27 October 2026: 33 existing backend regressions plus 27 dedicated OAuth regressions pass in separate isolated processes/databases. The OAuth suite covers state/nonce binding, expiry/replay, session/account switching, identity conflicts and same-email protection, owned Page selection, Instagram permission/identity verification, separate/full disconnect, signed deauthorization replay, token-free browser responses and callback log redaction.

8 browser OAuth checks passed against an entirely local provider simulator: Facebook authorize/callback/Page selection; refresh persistence; separate Instagram authorize/selection; Instagram disconnect preserving Facebook; Facebook disconnect; fresh reconnect; social sign-in mapping to the linked local identity; no uncaught UI errors. Real Facebook/Instagram domains were blocked during this test. This is not evidence of actual provider approval/consent.

At the OAuth checkpoint, schema head was 8051cdb33264 and lint reported seven warnings. This historical checkpoint is superseded by the moderation/pricing package below: schema head 697c642caf16 and zero lint warnings.

## Latest approved moderation/pricing package

- 33 core, 27 OAuth and 13 dedicated review tests pass through `python backend/run_tests.py` (73 total).
- Dedicated tests cover pricing consent, 200/70 and 200/50 splits, prospective settings, stale edits, owner isolation, duplicate approvals, fund reservations/refund exclusion, release/reapproval, worker version binding and private admin login.
- Frontend build and lint pass with zero warnings.
- Migration head is `697c642caf16`; backup/trial-copy upgrade completed, old table row counts preserved, zero foreign-key violations.
- See `ad-review-and-payments.md` for browser evidence, fake-provider boundaries and remaining provider activation dependencies. These checks do not certify live merchant transactions or Meta publication.

The latest review browser run passed seven check groups: candidate creation/edit/resubmission; private admin/no-funds/save/request-changes; candidate corrections and mock-payment refusal; fake-SDK checkout with backend signature/capture verification; verified funds/queue/release; fixed-Meta allocation arithmetic; mobile width/no uncaught browser errors. All provider domains were blocked.

## Latest system design correction package

97 maintained tests passed: 33 core, 27 OAuth, 13 review and 24 system-design tests. New coverage includes expired/refunded access, immutable purchased plans, concurrent aggregate caps, frozen targeting, credential/ownership preflight contracts, daily settlement/refund bounds, unknown spend, funding rollover, stale/expired worker leases, bounded retries, paginated history, scoped media and legacy migration.

Eleven browser check groups passed with provider domains blocked, including saved-image loading, queue pagination/search and an expired-access screen showing zero entitlement. Build/lint are clean; migration head `48ab8d5a2bd0` matches ORM models. Existing table row counts stayed unchanged and FK checks returned zero violations. See `system-design-fixes.md` for backup paths, screenshots and limitations.
