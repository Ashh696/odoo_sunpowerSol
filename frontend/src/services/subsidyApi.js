import api from './api';

// ==========================================
// SUBSIDY & DISCOM LIAISON API CLIENT
// ==========================================

export const getSubsidyApplications = async (params = {}) => {
  return await api.get('/api/v1/subsidy/applications', { params });
};

export const getSubsidyApplication = async (id) => {
  return await api.get(`/api/v1/subsidy/applications/${id}`);
};

export const createSubsidyApplication = async (data) => {
  return await api.post('/api/v1/subsidy/applications', data);
};

export const updateSubsidyStatus = async (id, data) => {
  return await api.patch(`/api/v1/subsidy/applications/${id}/status`, data);
};

export const uploadSubsidyDocument = async (id, data) => {
  return await api.post(`/api/v1/subsidy/applications/${id}/documents`, data);
};

export const verifySubsidyDocument = async (docId, data) => {
  return await api.patch(`/api/v1/subsidy/documents/${docId}/verify`, data);
};

export const recordSubsidyDisbursement = async (id, data) => {
  return await api.post(`/api/v1/subsidy/applications/${id}/disbursements`, data);
};
