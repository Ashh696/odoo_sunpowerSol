import api from './api';

// ==========================================
// WARRANTY & SERVICE MANAGEMENT API CLIENT
// ==========================================

export const getWarrantyPolicies = async () => {
  return await api.get('/api/v1/warranty/policies');
};

export const createWarrantyPolicy = async (data) => {
  return await api.post('/api/v1/warranty/policies', data);
};

export const getWarrantyRecords = async (params = {}) => {
  return await api.get('/api/v1/warranty/records', { params });
};

export const getWarrantyRecord = async (id) => {
  return await api.get(`/api/v1/warranty/records/${id}`);
};

export const registerProjectWarranties = async (projectId, data = {}) => {
  return await api.post(`/api/v1/projects/${projectId}/warranty-register`, data);
};

export const getServiceTickets = async (params = {}) => {
  return await api.get('/api/v1/service-tickets', { params });
};

export const getServiceTicket = async (id) => {
  return await api.get(`/api/v1/service-tickets/${id}`);
};

export const createServiceTicket = async (data) => {
  return await api.post('/api/v1/service-tickets', data);
};

export const updateServiceTicketStatus = async (id, data) => {
  return await api.patch(`/api/v1/service-tickets/${id}/status`, data);
};

export const scheduleServiceVisit = async (ticketId, data) => {
  return await api.post(`/api/v1/service-tickets/${ticketId}/visits`, data);
};

export const completeServiceVisit = async (visitId, data) => {
  return await api.patch(`/api/v1/service-visits/${visitId}/complete`, data);
};

export const replaceComponentUnderWarranty = async (ticketId, data) => {
  return await api.post(`/api/v1/service-tickets/${ticketId}/replacements`, data);
};

export const confirmServiceTicketResolution = async (ticketId, data) => {
  return await api.post(`/api/v1/service-tickets/${ticketId}/confirm`, data);
};

export const getWarrantySLAMetrics = async () => {
  return await api.get('/api/v1/warranty/sla-metrics');
};

export const getServiceVisits = async (params = {}) => {
  return await api.get('/api/v1/service-visits', { params });
};
