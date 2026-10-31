import api from './api';

// Authentication APIs
export const loginUser = async (email, password) => {
  return await api.post('/api/v1/auth/login', { email, password });
};

export const getMe = async () => {
  return await api.get('/api/v1/auth/me');
};

// Employee APIs
export const fetchEmployees = async (params = {}) => {
  return await api.get('/api/v1/employees', { params });
};

export const fetchEmployeeById = async (id) => {
  return await api.get(`/api/v1/employees/${id}`);
};

export const createEmployee = async (data) => {
  return await api.post('/api/v1/employees', data);
};

export const updateEmployee = async (id, data) => {
  return await api.put(`/api/v1/employees/${id}`, data);
};

export const toggleEmployeeStatus = async (id, data) => {
  return await api.patch(`/api/v1/employees/${id}/status`, data);
};

// Department APIs
export const fetchDepartments = async (params = {}) => {
  return await api.get('/api/v1/departments', { params });
};

export const fetchDepartmentById = async (id) => {
  return await api.get(`/api/v1/departments/${id}`);
};

export const createDepartment = async (data) => {
  return await api.post('/api/v1/departments', data);
};

export const updateDepartment = async (id, data) => {
  return await api.put(`/api/v1/departments/${id}`, data);
};

export const fetchDepartmentEmployees = async (id) => {
  return await api.get(`/api/v1/departments/${id}/employees`);
};

// Skills APIs
export const fetchSkills = async (params = {}) => {
  return await api.get('/api/v1/skills', { params });
};

export const createSkill = async (data) => {
  return await api.post('/api/v1/skills', data);
};

export const updateSkill = async (id, data) => {
  return await api.put(`/api/v1/skills/${id}`, data);
};

export const fetchEmployeeSkills = async (empId) => {
  return await api.get(`/api/v1/employees/${empId}/skills`);
};

export const assignEmployeeSkill = async (empId, data) => {
  return await api.post(`/api/v1/employees/${empId}/skills`, data);
};

export const removeEmployeeSkill = async (empId, skillId) => {
  return await api.delete(`/api/v1/employees/${empId}/skills/${skillId}`);
};

// Certification APIs
export const fetchEmployeeCertifications = async (empId) => {
  return await api.get(`/api/v1/employees/${empId}/certifications`);
};

export const addEmployeeCertification = async (empId, data) => {
  return await api.post(`/api/v1/employees/${empId}/certifications`, data);
};

export const updateCertification = async (id, data) => {
  return await api.put(`/api/v1/certifications/${id}`, data);
};

export const fetchExpiringCertifications = async (params = {}) => {
  return await api.get('/api/v1/certifications/expiring', { params });
};
