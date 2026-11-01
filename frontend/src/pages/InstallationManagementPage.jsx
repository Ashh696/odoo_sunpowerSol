import React, { useState, useEffect } from 'react';
import {
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Clock,
  User,
  Plus,
  RefreshCw,
  Search,
  CheckSquare,
  Zap,
  Activity,
  FileCheck,
  Star,
  X,
  ShieldCheck,
  Check,
} from 'lucide-react';
import {
  getInstallations,
  getInstallation,
  createInstallation,
  updateInstallationStatus,
  getInstallationSchedules,
  createInstallationSchedule,
  updateInstallationScheduleStatus,
  updateChecklistItem,
  submitTechnicianWorklog,
  approveTechnicianWorklog,
  recordInstallationTest,
  recordMaterialConsumption,
  recordCustomerAcceptance,
} from '../services/installationApi';
import { getProjects } from '../services/projectApi';

export default function InstallationManagementPage() {
  const [activeTab, setActiveTab] = useState('installations'); // 'installations' | 'schedules'
  const [installations, setInstallations] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  // Selected Detail Modal
  const [selectedInst, setSelectedInst] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeDetailTab, setActiveDetailTab] = useState('checklists'); // 'checklists' | 'tests' | 'worklogs' | 'materials' | 'acceptance'

  // Modals for Actions
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showAcceptanceModal, setShowAcceptanceModal] = useState(false);
  const [acceptanceForm, setAcceptanceForm] = useState({
    rating_overall: 5,
    satisfaction_notes: '',
    is_accepted: true,
  });

  // Test form state
  const [testForm, setTestForm] = useState({
    test_name: 'VOC_TEST',
    standard_value: '',
    measured_value: '',
    unit_of_measure: 'Volts',
    is_passed: true,
    tested_by: '',
    remarks: '',
  });

  // Worklog form state
  const [worklogForm, setWorklogForm] = useState({
    employee_id: '',
    hours_worked: 8,
    work_description: '',
  });

  // Projects list for creation
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchInstallations();
    fetchSchedules();
    fetchProjectsList();
  }, [statusFilter]);

  const fetchInstallations = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      const res = await getInstallations(params);
      if (res.data?.success) {
        setInstallations(res.data.data.items || []);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load installations');
    } finally {
      setLoading(false);
    }
  };

  const fetchSchedules = async () => {
    try {
      const res = await getInstallationSchedules();
      if (res.data?.success) {
        setSchedules(res.data.data.items || []);
      }
    } catch (err) {
      console.error('Failed to load schedules', err);
    }
  };

  const fetchProjectsList = async () => {
    try {
      const res = await getProjects();
      if (res.data?.success) {
        setProjects(res.data.data.items || res.data.data || []);
      }
    } catch (err) {
      console.error('Failed to load projects list', err);
    }
  };

  const handleOpenDetail = async (instId) => {
    setDetailLoading(true);
    try {
      const res = await getInstallation(instId);
      if (res.data?.success) {
        setSelectedInst(res.data.data);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load installation details');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleToggleChecklist = async (checklistId, currentChecked) => {
    try {
      const res = await updateChecklistItem(checklistId, {
        is_checked: !currentChecked,
        remarks: !currentChecked ? 'Verified on site' : '',
      });
      if (res.data?.success && selectedInst) {
        handleOpenDetail(selectedInst.id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update checklist item');
    }
  };

  const handleRecordTestSubmit = async (e) => {
    e.preventDefault();
    if (!selectedInst) return;
    try {
      const res = await recordInstallationTest(selectedInst.id, {
        ...testForm,
        tested_by: Number(testForm.tested_by || selectedInst.lead_technician_id),
      });
      if (res.data?.success) {
        alert('Electrical test recorded successfully!');
        setTestForm({
          test_name: 'VOC_TEST',
          standard_value: '',
          measured_value: '',
          unit_of_measure: 'Volts',
          is_passed: true,
          tested_by: '',
          remarks: '',
        });
        handleOpenDetail(selectedInst.id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record test');
    }
  };

  const handleWorklogSubmit = async (e) => {
    e.preventDefault();
    if (!selectedInst) return;
    try {
      const res = await submitTechnicianWorklog(selectedInst.id, {
        employee_id: Number(worklogForm.employee_id || selectedInst.lead_technician_id),
        hours_worked: Number(worklogForm.hours_worked),
        work_description: worklogForm.work_description,
      });
      if (res.data?.success) {
        alert('Worklog submitted successfully!');
        setWorklogForm({ employee_id: '', hours_worked: 8, work_description: '' });
        handleOpenDetail(selectedInst.id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to log hours');
    }
  };

  const handleApproveWorklog = async (worklogId) => {
    try {
      const res = await approveTechnicianWorklog(worklogId);
      if (res.data?.success && selectedInst) {
        handleOpenDetail(selectedInst.id);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve worklog');
    }
  };

  const handleAcceptanceSubmit = async (e) => {
    e.preventDefault();
    if (!selectedInst) return;
    try {
      const res = await recordCustomerAcceptance(selectedInst.id, acceptanceForm);
      if (res.data?.success) {
        alert('Customer acceptance and project commissioning recorded successfully!');
        setShowAcceptanceModal(false);
        handleOpenDetail(selectedInst.id);
        fetchInstallations();
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record customer acceptance');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
            <Wrench className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Installation & Commissioning</h2>
            <p className="text-xs text-slate-500">
              Manage on-site technician teams, checklists, electrical testing, and customer sign-off
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs font-medium">
            <button
              onClick={() => setActiveTab('installations')}
              className={`px-3 py-1.5 rounded-md transition ${
                activeTab === 'installations'
                  ? 'bg-white text-slate-900 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Active Installations
            </button>
            <button
              onClick={() => setActiveTab('schedules')}
              className={`px-3 py-1.5 rounded-md transition ${
                activeTab === 'schedules'
                  ? 'bg-white text-slate-900 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Team Schedules
            </button>
          </div>

          <button
            onClick={() => {
              fetchInstallations();
              fetchSchedules();
            }}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: INSTALLATIONS LIST */}
      {activeTab === 'installations' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500"
              >
                <option value="">All Statuses</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="PENDING_INSPECTION">PENDING_INSPECTION</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="COMMISSIONED">COMMISSIONED</option>
              </select>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
                <span>Loading installations...</span>
              </div>
            ) : installations.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No installation records found. Dispatched projects will appear here once initial setup begins.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-bold tracking-wider">
                      <th className="py-3 px-4">Project</th>
                      <th className="py-3 px-4">Lead Technician</th>
                      <th className="py-3 px-4">System Specs</th>
                      <th className="py-3 px-4">Start Date</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Commissioned</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {installations.map((inst) => (
                      <tr key={inst.id} className="hover:bg-slate-50/70 transition">
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900">{inst.project_code}</div>
                          <div className="text-[11px] text-slate-500">{inst.customer_name}</div>
                        </td>
                        <td className="py-3 px-4 text-slate-800 font-medium">
                          {inst.lead_technician_name || `Emp #${inst.lead_technician_id}`}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900">{inst.system_capacity_kw} kW</div>
                          <div className="text-[11px] text-slate-500">
                            {inst.total_panels_installed} panels • {inst.structure_type || 'Rooftop'}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-600">{inst.installation_date}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide ${
                              inst.status === 'COMPLETED' || inst.status === 'COMMISSIONED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : inst.status === 'PENDING_INSPECTION'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {inst.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {inst.is_commissioned ? (
                            <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Sign-off Done
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-slate-400 text-[11px]">
                              <Clock className="w-3.5 h-3.5" /> Pending
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleOpenDetail(inst.id)}
                            className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-medium text-xs shadow-xs"
                          >
                            Manage
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
      )}

      {/* TAB 2: SCHEDULES LIST */}
      {activeTab === 'schedules' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-bold tracking-wider">
                    <th className="py-3 px-4">Project</th>
                    <th className="py-3 px-4">Scheduled Window</th>
                    <th className="py-3 px-4">Team Assigned</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {schedules.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{s.project_code}</div>
                        <div className="text-[11px] text-slate-500">{s.customer_name}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {s.scheduled_start_date} → {s.scheduled_end_date}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {s.technicians?.map((t) => (
                            <span
                              key={t.id}
                              className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 text-[10px] font-semibold border border-slate-200"
                            >
                              {t.employee_name || `Emp #${t.employee_id}`} ({t.role_in_team})
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500 max-w-xs truncate">{s.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* DETAIL MODAL */}
      {selectedInst && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-4 border border-slate-200 shadow-xl">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">
                    Project: {selectedInst.project_code}
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    {selectedInst.status}
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Customer: {selectedInst.customer_name} • Capacity: {selectedInst.system_capacity_kw} kW • Lead Tech: {selectedInst.lead_technician_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedInst(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-tabs */}
            <div className="flex border-b border-slate-200 text-xs font-semibold space-x-4">
              <button
                onClick={() => setActiveDetailTab('checklists')}
                className={`pb-2 border-b-2 transition ${
                  activeDetailTab === 'checklists'
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Quality & Safety Checklist ({selectedInst.checklists?.length || 0})
              </button>
              <button
                onClick={() => setActiveDetailTab('tests')}
                className={`pb-2 border-b-2 transition ${
                  activeDetailTab === 'tests'
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Electrical Tests ({selectedInst.tests?.length || 0})
              </button>
              <button
                onClick={() => setActiveDetailTab('worklogs')}
                className={`pb-2 border-b-2 transition ${
                  activeDetailTab === 'worklogs'
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Daily Worklogs ({selectedInst.worklogs?.length || 0})
              </button>
              <button
                onClick={() => setActiveDetailTab('acceptance')}
                className={`pb-2 border-b-2 transition ${
                  activeDetailTab === 'acceptance'
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Customer Sign-off
              </button>
            </div>

            {/* TAB CONTENT: CHECKLISTS */}
            {activeDetailTab === 'checklists' && (
              <div className="space-y-3">
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {selectedInst.checklists?.map((cl) => (
                    <div
                      key={cl.id}
                      onClick={() => handleToggleChecklist(cl.id, cl.is_checked)}
                      className="p-3 flex items-start gap-3 hover:bg-slate-50 cursor-pointer transition"
                    >
                      <input
                        type="checkbox"
                        checked={cl.is_checked}
                        onChange={() => {}}
                        className="mt-0.5 rounded text-amber-600 focus:ring-amber-500"
                      />
                      <div className="flex-1 text-xs">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-semibold ${
                              cl.is_checked ? 'line-through text-slate-400' : 'text-slate-800'
                            }`}
                          >
                            {cl.checklist_item}
                          </span>
                          <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 text-[9px] uppercase font-bold">
                            {cl.category}
                          </span>
                        </div>
                        {cl.is_checked && cl.verifier_name && (
                          <div className="text-[10px] text-emerald-600 mt-0.5">
                            Verified by {cl.verifier_name} {cl.remarks ? `• ${cl.remarks}` : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT: ELECTRICAL TESTS */}
            {activeDetailTab === 'tests' && (
              <div className="space-y-4">
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-bold uppercase tracking-wider">
                      <tr>
                        <th className="py-2.5 px-3">Test Name</th>
                        <th className="py-2.5 px-3">Standard Spec</th>
                        <th className="py-2.5 px-3">Measured</th>
                        <th className="py-2.5 px-3">Result</th>
                        <th className="py-2.5 px-3">Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedInst.tests?.map((t) => (
                        <tr key={t.id}>
                          <td className="py-2.5 px-3 font-semibold text-slate-900">{t.test_name}</td>
                          <td className="py-2.5 px-3 text-slate-500">{t.standard_value || 'N/A'}</td>
                          <td className="py-2.5 px-3 font-mono font-bold text-slate-800">
                            {t.measured_value} {t.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-3">
                            {t.is_passed ? (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                PASSED
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                                FAILED
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-slate-600">{t.remarks || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Test Recording Form */}
                <form
                  onSubmit={handleRecordTestSubmit}
                  className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs"
                >
                  <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">
                    Record New Electrical Test
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-slate-600 font-medium mb-1">Test Type</label>
                      <select
                        value={testForm.test_name}
                        onChange={(e) => setTestForm({ ...testForm, test_name: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500"
                      >
                        <option value="VOC_TEST">VOC_TEST (Open-circuit Voltage)</option>
                        <option value="ISC_TEST">ISC_TEST (Short-circuit Current)</option>
                        <option value="INSULATION_RESISTANCE">INSULATION_RESISTANCE (Megaohms)</option>
                        <option value="EARTHING_RESISTANCE">EARTHING_RESISTANCE (Ohms)</option>
                        <option value="GRID_SYNC">GRID_SYNC (Inverter Grid Tie)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-slate-600 font-medium mb-1">Measured Value *</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. 448.5V"
                        value={testForm.measured_value}
                        onChange={(e) => setTestForm({ ...testForm, measured_value: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-600 font-medium mb-1">Standard / Nominal Value</label>
                      <input
                        type="text"
                        placeholder="e.g. 450V"
                        value={testForm.standard_value}
                        onChange={(e) => setTestForm({ ...testForm, standard_value: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg text-xs transition"
                    >
                      Record Test
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* TAB CONTENT: WORKLOGS */}
            {activeDetailTab === 'worklogs' && (
              <div className="space-y-4">
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-bold uppercase tracking-wider">
                      <tr>
                        <th className="py-2 px-3">Date</th>
                        <th className="py-2 px-3">Technician</th>
                        <th className="py-2 px-3 text-right">Hours</th>
                        <th className="py-2 px-3">Description</th>
                        <th className="py-2 px-3">Approval</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedInst.worklogs?.map((w) => (
                        <tr key={w.id}>
                          <td className="py-2 px-3 text-slate-600">{w.work_date}</td>
                          <td className="py-2 px-3 font-semibold text-slate-800">{w.employee_name}</td>
                          <td className="py-2 px-3 text-right font-bold text-slate-900">{w.hours_worked} hrs</td>
                          <td className="py-2 px-3 text-slate-700">{w.work_description}</td>
                          <td className="py-2 px-3">
                            {w.approved_by ? (
                              <span className="text-emerald-700 font-semibold text-[11px] flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3" /> Approved
                              </span>
                            ) : (
                              <button
                                onClick={() => handleApproveWorklog(w.id)}
                                className="px-2 py-0.5 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded font-medium text-[10px]"
                              >
                                Approve
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <form
                  onSubmit={handleWorklogSubmit}
                  className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs"
                >
                  <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Log Hours Worked</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-600 font-medium mb-1">Hours Worked</label>
                      <input
                        type="number"
                        min="0.5"
                        max="24"
                        step="0.5"
                        required
                        value={worklogForm.hours_worked}
                        onChange={(e) => setWorklogForm({ ...worklogForm, hours_worked: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-600 font-medium mb-1">Work Description *</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Structure assembly and module mounting"
                        value={worklogForm.work_description}
                        onChange={(e) => setWorklogForm({ ...worklogForm, work_description: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg text-xs transition"
                    >
                      Submit Worklog
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* TAB CONTENT: ACCEPTANCE */}
            {activeDetailTab === 'acceptance' && (
              <div className="space-y-4">
                {selectedInst.customer_acceptance ? (
                  <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3 text-xs">
                    <div className="flex items-center gap-2 font-bold text-emerald-900 text-sm">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      <span>Customer Acceptance & Commissioning Completed</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-slate-800">
                      <div>
                        <span className="text-slate-500 block">Accepted On:</span>
                        <span className="font-semibold">{selectedInst.customer_acceptance.acceptance_date}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Overall Rating:</span>
                        <span className="font-semibold">{selectedInst.customer_acceptance.rating_overall} / 5 Stars</span>
                      </div>
                    </div>
                    <div className="text-slate-700 italic border-t border-emerald-100 pt-2">
                      "{selectedInst.customer_acceptance.satisfaction_notes || 'Customer fully satisfied.'}"
                    </div>
                  </div>
                ) : (
                  <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl space-y-4 text-xs">
                    <div className="flex items-center gap-2 font-bold text-slate-900">
                      <Star className="w-5 h-5 text-amber-500" />
                      <span>Customer Sign-off Pending</span>
                    </div>
                    <p className="text-slate-600">
                      Once all checklist items and electrical commissioning tests pass, record formal customer acceptance to mark the project as COMPLETED.
                    </p>

                    <form onSubmit={handleAcceptanceSubmit} className="space-y-3">
                      <div>
                        <label className="block text-slate-700 font-semibold mb-1">Customer Rating (1 to 5)</label>
                        <select
                          value={acceptanceForm.rating_overall}
                          onChange={(e) => setAcceptanceForm({ ...acceptanceForm, rating_overall: Number(e.target.value) })}
                          className="w-40 bg-white border border-slate-200 rounded p-1.5 focus:border-amber-500 font-medium"
                        >
                          <option value="5">⭐⭐⭐⭐⭐ (5 - Excellent)</option>
                          <option value="4">⭐⭐⭐⭐ (4 - Very Good)</option>
                          <option value="3">⭐⭐⭐ (3 - Satisfactory)</option>
                          <option value="2">⭐⭐ (2 - Needs Improvement)</option>
                          <option value="1">⭐ (1 - Unsatisfactory)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-slate-700 font-semibold mb-1">Customer Remarks / Testimonial</label>
                        <textarea
                          rows={2}
                          value={acceptanceForm.satisfaction_notes}
                          onChange={(e) => setAcceptanceForm({ ...acceptanceForm, satisfaction_notes: e.target.value })}
                          className="w-full bg-white border border-slate-200 rounded p-2 focus:border-amber-500"
                          placeholder="e.g. Clean installation work, generation started on schedule."
                        />
                      </div>

                      <button
                        type="submit"
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs shadow-sm transition"
                      >
                        Record Sign-off & Complete Project
                      </button>
                    </form>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
