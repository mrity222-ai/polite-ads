import { apiFetch } from './client';
export const reviewsApi = {
  quote: budget => apiFetch(`/api/campaigns/pricing-quote?budget_daily=${encodeURIComponent(budget)}`),
  detail: id => apiFetch(`/api/campaigns/${encodeURIComponent(id)}/review`),
  revise: (id, body) => apiFetch(`/api/campaigns/${encodeURIComponent(id)}/revise`, { method: 'POST', body }),
  queue: (state, page = 1, search = '') => apiFetch(`/api/admin/review-campaigns?state=${encodeURIComponent(state)}&page=${page}&page_size=10&search=${encodeURIComponent(search)}`),
  history: (id, before) => apiFetch(`/api/campaigns/${encodeURIComponent(id)}/history?page_size=10${before ? `&before_version=${before}` : ''}`),
  revisionMedia: (id, version) => apiFetch(`/api/campaigns/${encodeURIComponent(id)}/history/${version}/media`),
  decide: (id, body) => apiFetch(`/api/admin/review-campaigns/${encodeURIComponent(id)}`, { method: 'POST', body }),
  release: (id, body) => apiFetch(`/api/admin/review-campaigns/${encodeURIComponent(id)}/release`, { method: 'POST', body }),
  policy: () => apiFetch('/api/admin/pricing-policy'),
  savePolicy: body => apiFetch('/api/admin/pricing-policy', { method: 'POST', body }),
};
