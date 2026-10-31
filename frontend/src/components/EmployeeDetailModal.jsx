import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Building2,
  Mail,
  Phone,
  Calendar,
  Shield,
  Award,
  Plus,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  fetchEmployeeById,
  fetchSkills,
  assignEmployeeSkill,
  removeEmployeeSkill,
  addEmployeeCertification,
} from '../services/employeeApi';

export default function EmployeeDetailModal({ isOpen, onClose, employeeId, onUpdated }) {
  const [employee, setEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, skills, certifications
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Available skills catalog for assignment dropdown
  const [availableSkills, setAvailableSkills] = useState([]);
  const [showAssignSkill, setShowAssignSkill] = useState(false);
  const [newSkillId, setNewSkillId] = useState('');
  const [proficiency, setProficiency] = useState('INTERMEDIATE');
  const [experienceYears, setExperienceYears] = useState(1.0);
  const [isSkillVerified, setIsSkillVerified] = useState(true);

  // Certification add form state
  const [showAddCert, setShowAddCert] = useState(false);
  const [certName, setCertName] = useState('');
  const [certAuthority, setCertAuthority] = useState('');
  const [certNumber, setCertNumber] = useState('');
  const [certIssueDate, setCertIssueDate] = useState(new Date().toISOString().split('T')[0]);
  const [certExpiryDate, setCertExpiryDate] = useState('');
  const [certStatus, setCertStatus] = useState('VERIFIED');

  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async () => {
    if (!employeeId) return;
    setLoading(true);
    setError(null);
    try {
      const [empRes, skillRes] = await Promise.all([
        fetchEmployeeById(employeeId),
        fetchSkills({ is_active: true }),
      ]);
      setEmployee(empRes?.data || null);
      setAvailableSkills(skillRes?.data || []);
      if (skillRes?.data?.length > 0 && !newSkillId) {
        setNewSkillId(skillRes.data[0].id);
      }
    } catch (err) {
      setError(err.message || 'Failed to load employee details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && employeeId) {
      loadData();
    }
  }, [isOpen, employeeId]);

  if (!isOpen) return null;

  const handleAssignSkill = async (e) => {
    e.preventDefault();
    if (!newSkillId) return;
    setActionLoading(true);
    try {
      await assignEmployeeSkill(employeeId, {
        skill_id: Number(newSkillId),
        proficiency_level: proficiency,
        years_of_experience: Number(experienceYears),
        is_verified: isSkillVerified,
      });
      setShowAssignSkill(false);
      await loadData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert(`Failed to assign skill: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveSkill = async (skillId, skillName) => {
    if (!window.confirm(`Remove skill '${skillName}' from this employee?`)) return;
    try {
      await removeEmployeeSkill(employeeId, skillId);
      await loadData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert(`Failed to remove skill: ${err.message}`);
    }
  };

  const handleAddCertification = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await addEmployeeCertification(employeeId, {
        certification_name: certName.trim(),
        issuing_authority: certAuthority.trim(),
        certificate_number: certNumber.trim() || null,
        issue_date: certIssueDate,
        expiry_date: certExpiryDate ? certExpiryDate : null,
        verification_status: certStatus,
      });
      setShowAddCert(false);
      setCertName('');
      setCertAuthority('');
      setCertNumber('');
      await loadData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert(`Failed to add certification: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 max-w-3xl w-full p-6 shadow-2xl space-y-6 my-8">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-lg uppercase shadow-md">
              {employee?.full_name?.charAt(0) || 'E'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-extrabold text-slate-900 text-lg">
                  {employee?.full_name || 'Loading...'}
                </h3>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    employee?.is_active
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {employee?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                {employee?.designation} • <span className="font-mono text-amber-600">{employee?.employee_code}</span>
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

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-100 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-2.5 px-3 border-b-2 transition ${
              activeTab === 'overview'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Overview & Account
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'skills'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Assigned Skills</span>
            <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[10px]">
              {employee?.skills?.length || 0}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('certifications')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'certifications'
                ? 'border-amber-500 text-amber-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Certifications & Safety</span>
            <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[10px]">
              {employee?.certifications?.length || 0}
            </span>
          </button>
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading profile details...</div>
        ) : (
          <div>
            {/* OVERVIEW TAB */}
            {activeTab === 'overview' && (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-2">
                    <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                      <Building2 className="w-4 h-4 text-amber-500" />
                      Department & Employment
                    </h4>
                    <div className="divide-y divide-slate-200/60">
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Department</span>
                        <span className="font-semibold text-slate-800">{employee.department_name} ({employee.department_code})</span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Employment Type</span>
                        <span className="font-semibold text-slate-800">{employee.employment_type}</span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Joining Date</span>
                        <span className="font-semibold text-slate-800">{employee.joining_date}</span>
                      </div>
                      {employee.exit_date && (
                        <div className="py-1.5 flex justify-between text-rose-600">
                          <span>Exit Date</span>
                          <span className="font-semibold">{employee.exit_date}</span>
                        </div>
                      )}
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Emergency Contact</span>
                        <span className="font-semibold text-slate-800">{employee.emergency_contact || 'None listed'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-2">
                    <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                      <Shield className="w-4 h-4 text-amber-500" />
                      Linked User & Login Account
                    </h4>
                    <div className="divide-y divide-slate-200/60">
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">User ID</span>
                        <span className="font-mono text-slate-800">{employee.user_id}</span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Email Address</span>
                        <span className="font-semibold text-slate-800">{employee.email}</span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Phone Number</span>
                        <span className="font-semibold text-slate-800">{employee.phone || 'None'}</span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Assigned Role</span>
                        <span className="font-mono bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded text-[10px]">
                          {employee.user_role || 'No Role'}
                        </span>
                      </div>
                      <div className="py-1.5 flex justify-between">
                        <span className="text-slate-500">Portal Login Status</span>
                        <span className="font-bold text-emerald-600">
                          {employee.has_login_access ? 'Login Enabled' : 'No Login (Staff Profile Only)'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SKILLS TAB */}
            {activeTab === 'skills' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Technical Capabilities ({employee.skills?.length || 0})
                  </h4>
                  <button
                    onClick={() => setShowAssignSkill(!showAssignSkill)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg text-xs font-bold transition shadow-sm"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Assign Skill</span>
                  </button>
                </div>

                {showAssignSkill && (
                  <form onSubmit={handleAssignSkill} className="p-4 bg-slate-50 border border-amber-200 rounded-xl text-xs space-y-3">
                    <h5 className="font-bold text-slate-800">Assign Technical Skill</h5>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Skill Catalog</label>
                        <select
                          value={newSkillId}
                          onChange={(e) => setNewSkillId(e.target.value)}
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                          required
                        >
                          {availableSkills.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} ({s.category})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Proficiency</label>
                        <select
                          value={proficiency}
                          onChange={(e) => setProficiency(e.target.value)}
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        >
                          <option value="BEGINNER">Beginner</option>
                          <option value="INTERMEDIATE">Intermediate</option>
                          <option value="EXPERT">Expert</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Experience (Years)</label>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          value={experienceYears}
                          onChange={(e) => setExperienceYears(e.target.value)}
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                          required
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <label className="flex items-center gap-2 cursor-pointer text-slate-700">
                        <input
                          type="checkbox"
                          checked={isSkillVerified}
                          onChange={(e) => setIsSkillVerified(e.target.checked)}
                          className="rounded text-amber-500"
                        />
                        <span>Mark as verified by current supervisor</span>
                      </label>

                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setShowAssignSkill(false)}
                          className="px-3 py-1 bg-slate-200 rounded text-slate-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={actionLoading}
                          className="px-4 py-1 bg-amber-500 font-bold text-slate-950 rounded hover:bg-amber-400"
                        >
                          {actionLoading ? 'Assigning...' : 'Assign'}
                        </button>
                      </div>
                    </div>
                  </form>
                )}

                {employee.skills?.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No skills assigned yet. Click "Assign Skill" to log solar installation competencies.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {employee.skills.map((es) => (
                      <div
                        key={es.id}
                        className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm flex items-center justify-between hover:border-amber-300 transition"
                      >
                        <div className="space-y-1">
                          <div className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                            <span>{es.skill_name}</span>
                            <span className="bg-slate-100 text-slate-600 text-[10px] px-1.5 py-0.2 rounded font-mono">
                              {es.skill_category}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 flex items-center gap-2">
                            <span
                              className={`font-semibold ${
                                es.proficiency_level === 'EXPERT'
                                  ? 'text-amber-600'
                                  : 'text-slate-700'
                              }`}
                            >
                              {es.proficiency_level}
                            </span>
                            <span>•</span>
                            <span>{es.years_of_experience} yrs exp</span>
                            {es.verified_at && (
                              <span className="text-emerald-600 flex items-center gap-0.5 text-[10px]">
                                <CheckCircle className="w-3 h-3" /> Verified
                              </span>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => handleRemoveSkill(es.skill_id, es.skill_name)}
                          title="Remove skill"
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CERTIFICATIONS TAB */}
            {activeTab === 'certifications' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Certifications & Safety Records ({employee.certifications?.length || 0})
                  </h4>
                  <button
                    onClick={() => setShowAddCert(!showAddCert)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg text-xs font-bold transition shadow-sm"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Certification</span>
                  </button>
                </div>

                {showAddCert && (
                  <form onSubmit={handleAddCertification} className="p-4 bg-slate-50 border border-amber-200 rounded-xl text-xs space-y-3">
                    <h5 className="font-bold text-slate-800">Add Technical / Safety Certification</h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Certification Name *</label>
                        <input
                          type="text"
                          value={certName}
                          onChange={(e) => setCertName(e.target.value)}
                          placeholder="e.g. Working at Heights Level 2"
                          required
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Issuing Authority *</label>
                        <input
                          type="text"
                          value={certAuthority}
                          onChange={(e) => setCertAuthority(e.target.value)}
                          placeholder="e.g. National Safety Council / MNRE"
                          required
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Certificate Number</label>
                        <input
                          type="text"
                          value={certNumber}
                          onChange={(e) => setCertNumber(e.target.value)}
                          placeholder="e.g. CERT-2026-990"
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Verification Status</label>
                        <select
                          value={certStatus}
                          onChange={(e) => setCertStatus(e.target.value)}
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        >
                          <option value="VERIFIED">Verified</option>
                          <option value="PENDING">Pending Verification</option>
                          <option value="EXPIRED">Expired</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Issue Date *</label>
                        <input
                          type="date"
                          value={certIssueDate}
                          onChange={(e) => setCertIssueDate(e.target.value)}
                          required
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-slate-600 mb-1 font-medium">Expiry Date (optional)</label>
                        <input
                          type="date"
                          value={certExpiryDate}
                          onChange={(e) => setCertExpiryDate(e.target.value)}
                          className="w-full bg-white border border-slate-200 rounded px-2.5 py-1.5 text-xs"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => setShowAddCert(false)}
                        className="px-3 py-1 bg-slate-200 rounded text-slate-700"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={actionLoading}
                        className="px-4 py-1 bg-amber-500 font-bold text-slate-950 rounded hover:bg-amber-400"
                      >
                        {actionLoading ? 'Recording...' : 'Add Certificate'}
                      </button>
                    </div>
                  </form>
                )}

                {employee.certifications?.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No certifications recorded for this employee yet.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {employee.certifications.map((c) => (
                      <div
                        key={c.id}
                        className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                          c.is_expired
                            ? 'bg-rose-50/60 border-rose-200'
                            : c.days_to_expiry !== null && c.days_to_expiry <= 30
                            ? 'bg-amber-50/60 border-amber-200'
                            : 'bg-white border-slate-200'
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{c.certification_name}</span>
                            {c.certificate_number && (
                              <span className="text-[10px] text-slate-400 font-mono">
                                #{c.certificate_number}
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            Authority: <span className="font-medium text-slate-700">{c.issuing_authority}</span> • Issued: {c.issue_date}
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-[10px] text-slate-400">
                              {c.expiry_date ? `Expires: ${c.expiry_date}` : 'No Expiry'}
                            </div>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                c.is_expired
                                  ? 'bg-rose-100 text-rose-800'
                                  : c.days_to_expiry !== null && c.days_to_expiry <= 30
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-emerald-100 text-emerald-800'
                              }`}
                            >
                              {c.is_expired
                                ? 'EXPIRED'
                                : c.days_to_expiry !== null && c.days_to_expiry <= 30
                                ? `${c.days_to_expiry}d to expiry`
                                : c.verification_status}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="border-t border-slate-100 pt-3 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
