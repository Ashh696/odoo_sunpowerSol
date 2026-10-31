import React, { useState, useEffect } from 'react';
import {
  Users,
  UserCheck,
  UserX,
  Building2,
  Award,
  AlertTriangle,
  Clock,
  ArrowRight,
  ShieldAlert,
  Plus,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import {
  fetchEmployees,
  fetchDepartments,
  fetchExpiringCertifications,
} from '../services/employeeApi';

export default function EmployeeDashboard({ onNavigate, onAddEmployee, onViewEmployee }) {
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    departments: 0,
    expiringCerts: 0,
  });
  const [departmentCounts, setDepartmentCounts] = useState([]);
  const [recentEmployees, setRecentEmployees] = useState([]);
  const [criticalCertifications, setCriticalCertifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [empRes, deptRes, certRes] = await Promise.all([
        fetchEmployees({ page_size: 100 }),
        fetchDepartments(),
        fetchExpiringCertifications({ days: 30 }),
      ]);

      const allEmps = empRes?.data?.items || [];
      const totalCount = empRes?.data?.total || allEmps.length;
      const activeCount = allEmps.filter((e) => e.is_active).length;
      const inactiveCount = allEmps.filter((e) => !e.is_active).length;

      const allDepts = deptRes?.data || [];
      const allCerts = certRes?.data || [];

      setStats({
        total: totalCount,
        active: activeCount,
        inactive: inactiveCount,
        departments: allDepts.length,
        expiringCerts: allCerts.length,
      });

      setDepartmentCounts(allDepts);
      setRecentEmployees(allEmps.slice(0, 5));
      setCriticalCertifications(allCerts.slice(0, 5));
    } catch (err) {
      setError(err.message || 'Failed to load employee metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
        <span className="text-sm font-medium">Aggregating workforce intelligence...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Welcome Bar */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/40 rounded-2xl p-6 text-white border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" /> Workforce Analytics & Operations
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight">Employee & Department Command</h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Real-time management for SunPower Solutions solar workforce, engineering teams, and certified rooftop installation technicians.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onAddEmployee && onAddEmployee()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Employee</span>
          </button>
          <button
            onClick={loadDashboardData}
            title="Refresh statistics"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-amber-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Headcount</span>
            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{stats.total}</span>
            <span className="text-xs font-medium text-slate-500">Registered</span>
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center justify-between">
            <span>Active: {stats.active}</span>
            <span className="text-slate-400">Inactive: {stats.inactive}</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-amber-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Workforce</span>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-600">{stats.active}</span>
            <span className="text-xs font-medium text-emerald-700 font-mono">
              {stats.total > 0 ? `${Math.round((stats.active / stats.total) * 100)}%` : '0%'}
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-500">Currently deployed on solar projects</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-amber-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Departments</span>
            <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{stats.departments}</span>
            <span className="text-xs font-medium text-slate-500">Functional Units</span>
          </div>
          <button
            onClick={() => onNavigate && onNavigate('departments')}
            className="mt-2 text-xs text-amber-600 hover:text-amber-700 font-semibold flex items-center gap-1"
          >
            <span>View departments</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-amber-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Expiring Certs</span>
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${stats.expiringCerts > 0 ? 'bg-rose-50 text-rose-600' : 'bg-slate-100 text-slate-400'}`}>
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${stats.expiringCerts > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
              {stats.expiringCerts}
            </span>
            <span className="text-xs font-medium text-slate-500">Within 30 Days</span>
          </div>
          <button
            onClick={() => onNavigate && onNavigate('certifications')}
            className="mt-2 text-xs text-rose-600 hover:text-rose-700 font-semibold flex items-center gap-1"
          >
            <span>Audit certifications</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* 2-Column Operational Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Department Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Building2 className="w-4 h-4 text-amber-500" /> Department Distribution
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('departments')}
              className="text-xs text-amber-600 hover:underline"
            >
              Manage
            </button>
          </div>

          <div className="space-y-3">
            {departmentCounts.map((dept) => {
              const maxCount = Math.max(...departmentCounts.map((d) => d.employee_count), 1);
              const percentage = Math.round((dept.employee_count / maxCount) * 100);
              return (
                <div key={dept.id} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{dept.name}</span>
                    <span className="text-slate-500 font-mono font-semibold">{dept.employee_count}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-slate-400 flex justify-between">
                    <span>Code: {dept.code}</span>
                    <span>Manager: {dept.manager_name || 'Unassigned'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Employees Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Users className="w-4 h-4 text-amber-500" /> Recently Added Staff
            </h3>
            <button
              onClick={() => onNavigate && onNavigate('employees')}
              className="text-xs text-amber-600 hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View Directory</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {recentEmployees.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              No employee records registered yet. Click "Add New Employee" to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 uppercase text-[10px]">
                    <th className="pb-2">Employee</th>
                    <th className="pb-2">Department</th>
                    <th className="pb-2">Designation</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentEmployees.map((emp) => (
                    <tr key={emp.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-2.5">
                        <div className="font-semibold text-slate-900">{emp.full_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{emp.employee_code}</div>
                      </td>
                      <td className="py-2.5 text-slate-600">{emp.department_name}</td>
                      <td className="py-2.5 text-slate-600">{emp.designation}</td>
                      <td className="py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            emp.is_active
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {emp.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-2.5 text-right">
                        <button
                          onClick={() => onViewEmployee && onViewEmployee(emp.id)}
                          className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Critical Expiry Watch */}
      {criticalCertifications.length > 0 && (
        <div className="bg-rose-50/50 border border-rose-200 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-rose-900 text-xs sm:text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              Safety & Technical Certifications Approaching Expiry / Expired
            </h4>
            <button
              onClick={() => onNavigate && onNavigate('certifications')}
              className="text-xs font-semibold text-rose-700 hover:underline"
            >
              View all ({criticalCertifications.length})
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {criticalCertifications.map((cert) => (
              <div
                key={cert.id}
                className="bg-white border border-rose-200 rounded-lg p-3 text-xs space-y-1 shadow-sm"
              >
                <div className="flex justify-between items-start">
                  <span className="font-bold text-slate-900">{cert.certification_name}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      cert.is_expired
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {cert.is_expired
                      ? 'EXPIRED'
                      : `${cert.days_to_expiry} days left`}
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  Employee: <span className="font-medium text-slate-800">{cert.employee_name}</span> ({cert.employee_code})
                </div>
                <div className="text-[10px] text-slate-400">
                  Authority: {cert.issuing_authority} • Expiry: {cert.expiry_date}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
