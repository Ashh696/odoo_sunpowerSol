import api from './api';

// ==========================================
// 1. INSTALLATION SCHEDULES API
// ==========================================

export const getInstallationSchedules = async (params = {}) => {
  return await api.get('/api/v1/installation-schedules', { params });
};

export const createInstallationSchedule = async (data) => {
  return await api.post('/api/v1/installation-schedules', data);
};

export const updateInstallationScheduleStatus = async (id, data) => {
  return await api.patch(`/api/v1/installation-schedules/${id}/status`, data);
};

// ==========================================
// 2. MAIN INSTALLATIONS API
// ==========================================

export const getInstallations = async (params = {}) => {
  return await api.get('/api/v1/installations', { params });
};

export const getInstallation = async (id) => {
  return await api.get(`/api/v1/installations/${id}`);
};

export const createInstallation = async (data) => {
  return await api.post('/api/v1/installations', data);
};

export const updateInstallationStatus = async (id, data) => {
  return await api.patch(`/api/v1/installations/${id}/status`, data);
};

// ==========================================
// 3. CHECKLISTS API
// ==========================================

export const getInstallationChecklists = async (installationId) => {
  return await api.get(`/api/v1/installations/${installationId}/checklists`);
};

export const addChecklistItem = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/checklists`, data);
};

export const updateChecklistItem = async (checklistId, data) => {
  return await api.patch(`/api/v1/installations/checklists/${checklistId}`, data);
};

// ==========================================
// 4. WORKLOGS API
// ==========================================

export const submitTechnicianWorklog = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/worklogs`, data);
};

export const approveTechnicianWorklog = async (worklogId) => {
  return await api.post(`/api/v1/installations/worklogs/${worklogId}/approve`);
};

// ==========================================
// 5. ELECTRICAL TESTS API
// ==========================================

export const recordInstallationTest = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/tests`, data);
};

// ==========================================
// 6. MATERIAL CONSUMPTION API
// ==========================================

export const recordMaterialConsumption = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/materials`, data);
};

// ==========================================
// 7. CUSTOMER ACCEPTANCE API
// ==========================================

export const recordCustomerAcceptance = async (installationId, data) => {
  return await api.post(`/api/v1/installations/${installationId}/customer-acceptance`, data);
};
