import api from './api';

export const authService = {
  async login(usernameOrEmail, password, role = null, customId = null) {
    const response = await api.post('/api/auth/login', {
      username_or_email: usernameOrEmail,
      password: password,
      role: role,
      custom_id: customId,
    });
    return response.data;
  },

  async logout() {
    try {
      await api.post('/api/auth/logout');
    } catch (e) {
      console.warn('Logout API call notice:', e);
    } finally {
      sessionStorage.removeItem('quickfixer_token');
      sessionStorage.removeItem('quickfixer_user');
    }
  },

  async getMe() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

