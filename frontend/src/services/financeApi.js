import api from './api';

// ==========================================
// FINANCE & INVOICING API CLIENT
// ==========================================

/**
 * List commercial milestone invoices with search, status, type, and pagination filters.
 */
export const getInvoices = async (params = {}) => {
  return await api.get('/api/v1/invoices', { params });
};

/**
 * Retrieve full invoice details including line items, allocations, customer and order context.
 */
export const getInvoice = async (id) => {
  return await api.get(`/api/v1/invoices/${id}`);
};

/**
 * Retrieve all invoices belonging to a specific customer Order.
 */
export const getOrderInvoices = async (orderId) => {
  return await api.get(`/api/v1/orders/${orderId}/invoices`);
};

/**
 * Generate a new milestone or advance invoice against an eligible Order.
 * Requires 'invoices.create' permission (SUPER_ADMIN, FINANCE_ACCOUNTS).
 */
export const createInvoice = async (data) => {
  return await api.post('/api/v1/invoices', data);
};

/**
 * Allocate cash from an existing completed Payment receipt to an outstanding Invoice.
 * Requires 'payments.record' permission (SUPER_ADMIN, FINANCE_ACCOUNTS).
 */
export const allocatePaymentToInvoice = async (invoiceId, data) => {
  return await api.post(`/api/v1/invoices/${invoiceId}/allocations`, data);
};

/**
 * Directly record customer payment towards an Invoice, creating receipt and allocation atomically.
 * Requires 'payments.record' permission (SUPER_ADMIN, FINANCE_ACCOUNTS).
 */
export const recordDirectInvoicePayment = async (invoiceId, data) => {
  return await api.post(`/api/v1/invoices/${invoiceId}/payments`, data);
};

/**
 * List customer payment receipts and allocations.
 * Requires 'payments.read' permission.
 */
export const getPayments = async (params = {}) => {
  return await api.get('/api/v1/payments', { params });
};
