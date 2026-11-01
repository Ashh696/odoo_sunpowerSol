import api from './api';

// ==========================================
// REPORTS & ANALYTICS API SERVICE
// ==========================================

export const getExecutiveAnalytics = async (params = {}) => {
  return await api.get('/api/v1/analytics/executive', { params });
};

export const getSalesAnalytics = async (params = {}) => {
  return await api.get('/api/v1/analytics/sales', { params });
};

export const getProjectAnalytics = async (params = {}) => {
  return await api.get('/api/v1/analytics/projects', { params });
};

export const getInventoryAnalytics = async (params = {}) => {
  return await api.get('/api/v1/analytics/inventory', { params });
};

export const getFinanceAnalytics = async (params = {}) => {
  return await api.get('/api/v1/analytics/finance', { params });
};

export const getOperationsAnalytics = async () => {
  return await api.get('/api/v1/analytics/operations');
};

/**
 * Downloads authorized analytical tabular report as an Excel-compatible CSV file.
 */
export const downloadAnalyticsCSV = async (reportType, params = {}) => {
  const queryParams = new URLSearchParams({
    report_type: reportType,
    ...(params.date_from ? { date_from: params.date_from } : {}),
    ...(params.date_to ? { date_to: params.date_to } : {}),
  }).toString();

  const response = await api.get(`/api/v1/analytics/export?${queryParams}`, {
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.setAttribute('download', `sims_${reportType}_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
};
