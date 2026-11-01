import api from './api';

// ==========================================
// SUNPOWER SOLUTIONS SIMS - AUTHENTICATION API
// ==========================================

export const loginUser = async (email, password) => {
  return await api.post('/api/v1/auth/login', { email, password });
};

export const registerCustomer = async (data) => {
  return await api.post('/api/v1/auth/register', data);
};

export const getMe = async () => {
  return await api.get('/api/v1/auth/me');
};

export const changePassword = async (data) => {
  return await api.post('/api/v1/auth/change-password', data);
};

export const logoutUser = () => {
  localStorage.removeItem('access_token');
};

/**
 * Returns canonical destination dashboard path based on user role.
 */
export const getRoleDefaultPath = (roleSlug) => {
  switch (roleSlug) {
    case 'CUSTOMER':
      return '/portal';
    case 'FIELD_TECHNICIAN':
      return '/technician-tasks';
    case 'SALES':
      return '/crm';
    case 'TECHNICAL_MANAGER':
      return '/installations';
    case 'WAREHOUSE_PROCUREMENT':
      return '/procurement';
    case 'SERVICE_WARRANTY':
      return '/warranty';
    case 'FINANCE_ACCOUNTS':
      return '/invoices';
    case 'DIRECTOR':
      return '/analytics';
    case 'SUPER_ADMIN':
      return '/crm';
    default:
      return '/crm';
  }
};

/**
 * Allowed path whitelist per role for strict client-side route protection.
 * Backend authorization remains the ultimate security boundary.
 */
export const ROLE_ALLOWED_ROUTES = {
  CUSTOMER: [
    '/portal',
  ],
  FIELD_TECHNICIAN: [
    '/technician-tasks',
    '/surveys',
    '/installations',
    '/warranty',
    '/status',
    '/architecture',
  ],
  SALES: [
    '/crm',
    '/surveys',
    '/products',
    '/bom',
    '/quotations',
    '/orders',
    '/projects',
    '/subsidy',
    '/invoices',
    '/status',
    '/architecture',
  ],
  TECHNICAL_MANAGER: [
    '/surveys',
    '/products',
    '/bom',
    '/projects',
    '/installations',
    '/dispatch',
    '/technician-tasks',
    '/warranty',
    '/status',
    '/architecture',
  ],
  WAREHOUSE_PROCUREMENT: [
    '/procurement',
    '/dispatch',
    '/products',
    '/bom',
    '/orders',
    '/status',
    '/architecture',
  ],
  SERVICE_WARRANTY: [
    '/warranty',
    '/projects',
    '/products',
    '/status',
    '/architecture',
  ],
  FINANCE_ACCOUNTS: [
    '/invoices',
    '/orders',
    '/quotations',
    '/subsidy',
    '/analytics',
    '/status',
    '/architecture',
  ],
  DIRECTOR: [
    '/analytics',
    '/crm',
    '/surveys',
    '/products',
    '/bom',
    '/quotations',
    '/orders',
    '/projects',
    '/procurement',
    '/dispatch',
    '/installations',
    '/technician-tasks',
    '/warranty',
    '/subsidy',
    '/invoices',
    '/employees',
    '/status',
    '/architecture',
  ],
  SUPER_ADMIN: [
    '/crm',
    '/analytics',
    '/surveys',
    '/products',
    '/bom',
    '/quotations',
    '/orders',
    '/projects',
    '/procurement',
    '/dispatch',
    '/installations',
    '/technician-tasks',
    '/warranty',
    '/subsidy',
    '/invoices',
    '/employees',
    '/status',
    '/architecture',
    '/portal',
  ],
};

export const isRouteAllowedForRole = (roleSlug, pathname) => {
  if (!roleSlug) return false;
  const allowed = ROLE_ALLOWED_ROUTES[roleSlug] || [];
  return allowed.some((route) => pathname === route || pathname.startsWith(`${route}/`));
};
