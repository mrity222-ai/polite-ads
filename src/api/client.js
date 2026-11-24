/**
 * Centralized API Client for PolitiAds Frontend
 * Enforces session credentials, consistent JSON handling, and structured error formatting.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Perform an authenticated API request with cookie credentials
 * @param {string} endpoint - API path e.g. '/api/auth/me'
 * @param {RequestInit} options - fetch options
 * @returns {Promise<any>}
 */
export async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  const headers = { ...options.headers };

  // If body is an object and not FormData, serialize to JSON
  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  const config = {
    ...options,
    headers,
    body,
    credentials: 'include', // Automatically send HttpOnly politiads_session cookie
  };

  try {
    const method = (config.method || 'GET').toUpperCase();
    const isAuth = ['/api/auth/login', '/api/auth/register', '/api/auth/facebook/start', '/api/auth/super-admin/login'].includes(endpoint);
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && !isAuth) {
      const csrf = await fetch(`${API_BASE_URL}/api/auth/csrf`, { credentials: 'include' });
      if (!csrf.ok) {
        if ([401, 403].includes(csrf.status)) window.dispatchEvent(new CustomEvent('politiads:session-invalid', { detail: 'Session expired or account restricted.' }));
        throw new ApiError('Cannot authorize this change. Please check your session.', csrf.status);
      }
      config.headers['X-CSRF-Token'] = (await csrf.json()).csrf_token;
    }
    const response = await fetch(url, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    // Try parsing JSON response
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      if ([401, 403].includes(response.status) && !endpoint.startsWith('/api/auth/')) {
        // Admin permission errors do not invalidate an otherwise active candidate.
        if (response.status === 401 || String(data?.detail || '').includes('suspended')) window.dispatchEvent(new CustomEvent('politiads:session-invalid', { detail: data?.detail }));
      }
      // Extract human-readable error message
      let message = 'An error occurred while processing the request.';
      if (typeof data === 'object' && data !== null) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Pydantic validation errors
          message = data.detail.map((err) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`).join(', ');
        } else if (data.message) {
          message = data.message;
        }
      } else if (typeof data === 'string' && data.length > 0) {
        message = data;
      }

      throw new ApiError(message, response.status, data);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or connection failure
    throw new ApiError(
      'Unable to connect to the PolitiAds server. Please check your internet connection.',
      0,
      error
    );
  }
}
