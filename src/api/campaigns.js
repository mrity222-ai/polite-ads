import { apiFetch } from './client';

export const campaignsApi = {
  /**
   * Fetch all campaigns belonging to the authenticated candidate
   */
  getCampaigns() {
    return apiFetch('/api/campaigns', {
      method: 'GET',
    });
  },

  /**
   * Submit a new campaign draft for company review & Meta launch
   * @param {{
   *   title: string,
   *   whatsapp_phone: string,
   *   slogan: string,
   *   area: string,
   *   pincode: string,
   *   radius_km: number,
   *   budget_daily: number,
   *   template_id: number,
   *   symbol: string,
   *   photo_url?: string
   * }} payload
   */
  createCampaign(payload) {
    return apiFetch('/api/campaigns/create', {
      method: 'POST',
      body: payload,
    });
  },

  /**
   * Toggle campaign status between Live and Paused
   * Note: Campaigns under company review cannot be toggled.
   * @param {string} campaignId
   */
  toggleCampaignStatus(campaignId) {
    return apiFetch(`/api/campaigns/${encodeURIComponent(campaignId)}/toggle-status`, {
      method: 'POST',
    });
  },
};
