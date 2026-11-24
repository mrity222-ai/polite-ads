# Remaining limitations — 27 October 2026

1. **Live Meta publication is blocked.** No fake IDs are returned in live write/status branches. Read-token/page adapters exist, but actual credentials, current permissions, authorization, account selection and provider acceptance remain unverified. Do not enable customer spending.
2. **Razorpay is not activated.** Real order/payment-fetch/refund HTTP adapters exist; contract tests used a fake transport. Merchant acceptance, credentials, test-mode provider runs, verified settlement and hosted checkout remain prerequisites. Shared browser checkout is now wired for campaigns and subscriptions, with server capture verification and no mock fast-activation; actual SDK/provider merchant acceptance remains unverified. See ad-review-and-payments.md.
3. **No WhatsApp Business Platform automation.** No political broadcasts are offered. In-app notifications are polled; they are not a WebSocket or instant delivery guarantee. Existing user-initiated chat links are not a blanket compliance certification.
4. **Journal history starts with this fix.** Historical ledger summary rows remain unchanged and are not double-entry proof. New captures debit provider receivable and credit candidate credit; refunds reverse them. Fee recognition, real advertising expense, settlement accounting, historical reconciliation and subscription fulfillment require explicit business rules. No escrow claim is made.
5. **Refund timeout is intentionally pending.** Do not blindly replay provider writes. Reconcile by provider payment/receipt before releasing a reservation or recording provider confirmation. No scheduler magically resolves unknown provider results.
6. **Publishing worker handles deterministic mock recovery.** Use one supervised process operationally; conditional claims prevent duplicate queued execution. Live ambiguous jobs require reconciliation; general live worker leasing is not implemented.
7. **Media uses validated data URLs.** Server validates upload and profile/campaign inline paths, re-encodes images and rejects malformed/oversized content. Object storage, file references and production CDN hosting remain future work.
8. **PostgreSQL is unverified.** ORM and migration structure support a future port; a driver, migration run and concurrent tests are still required. Financial upgrade downgrades refuse automatic history deletion.
9. **Deployment is unverified.** Review HTTPS/reverse-proxy trust, shared login-rate semantics, secret management, backup storage, retention, worker supervision, monitoring and provider access before release.
10. **UI verification is scoped.** Main desktop flows and 390px dashboard width passed. Other mobile devices, real GPS permission states, full accessibility and every admin tab have not been exhaustively tested. Simulator/pricing content is product presentation, not confirmed service availability.
11. **Ancillary polls/inquiries persist and are owner-scoped.** Inquiry storage is not fulfillment of field services, live survey delivery, or external messaging. Competitor feeds and AI generation are unavailable.

The application is not certified production-ready. Read docs/verification-report.md for exactly what ran.


Facebook/Instagram OAuth update: authorization, identity linking, Page and linked professional Instagram discovery/selection, and disconnect are implemented and tested locally. Existing app credentials are preserved, but real provider consent and Dashboard permissions are not verified. Localhost callback is explicitly selected by the user; a production HTTPS callback must later be registered in both places. The old manual-token UI and unverified manual Page fallback are removed. See integrations/facebook-instagram-setup.md.

Versioned moderation, prospective pricing/overrides with candidate consent, private admin login and one-day campaign fund reservations are now implemented and locally tested. Live provider amendments, rolling daily funding, actual Meta spend and fee recognition remain unavailable. See ad-review-and-payments.md for the current package boundaries and local admin password setup.

## Superseding system-design update

Independent subscription entitlements, immutable purchased-plan/publishing snapshots, individual/aggregate budget caps, daily funding/final-report accounting ports, leased worker recovery, bounded retries and paginated review/history/media are now implemented and locally verified. Earlier wording implying these local mechanisms are entirely absent is historical. Actual provider spend retrieval and pause/resume evidence, cash settlement, live activation, load and PostgreSQL verification remain outstanding. A local adapter contract test is not confirmation of real delivery or spend. See `system-design-fixes.md`.
