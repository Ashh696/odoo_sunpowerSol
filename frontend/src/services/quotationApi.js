import api from './api';

// ==========================================
// QUOTATION ENGINE API
// ==========================================

/**
 * List quotations with search, status filtering, enquiry filtering, and pagination.
 */
export const getQuotations = async (params = {}) => {
  return await api.get('/api/v1/quotations', { params });
};

/**
 * Retrieve full quotation details including line items, pricing, customer/enquiry details, and revision history.
 */
export const getQuotation = async (id) => {
  return await api.get(`/api/v1/quotations/${id}`);
};

/**
 * Create a new quotation in DRAFT status (version 1).
 */
export const createQuotation = async (data) => {
  return await api.post('/api/v1/quotations', data);
};

/**
 * Update an existing DRAFT quotation.
 */
export const updateQuotation = async (id, data) => {
  return await api.put(`/api/v1/quotations/${id}`, data);
};

/**
 * Submit a DRAFT quotation for approval (transitions DRAFT -> PENDING_APPROVAL).
 */
export const submitQuotation = async (id) => {
  return await api.post(`/api/v1/quotations/${id}/submit`);
};

/**
 * Approve a quotation in review (transitions PENDING_APPROVAL -> APPROVED).
 */
export const approveQuotation = async (id, data = {}) => {
  return await api.post(`/api/v1/quotations/${id}/approve`, data);
};

/**
 * Reject a quotation in review (transitions PENDING_APPROVAL -> REJECTED).
 */
export const rejectQuotation = async (id, data) => {
  return await api.post(`/api/v1/quotations/${id}/reject`, data);
};

/**
 * Send an approved quotation to the customer (transitions APPROVED -> SENT, enquiry -> QUOTED).
 */
export const sendQuotation = async (id) => {
  return await api.post(`/api/v1/quotations/${id}/send`);
};

/**
 * Customer accepts quotation (transitions SENT -> ACCEPTED, enquiry -> WON).
 * For SUPER_ADMIN: acts as administrative acceptance on behalf of customer.
 */
export const acceptQuotation = async (id, data = {}) => {
  return await api.post(`/api/v1/quotations/${id}/accept`, data);
};

/**
 * Customer declines quotation (transitions SENT -> REJECTED).
 */
export const customerRejectQuotation = async (id, data) => {
  return await api.post(`/api/v1/quotations/${id}/customer-reject`, data);
};

/**
 * Revise a quotation (snapshots prior version to history, increments version, returns to DRAFT).
 */
export const reviseQuotation = async (id, data) => {
  return await api.post(`/api/v1/quotations/${id}/revise`, data);
};

/**
 * Delete a DRAFT quotation.
 */
export const deleteQuotation = async (id) => {
  return await api.delete(`/api/v1/quotations/${id}`);
};
