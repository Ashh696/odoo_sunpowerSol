import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { checkHealth } from './services/api';
import {
  Sun,
  ShieldCheck,
  Server,
  Database,
  Users,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  ArrowRight
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

function Navbar() {
  const location = useLocation();

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-amber-500/30">
            <Sun className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight leading-tight">SunPower Solutions</h1>
            <p className="text-xs text-amber-400 font-medium tracking-wide">SIMS • Solar Installation Management System</p>
          </div>
        </div>

        <nav className="flex items-center space-x-2">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              location.pathname === '/' ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            System Status
          </Link>
          <Link
            to="/architecture"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              location.pathname === '/architecture' ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            Architecture & Roles
          </Link>
        </nav>
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
              <Activity className="w-3.5 h-3.5 animate-pulse" /> Phase 1 Foundation Active
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
        {/* Frontend Card */}
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

        {/* Backend Card */}
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

        {/* Database Card */}
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
            <span className="text-slate-600">SQLAlchemy 2.x & Alembic</span>
            {loading ? (
              <span className="text-xs text-slate-400">Checking...</span>
            ) : health?.database?.connected ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-600 font-semibold text-xs">
                <CheckCircle2 className="w-4 h-4" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-amber-600 font-semibold text-xs">
                <AlertTriangle className="w-4 h-4" /> Ready for Connection
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
            <p className="text-xs text-amber-700 mt-2">
              Start the FastAPI backend with: <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">uvicorn app.main:app --reload</code> inside <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono">solar-management-system/backend</code>.
            </p>
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
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-100/70 flex flex-col">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<SystemStatusPage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          SunPower Solutions SIMS • Phase 1 Foundation Active • Ready for Phase 2 Modules
        </footer>
      </div>
    </BrowserRouter>
  );
}
