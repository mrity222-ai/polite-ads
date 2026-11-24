# Operations runbook

## Startup and schema

Run Alembic migrations before the API; startup refuses an outdated schema. It never auto-seeds or creates tables. Development seeding is an explicit command and is disabled in production. Provision a real admin with `backend/create_admin.py` and a privately entered password.

## SQLite upgrade/restore

Stop API and workers. Use `python backend/manage_db.py --existing-sqlite backend/data/politiads.db`; it backs up via SQLite's backup API, upgrades a trial copy, checks schema/foreign keys, then upgrades the original. Do not run upgrade concurrently with live writes.

Backups are timestamped in `backend/data/backups/`. Restore only with services stopped: preserve the current file separately, restore the selected backup, then run migrations/checks against a copy before activating it. Automatic destructive downgrade is intentionally refused. Retain backups outside the deployment volume according to an explicit retention policy.

## Publishing

Run `python backend/worker.py` separately from the API. Company approval queues work; a successful HTTP response is not provider publication. The current worker only simulates provider creation. Live Meta writes fail closed.

Activate `/api/admin/emergency-kill-switch` with `{"enabled":true}` as an authenticated admin with CSRF protection. It blocks publishing jobs and Meta read routes. It does not pause existing external ads or reverse already completed payments. Interrupted jobs are not silently replayed. After stopping all workers, `python backend/worker.py --recover-mock --once` can recover deterministic interrupted mock jobs. Live ambiguous writes require provider reconciliation.

## Payment events

Configure `POST /api/webhooks/razorpay` with a separate webhook secret. It requires signature validation over raw bytes and `X-Razorpay-Event-Id`; body IDs are not substituted. `payment.captured` needs payment ID, order ID, integer amount, currency, and captured status. A failed receipt remains unprocessed and returns a non-success HTTP response so it can be retried.

Use admin `GET /api/admin/webhooks` to inspect failures. After fixing the underlying condition, `POST /api/admin/webhooks/{event_id}/retry` reprocesses a stored verified event. Replay does not accept modified payloads, nor create a second credit. Unsupported event types are acknowledged without fabricating financial activity; authoritative capture is `payment.captured` or a verified provider payment fetch.

## Refunds

Admin `POST /api/admin/refunds/process` requires payment_id, positive amount_inr (at most two decimal places), reason and a stable unique operation_id. Reuse that operation ID for an HTTP retry. Do not generate a new ID when the result is uncertain.

Pending and processed refunds reserve balance; failed refunds release their reservation. Provider timeout leaves a pending record. This is intentional. Reconcile against provider payment/refund records before any manual resolution; never issue a second refund to probe status. Verified refund.processed/refund.failed events update existing reservations and append reversal journal entries exactly once. A refund.created event alone does not establish completion.

## Accounting

New captured money is candidate credit, not recognized fees or confirmed Meta spend. Paired journal debit/credit lines balance per payment/refund transaction. ORM accounting records are append-only and have one-sided/uniqueness constraints. Database operators can still change records directly; restrict those privileges. Historical summary rows are retained, not retroactively certified.

## Session and production configuration

Cookie-authenticated unsafe requests require `X-CSRF-Token`; fetch it from `/api/auth/csrf`. Foreign browser origins are rejected. Logout revokes server state; UI reports a failure if the request cannot be confirmed. Suspension revokes sessions and blocks further access.

Production requires APP_ENV=production, HTTPS FRONTEND_ORIGIN, COOKIE_SECURE=true, independent secrets, and removal/disablement of active default-password accounts. Review trusted proxy forwarding and shared throttling/retention before deployment. Test credentials and mock flags must remain visibly separate from real-provider operation.
