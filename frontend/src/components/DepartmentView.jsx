import React, { useState, useEffect } from 'react';
import {
  Building2,
  Plus,
  Edit2,
  Users,
  Search,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  User,
  Shield,
  RefreshCw,
} from 'lucide-react';
import {
  fetchDepartments,
  createDepartment,
  updateDepartment,
  fetchDepartmentEmployees,
  fetchEmployees,
} from '../services/employeeApi';

export default function DepartmentView({ onViewEmployee }) {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  // Selected department for viewing members
  const [expandedDeptId, setExpandedDeptId] = useState(null);
  const [deptEmployees, setDeptEmployees] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [managerId, setManagerId] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState(null);

  // List of potential managers (all active employees/users)
  const [candidateManagers, setCandidateManagers] = useState([]);

  const loadDepartments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDepartments({ search: search.trim() || undefined });
      setDepartments(res?.data || []);
    } catch (err) {
      setError(err.message || 'Failed to retrieve departments');
    } finally {
      setLoading(false);
    }
  };

  const loadCandidateManagers = async () => {
    try {
      const res = await fetchEmployees({ page_size: 100, is_active: true });
      if (res?.data?.items) {
        setCandidateManagers(res.data.items);
      }
    } catch (err) {
      console.error('Failed to load candidate managers', err);
    }
  };

  useEffect(() => {
    loadDepartments();
    loadCandidateManagers();
  }, []);

  const handleToggleExpand = async (deptId) => {
    if (expandedDeptId === deptId) {
      setExpandedDeptId(null);
      setDeptEmployees([]);
      return;
    }
    setExpandedDeptId(deptId);
    setMembersLoading(true);
    try {
      const res = await fetchDepartmentEmployees(deptId);
      setDeptEmployees(res?.data || []);
    } catch (err) {
      alert(`Failed to load members: ${err.message}`);
    } finally {
      setMembersLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingDept(null);
    setName('');
    setCode('');
    setManagerId('');
    setIsActive(true);
    setModalError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (dept) => {
    setEditingDept(dept);
    setName(dept.name || '');
    setCode(dept.code || '');
    setManagerId(dept.manager_id ? String(dept.manager_id) : '');
    setIsActive(dept.is_active);
    setModalError(null);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setModalLoading(true);
    setModalError(null);
    try {
      if (editingDept) {
        await updateDepartment(editingDept.id, {
          name: name.trim(),
          code: code.trim().toUpperCase(),
          manager_id: managerId ? Number(managerId) : 0,
          is_active: isActive,
        });
      } else {
        await createDepartment({
          name: name.trim(),
          code: code.trim().toUpperCase(),
          manager_id: managerId ? Number(managerId) : null,
          is_active: isActive,
        });
      }
      setShowModal(false);
      loadDepartments();
    } catch (err) {
      setModalError(err.message || 'Failed to save department');
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <Building2 className="w-5 h-5 text-amber-500" /> Department Architecture
          </h3>
          <p className="text-xs text-slate-500">
            Configure SunPower functional divisions, assign executive managers, and view team rosters.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Department</span>
          </button>
          <button
            onClick={loadDepartments}
            title="Refresh"
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {error}
        </div>
      )}

      {/* Department Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">Loading department units...</div>
      ) : departments.length === 0 ? (
        <div className="p-12 text-center text-slate-500 text-xs">No departments found.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((dept) => {
            const isExpanded = expandedDeptId === dept.id;
            return (
              <div
                key={dept.id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm hover:border-amber-300 transition flex flex-col justify-between overflow-hidden"
              >
                <div className="p-5 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-bold">
                        {dept.code}
                      </span>
                      <h4 className="font-bold text-slate-900 text-sm mt-1">{dept.name}</h4>
                    </div>
                    <button
                      onClick={() => handleOpenEdit(dept)}
                      title="Edit department"
                      className="p-1.5 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="text-xs text-slate-500 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Manager:{' '}
                        <strong className="text-slate-800">
                          {dept.manager_name || 'Not assigned'}
                        </strong>
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      <span>
                        Members: <strong className="text-slate-800">{dept.employee_count}</strong> active staff
                      </span>
                    </div>
                  </div>
                </div>

                {/* Collapsible Members Section */}
                <div className="border-t border-slate-100 bg-slate-50/50">
                  <button
                    onClick={() => handleToggleExpand(dept.id)}
                    className="w-full px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center justify-between transition"
                  >
                    <span>
                      {isExpanded ? 'Hide Department Members' : `View Members (${dept.employee_count})`}
                    </span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {isExpanded && (
                    <div className="p-3 border-t border-slate-200/60 bg-white space-y-2 max-h-52 overflow-y-auto">
                      {membersLoading ? (
                        <div className="p-3 text-center text-[11px] text-slate-400">Loading roster...</div>
                      ) : deptEmployees.length === 0 ? (
                        <div className="p-3 text-center text-[11px] text-slate-400">
                          No employees assigned to this department yet.
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          {deptEmployees.map((emp) => (
                            <div
                              key={emp.id}
                              className="p-2 rounded bg-slate-50 hover:bg-amber-50/50 border border-slate-100 flex items-center justify-between text-xs transition"
                            >
                              <div>
                                <div className="font-semibold text-slate-900">{emp.full_name}</div>
                                <div className="text-[10px] text-slate-400 font-mono">
                                  {emp.employee_code} • {emp.designation}
                                </div>
                              </div>
                              <button
                                onClick={() => onViewEmployee && onViewEmployee(emp.id)}
                                className="text-[10px] text-amber-600 font-bold hover:underline"
                              >
                                View
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create / Edit Department Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">
                {editingDept ? 'Update Department' : 'Create New Department'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Department Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Field Operations & Testing"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Department Code *</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. FIELD"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs font-mono uppercase focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Department Manager</label>
                <select
                  value={managerId}
                  onChange={(e) => setManagerId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                >
                  <option value="">No Manager Assigned</option>
                  {candidateManagers.map((emp) => (
                    <option key={emp.user_id} value={emp.user_id}>
                      {emp.full_name} ({emp.designation} - {emp.employee_code})
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-slate-400 mt-1">
                  Manager assignment references the user account record in database.
                </p>
              </div>

              <div className="pt-2 flex justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  {modalLoading ? 'Saving...' : editingDept ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
