import api from './api';

// ==========================================
// PROJECT & HANDOVER API
// ==========================================

/**
 * List solar rooftop execution projects with filters and pagination.
 */
export const getProjects = async (params = {}) => {
  return await api.get('/api/v1/projects', { params });
};

/**
 * Retrieve full project details including Order, Customer, BOM items, Notes, and Tasks.
 */
export const getProject = async (id) => {
  return await api.get(`/api/v1/projects/${id}`);
};

/**
 * Operations handover: Initialize a Project from an eligible Order.
 * Requires 'projects.create' permission (SUPER_ADMIN, TECHNICAL_MANAGER).
 */
export const handoverProject = async (orderId, data = {}) => {
  return await api.post(`/api/v1/projects/orders/${orderId}/handover`, data);
};

/**
 * Update project dates, status, or assigned project manager.
 */
export const updateProject = async (id, data) => {
  return await api.put(`/api/v1/projects/${id}`, data);
};

/**
 * Add a site/technical/general note to a project.
 */
export const addProjectNote = async (id, data) => {
  return await api.post(`/api/v1/projects/${id}/notes`, data);
};
