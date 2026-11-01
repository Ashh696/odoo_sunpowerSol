import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { checkHealth } from './services/api';
import { getMe, getRoleDefaultPath, isRouteAllowedForRole, logoutUser } from './services/authApi';
import AuthBar from './components/AuthBar';
import AccessDenied from './components/AccessDenied';
import LoginPage from './pages/LoginPage';
import CustomerSignUpPage from './pages/CustomerSignUpPage';
import CustomerPortalPage from './pages/CustomerPortalPage';
import FieldTechnicianTasksPage from './pages/FieldTechnicianTasksPage';
import CRMManagementPage from './pages/CRMManagementPage';
import SurveyManagementPage from './pages/SurveyManagementPage';
import ProductManagementPage from './pages/ProductManagementPage';
import BOMManagementPage from './pages/BOMManagementPage';
import QuotationManagementPage from './pages/QuotationManagementPage';
import OrderManagementPage from './pages/OrderManagementPage';
import ProjectManagementPage from './pages/ProjectManagementPage';
import ProcurementManagementPage from './pages/ProcurementManagementPage';
import DispatchManagementPage from './pages/DispatchManagementPage';
import InstallationManagementPage from './pages/InstallationManagementPage';
import ServiceWarrantyManagementPage from './pages/ServiceWarrantyManagementPage';
import SubsidyManagementPage from './pages/SubsidyManagementPage';
import InvoiceManagementPage from './pages/InvoiceManagementPage';
import AnalyticsDashboardPage from './pages/AnalyticsDashboardPage';
import EmployeeManagementPage from './pages/EmployeeManagementPage';
import {
  Sun,
  Compass,
  Package,
  ShieldCheck,
  Server,
  Database,
  Users,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  FileText,
  Briefcase,
  FolderKanban,
  Receipt,
  BarChart3,
  Boxes,
  Truck,
  Wrench,
  ArrowRight,
  ClipboardList,
  LogOut,
} from 'lucide-react';

const USER_ROLES = [
  'Super Admin',
  'Director',
  'Sales Executive',
  'Technical / Installation Manager',
  'Warehouse & Procurement Manager',
  'Field Technician',
  'Service & Warranty Executive',
  'Finance & Accounts Manager',
  'Customer'
];

/**
 * Route protection wrapper.
 * Strictly blocks unauthorized roles from accessing employee dashboards or customer portal.
 */
function ProtectedRoute({ currentUser, children, onLogout }) {
  const location = useLocation();
  const roleSlug = currentUser?.role?.slug;

  if (!isRouteAllowedForRole(roleSlug, location.pathname)) {
    return <AccessDenied currentUser={currentUser} onLogout={onLogout} />;
  }

  return children;
}

