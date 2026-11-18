import api from './api';

export const chatService = {
  async sendMessage(message, conversationHistory = [], sessionId = null) {
    const response = await api.post('/api/chat/message', {
      message,
      conversation_history: conversationHistory,
      session_id: sessionId,
    });
    return response.data;
  },

  async escalateToTicket(conversationHistory, title = null, deviceInfo = null) {
    const response = await api.post('/api/chat/escalate', {
      conversation_history: conversationHistory,
      title,
      device_info: deviceInfo,
    });
    return response.data;
  },

  async submitFeedback(rating, comments = '', sessionId = null, ticketId = null) {
    const response = await api.post('/api/chat/feedback', {
      rating,
      comments,
      session_id: sessionId,
      ticket_id: ticketId,
    });
    return response.data;
  },
};

