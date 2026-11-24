import { apiFetch } from './client';

export const integrationsApi = {
  // --- Meta Marketing API ---
  getMetaStatus() {
    return apiFetch('/api/meta/status', { method: 'GET' });
  },

  startFacebookLogin() {
    return apiFetch('/api/auth/facebook/start', { method: 'POST' });
  },

  startMetaAuthorization(target = 'facebook') {
    return apiFetch('/api/meta/oauth/start', { method: 'POST', body: { target } });
  },

  getMetaAssets(target = 'facebook') {
    return apiFetch(`/api/meta/assets?target=${encodeURIComponent(target)}`);
  },

  selectInstagramAccount(pageId) {
    return apiFetch('/api/meta/instagram/select', { method: 'POST', body: { page_id: pageId } });
  },

  selectMetaPage(pageId, pageName) {
    return apiFetch('/api/meta/select-page', {
      method: 'POST',
      body: { page_id: pageId, page_name: pageName }
    });
  },

  disconnectMeta(target = 'all') {
    return apiFetch('/api/meta/disconnect', { method: 'POST', body: { target } });
  },

  // --- Payments (Razorpay) ---
  createPaymentOrder(itemType, itemId, customBudgetPaise = null) {
    return apiFetch('/api/payments/create-order', {
      method: 'POST',
      body: {
        item_type: itemType,
        item_id: itemId,
        custom_budget_paise: customBudgetPaise
      }
    });
  },

  verifyPayment(orderId, paymentId, signature, method = 'upi') {
    return apiFetch('/api/payments/verify', {
      method: 'POST',
      body: {
        razorpay_order_id: orderId,
        razorpay_payment_id: paymentId,
        razorpay_signature: signature,
        payment_method: method
      }
    });
  },

  getPaymentHistory() {
    return apiFetch('/api/payments/history', { method: 'GET' });
  },

  // --- Dynamic Single-Source Plans & Invoices ---
  getPublicPlans() {
    return apiFetch('/api/plans', { method: 'GET' });
  },

  getSubscriptionStatus() {
    return apiFetch('/api/billing/subscription-status', { method: 'GET' });
  },

  getInvoices() {
    return apiFetch('/api/billing/invoices', { method: 'GET' });
  },

  // --- In-App Notifications ---
  getNotifications() {
    return apiFetch('/api/notifications', { method: 'GET' });
  },

  markNotificationRead(notifId) {
    return apiFetch(`/api/notifications/${encodeURIComponent(notifId)}/read`, { method: 'PATCH' });
  },

  markAllNotificationsRead() {
    return apiFetch('/api/notifications/mark-all-read', { method: 'POST' });
  },

  // --- Admin Integrations Controls ---
  getPublishingJobs() {
    return apiFetch('/api/admin/publishing-jobs', { method: 'GET' });
  },

  retryPublishingJob(jobId) {
    return apiFetch(`/api/admin/publishing-jobs/${encodeURIComponent(jobId)}/retry`, { method: 'POST' });
  },

  getRecentWebhooks() {
    return apiFetch('/api/admin/webhooks', { method: 'GET' });
  },

  toggleKillSwitch(enabled) {
    return apiFetch('/api/admin/emergency-kill-switch', {
      method: 'POST',
      body: { enabled }
    });
  },

  processRefund(paymentId, amountInr, reason, operationId) {
    return apiFetch('/api/admin/refunds/process', {
      method: 'POST',
      body: { payment_id: paymentId, amount_inr: amountInr, reason, operation_id: operationId }
    });
  }
};