function Navbar({ currentUser, onLogout }) {
  const location = useLocation();
  const isCustomer = currentUser?.role?.slug === 'CUSTOMER';
  const isTechnician = currentUser?.role?.slug === 'FIELD_TECHNICIAN';
  const roleSlug = currentUser?.role?.slug;

  const userChip = (
    <div className="flex items-center gap-2 shrink-0 ml-3">
      <div className="hidden sm:flex flex-col text-right">
        <span className="text-xs font-bold text-white leading-tight truncate max-w-[140px]">
          {currentUser?.full_name || 'User'}
        </span>
        <span className="text-[10px] text-amber-400 font-mono">
          {currentUser?.role?.slug || 'USER'}
        </span>
      </div>
      {onLogout && (
        <button
          onClick={onLogout}
          title="Sign Out"
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/50 hover:text-rose-400 text-slate-300 transition border border-slate-700/60"
        >
          <LogOut className="w-4 h-4" />
        </button>
      )}
    </div>
  );

  // 1. CUSTOMER PORTAL NAVIGATION
  // Zero internal ERP links are rendered. Only Customer Portal navigation is exposed.
  if (isCustomer) {
    return (
      <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center space-x-3 shrink-0">
            <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-amber-500/30">
              <Sun className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight leading-tight">SunPower Solutions</h1>
              <p className="text-xs text-amber-400 font-medium tracking-wide">Customer Self-Service Portal</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <nav className="flex items-center space-x-2">
              <Link
                to="/portal"
                className="px-4 py-2 rounded-lg text-sm font-bold bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20 flex items-center gap-2 hover:bg-amber-400 transition"
              >
                <Sun className="w-4 h-4 stroke-[2.5]" />
                <span>My Solar Portal</span>
              </Link>
            </nav>
            {userChip}
          </div>
        </div>
      </header>
    );
  }

  // 2. FIELD TECHNICIAN OPERATIONS NAVIGATION
  if (isTechnician) {
    return (
      <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center space-x-3 shrink-0">
            <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-amber-500/30">
              <Wrench className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight leading-tight">SunPower Field Hub</h1>
              <p className="text-xs text-amber-400 font-medium tracking-wide">Technician Operations & Site Execution</p>
            </div>
          </div>

          <div className="flex items-center">
            <nav className="flex items-center space-x-2 overflow-x-auto py-2">
              <Link
                to="/technician-tasks"
                className={`px-3 py-1.5 rounded-md text-sm font-bold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/technician-tasks'
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30'
                }`}
              >
                <ClipboardList className="w-4 h-4" />
                <span>My Tasks & Visits</span>
              </Link>
              <Link
                to="/surveys"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname.startsWith('/surveys')
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Compass className="w-4 h-4" />
                <span>Surveys</span>
              </Link>
              <Link
                to="/installations"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname.startsWith('/installations')
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Installations</span>
              </Link>
              <Link
                to="/warranty"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname.startsWith('/warranty')
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Service Tickets</span>
              </Link>
              <Link
                to="/status"
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition shrink-0 ${
                  location.pathname === '/status' ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                Status
              </Link>
            </nav>
            {userChip}
          </div>
        </div>
      </header>
    );
  }

  // 3. INTERNAL STAFF ERP NAVIGATION (Role-Filtered)
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        <div className="flex items-center space-x-3 shrink-0">
          <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-amber-500/30">
            <Sun className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight leading-tight">SunPower Solutions</h1>
            <p className="text-xs text-amber-400 font-medium tracking-wide">SIMS • Solar Installation Management System</p>
          </div>
        </div>

        <div className="flex items-center overflow-hidden">
          <nav className="flex items-center space-x-2 overflow-x-auto py-2 ml-4">
            {isRouteAllowedForRole(roleSlug, '/crm') && (
              <Link
                to="/crm"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/crm' || location.pathname.startsWith('/crm')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>CRM & Sales</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/surveys') && (
              <Link
                to="/surveys"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/surveys' || location.pathname.startsWith('/surveys')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Compass className="w-4 h-4" />
                <span>Site Surveys</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/products') && (
              <Link
                to="/products"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/products' || location.pathname.startsWith('/products')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Package className="w-4 h-4" />
                <span>Products</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/bom') && (
              <Link
                to="/bom"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/bom' || location.pathname.startsWith('/bom')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>BOM</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/quotations') && (
              <Link
                to="/quotations"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/quotations' || location.pathname.startsWith('/quotations')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Quotations</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/orders') && (
              <Link
                to="/orders"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/orders' || location.pathname.startsWith('/orders')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Briefcase className="w-4 h-4" />
                <span>Orders</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/projects') && (
              <Link
                to="/projects"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/projects' || location.pathname.startsWith('/projects')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <FolderKanban className="w-4 h-4" />
                <span>Projects</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/procurement') && (
              <Link
                to="/procurement"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/procurement' || location.pathname.startsWith('/procurement')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Boxes className="w-4 h-4" />
                <span>Procurement</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/dispatch') && (
              <Link
                to="/dispatch"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/dispatch' || location.pathname.startsWith('/dispatch')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Truck className="w-4 h-4" />
                <span>Dispatch</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/installations') && (
              <Link
                to="/installations"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/installations' || location.pathname.startsWith('/installations')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Wrench className="w-4 h-4" />
                <span>Installation</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/technician-tasks') && (
              <Link
                to="/technician-tasks"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/technician-tasks' || location.pathname.startsWith('/technician-tasks')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <ClipboardList className="w-4 h-4" />
                <span>Technician Hub</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/warranty') && (
              <Link
                to="/warranty"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/warranty' || location.pathname.startsWith('/warranty')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Warranty & Service</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/subsidy') && (
              <Link
                to="/subsidy"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/subsidy' || location.pathname.startsWith('/subsidy')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Subsidy & DISCOM</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/invoices') && (
              <Link
                to="/invoices"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/invoices' || location.pathname.startsWith('/invoices')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Receipt className="w-4 h-4" />
                <span>Invoices</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/analytics') && (
              <Link
                to="/analytics"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/analytics' || location.pathname.startsWith('/analytics')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Analytics</span>
              </Link>
            )}

            {isRouteAllowedForRole(roleSlug, '/employees') && (
              <Link
                to="/employees"
                className={`px-3 py-1.5 rounded-md text-sm font-semibold transition flex items-center gap-1.5 shrink-0 ${
                  location.pathname === '/employees' || location.pathname.startsWith('/employees')
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Users className="w-4 h-4" />
                <span>Employees</span>
              </Link>
            )}

            <Link
              to="/status"
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition shrink-0 ${
                location.pathname === '/status' ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Status
            </Link>
            <Link
              to="/architecture"
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition shrink-0 ${
                location.pathname === '/architecture' ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              Architecture
            </Link>
          </nav>
          {userChip}
        </div>
      </div>
    </header>
  );
}

function SystemStatusPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await checkHealth();
      setHealth(res.data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server');
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Welcome */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/40 rounded-2xl p-8 border border-slate-800 shadow-xl text-white">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <Activity className="w-3.5 h-3.5 animate-pulse" /> SIMS Core Operational
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight">
              Solar Installation Management Platform
            </h2>
            <p className="text-slate-300 max-w-2xl text-sm leading-relaxed">
              Engineered for rooftop solar deployment: 1 kW to 5 kW On-Grid & Off-Grid systems, managing 40+ installations monthly across 15 technicians.
            </p>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold px-4 py-2.5 rounded-lg text-sm shadow-md transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Connectivity
          </button>
        </div>
      </div>

      {/* Connectivity Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Client Engine</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1">React + Vite</h3>
            </div>
            <div className="p-2.5 bg-sky-50 text-sky-600 rounded-lg">
              <Cpu className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-sm">
            <span className="text-slate-600">Tailwind CSS & Router</span>
            <span className="inline-flex items-center gap-1.5 text-emerald-600 font-semibold text-xs">
              <CheckCircle2 className="w-4 h-4" /> Operational
            </span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">API Service</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1">FastAPI Backend</h3>
            </div>
            <div className={`p-2.5 rounded-lg ${health ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
              <Server className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-sm">
            <span className="text-slate-600">{health?.app_name || 'SunPower SIMS'}</span>
            {loading ? (
              <span className="text-xs text-slate-400">Pinging...</span>
            ) : health ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-600 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4" /> Healthy ({health.status})
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-rose-600 font-semibold text-xs">
                <AlertTriangle className="w-4 h-4" /> Unreachable
              </span>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Storage & Relational</span>
              <h3 className="text-xl font-bold text-slate-900 mt-1">PostgreSQL</h3>
            </div>
            <div className={`p-2.5 rounded-lg ${health?.database?.connected ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
              <Database className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-sm">
            <span className="text-slate-600">SQLAlchemy 2.x & PostgreSQL</span>
            {loading ? (
              <span className="text-xs text-slate-400">Checking...</span>
            ) : health?.database?.connected ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-600 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-amber-600 font-semibold text-xs">
                <AlertTriangle className="w-4 h-4" /> Ready
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Diagnostics Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h4 className="text-base font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Layers className="w-5 h-5 text-amber-500" /> API Communication Diagnostics
        </h4>

        {loading ? (
          <div className="p-4 bg-slate-50 rounded-lg text-sm text-slate-600 flex items-center gap-3">
            <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
            Running probe against FastAPI endpoint...
          </div>
        ) : error ? (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900 space-y-1">
            <p className="font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" /> Backend connection notice:
            </p>
            <p className="text-xs text-amber-800">{error}</p>
          </div>
        ) : (
          <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-lg text-xs font-mono text-emerald-950 overflow-x-auto">
            <pre>{JSON.stringify(health, null, 2)}</pre>
          </div>
        )}

        <div className="mt-3 text-right text-xs text-slate-400">
          Last probe: {lastChecked || 'Never'}
        </div>
      </div>
    </div>
  );
}

function ArchitecturePage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">System Architecture & Role Hierarchy</h2>
        <p className="text-slate-600 text-sm mt-1">
          SunPower Solutions SIMS nine defined user roles with backend-enforced RBAC.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-amber-500" /> Configured Roles (9 Modules)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {USER_ROLES.map((role, idx) => (
            <div
              key={role}
              className="p-4 rounded-lg border border-slate-100 bg-slate-50/70 hover:bg-white hover:border-amber-300 hover:shadow-sm transition flex items-center gap-3"
            >
              <div className="w-7 h-7 rounded-full bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs">
                {idx + 1}
              </div>
              <span className="text-sm font-semibold text-slate-800">{role}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-amber-500" /> Core Workflow Parameters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-700">
          <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200/60">
            <h4 className="font-semibold text-amber-950 mb-1">Capacities & Types</h4>
            <p className="text-xs text-amber-900">
              Configured for 1 kW, 2 kW, 3 kW, 4 kW, and 5 kW residential rooftop systems. Both On-Grid (net-metered) and Off-Grid (battery-backed) configurations supported.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
            <h4 className="font-semibold text-slate-900 mb-1">Operational Capacity</h4>
            <p className="text-xs text-slate-600">
              Designed for 40 solar projects monthly with dispatch, serial tracking, and scheduling across 15 field technicians.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  const loadSession = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setCurrentUser(null);
      setAuthLoading(false);
      return;
    }
    try {
      const res = await getMe();
      const userData = res?.data?.email
        ? res.data
        : (res?.email ? res : (res?.data?.data || res?.data));
      if (userData && userData.email) {
        setCurrentUser(userData);
      } else {
        localStorage.removeItem('access_token');
        setCurrentUser(null);
      }
    } catch (err) {
      localStorage.removeItem('access_token');
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
  };

  // Initial loading splash
  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white p-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-500 flex items-center justify-center text-slate-950 font-black shadow-xl shadow-amber-500/30 animate-pulse mb-4">
          <Sun className="w-7 h-7 stroke-[2.5]" />
        </div>
        <p className="text-sm font-bold text-slate-200">Initializing SunPower SIMS...</p>
        <span className="text-xs text-amber-400 font-mono mt-1">Verifying secure local session</span>
      </div>
    );
  }

  // ==========================================
  // 1. UNAUTHENTICATED APPLICATION STATE
  // Show clean Login or Customer Sign Up page.
  // Internal dashboards and ERP navigation are completely hidden.
  // ==========================================
  if (!currentUser) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
          <Route path="/signup" element={<CustomerSignUpPage onSignUpSuccess={handleLoginSuccess} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    );
  }

  // ==========================================
  // 2. AUTHENTICATED APPLICATION STATE
  // Role-based destination & protected routes.
  // ==========================================
  const defaultDashboard = getRoleDefaultPath(currentUser?.role?.slug);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-100/70 flex flex-col">
        <AuthBar currentUser={currentUser} onLogout={handleLogout} />
        <Navbar currentUser={currentUser} onLogout={handleLogout} />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            {/* Redirect unneeded login/signup requests to user's dashboard */}
            <Route path="/login" element={<Navigate to={defaultDashboard} replace />} />
            <Route path="/signup" element={<Navigate to={defaultDashboard} replace />} />
            <Route path="/" element={<Navigate to={defaultDashboard} replace />} />

            {/* Customer Self-Service Portal */}
            <Route
              path="/portal"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <CustomerPortalPage />
                </ProtectedRoute>
              }
            />

            {/* Field Technician Tasks & Visits Hub */}
            <Route
              path="/technician-tasks"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <FieldTechnicianTasksPage />
                </ProtectedRoute>
              }
            />

            {/* Internal ERP Business Modules */}
            <Route
              path="/crm"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <CRMManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/surveys"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <SurveyManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/products"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <ProductManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bom"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <BOMManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/quotations"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <QuotationManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/orders"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <OrderManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <ProjectManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/procurement"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <ProcurementManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dispatch"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <DispatchManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/installations"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <InstallationManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/warranty"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <ServiceWarrantyManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/subsidy"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <SubsidyManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/invoices"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <InvoiceManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <AnalyticsDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employees"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <EmployeeManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/status"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <SystemStatusPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/architecture"
              element={
                <ProtectedRoute currentUser={currentUser} onLogout={handleLogout}>
                  <ArchitecturePage />
                </ProtectedRoute>
              }
            />

            {/* Catch-all unmatched routes redirect to user's dashboard */}
            <Route path="*" element={<Navigate to={defaultDashboard} replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          {currentUser?.role?.slug === 'CUSTOMER'
            ? 'SunPower Solutions Customer Portal • Rooftop Solar Installation & Service Support'
            : 'SunPower Solutions SIMS • CRM, Surveys, Products, Quotations, Orders, Projects & Commercial Billing Active'}
        </footer>
      </div>
    </BrowserRouter>
  );
}
