# Ad review, pricing and payments — 27 October 2026

Implemented with the user's explicit approval. Interface labels remain English; candidate screens remain light and the admin hub remains dark. No new poster upload, AI creation or AI editing option was added.

## Local workflow

1. Candidate opens **Launch New Ad**, fills the content and sees the server-calculated daily customer total, Meta allocation and company fee.
2. **Save Draft** keeps the ad out of the admin queue. **Submit for Review** requires acceptance of the displayed pricing snapshot.
3. Candidate uses **Ads Manager → View / Edit** to view statuses/history, edit, resubmit, or fund 1–365 whole daily budgets through checkout. Funding is a one-time payment, not a recurring debit.
4. Admin uses **Approvals Studio** to review individual posts, compare the original submission, edit supported fields, preview, and choose **Save Changes**, **Request Changes**, **Reject**, or **Approve & Queue**.
5. Approving requires an active owner, a current version, candidate-accepted pricing and verified campaign credit covering at least one daily customer total. The same database transaction reserves funds and creates the durable job.
6. Company approval, provider review and delivery statuses remain separate. A job ID is not proof of publication or delivery.

The editor supports title, caption, area, pincode, phone, radius, election symbol and existing layout; it previews the campaign's existing image. Admin cannot increase the customer's agreed total. Candidate revisions invalidate queued/failed jobs and release their unused reservations. Old submitted/processing jobs cannot be edited locally: provider pause/cancellation must first be implemented and confirmed. Live Meta publishing remains unavailable, so this release does not claim working live ad amendments.

## Pricing

**Profit Engine → Pricing & Margin Settings** supports percentage fee or fixed Meta daily allocation. For a customer total of ₹200, a ₹70 Meta allocation produces ₹130 company fee; ₹50 produces ₹150. These are allocation examples, not confirmed spend or a guarantee that Meta will accept that daily budget.

Policies have versions and affect new quotes. Existing campaign agreements retain their snapshot. Admin may propose a campaign allocation override; saving it sets **Changes Requested**, and the candidate must accept the revised breakdown and resubmit before approval. Review saves cannot bypass this consent step.

All stored amounts use integer paise. Invalid/negative/excess allocations, stale writes and duplicate approvals are rejected. Historical content/pricing and before/after audit records are retained. Campaign revision rows are append-only through the ORM.

## Checkout and refunds

The shared Razorpay checkout uses the server-returned public key, order ID, amount and currency. It loads the official checkout SDK when required. Success calls the backend, which checks the signature and fetches provider capture details; capture/webhook reconciliation remains idempotent. Mock mode displays a simulation notice and never fabricates a successful browser payment.

Provider setup follows the [official Razorpay integration documentation](https://github.com/razorpay/markdown-docs/blob/master/payments/payment-gateway/web-integration/standard/integration-steps.md). Keep `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET` on the backend. To test actual checkout, configure merchant test keys and the matching webhook secret, set `RAZORPAY_MOCK_MODE=false`, restart the backend, and complete a provider test payment. Real provider acceptance has **not** been performed here. Public webhook delivery requires a reachable deployment/tunnel configured in the provider dashboard; localhost remains the user's selected app configuration.

Campaign deposits stay customer credit. Approval reserves one daily customer total; the remainder remains available credit. There is no automatic multi-day spend scheduler or service-fee recognition yet. Actual provider spend, settlement, fee earning, continuous budget coverage and live provider minimum-budget validation must be completed before live spending is enabled.

For an approved job that has not entered provider submission, admin can **Return for Changes & Release Reserved Funds** with a reason. This cancels queued/failed jobs, records the event, and releases unused credit. It does not issue a gateway refund. **Payment Ledger → Refund available credit** requests a bounded provider refund with a unique operation ID. Campaign-reserved and already-refund-reserved money is excluded. Ambiguous refunds remain reserved and require provider reconciliation; do not create another refund for the same operation. Mock gateway rows do not offer a real refund button.

Payment receipts show actual captured amounts and their saved pricing breakdown. The old hardcoded GSTIN, tax calculations and regulatory-certification claims were removed. These are payment receipts, not certified tax invoices.

## Private administrator access

Public admin shortcuts, prefilled passwords and demo quick-login controls are removed. Ordinary candidate registration cannot choose an admin role or reserve a private username. The ordinary login form accepts the private configured username `super admin` plus the administrator's password. Backend admin permission remains mandatory.

The migration suspends existing admin accounts using known demo passwords and revokes their sessions. New demo seeding no longer creates an administrator. **A personal password must be entered locally**; it was not invented or printed by the agent.

For the existing seeded admin, from the project root:

```powershell
python backend/create_admin.py --email admin@politiads.com --mobile 9999999999 --name "Administrator" --username "super admin" --reset-existing
```

The command prompts privately for the new password twice, preserves the admin's ID and records, reactivates the account and revokes prior sessions. Use your actual existing admin email/mobile for another administrator. For a new administrator use a new email/mobile and omit `--reset-existing`. Existing candidate roles are never promoted by this command. MFA is not implemented in this release.

## Storage, verification and operational limits

- Migration: `697c642caf16`, following `8051cdb33264`.
- New storage: campaign revisions, pricing/approved snapshots, job version binding, fund reservations and private usernames.
- Existing SQLite database was upgraded after a successful trial-copy migration. Backup: `backend/data/backups/politiads-20261027T115801456344.db`. Historical table row counts stayed unchanged; foreign-key violations: zero.
- `python backend/run_tests.py`: 33 core + 27 OAuth + 13 review/financial boundary tests passed.
- `npm run lint`: passed with zero warnings. `npm run build`: passed.
- `python scratch/test_review_browser.py`: temporary migrated SQLite and headless Chrome verify the scoped flows. All provider domains are blocked; checkout success uses a guarded local fake provider and fake browser SDK. This is not merchant acceptance.
- Screenshots: `scratch/review_pricing_verified.png`, `scratch/review_mobile_verified.png`.

Restart any existing API process to load the new models/routes. Live Meta publication, provider pause/edit, real merchant checkout/refund/settlement, rolling daily budget funding and production activation remain unverified or unavailable. No real ad spend, external publication, customer charge or refund was initiated by this implementation task.

## Superseded daily funding and worker limits

The later approved system-design package replaces the earlier one-day-only reservation/no-lease implementation and adds expiry/refund-aware entitlements, full publishing context, paginated history and on-demand media. See [current system-design report](system-design-fixes.md). Actual report retrieval, provider pause/resume and live activation remain blocked/unverified; the local accounting port does not invent provider confirmation.
