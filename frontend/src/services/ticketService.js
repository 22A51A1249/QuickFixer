import api from './api';

export const ticketService = {
  async listTickets(params = {}) {
    const response = await api.get('/api/tickets', { params });
    return response.data;
  },

  async createTicket(ticketData) {
    const response = await api.post('/api/tickets', ticketData);
    return response.data;
  },

  async getTicket(ticketId) {
    const response = await api.get(`/api/tickets/${ticketId}`);
    return response.data;
  },

  async getMessages(ticketId) {
    const response = await api.get(`/api/tickets/${ticketId}/messages`);
    return response.data;
  },

  async addMessage(ticketId, message) {
    const response = await api.post(`/api/tickets/${ticketId}/messages`, { message });
    return response.data;
  },

  async updateStatus(ticketId, data) {
    const response = await api.patch(`/api/tickets/${ticketId}/status`, data);
    return response.data;
  },

  async previewTriage(description) {
    const response = await api.post('/api/tickets/triage-preview', { description });
    return response.data;
  },

  async generateResolutionSummary(ticketId) {
    const response = await api.post(`/api/tickets/${ticketId}/generate-summary`);
    return response.data;
  },
};

