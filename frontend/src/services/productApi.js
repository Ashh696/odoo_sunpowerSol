import api from './api';

// 1. Product Directory & Details
export const getProducts = async (params = {}) => {
  return await api.get('/api/v1/products', { params });
};

export const getProduct = async (id) => {
  return await api.get(`/api/v1/products/${id}`);
};

// 2. Create Product
export const createProduct = async (data) => {
  return await api.post('/api/v1/products', data);
};

// 3. Update Product
export const updateProduct = async (id, data) => {
  return await api.put(`/api/v1/products/${id}`, data);
};

// 4. Activate / Deactivate Product
export const updateProductStatus = async (id, isActive) => {
  return await api.patch(`/api/v1/products/${id}/status`, { is_active: isActive });
};
