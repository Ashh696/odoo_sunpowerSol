import api from './api';

// ==========================================
// 1. SUPPLIERS API
// ==========================================

export const getSuppliers = async (params = {}) => {
  return await api.get('/api/v1/suppliers', { params });
};

export const getSupplier = async (id) => {
  return await api.get(`/api/v1/suppliers/${id}`);
};

export const createSupplier = async (data) => {
  return await api.post('/api/v1/suppliers', data);
};

export const updateSupplier = async (id, data) => {
  return await api.put(`/api/v1/suppliers/${id}`, data);
};

export const updateSupplierStatus = async (id, isActive) => {
  return await api.patch(`/api/v1/suppliers/${id}/status`, { is_active: isActive });
};

// ==========================================
// 2. PURCHASE ORDERS API
// ==========================================

export const getPurchaseOrders = async (params = {}) => {
  return await api.get('/api/v1/purchase-orders', { params });
};

export const getPurchaseOrder = async (id) => {
  return await api.get(`/api/v1/purchase-orders/${id}`);
};

export const createPurchaseOrder = async (data) => {
  return await api.post('/api/v1/purchase-orders', data);
};

export const updatePurchaseOrder = async (id, data) => {
  return await api.put(`/api/v1/purchase-orders/${id}`, data);
};

export const issuePurchaseOrder = async (id) => {
  return await api.post(`/api/v1/purchase-orders/${id}/issue`);
};

export const cancelPurchaseOrder = async (id) => {
  return await api.post(`/api/v1/purchase-orders/${id}/cancel`);
};

// ==========================================
// 3. GOODS RECEIPTS (GRN) API
// ==========================================

export const getGoodsReceipts = async (params = {}) => {
  return await api.get('/api/v1/goods-receipts', { params });
};

export const getGoodsReceipt = async (id) => {
  return await api.get(`/api/v1/goods-receipts/${id}`);
};

export const getPOGoodsReceipts = async (poId) => {
  return await api.get(`/api/v1/purchase-orders/${poId}/goods-receipts`);
};

export const createGoodsReceipt = async (data) => {
  return await api.post('/api/v1/goods-receipts', data);
};

// ==========================================
// 4. WAREHOUSE INVENTORY & SHORTAGES API
// ==========================================

export const getWarehouseInventory = async (params = {}) => {
  return await api.get('/api/v1/inventory', { params });
};

export const getProductStockMovements = async (productId, params = {}) => {
  return await api.get(`/api/v1/inventory/${productId}/movements`, { params });
};

export const getProductSerials = async (productId, params = {}) => {
  return await api.get(`/api/v1/inventory/${productId}/serials`, { params });
};

export const getProjectMaterialShortages = async (projectId) => {
  return await api.get(`/api/v1/inventory/project-shortages/${projectId}`);
};
