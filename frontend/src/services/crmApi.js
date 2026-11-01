import api from './api';

// Customers API
export const getCustomers = async (params = {}) => {
  return await api.get('/api/v1/customers', { params });
};

export const getCustomer = async (id) => {
  return await api.get(`/api/v1/customers/${id}`);
};

export const createCustomer = async (data) => {
  return await api.post('/api/v1/customers', data);
};

export const updateCustomer = async (id, data) => {
  return await api.put(`/api/v1/customers/${id}`, data);
};

// Enquiries API
export const getEnquiries = async (params = {}) => {
  return await api.get('/api/v1/enquiries', { params });
};

export const getEnquiry = async (id) => {
  return await api.get(`/api/v1/enquiries/${id}`);
};

export const createEnquiry = async (data) => {
  return await api.post('/api/v1/enquiries', data);
};

export const updateEnquiry = async (id, data) => {
  return await api.put(`/api/v1/enquiries/${id}`, data);
};

export const updateEnquiryStatus = async (id, status, notes = '') => {
  return await api.put(`/api/v1/enquiries/${id}/status`, { status, notes });
};

export const assignEnquirySalesRep = async (id, assigned_sales_id) => {
  return await api.put(`/api/v1/enquiries/${id}/assign`, { assigned_sales_id });
};

// Followups API
export const getFollowups = async (params = {}) => {
  return await api.get('/api/v1/followups', { params });
};

export const createFollowup = async (data) => {
  return await api.post('/api/v1/followups', data);
};

export const completeFollowup = async (id, data) => {
  return await api.put(`/api/v1/followups/${id}/complete`, data);
};

export const rescheduleFollowup = async (id, scheduled_at, reason) => {
  return await api.put(`/api/v1/followups/${id}/reschedule`, { scheduled_at, reason });
};

// CRM Dashboard API
export const getCRMDashboard = async () => {
  return await api.get('/api/v1/crm/dashboard');
};

// Utility to fetch active sales employees for assignment dropdowns
export const getSalesEmployees = async () => {
  return await api.get('/api/v1/employees', { params: { is_active: true, limit: 100 } });
};
