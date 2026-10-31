import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Plus,
  Building2,
  Phone,
  Mail,
  UserCheck,
  UserX,
  Eye,
  Edit2,
  Power,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Shield,
  Award,
} from 'lucide-react';
import {
  fetchEmployees,
  fetchDepartments,
  fetchSkills,
  toggleEmployeeStatus,
} from '../services/employeeApi';

export default function EmployeeList({ onAddEmployee, onEditEmployee, onViewEmployee }) {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [employmentType, setEmploymentType] = useState('');
  const [skillId, setSkillId] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Status toggle action state
  const [statusActionLoading, setStatusActionLoading] = useState(null);

  const loadFilterOptions = async () => {
    try {
      const [deptRes, skillRes] = await Promise.all([
        fetchDepartments({ is_active: true }),
        fetchSkills({ is_active: true }),
      ]);
      setDepartments(deptRes?.data || []);
      setSkills(skillRes?.data || []);
    } catch (err) {
      console.error('Failed to load filter options', err);
    }
  };

  const loadEmployees = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (search.trim()) params.search = search.trim();
      if (departmentId) params.department_id = Number(departmentId);
      if (statusFilter !== '') params.is_active = statusFilter === 'true';
      if (employmentType) params.employment_type = employmentType;
      if (skillId) params.skill_id = Number(skillId);

      const res = await fetchEmployees(params);
      if (res?.data) {
        setEmployees(res.data.items || []);
        setTotalCount(res.data.total || 0);
        setTotalPages(res.data.total_pages || 1);
      }
    } catch (err) {
      setError(err.message || 'Failed to retrieve employee directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    loadEmployees();
  }, [page, pageSize, departmentId, statusFilter, employmentType, skillId]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadEmployees();
  };

  const handleResetFilters = () => {
    setSearch('');
    setDepartmentId('');
    setStatusFilter('');
    setEmploymentType('');
    setSkillId('');
    setPage(1);
  };

  const handleToggleStatus = async (emp) => {
    const willDeactivate = emp.is_active;
    const confirmMsg = willDeactivate
      ? `Are you sure you want to deactivate employee ${emp.full_name} (${emp.employee_code})? Historical records will be safely preserved.`
      : `Reactivate employee ${emp.full_name} (${emp.employee_code})?`;

    if (!window.confirm(confirmMsg)) return;

    setStatusActionLoading(emp.id);
    try {
      await toggleEmployeeStatus(emp.id, {
        is_active: !willDeactivate,
        exit_date: willDeactivate ? new Date().toISOString().split('T')[0] : null,
      });
      loadEmployees();
    } catch (err) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setStatusActionLoading(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Filter Controls */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, employee code, email, or designation..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-amber-500 focus:bg-white transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={departmentId}
              onChange={(e) => {
                setDepartmentId(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Statuses</option>
              <option value="true">Active Only</option>
              <option value="false">Inactive Only</option>
            </select>

            <select
              value={employmentType}
              onChange={(e) => {
                setEmploymentType(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Types</option>
              <option value="FULL_TIME">Full Time</option>
              <option value="CONTRACTOR">Contractor</option>
              <option value="INTERN">Intern</option>
            </select>

            <select
              value={skillId}
              onChange={(e) => {
                setSkillId(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
            >
              <option value="">Filter by Skill</option>
              {skills.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.category})
                </option>
              ))}
            </select>

            <button
              type="submit"
              className="px-3.5 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-xs font-semibold transition"
            >
              Search
            </button>

            {(search || departmentId || statusFilter !== '' || employmentType || skillId) && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-3 py-2 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg text-xs font-medium transition"
              >
                Clear
              </button>
            )}

            <button
              type="button"
              onClick={() => onAddEmployee && onAddEmployee()}
              className="px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 transition ml-auto shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Employee</span>
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {error}
        </div>
      )}

      {/* Main Employee Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-800">{employees.length}</span> of{' '}
            <span className="font-semibold text-slate-800">{totalCount}</span> employees
          </div>
          <button
            onClick={loadEmployees}
            title="Refresh directory"
            className="flex items-center gap-1 text-slate-500 hover:text-slate-800 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-500" />
            <span>Loading employee records...</span>
          </div>
        ) : employees.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs space-y-2">
            <p className="font-medium text-slate-700">No employees match your search criteria.</p>
            <p className="text-slate-400">Try adjusting your filters or search keywords.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Employee</th>
                  <th className="py-3 px-4">Department & Role</th>
                  <th className="py-3 px-4">Contact Details</th>
                  <th className="py-3 px-4">Joining Date</th>
                  <th className="py-3 px-4">Skills & Certs</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {employees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/70 transition">
                    {/* Employee Profile */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                          {emp.full_name?.charAt(0) || 'E'}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 flex items-center gap-1.5">
                            <span>{emp.full_name}</span>
                            {emp.has_login_access && (
                              <span title="Linked Login Account" className="text-amber-500">
                                <Shield className="w-3 h-3 inline" />
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            {emp.employee_code} • {emp.employment_type}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Department & Designation */}
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{emp.designation}</div>
                      <div className="text-[11px] text-amber-700 flex items-center gap-1">
                        <Building2 className="w-3 h-3 text-amber-500" />
                        <span>{emp.department_name}</span>
                      </div>
                    </td>

                    {/* Contact Info */}
                    <td className="py-3 px-4 text-slate-600">
                      <div className="flex items-center gap-1 text-[11px]">
                        <Mail className="w-3 h-3 text-slate-400" />
                        <span>{emp.email}</span>
                      </div>
                      {emp.phone && (
                        <div className="flex items-center gap-1 text-[11px] text-slate-500 mt-0.5">
                          <Phone className="w-3 h-3 text-slate-400" />
                          <span>{emp.phone}</span>
                        </div>
                      )}
                    </td>

                    {/* Joining Date */}
                    <td className="py-3 px-4 text-slate-600">
                      <div>{emp.joining_date}</div>
                      {emp.exit_date && (
                        <div className="text-[10px] text-rose-500">Exit: {emp.exit_date}</div>
                      )}
                    </td>

                    {/* Skills & Certs badges */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-medium">
                          {emp.skills?.length || 0} Skills
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-medium">
                          {emp.certifications?.length || 0} Certs
                        </span>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          emp.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-500 border border-slate-200'
                        }`}
                      >
                        {emp.is_active ? (
                          <>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span>Active</span>
                          </>
                        ) : (
                          <>
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                            <span>Inactive</span>
                          </>
                        )}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        <button
                          onClick={() => onViewEmployee && onViewEmployee(emp.id)}
                          title="View Employee Profile"
                          className="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => onEditEmployee && onEditEmployee(emp)}
                          title="Edit Information"
                          className="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(emp)}
                          disabled={statusActionLoading === emp.id}
                          title={emp.is_active ? 'Deactivate Employee' : 'Activate Employee'}
                          className={`p-1.5 rounded transition ${
                            emp.is_active
                              ? 'bg-rose-50 text-rose-600 hover:bg-rose-100'
                              : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                          }`}
                        >
                          <Power className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <div>
              Page <span className="font-semibold text-slate-800">{page}</span> of{' '}
              <span className="font-semibold text-slate-800">{totalPages}</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page <= 1}
                className="px-2.5 py-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page >= totalPages}
                className="px-2.5 py-1 rounded border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
