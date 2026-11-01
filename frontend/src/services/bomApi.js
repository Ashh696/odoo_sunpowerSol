import api from './api';

// ==========================================
// BOM TEMPLATES API
// ==========================================

/**
 * List BOM templates with search, filtering (system_type, capacity_kw, is_active), and pagination.
 */
export const getBomTemplates = async (params = {}) => {
  return await api.get('/api/v1/bom/templates', { params });
};

/**
 * Retrieve full details of a BOM template including all component lines.
 */
export const getBomTemplate = async (id) => {
  return await api.get(`/api/v1/bom/templates/${id}`);
};

/**
 * Create a new master BOM template (optionally with component items).
 */
export const createBomTemplate = async (data) => {
  return await api.post('/api/v1/bom/templates', data);
};

/**
 * Update BOM template header metadata.
 */
export const updateBomTemplate = async (id, data) => {
  return await api.put(`/api/v1/bom/templates/${id}`, data);
};

/**
 * Activate or deactivate a BOM template.
 */
export const updateBomTemplateStatus = async (id, isActive) => {
  return await api.patch(`/api/v1/bom/templates/${id}/status`, { is_active: isActive });
};

// ==========================================
// BOM TEMPLATE ITEMS API
// ==========================================

/**
 * Add a component line to an existing BOM template.
 */
export const addBomTemplateItem = async (templateId, itemData) => {
  return await api.post(`/api/v1/bom/templates/${templateId}/items`, itemData);
};

/**
 * Update a component line within a BOM template.
 */
export const updateBomTemplateItem = async (templateId, itemId, itemData) => {
  return await api.put(`/api/v1/bom/templates/${templateId}/items/${itemId}`, itemData);
};

/**
 * Remove a component line from a BOM template.
 */
export const deleteBomTemplateItem = async (templateId, itemId) => {
  return await api.delete(`/api/v1/bom/templates/${templateId}/items/${itemId}`);
};

// ==========================================
// PROJECT BOM API
// ==========================================

/**
 * Retrieve project BOM items and cost summary for a project.
 */
export const getProjectBom = async (projectId) => {
  return await api.get(`/api/v1/projects/${projectId}/bom`);
};

/**
 * Generate project BOM lines by cloning an active master template.
 */
export const generateProjectBom = async (projectId, templateId) => {
  return await api.post(`/api/v1/projects/${projectId}/bom/generate`, { template_id: templateId });
};

/**
 * Adjust the planned quantity of a project BOM item.
 */
export const updateProjectBomItemQuantity = async (projectId, itemId, plannedQuantity) => {
  return await api.put(`/api/v1/projects/${projectId}/bom/items/${itemId}`, {
    planned_quantity: plannedQuantity,
  });
};
