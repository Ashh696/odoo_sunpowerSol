import api from './api';

// ==========================================
// FIELD TECHNICIAN MOBILE WORKLOAD API CLIENT
// ==========================================

export const getMyAssignedSurveys = async (params = {}) => {
  return await api.get('/api/v1/surveys', { params });
};

export const getMyInstallationSchedules = async (params = {}) => {
  return await api.get('/api/v1/installation-schedules', { params });
};

export const getMyInstallations = async (params = {}) => {
  return await api.get('/api/v1/installations', { params });
};

export const getMyServiceVisits = async (params = {}) => {
  return await api.get('/api/v1/service-visits', { params });
};

export const submitInstallationChecklist = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/checklists`, data);
};

export const submitInstallationTest = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/tests`, data);
};

export const recordTechnicianWorklog = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/worklogs`, data);
};

export const recordMaterialConsumption = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/consumption`, data);
};

export const completeTechnicianServiceVisit = async (visitId, data) => {
  return await api.patch(`/api/v1/service-visits/${visitId}/complete`, data);
};
