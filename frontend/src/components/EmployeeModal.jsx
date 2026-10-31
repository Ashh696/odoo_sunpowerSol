import React, { useState, useEffect } from 'react';
import { X, UserPlus, Edit2, AlertCircle, Shield, Check } from 'lucide-react';
import { createEmployee, updateEmployee, fetchDepartments } from '../services/employeeApi';

const SYSTEM_INTERNAL_ROLES = [
  { slug: 'FIELD_TECHNICIAN', label: 'Field Technician' },
  { slug: 'TECHNICAL_MANAGER', label: 'Technical / Installation Manager' },
  { slug: 'SALES', label: 'Sales Executive' },
  { slug: 'WAREHOUSE_PROCUREMENT', label: 'Warehouse & Procurement Manager' },
  { slug: 'SERVICE_WARRANTY', label: 'Service & Warranty Executive' },
  { slug: 'FINANCE_ACCOUNTS', label: 'Finance & Accounts Manager' },
  { slug: 'DIRECTOR', label: 'Director' },
  { slug: 'SUPER_ADMIN', label: 'Super Admin' },
];

export default function EmployeeModal({ isOpen, onClose, employee, onSaved }) {
  const isEditing = Boolean(employee);

  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form State
  const [employeeCode, setEmployeeCode] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [designation, setDesignation] = useState('');
  const [employmentType, setEmploymentType] = useState('FULL_TIME');
  const [joiningDate, setJoiningDate] = useState(new Date().toISOString().split('T')[0]);
  const [exitDate, setExitDate] = useState('');
  const [emergencyContact, setEmergencyContact] = useState('');

  // User / Personal State
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  // Login provisioning (only relevant on creation)
  const [createLogin, setCreateLogin] = useState(false);
  const [password, setPassword] = useState('');
  const [roleSlug, setRoleSlug] = useState('FIELD_TECHNICIAN');

  useEffect(() => {
    fetchDepartments({ is_active: true }).then((res) => {
      if (res?.data) {
        setDepartments(res.data);
        if (!departmentId && res.data.length > 0 && !isEditing) {
          setDepartmentId(res.data[0].id);
        }
      }
    });
  }, []);

  useEffect(() => {
    if (employee) {
      setEmployeeCode(employee.employee_code || '');
      setDepartmentId(employee.department_id || '');
      setDesignation(employee.designation || '');
      setEmploymentType(employee.employment_type || 'FULL_TIME');
      setJoiningDate(employee.joining_date || '');
      setExitDate(employee.exit_date || '');
      setEmergencyContact(employee.emergency_contact || '');
      setFullName(employee.full_name || '');
      setEmail(employee.email || '');
      setPhone(employee.phone || '');
    } else {
      // Defaults for new employee
      const randomSuffix = Math.floor(100 + Math.random() * 900);
      setEmployeeCode(`EMP-${randomSuffix}`);
      setDesignation('');
      setEmploymentType('FULL_TIME');
      setJoiningDate(new Date().toISOString().split('T')[0]);
      setExitDate('');
      setEmergencyContact('');
      setFullName('');
      setEmail('');
      setPhone('');
      setCreateLogin(false);
      setPassword('');
      setRoleSlug('FIELD_TECHNICIAN');
    }
    setError(null);
  }, [employee, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEditing) {
        const payload = {
          department_id: Number(departmentId),
          designation: designation.trim(),
          employment_type: employmentType,
          joining_date: joiningDate,
          exit_date: exitDate ? exitDate : null,
          emergency_contact: emergencyContact.trim() || null,
          full_name: fullName.trim(),
          phone: phone.trim() || null,
          email: email.trim(),
        };
        await updateEmployee(employee.id, payload);
      } else {
        if (createLogin && (!password || password.length < 8)) {
          setError('A password of at least 8 characters is required when provisioning a login account.');
          setLoading(false);
          return;
        }

        const payload = {
          employee_code: employeeCode.trim().toUpperCase(),
          department_id: Number(departmentId),
          designation: designation.trim(),
          employment_type: employmentType,
          joining_date: joiningDate,
          emergency_contact: emergencyContact.trim() || null,
          full_name: fullName.trim(),
          email: email.trim(),
          phone: phone.trim() || null,
          role_slug: roleSlug,
          create_login_account: createLogin,
          password: createLogin ? password : null,
        };
        await createEmployee(payload);
      }

      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save employee profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 max-w-2xl w-full p-6 shadow-2xl space-y-5 my-8">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
              {isEditing ? <Edit2 className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">
                {isEditing ? `Edit Employee (${employee.employee_code})` : 'Register New Employee'}
              </h3>
              <p className="text-xs text-slate-500">
                {isEditing
                  ? 'Update operational details and employee contact info'
                  : 'Add team member to SunPower workforce registry'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Section: Employee Identification & Role */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Employment Details
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Employee Code <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={employeeCode}
                  onChange={(e) => setEmployeeCode(e.target.value)}
                  disabled={isEditing}
                  placeholder="e.g. EMP-101"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:border-amber-500 disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Department <span className="text-rose-500">*</span>
                </label>
                <select
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                >
                  <option value="">Select Department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Designation <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  placeholder="e.g. Senior Solar Installer"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Employment Type
                </label>
                <select
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                >
                  <option value="FULL_TIME">Full-Time Employee</option>
                  <option value="CONTRACTOR">Contractor / Freelance</option>
                  <option value="INTERN">Intern / Apprentice</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Joining Date <span className="text-rose-500">*</span>
                </label>
                <input
                  type="date"
                  value={joiningDate}
                  onChange={(e) => setJoiningDate(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Emergency Contact Phone
                </label>
                <input
                  type="text"
                  value={emergencyContact}
                  onChange={(e) => setEmergencyContact(e.target.value)}
                  placeholder="e.g. +91 9876543210 (Kin)"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              {isEditing && (
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Exit Date (if inactive)
                  </label>
                  <input
                    type="date"
                    value={exitDate}
                    onChange={(e) => setExitDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Section: Personal & Contact Information */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Personal & Contact Information
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Full Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="sm:col-span-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Email Address <span className="text-rose-500">*</span>
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. ramesh@sunpower.com"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="sm:col-span-1">
                <label className="block text-xs font-medium text-slate-700 mb-1">Phone Number</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="e.g. +91 9845012345"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* Section: Login Account Provisioning (only on creation) */}
          {!isEditing && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                    <Shield className="w-4 h-4 text-amber-500" />
                    Provision System Login Account
                  </h5>
                  <p className="text-[11px] text-slate-500">
                    Create credentials to allow this employee to access the SIMS application.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={createLogin}
                    onChange={(e) => setCreateLogin(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
                </label>
              </div>

              {createLogin && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-200/70">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      System Role Assignment
                    </label>
                    <select
                      value={roleSlug}
                      onChange={(e) => setRoleSlug(e.target.value)}
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                    >
                      {SYSTEM_INTERNAL_ROLES.map((r) => (
                        <option key={r.slug} value={r.slug}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Initial Password (min 8 chars) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter secure initial password"
                      required={createLogin}
                      minLength={8}
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shadow-sm"
            >
              {loading ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Employee Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
