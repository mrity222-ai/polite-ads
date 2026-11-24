# Test/live activation checklist

- [x] Local migrated SQLite and scoped regression checks.
- [x] Browser login/onboarding/draft flows through proxy and CSRF.
- [x] Mock/live boundaries; no synthetic live publishing success.
- [x] Payment capture/refund HTTP contract checks using test transport.
- [ ] Actual merchant eligibility and provider test credentials confirmed.
- [ ] Real hosted checkout and provider sandbox capture/refund verification.
- [ ] External ownership, fee recognition, refund rules and settlement reconciliation agreed.
- [ ] Meta permissions, current requirements, authorization and actual publishing implementation completed.
- [ ] HTTPS, independent secrets, demo credentials disabled, proxy trust and operational monitoring reviewed.
- [ ] PostgreSQL/production infrastructure verified if selected.
- [ ] Explicit campaign/payment amount and live action reviewed before any external spending.

Unchecked items are blockers, not completed work. No live payment, refund, publication, or external message was performed during this fix.
