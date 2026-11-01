import React, { useState, useEffect } from 'react';
import {
  X,
  UserPlus,
  Edit2,
  AlertCircle,
  Shield,
  Check,
  RefreshCw,
  Copy,
  Eye,
  EyeOff,
  CheckCircle2,
  KeyRound,
  Mail,
} from 'lucide-react';
import {
  createEmployee,
  updateEmployee,
  fetchDepartments,
  generateEmployeeEmail,
} from '../services/employeeApi';
import { generateHumanFriendlyPassword } from '../utils/passwordGenerator';
import {
  generateWorkEmailPreview,
  COMPANY_EMAIL_DOMAIN,
} from '../utils/emailGenerator';

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
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  // Login provisioning (only relevant on creation)
  const [createLogin, setCreateLogin] = useState(true);
  const [password, setPassword] = useState('');
  const [roleSlug, setRoleSlug] = useState('FIELD_TECHNICIAN');
  const [showPassword, setShowPassword] = useState(true);
  const [copiedPassword, setCopiedPassword] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  // Post-creation one-time credentials modal state
  const [createdAccount, setCreatedAccount] = useState(null);

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
      setFirstName('');
      setLastName('');
      setEmail(employee.email || '');
      setPhone(employee.phone || '');
      setCreateLogin(false);
      setPassword('');
      setCreatedAccount(null);
    } else {
      // Defaults for new employee
      const randomSuffix = Math.floor(100 + Math.random() * 900);
      setEmployeeCode(`EMP-${randomSuffix}`);
      setDesignation('');
      setEmploymentType('FULL_TIME');
      setJoiningDate(new Date().toISOString().split('T')[0]);
      setExitDate('');
      setEmergencyContact('');
      setFirstName('');
      setLastName('');
      setFullName('');
      setEmail('');
      setPhone('');
      setCreateLogin(true);
      setPassword(generateHumanFriendlyPassword());
      setRoleSlug('FIELD_TECHNICIAN');
      setShowPassword(true);
      setCreatedAccount(null);
    }
    setCopiedPassword(false);
    setCopiedEmail(false);
    setCopiedAll(false);
    setError(null);
  }, [employee, isOpen]);

  // Debounced server-side unique email check & generation for conflict resolution
  useEffect(() => {
    if (isEditing) return;
    const fn = firstName.trim();
    const ln = lastName.trim();

    if (!fn) {
      setEmail('');
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await generateEmployeeEmail(fn, ln);
        const data = res?.data?.data || res?.data || res;
        if (data?.email) {
          setEmail(data.email);
        }
      } catch {
        // Fallback already populated via immediate client preview
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [firstName, lastName, isEditing]);

  const handleNameChange = (newFirst, newLast) => {
    setFirstName(newFirst);
    setLastName(newLast);
    const combined = `${newFirst || ''} ${newLast || ''}`.trim();
    setFullName(combined);

    // Instant client-side preview
    const preview = generateWorkEmailPreview(newFirst, newLast);
    setEmail(preview);
  };

  if (!isOpen) return null;

  const handleRegeneratePassword = () => {
    const freshPassword = generateHumanFriendlyPassword();
    setPassword(freshPassword);
    setCopiedPassword(false);
  };

  const handleCopyPassword = (textToCopy) => {
    const val = textToCopy || password;
    if (!val) return;
    navigator.clipboard.writeText(val);
    setCopiedPassword(true);
    setTimeout(() => setCopiedPassword(false), 2000);
  };

  const handleCopyEmail = (emailToCopy) => {
    const val = emailToCopy || email;
    if (!val) return;
    navigator.clipboard.writeText(val);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  const handleCopyAllCredentials = () => {
    if (!createdAccount) return;
    const text = [
      '--- SunPower SIMS Login Credentials ---',
      `Full Name: ${createdAccount.fullName}`,
      `Employee Code: ${createdAccount.employeeCode}`,
      `Role: ${createdAccount.roleLabel}`,
      `Work Login Email: ${createdAccount.email}`,
      `Temporary Password: ${createdAccount.password}`,
      `System URL: ${window.location.origin}/login`,
      '---------------------------------------',
      'Note: This is an internal SIMS work identity for application access.',
      'Please sign in and change your password upon initial login.',
    ].join('\n');
    navigator.clipboard.writeText(text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleFinalDismiss = () => {
    setCreatedAccount(null);
    if (onSaved) onSaved();
    onClose();
  };

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
          // Preserving existing email in edit mode (not overwritten)
        };
        await updateEmployee(employee.id, payload);
        if (onSaved) onSaved();
        onClose();
      } else {
        const resolvedFullName = (fullName.trim() || `${firstName.trim()} ${lastName.trim()}`).trim();
        if (!resolvedFullName) {
          setError('First Name and Last Name are required.');
          setLoading(false);
          return;
        }

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
          full_name: resolvedFullName,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          email: email.trim() || null,
          phone: phone.trim() || null,
          role_slug: roleSlug,
          create_login_account: createLogin,
          password: createLogin ? password : null,
        };
        const res = await createEmployee(payload);
        const createdEmp = res?.data?.data || res?.data || res;
        const assignedEmail = createdEmp?.email || email.trim();

        if (createLogin) {
          const roleObj = SYSTEM_INTERNAL_ROLES.find((r) => r.slug === roleSlug);
          setCreatedAccount({
            fullName: resolvedFullName,
            employeeCode: payload.employee_code,
            email: assignedEmail,
            roleSlug: payload.role_slug,
            roleLabel: roleObj ? roleObj.label : payload.role_slug,
            password: payload.password,
          });
        } else {
          if (onSaved) onSaved();
          onClose();
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to save employee profile');
    } finally {
      setLoading(false);
    }
  };

  // Render Post-Creation Credentials Modal when createdAccount is set
  if (createdAccount) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-white rounded-2xl border border-slate-200 max-w-lg w-full p-6 shadow-2xl space-y-5 my-8 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  Employee Created Successfully
                </h3>
                <p className="text-xs text-slate-500">
                  Login account provisioned with automated work email and credentials
                </p>
              </div>
            </div>
            <button
              onClick={handleFinalDismiss}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg transition"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Employee Summary Card */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs space-y-2">
            <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Employee Name:</span>
              <span className="font-bold text-slate-900">{createdAccount.fullName}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">Employee Code:</span>
              <span className="font-mono font-bold text-slate-900">{createdAccount.employeeCode}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-slate-200/60">
              <span className="text-slate-500 font-medium">System Role:</span>
              <span className="font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                {createdAccount.roleLabel}
              </span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-slate-500 font-medium">Work Login Email:</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-slate-800 font-bold">{createdAccount.email}</span>
                <button
                  type="button"
                  onClick={() => handleCopyEmail(createdAccount.email)}
                  className="p-1 text-slate-400 hover:text-amber-600 rounded transition"
                  title="Copy work email"
                >
                  {copiedEmail ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>

          {/* Temporary Password Box */}
          <div className="bg-amber-50/80 rounded-xl p-4 border border-amber-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                <KeyRound className="w-4 h-4 text-amber-600" />
                Temporary Generated Password
              </span>
              <span className="text-[10px] font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                Shown Once
              </span>
            </div>

            <div className="bg-white border border-amber-300 rounded-lg p-3 flex items-center justify-between shadow-inner">
              <span className="font-mono font-bold text-base text-slate-900 tracking-wider select-all">
                {showPassword ? createdAccount.password : '••••••••••••••••'}
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded transition"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => handleCopyPassword(createdAccount.password)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-sm"
                >
                  {copiedPassword ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-slate-950" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Security Alert & Mailbox Notice */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 space-y-1">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-[11px] leading-relaxed">
                <span className="font-bold">SIMS Authentication Account:</span> The generated work email and temporary password serve as internal SIMS access credentials. External email inboxes are not provisioned. Share these details securely with the employee.
              </div>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
            <button
              type="button"
              onClick={handleCopyAllCredentials}
              className="px-3.5 py-2 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 text-xs font-medium transition inline-flex items-center gap-1.5"
            >
              {copiedAll ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedAll ? 'Credentials Copied!' : 'Copy All Details'}</span>
            </button>
            <button
              type="button"
              onClick={handleFinalDismiss}
              className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shadow-sm"
            >
              Done & Close
            </button>
          </div>
        </div>
      </div>
    );
  }

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

            {!isEditing ? (
              <div className="space-y-3">
                {/* First and Last Name inputs */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      First Name <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={firstName}
                      onChange={(e) => handleNameChange(e.target.value, lastName)}
                      placeholder="e.g. Ramesh"
                      required
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Last Name <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => handleNameChange(firstName, e.target.value)}
                      placeholder="e.g. Kumar"
                      required
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>

                {/* Auto-generated Work Email & Phone */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-xs font-medium text-slate-700">
                        Generated Work Email <span className="text-rose-500">*</span>
                      </label>
                      <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <Mail className="w-2.5 h-2.5" />
                        @{COMPANY_EMAIL_DOMAIN}
                      </span>
                    </div>
                    <div className="relative flex items-center">
                      <input
                        type="email"
                        value={email}
                        readOnly
                        placeholder="firstname.lastname@sunpower.com"
                        required
                        className="w-full bg-slate-100 border border-slate-200 rounded-lg pl-3 pr-10 py-2 text-xs font-mono font-medium text-slate-800 focus:outline-none cursor-default select-all"
                      />
                      <button
                        type="button"
                        onClick={() => handleCopyEmail(email)}
                        disabled={!email}
                        className="absolute right-1.5 p-1 text-slate-400 hover:text-amber-600 disabled:opacity-30 rounded transition"
                        title="Copy work email"
                      >
                        {copiedEmail ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Format: firstname.lastname@{COMPANY_EMAIL_DOMAIN}</span>
                      {copiedEmail && <span className="text-emerald-600 font-semibold">Copied!</span>}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Phone Number
                    </label>
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
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-1">
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="sm:col-span-1">
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Work Email (Locked)
                  </label>
                  <input
                    type="email"
                    value={email}
                    disabled
                    className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono text-slate-500 cursor-not-allowed"
                  />
                  <p className="mt-0.5 text-[10px] text-slate-400">Preserved for audit integrity</p>
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
            )}
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
                    onChange={(e) => {
                      const willCreate = e.target.checked;
                      setCreateLogin(willCreate);
                      if (willCreate && !password) {
                        setPassword(generateHumanFriendlyPassword());
                      }
                    }}
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
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-xs font-medium text-slate-700">
                        Generated Password <span className="text-red-500">*</span>
                      </label>
                      <button
                        type="button"
                        onClick={handleRegeneratePassword}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-600 hover:text-amber-700 transition"
                        title="Generate a new human-friendly temporary password"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Regenerate</span>
                      </button>
                    </div>

                    <div className="relative flex items-center">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="e.g. Solar@4821Sun"
                        required={createLogin}
                        minLength={8}
                        className="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-16 py-2 text-xs font-mono font-medium text-slate-900 focus:outline-none focus:border-amber-500 shadow-sm"
                      />
                      <div className="absolute right-1.5 flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
                          title={showPassword ? 'Hide password' : 'Show password'}
                        >
                          {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleCopyPassword(password)}
                          className="p-1 text-slate-400 hover:text-amber-600 rounded transition"
                          title="Copy temporary password"
                        >
                          {copiedPassword ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Human-friendly format (e.g. Solar@4821Sun)</span>
                      {copiedPassword && <span className="text-emerald-600 font-semibold">Copied!</span>}
                    </div>
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
