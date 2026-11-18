import api from './api';

export const adminService = {
  async getDashboardStats() {
    const response = await api.get('/api/dashboard/stats');
    return response.data;
  },

  async listUsers(role = null) {
    const params = role ? { role } : {};
    const response = await api.get('/api/admin/users', { params });
    return response.data;
  },

  async createUser(userData) {
    const response = await api.post('/api/admin/users', userData);
    return response.data;
  },

  async updateUserStatus(userId, isActive) {
    const response = await api.patch(`/api/admin/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },

  async updateUserRole(userId, role, team = null) {
    const response = await api.patch(`/api/admin/users/${userId}/role`, { role, team });
    return response.data;
  },

  async listAuditLogs(limit = 100) {
    const response = await api.get('/api/admin/audit-logs', { params: { limit } });
    return response.data;
  },

  async listDocuments() {
    const response = await api.get('/api/knowledge/documents');
    return response.data;
  },

  async getDocumentContent(filename) {
    const response = await api.get(`/api/knowledge/documents/${filename}/content`);
    return response.data;
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async deleteDocument(filename) {
    const response = await api.delete(`/api/knowledge/documents/${filename}`);
    return response.data;
  },

  async reindexKnowledgeBase() {
    const response = await api.post('/api/knowledge/reindex');
    return response.data;
  },

  async searchKnowledgeBase(query, topK = 3) {
    const response = await api.post('/api/knowledge/search', { query, top_k: topK });
    return response.data;
  },

  async getSystemHealth() {
    const response = await api.get('/api/system/health');
    return response.data;
  },

  async getSettings() {
    const response = await api.get('/api/system/settings');
    return response.data;
  },

  async updateSettings(data) {
    const response = await api.post('/api/system/settings', data);
    return response.data;
  },
};

