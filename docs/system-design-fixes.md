# System design fixes — 27 October 2026

The user approved four local implementation packages. This report supersedes earlier limitations about subscriptions, one-day-only accounting, incomplete publishing context, worker leases and unbounded review responses. It does not certify live provider operations.

## 1. Purchased subscriptions and limits

- `subscriptions` records are separate from payment records and mutable plan catalog rows.
- An order saves the original plan price, features, daily customer budget cap, 30-day duration and renewal rule before capture. Capture activates that saved agreement exactly once.
- Access requires both an active record and a valid start/end window. Expiry takes effect at the backend immediately, even if a page remains open. An expired trial also has zero entitlement.
- A fully processed refund revokes the corresponding purchase. Partial refunds retain the original access; they do not extend validity or silently prorate it. Refunding a replacement does not reactivate a superseded purchase.
- Renewal rule: a new verified purchase replaces access immediately for 30 days. Unused time is not carried forward. The billing checkout displays this rule before proceeding.
- Create, edit, campaign funding checkout and approval enforce the saved cap and active-owner status. Approval also checks the aggregate customer daily totals of other approved, unfinished campaigns, using an owner-row write to serialize concurrent approvals.
- Trial cap: ₹500 customer daily total, for 30 days from account creation. Trial access does not establish real Meta eligibility or provider service availability.
- Legacy subscription payments lacking their original plan snapshot become `review_required`; full refunds become `revoked`. No historical agreement is invented from today's catalog. These records require original purchase evidence before a business reconciliation can restore access.

Core code: `backend/services/subscriptions.py`, payment/reconciliation routers and campaign review services.

## 2. Approved publishing input

Each new job freezes campaign content, existing image, location coordinates, radius, Page, Instagram identity, connection generation/subject, disclaimer, existing political category setting, pricing, duration and billing timezone. The first reserved billing date is recorded too. Tokens never enter this snapshot or browser response.

Execution uses the saved business payload, so changing a profile's location or disclaimer after approval cannot change the approved ad. Connection identity/generation and active-owner checks occur before stages; a disconnect or account change blocks further stages. The live preflight port rechecks token validity, app/subject, permissions and Page/Instagram ownership. Contract tests use a fake provider.

Legacy jobs without the complete payload require fresh review. Actual live Meta writes remain blocked before provider execution; credentials, ad-account selection, political eligibility, live budget minimums and provider acceptance still require a separate integration release. This package does not claim that an ad has been delivered or amended on Meta.

## 3. Daily funding and accounting

Campaign duration is 1–365 days. The billing calendar is explicitly `Asia/Kolkata`; `tzdata` is listed for Windows. Provider account/report timezone alignment must be verified before live activation.

```text
Verified customer credit
    → daily customer-total reservation
    → verified FINAL provider spend + confirmed provider pause
    → actual Meta expense + proportional earned fee
    → unused credit released
```

Each funding day stores its campaign version, local date, timezone, customer total, Meta allocation, planned fee, final expense, earned fee and state. Payments separately track refund reservations, campaign reservations and consumed amounts; consumed or still-reserved credit cannot be refunded or reserved again.

Fee rule: `planned company fee × verified final Meta spend / Meta allocation`, rounded half up to integer paise. For ₹200 customer total, ₹70 Meta allocation and ₹130 planned fee, confirmed full ₹70 spend earns ₹130; half of that Meta spend earns half the fee. A deposit or unknown delivery earns no fee automatically.

`settle_verified_day` accepts only the internal `VerifiedSpendConfirmation` adapter type. It validates the exact completed billing period, ad, INR amount, final-report flag and provider pause evidence. There is **no public/admin endpoint to type in or invent provider spend**. The caller owns commit/rollback. A real provider adapter must independently verify evidence before invoking this port; it is not implemented or activated here.

Final reports are idempotent and append-only. The admin ledger summary reads verified settled-day totals, showing unknown amounts as not reconciled/not recognized instead of treating deposits as spend or revenue. Settlement consumes reserved funds, writes balanced customer-credit/Meta-payable/service-revenue journal lines, and releases the unused remainder. Provider overspend creates a reconciliation audit event and keeps funds reserved rather than making the balance negative. Unknown or unfinished reports do not authorize release.

The worker checks due campaigns in bounded batches. A next current-calendar day can be funded only after the previous day has verified final settlement and sufficient credit/entitlement. Funding alone never resumes Meta delivery. Missing funds show `Funding Required`; unknown provider delivery shows `Reconciliation Required`. An expired, never-submitted reservation can be returned by admin for review/release. Missed calendar days require review rather than being backdated automatically.

Actual Meta report retrieval, provider pause/resume confirmation, bank settlement and production daily budget scheduling are still integration dependencies. Local ledger tests use temporary databases and fabricated test-provider evidence, not real spend.

## 4. Worker and review performance

- A durable worker claim carries an owner token, 90-second lease, heartbeat, attempt count and next-attempt time. A stale owner cannot renew or overwrite another owner's claim.
- Attempts/stages persist separately. Only explicitly safe transient operations use bounded exponential retries, with a maximum of three attempts. An ambiguous live write must be reconciled, not blindly retried.
- Expired simulation leases can be recovered. Expired live claims move to `Reconciliation Required`. The compatibility `--recover-mock` flag no longer forces active workers' leases back into the queue.
- Review queue API returns paginated summaries, at most 50 per page; UI uses 10. Search supports candidate, title and ad ID. One selected card loads detailed content.
- History uses version-cursor pagination, 10 initially and at most 50 per request. Historical image data is stored separately from the snapshot JSON and deferred in list/history queries. An owner/admin-only endpoint loads a saved image on demand.
- Queue/owner/subscription indexes were added. Bounded response behavior is tested; large-scale load, PostgreSQL and multi-host deployment are not certified.

API changes: `/api/admin/review-campaigns` now returns `{items,total,page,page_size,has_more}`. Existing frontend consumers and tests were updated. History and media endpoints enforce the same owner/admin permissions as campaign detail.

## Database upgrade and verification

- Migration `b04322338644`: entitlements, daily funding, provider evidence and leased attempts.
- Migration `48ab8d5a2bd0`: move historical revision media into deferred storage without dropping content.
- Both upgrades were first tested on a database copy and backed up before upgrading the local database.
- Backups: `backend/data/backups/politiads-20261027T171928623509.db` and `backend/data/backups/politiads-20261027T173720447293.db`.
- Historical table row counts remained unchanged; zero SQLite foreign-key violations. The legacy migration test also verifies that old payment/media records survive and missing agreements do not gain paid access.
- Maintained suites: 33 core + 27 OAuth + 13 review + 24 system-design tests = 97 tests passed.
- `npm run lint`: passed, zero warnings. `npm run build`, Python compilation and Alembic model comparison passed.
- Headless browser: eleven check groups passed with external provider domains blocked. Includes fake-SDK checkout, review/resubmission, saved-media loading, funds/release, fixed allocation, mobile width, pagination/search and expired-access UI.
- Browser artifacts: `scratch/system_design_queue_verified.png`, `scratch/system_design_expired_verified.png`, `scratch/review_mobile_verified.png`.

Restart any already-running API and worker processes to load this code/schema. Do not run a production build concurrently with browser verification against the dev server; generated HTML may cause a Vite reload.

No real customer charge, gateway refund, external publication, ad spend or deployment was initiated. Real provider acceptance, evidence adapters, delivery controls, operational monitoring and deployment verification remain prerequisites for production activation.
