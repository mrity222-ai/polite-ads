# PolitiAds

Candidate draft submission and company review application: React 19/Vite, FastAPI, SQLAlchemy, Alembic, and SQLite.

**Status — 27 October 2026:** Local security/data-integrity fixes and browser workflows verified. Live Meta publication is unavailable and fails closed. Razorpay HTTP adapters are implemented and tested with an in-process fake provider; no real merchant transaction or refund has been performed. This is not a production certification.

## Requirements

- Node compatible with Vite: `^20.19.0 || >=22.12.0`; verified here with Node 24.13.1.
- Python 3.14 on Windows was verified. Python 3.11+ is intended but not independently tested.
- SQLite is verified. PostgreSQL operation remains unverified; configure its driver and test migrations before use.

## Backend setup — project root, PowerShell

```powershell
cd "D:\a\polite ads"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item backend/.env.example backend/.env
.\.venv\Scripts\python.exe -m alembic upgrade head
# Optional DEVELOPMENT demo accounts only; never auto-run on server startup.
.\.venv\Scripts\python.exe backend/seed.py
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

`requirements.lock.txt` is the tested Windows/Python 3.14 snapshot. `requirements.txt` lists portable direct dependencies; another OS/Python version needs its own installation verification. The backend explicitly loads `backend/.env`; process environment takes precedence. Relative SQLite paths resolve from `backend/`.

API: http://127.0.0.1:8000/ — API schema: http://127.0.0.1:8000/docs

### Existing database

Stop API and workers before upgrading. Do not blindly stamp or recreate an existing schema.

```powershell
.\.venv\Scripts\python.exe backend/manage_db.py --existing-sqlite backend/data/politiads.db
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

The management command creates a SQLite backup, verifies/upgrades a copy first, and only then upgrades the original. It checks an unversioned legacy baseline before stamping. Unknown schemas fail rather than being silently reset. This release upgraded the local development database to `48ab8d5a2bd0`; old-table row counts were preserved and SQLite foreign-key checks passed. Backups are in `backend/data/backups/`.

### Admin provisioning

Development seeding creates candidate demos only. Public quick-login controls are removed. Known demo admin passwords are disabled; the review migration suspends affected administrators and revokes their sessions. Seeded candidate records are historical demos, not real delivery. Production disables seeding and refuses active known default passwords.

For a new administrator, use interactive password entry:

```powershell
.\.venv\Scripts\python.exe backend/create_admin.py --email admin@example.com --mobile 9999999999 --name "Administrator"
```

The private username defaults to `super admin`. To rotate the existing seeded administrator password, use `--email admin@politiads.com --mobile 9999999999 --name "Administrator" --reset-existing`; enter the new password privately when prompted. Existing candidate roles are never promoted by this command.

## Frontend — separate terminal, project root

```powershell
npm ci
npm run dev
```

Use Vite's printed URL, normally http://localhost:5173/. `/api` is proxied to the backend. The root `.env.example` documents optional overrides. Frontend variables are public: never place provider secrets in `VITE_*` values.

## Publishing worker — separate backend terminal

```powershell
.\.venv\Scripts\python.exe backend/worker.py
# Or process the current queue once:
.\.venv\Scripts\python.exe backend/worker.py --once
```

Company approval commits campaign/review/job together. It does not publish inside the HTTP request. The worker claims queued jobs through a database conditional update. Mock jobs retain stage IDs and never become real Live delivery. After stopping all workers, interrupted deterministic mock jobs can be requeued with `--recover-mock`. Real ambiguous provider operations require reconciliation, not automatic replay. Live Meta writes remain intentionally blocked.

## Verification

```powershell
npm run lint
npm run build
.\.venv\Scripts\python.exe -m unittest discover -s backend -p test_regressions.py -v
```

Browser verification additionally requires Selenium, Chrome, and an available ChromeDriver:

```powershell
python scratch/test_browser_regressions.py
```

It starts isolated API/Vite processes on free ports and uses a temporary migrated database. It does not test against development accounts/data. The backend suite also creates an isolated migrated database.

Old `test_final_audit.py`, `test_verification.py`, and `test_integrations.py` commands delegate to the maintained suite; they are not independent 35/11/10-check certifications. Original scripts are retained in `docs/archived-tests/`, because their old Live/mock assertions and unsafe default-database integration checks are obsolete.

## Security and financial boundaries

- Argon2id passwords, hashed opaque session records, HttpOnly cookies, session revocation, role/ownership checks, CSRF protection and trusted browser origins.
- Auth endpoints have database-backed per-client throttling. Production proxy trust/IP handling and edge limits need deployment review.
- Production requires secure cookies, HTTPS frontend origin and independent encryption/session secrets. No real provider credentials are included.
- Captures verify order, amount, currency and status. Signature alone does not prove capture.
- Webhooks read `X-Razorpay-Event-Id`, verify the raw body, retain failures and allow explicit retry.
- Refunds reserve balance before provider requests. Pending/processed refunds count toward the limit. Timeout retains a pending reservation.
- New deposits/refunds create balanced debit/credit journal lines. Deposits are customer credit, not earned fees or Meta spend. Older summary rows are preserved without fabricating journal history.
- Accounting records are append-only through ORM services; privileged direct database access is outside that boundary.
- Uploaded/inline images are decoded, size-limited and re-encoded on the server. Images remain validated data URLs in SQLite, not object-store uploads.

See [verification report](docs/verification-report.md), [limitations](docs/known-limitations.md), [operations](docs/operations.md), and [project guide](PROJECT_STATUS_AI_GUIDE.md).


## Facebook login / Facebook and Instagram connections

Real browser authorization code flow is implemented; manual token paste and demo-social login are removed. Facebook Page and linked professional Instagram selection are separate, verified operations. Local connection disconnect does not delete external social accounts or start/stop externally running ads.

See [Facebook/Instagram setup](docs/integrations/facebook-instagram-setup.md) for the localhost callback, environment keys and Meta Dashboard steps. Existing credentials are retained in backend/.env. Account-side permissions/approval and real consent remain unverified; no claim of live provider acceptance is made.

Run `python backend/run_tests.py` for both isolated suites (33 regressions + 27 OAuth tests), and `python scratch/test_oauth_browser.py` for the 8 local-simulator browser checks. New schema head: `8051cdb33264`. Existing database upgrade was backed up and trialed first. The prior zero-warning lint result is historical; current unrelated billing/landing/admin modules report seven warnings, while the build passes.

## Versioned ad review and pricing

Candidate drafts/editing, individual admin decisions, prospective percentage/fixed-Meta pricing, customer consent, fund reservations, real-checkout wiring and bounded refund controls are implemented locally. See [workflow and private admin setup](docs/ad-review-and-payments.md) for usage, verification and explicit live-provider limitations.

## System design fixes

Expiry/refunds now control independent subscription entitlements; purchases retain immutable plan snapshots. Campaign budgets enforce individual and aggregate limits. Approved jobs freeze the full publishing context. Daily reservations/settlement, leased worker recovery, paginated reviews/history and on-demand historical media are implemented locally. See [system design report](docs/system-design-fixes.md) for the fee/renewal rules, migration backups, 97-test verification and remaining live-provider dependencies.
