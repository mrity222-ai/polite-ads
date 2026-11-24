import { apiFetch } from './client';

export const adminApi = {
  /**
   * Fetch all ads waiting in the review & quick-fix queue
   */
  getPendingReviews() {
    return apiFetch('/api/admin/pending-reviews', {
      method: 'GET',
    }).then(rows => rows.map(row => ({ ...row, candidateName: row.candidate_name, rawSlogan: row.original_slogan, enhancedSlogan: row.enhanced_slogan, correctionNote: row.correction_note })));
  },

  /**
   * Approve, polish slogan, adjust budget/radius, and push ad to Meta network
   * @param {{
   *   ad_id: string,
   *   enhanced_slogan: string,
   *   adjusted_budget?: number,
   *   adjusted_radius?: number,
   *   correction_note?: string
   * }} payload
   */
  enhanceAndPush(payload) {
    return apiFetch('/api/admin/enhance-and-push', {
      method: 'POST',
      body: payload,
    });
  },

  /**
   * Fetch all registered candidates in the directory
   */
  getCandidates() {
    return apiFetch('/api/admin/candidates', {
      method: 'GET',
    });
  },

  /**
   * Update candidate account status (Active | Suspended | Pending)
   * @param {string} candidateId
   * @param {string} status
   */
  updateCandidateStatus(candidateId, status) {
    return apiFetch(`/api/admin/candidates/${encodeURIComponent(candidateId)}/status`, {
      method: 'PATCH',
      body: { status },
    });
  },

  /**
   * Fetch company profit commission settings
   */
  getCommissionSettings() {
    return apiFetch('/api/admin/commission', {
      method: 'GET',
    });
  },

  /**
   * Update company profit commission percentage
   * @param {number} commissionPct
   */
  updateCommissionSettings(commissionPct) {
    return apiFetch('/api/admin/commission', {
      method: 'POST',
      body: { commission_pct: commissionPct },
    });
  },

  /**
   * Fetch all active subscription tiers
   */
  getSubscriptionPlans() {
    return apiFetch('/api/admin/subscriptions', {
      method: 'GET',
    });
  },

  /**
   * Create a new custom subscription plan
   * @param {{ name: string, price: number, daily_ad_limit: number, features: string[], badge?: string }} payload
   */
  createSubscriptionPlan(payload) {
    return apiFetch('/api/admin/subscriptions', {
      method: 'POST',
      body: payload,
    });
  },

  /**
   * Toggle subscription plan active status
   * @param {string} planId
   */
  toggleSubscriptionPlan(planId) {
    return apiFetch(`/api/admin/subscriptions/${encodeURIComponent(planId)}/toggle`, {
      method: 'PATCH',
    });
  },

  /**
   * Delete or archive a subscription plan
   * @param {string} planId
   */
  deleteSubscriptionPlan(planId) {
    return apiFetch(`/api/admin/subscriptions/${encodeURIComponent(planId)}`, {
      method: 'DELETE',
    });
  },

  /**
   * Fetch Meta Graph, WhatsApp, and AI gateway health status
   */
  getApiHealth() {
    return apiFetch('/api/admin/api-health', {
      method: 'GET',
    });
  },

  /**
   * Test live handshake with Meta Graph API
   */
  testMetaConnection() {
    return apiFetch('/api/admin/api-health/test-meta', {
      method: 'POST',
    });
  },

  /**
   * Fetch financial transactions and payout ledger
   */
  getTransactions() {
    return apiFetch('/api/admin/transactions', {
      method: 'GET',
    });
  },
  getFinanceSummary() {
    return apiFetch('/api/admin/finance-summary');
  },
};
