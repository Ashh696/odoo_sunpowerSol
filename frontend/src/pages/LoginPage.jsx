import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Sun,
  Mail,
  Lock,
  Eye,
  EyeOff,
  LogIn,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  UserCheck,
} from 'lucide-react';
import { loginUser, getRoleDefaultPath } from '../services/authApi';

// Pre-configured local role accounts for quick local testing and evaluation
const DEMO_ACCOUNTS = [
  { role: 'SUPER_ADMIN', label: 'Super Admin', email: 'master_e2e_super_admin@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'DIRECTOR', label: 'Director', email: 'master_e2e_director@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'SALES', label: 'Sales Executive', email: 'master_e2e_sales@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'TECHNICAL_MANAGER', label: 'Technical Manager', email: 'master_e2e_technical_manager@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'WAREHOUSE_PROCUREMENT', label: 'Warehouse & Procurement', email: 'master_e2e_warehouse_procurement@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'FIELD_TECHNICIAN', label: 'Field Technician', email: 'master_e2e_field_technician@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'SERVICE_WARRANTY', label: 'Service & Warranty', email: 'master_e2e_service_warranty@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'FINANCE_ACCOUNTS', label: 'Finance & Accounts', email: 'master_e2e_finance_accounts@sunpower.com', pass: 'Pass123!Safe' },
  { role: 'CUSTOMER', label: 'Customer', email: 'master_e2e_customer@sunpower.com', pass: 'Pass123!Safe' },
];

export default function LoginPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDemoDrawer, setShowDemoDrawer] = useState(false);

  // Success message passed from registration page
  const successMessage = location.state?.message;

  const handleQuickFill = (acc) => {
    setEmail(acc.email);
    setPassword(acc.pass);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setLoading(true);
    try {
      const res = await loginUser(cleanEmail, password);
      // Support both intercepted axios response (res.data) and unintercepted response (res.data.data)
      const data = res?.data?.access_token
        ? res.data
        : (res?.access_token ? res : (res?.data?.data || res?.data));

      if (data && data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        if (onLoginSuccess) {
          onLoginSuccess(data.user);
        }
        // Redirect to role default dashboard
        const roleSlug = data.user?.role?.slug;
        const targetPath = getRoleDefaultPath(roleSlug);
        navigate(targetPath, { replace: true });
      } else {
        throw new Error('Invalid response from authentication service.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex flex-col justify-between text-slate-100 p-4 sm:p-6 lg:p-8">
      {/* Top Brand Header */}
      <div className="max-w-6xl w-full mx-auto flex items-center justify-between py-2">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-amber-500/20">
            <Sun className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <span className="font-extrabold text-base tracking-tight text-white block">SunPower Solutions</span>
            <span className="text-[11px] text-amber-400 font-medium tracking-wider block">SIMS • Solar Management System</span>
          </div>
        </div>

        <Link
          to="/signup"
          className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 transition flex items-center gap-1.5"
        >
          <span>Customer Sign Up</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Main Authentication Card */}
      <div className="max-w-md w-full mx-auto my-8">
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
          {/* Subtle Top Accent */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-amber-400 to-amber-600" />

          {/* Heading */}
          <div className="text-center mb-6">
            <h1 className="text-2xl font-black text-white tracking-tight">Sign In to SIMS</h1>
            <p className="text-xs text-slate-400 mt-1">
              Enter your credentials to access your solar management dashboard
            </p>
          </div>

          {/* Success Banner if redirected from registration */}
          {successMessage && (
            <div className="mb-5 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com or personal email"
                  required
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-300 transition"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-black rounded-xl text-xs uppercase tracking-wider transition shadow-lg shadow-amber-500/25 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Customer Registration Callout */}
          <div className="mt-6 pt-5 border-t border-slate-800 text-center">
            <p className="text-xs text-slate-400">
              New Rooftop Solar Customer?{' '}
              <Link to="/signup" className="text-amber-400 hover:text-amber-300 font-bold underline underline-offset-2">
                Register Customer Portal Account
              </Link>
            </p>
          </div>

          {/* Employee Provisioning Notice */}
          <div className="mt-4 p-3 bg-slate-950/50 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
            <span className="font-semibold text-slate-300">Company Employees:</span> Accounts are provisioned by system administration. Use your company email. Public sign up is restricted to rooftop solar customers only.
          </div>

          {/* Quick Demo Credentials Drawer for Local Verification */}
          <div className="mt-5 border-t border-slate-800/80 pt-3">
            <button
              type="button"
              onClick={() => setShowDemoDrawer(!showDemoDrawer)}
              className="w-full flex items-center justify-between text-[11px] font-bold text-slate-400 hover:text-amber-400 transition"
            >
              <span className="flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5 text-amber-500" />
                <span>Quick Role Fill (Local Testing Helper)</span>
              </span>
              {showDemoDrawer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showDemoDrawer && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1 text-left max-h-48 overflow-y-auto">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.role}
                    type="button"
                    onClick={() => handleQuickFill(acc)}
                    className="p-2 bg-slate-950/70 hover:bg-amber-500/10 border border-slate-800 hover:border-amber-500/40 rounded-lg text-left transition group"
                  >
                    <div className="text-[10px] font-black text-amber-400 group-hover:text-amber-300">{acc.label}</div>
                    <div className="text-[10px] text-slate-400 font-mono truncate">{acc.email}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="max-w-6xl w-full mx-auto text-center text-xs text-slate-500 py-2">
        SunPower Solutions SIMS • Solar Installation Management System • Phase 1–14 Architecture
      </footer>
    </div>
  );
}
