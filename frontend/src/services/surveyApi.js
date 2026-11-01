import api from './api';

// 1. Survey Directory & Details
export const getSurveys = async (params = {}) => {
  return await api.get('/api/v1/surveys', { params });
};

export const getSurvey = async (id) => {
  return await api.get(`/api/v1/surveys/${id}`);
};

// 2. Schedule New Survey
export const scheduleSurvey = async (data) => {
  return await api.post('/api/v1/surveys', data);
};

// 3. Technical Observations Update
export const updateSurveyObservations = async (id, data) => {
  return await api.put(`/api/v1/surveys/${id}`, data);
};

// 4. Survey Submission
export const submitSurvey = async (id) => {
  return await api.put(`/api/v1/surveys/${id}/submit`);
};

// 5. Technical Approval / Review Decision
export const reviewSurvey = async (id, data) => {
  return await api.post(`/api/v1/surveys/${id}/review`, data);
};

// 6. File Attachments
export const uploadSurveyAttachment = async (id, file) => {
  const formData = new FormData();
  formData.append('file', file);
  return await api.post(`/api/v1/surveys/${id}/attachments`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getSurveyAttachments = async (id) => {
  return await api.get(`/api/v1/surveys/${id}/attachments`);
};

// 7. Helpers for dropdown lookups
export const getActiveSurveyors = async () => {
  return await api.get('/api/v1/employees', { params: { is_active: true, limit: 100 } });
};

export const getEligibleEnquiries = async (params = {}) => {
  return await api.get('/api/v1/enquiries', {
    params: {
      limit: 100,
      ...params,
    },
  });
};
