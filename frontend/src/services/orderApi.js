import api from './api';

// ==========================================
// ORDER MANAGEMENT API
// ==========================================

/**
 * List orders with search, status, customer, and pagination filters.
 */
export const getOrders = async (params = {}) => {
  return await api.get('/api/v1/orders', { params });
};

/**
 * Retrieve full order details including customer, quotation, project, and payments.
 */
export const getOrder = async (id) => {
  return await api.get(`/api/v1/orders/${id}`);
};

/**
 * Convert an accepted quotation into an order.
 * Requires 'orders.create' permission (SUPER_ADMIN).
 */
export const createOrder = async (data) => {
  return await api.post('/api/v1/orders', data);
};

/**
 * Update order execution status.
 */
export const updateOrderStatus = async (id, data) => {
  return await api.put(`/api/v1/orders/${id}/status`, data);
};

/**
 * Record an advance or milestone payment against an order.
 * Requires 'payments.record' permission (FINANCE_ACCOUNTS, SUPER_ADMIN).
 */
export const recordOrderPayment = async (id, data) => {
  return await api.post(`/api/v1/orders/${id}/payments`, data);
};
