import api from './api';

// ==========================================
// CUSTOMER SELF-SERVICE PORTAL API CLIENT
// ==========================================

export const getMyCustomerProfile = async () => {
  return await api.get('/api/v1/customers/me');
};

export const updateMyCustomerProfile = async (data) => {
  return await api.put('/api/v1/customers/me', data);
};

export const getMyProjects = async (params = {}) => {
  return await api.get('/api/v1/projects', { params });
};

export const getMyQuotations = async (params = {}) => {
  return await api.get('/api/v1/quotations', { params });
};

export const acceptQuotation = async (id) => {
  return await api.post(`/api/v1/quotations/${id}/accept`);
};

export const rejectQuotation = async (id, rejectionReason) => {
  return await api.post(`/api/v1/quotations/${id}/customer-reject`, {
    rejection_reason: rejectionReason,
  });
};

export const getMyInvoices = async (params = {}) => {
  return await api.get('/api/v1/invoices', { params });
};

export const getMyPayments = async (params = {}) => {
  return await api.get('/api/v1/payments', { params });
};

export const getMyWarranties = async (params = {}) => {
  return await api.get('/api/v1/warranty', { params });
};

export const getMyServiceTickets = async (params = {}) => {
  return await api.get('/api/v1/service-tickets', { params });
};

export const createCustomerServiceTicket = async (data) => {
  return await api.post('/api/v1/service-tickets', data);
};

export const submitCustomerAcceptance = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/customer-acceptance`, data);
};

export const getMySubsidyApplications = async (params = {}) => {
  return await api.get('/api/v1/subsidy/applications', { params });
};

export const getMyEnquiries = async (params = {}) => {
  return await api.get('/api/v1/enquiries', { params });
};

export const createCustomerEnquiry = async (data) => {
  return await api.post('/api/v1/enquiries', data);
};

export const getMySurveys = async (params = {}) => {
  return await api.get('/api/v1/surveys', { params });
};

export const getMyDispatches = async (params = {}) => {
  return await api.get('/api/v1/dispatches', { params });
};
