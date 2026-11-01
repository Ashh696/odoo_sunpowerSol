import api from './api';

// ==========================================
// DISPATCH & LOGISTICS API
// ==========================================

export const getProjectMaterialReadiness = async (projectId) => {
  return await api.get(`/api/v1/projects/${projectId}/material-readiness`);
};

export const createStockReservation = async (data) => {
  return await api.post('/api/v1/dispatches/reservations', data);
};

export const releaseStockReservation = async (reservationId) => {
  return await api.delete(`/api/v1/dispatches/reservations/${reservationId}`);
};

export const getDispatches = async (params = {}) => {
  return await api.get('/api/v1/dispatches', { params });
};

export const getDispatch = async (id) => {
  return await api.get(`/api/v1/dispatches/${id}`);
};

export const createDispatch = async (data) => {
  return await api.post('/api/v1/dispatches', data);
};

export const updateDispatchStatus = async (id, data) => {
  return await api.patch(`/api/v1/dispatches/${id}/status`, data);
};

export const confirmDelivery = async (id, data) => {
  return await api.post(`/api/v1/dispatches/${id}/delivery-confirm`, data);
};
