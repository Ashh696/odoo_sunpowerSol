import React, { useState, useEffect } from 'react';
import { User, Shield, LogIn, LogOut, CheckCircle, AlertCircle } from 'lucide-react';
import { loginUser, getMe } from '../services/employeeApi';

export default function AuthBar({ onAuthChange }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const checkCurrentUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setCurrentUser(null);
      if (onAuthChange) onAuthChange(null);
      return;
    }
    try {
      const res = await getMe();
      if (res && res.data) {
        setCurrentUser(res.data);
        if (onAuthChange) onAuthChange(res.data);
      }
    } catch (err) {
      localStorage.removeItem('access_token');
      setCurrentUser(null);
      if (onAuthChange) onAuthChange(null);
    }
  };

  useEffect(() => {
    checkCurrentUser();
  }, []);

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await loginUser(email, password);
      if (res && res.data && res.data.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        setCurrentUser(res.data.user);
        setShowLoginModal(false);
        if (onAuthChange) onAuthChange(res.data.user);
      }
    } catch (err) {
      setError(err.message || 'Login failed. Check email and password.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setCurrentUser(null);
    if (onAuthChange) onAuthChange(null);
  };

  return (
    <div className="bg-slate-900 border-b border-slate-800 text-xs text-slate-300 py-1.5 px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5 text-slate-400">
          <Shield className="w-3.5 h-3.5 text-amber-500" />
          <span>SIMS Session:</span>
        </span>
        {currentUser ? (
          <span className="flex items-center gap-1.5 font-medium text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{currentUser.full_name}</span>
            <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-1.5 py-0.2 rounded text-[10px] font-mono">
              {currentUser.role?.slug || 'USER'}
            </span>
          </span>
        ) : (
          <span className="text-amber-400 font-medium">Guest (Not Authenticated)</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {currentUser ? (
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
          >
            <LogOut className="w-3 h-3" />
            <span>Logout</span>
          </button>
        ) : (
          <button
            onClick={() => {
              setError(null);
              setShowLoginModal(true);
            }}
            className="flex items-center gap-1 px-3 py-1 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold transition shadow-sm"
          >
            <LogIn className="w-3 h-3" />
            <span>Sign In</span>
          </button>
        )}
      </div>

      {showLoginModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-sm w-full p-6 text-white shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base flex items-center gap-2 text-amber-400">
                <Shield className="w-5 h-5" /> SIMS User Authentication
              </h3>
              <button
                onClick={() => setShowLoginModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="p-3 mb-4 rounded bg-red-950/60 border border-red-800 text-red-200 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-amber-500"
                  required
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowLoginModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs"
                >
                  {loading ? 'Authenticating...' : 'Sign In'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
