import React from 'react';
import { ShieldAlert, ArrowLeft, LogOut, Sun } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { getRoleDefaultPath } from '../services/authApi';

export default function AccessDenied({ currentUser, onLogout }) {
  const location = useLocation();
  const defaultPath = getRoleDefaultPath(currentUser?.role?.slug);

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white border border-rose-200 rounded-2xl shadow-xl p-6 sm:p-8 text-center space-y-6">
        <div className="w-16 h-16 bg-rose-50 border border-rose-200 text-rose-600 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <div>
          <span className="inline-block px-3 py-1 bg-rose-100 text-rose-800 border border-rose-200 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
            Access Restricted (403)
          </span>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">
            Unauthorized Area
          </h2>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Your authenticated account does not have permission to access the requested module.
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-xs text-left space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Attempted Route:</span>
            <span className="font-mono font-bold text-slate-800">{location.pathname}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Your Current Role:</span>
            <span className="font-mono font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              {currentUser?.role?.slug || 'USER'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Account:</span>
            <span className="font-medium text-slate-700">{currentUser?.email || 'N/A'}</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <Link
            to={defaultPath}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition shadow-md shadow-amber-500/20"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </Link>

          {onLogout && (
            <button
              onClick={onLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
