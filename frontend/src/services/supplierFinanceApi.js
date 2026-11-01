import api from './api';

// ==========================================
// SUPPLIER FINANCE & ACCOUNTS PAYABLE API CLIENT
// ==========================================

export const getSupplierInvoices = async (params = {}) => {
  return await api.get('/api/v1/supplier-invoices', { params });
};

export const getSupplierInvoice = async (id) => {
  return await api.get(`/api/v1/supplier-invoices/${id}`);
};

export const createSupplierInvoice = async (data) => {
  return await api.post('/api/v1/supplier-invoices', data);
};

export const updateSupplierInvoiceStatus = async (id, data) => {
  return await api.patch(`/api/v1/supplier-invoices/${id}/status`, data);
};

export const getSupplierPayments = async (params = {}) => {
  return await api.get('/api/v1/supplier-payments', { params });
};

export const createSupplierPayment = async (data) => {
  return await api.post('/api/v1/supplier-payments', data);
};

export const allocateSupplierPayment = async (invoiceId, data) => {
  return await api.post(`/api/v1/supplier-invoices/${invoiceId}/allocations`, data);
};

export const directSupplierInvoicePayment = async (invoiceId, data) => {
  return await api.post(`/api/v1/supplier-invoices/${invoiceId}/payments`, data);
};

export const getProjectCosts = async (projectId) => {
  return await api.get(`/api/v1/projects/${projectId}/costs`);
};

export const createProjectCost = async (projectId, data) => {
  return await api.post(`/api/v1/projects/${projectId}/costs`, data);
};

export const getProjectProfitability = async (projectId) => {
  return await api.get(`/api/v1/projects/${projectId}/profitability`);
};
