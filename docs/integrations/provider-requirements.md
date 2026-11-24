# Provider requirements — reviewed 27 October 2026

This is an implementation boundary record, not a certification of account eligibility or election compliance.

## Razorpay

The implementation follows the official order, payment-fetch, refund and webhook documentation:

- https://razorpay.com/docs/api/orders/create/
- https://razorpay.com/docs/api/payments/fetch-with-id/
- https://razorpay.com/docs/api/refunds/create-normal/
- https://razorpay.com/docs/webhooks/validate-test/

Real HTTP adapters exist. Tests intercept those HTTP requests; merchant acceptance, provider test credentials, capture/refund events and live settlement remain unverified. No claim is made that this business category is automatically accepted. Verify current merchant requirements with the provider before activation.

## Meta

Read-token and managed-page adapters exist; mock data is explicitly labeled. Live publication and delivery controls are unavailable and fail closed. Current account eligibility, official authorization/disclaimer process, permissions, supported API version, account ownership and political-ad restrictions must be verified for the actual operator before implementation/activation. A historical version string does not certify current support. There is no verified master agency account in this codebase.

## WhatsApp

Automated WhatsApp Business Platform political messaging is excluded. Official policy reference: https://business.whatsapp.com/policy . In-app notifications replace system alerts. Direct chat links do not establish a blanket legal/provider approval claim.
