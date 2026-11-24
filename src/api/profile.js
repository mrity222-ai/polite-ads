import { apiFetch } from './client';

export const profileApi = {
  /**
   * Fetch current candidate's profile
   */
  getProfile() {
    return apiFetch('/api/profile', {
      method: 'GET',
    });
  },

  /**
   * Update candidate's onboarding and campaign settings
   * @param {object} data - candidate profile fields
   */
  updateProfile(data) {
    return apiFetch('/api/profile', {
      method: 'PUT',
      body: data,
    });
  },

  /**
   * Upload candidate display photo
   * @param {File} file
   */
  uploadPhoto(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch('/api/profile/upload-photo', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Upload custom candidate election symbol
   * @param {File} file
   */
  uploadSymbol(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch('/api/profile/upload-symbol', {
      method: 'POST',
      body: formData,
    });
  },
};
