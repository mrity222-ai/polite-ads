import { apiFetch } from './client';

export const authApi = {
  /**
   * Register a new candidate user
   * @param {{ full_name, mobile, email, password, confirm_password }} data
   */
  register(data) {
    return apiFetch('/api/auth/register', {
      method: 'POST',
      body: data,
    });
  },

  /**
   * Login user by email or mobile
   * @param {{ login, password }} credentials
   */
  login(credentials) {
    return apiFetch('/api/auth/login', {
      method: 'POST',
      body: credentials,
    });
  },

  /**
   * Login Super Administrator through dedicated restricted portal
   * @param {{ login, password }} credentials
   */
  superAdminLogin(credentials) {
    return apiFetch('/api/auth/super-admin/login', {
      method: 'POST',
      body: credentials,
    });
  },

  /**
   * Get currently authenticated user details & session
   */
  getMe() {
    return apiFetch('/api/auth/me', {
      method: 'GET',
    });
  },

  /**
   * Terminate active session and clear cookie
   */
  logout() {
    return apiFetch('/api/auth/logout', {
      method: 'POST',
    });
  },
};
