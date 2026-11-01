import React, { useState, useEffect } from 'react';
import { Shield, LogOut, CheckCircle } from 'lucide-react';
import { getMe } from '../services/employeeApi';

export default function AuthBar({ currentUser: propUser, onLogout, onAuthChange }) {
  const [currentUser, setCurrentUser] = useState(propUser || null);

  useEffect(() => {
    if (propUser !== undefined) {
      setCurrentUser(propUser);
    }
  }, [propUser]);

  const checkCurrentUser = async () => {
    if (propUser !== undefined) return;
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

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setCurrentUser(null);
    if (onLogout) onLogout();
    if (onAuthChange) onAuthChange(null);
  };

  if (!currentUser) return null;

  return (
    <div className="bg-slate-900 border-b border-slate-800 text-xs text-slate-300 py-1.5 px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5 text-slate-400">
          <Shield className="w-3.5 h-3.5 text-amber-500" />
          <span>SIMS Session:</span>
        </span>
        <span className="flex items-center gap-1.5 font-medium text-emerald-400">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>{currentUser.full_name}</span>
          <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-1.5 py-0.2 rounded text-[10px] font-mono">
            {currentUser.role?.slug || 'USER'}
          </span>
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleLogout}
          className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
        >
          <LogOut className="w-3 h-3" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
