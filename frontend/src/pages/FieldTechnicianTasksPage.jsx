import React, { useState, useEffect } from 'react';
import {
  Wrench,
  Compass,
  CheckCircle2,
  Clock,
  Calendar,
  User,
  Phone,
  MapPin,
  AlertTriangle,
  Zap,
  RefreshCw,
  Plus,
  X,
  FileCheck,
  CheckSquare,
  Activity,
  ThumbsUp,
  ShieldAlert,
  Camera,
  Play,
  Check,
} from 'lucide-react';
import {
  getMyAssignedSurveys,
  getMyInstallationSchedules,
  getMyInstallations,
  getMyServiceVisits,
  submitInstallationChecklist,
  submitInstallationTest,
  recordTechnicianWorklog,
  recordMaterialConsumption,
  completeTechnicianServiceVisit,
} from '../services/technicianApi';
import { getInstallation, updateChecklistItem } from '../services/installationApi';
import SurveyObservationModal from '../components/SurveyObservationModal';

export default function FieldTechnicianTasksPage() {
  const [activeTab, setActiveTab] = useState('INSTALLATIONS'); // 'INSTALLATIONS' | 'SURVEYS' | 'SERVICE_VISITS'
  const [schedules, setSchedules] = useState([]);
  const [installations, setInstallations] = useState([]);
  const [surveys, setSurveys] = useState([]);
  const [serviceVisits, setServiceVisits] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected Survey for Observation Modal
  const [selectedSurvey, setSelectedSurvey] = useState(null);

  // Installation Detail & Actions Modal
  const [selectedInstId, setSelectedInstId] = useState(null);
  const [installationDetail, setInstallationDetail] = useState(null);
  const [instModalTab, setInstModalTab] = useState('checklists'); // 'checklists' | 'tests' | 'worklogs' | 'consumption'
  const [actionLoading, setActionLoading] = useState(false);

  // Test form
  const [testForm, setTestForm] = useState({
    test_name: 'VOC_TEST',
    standard_value: '600V',
    measured_value: '',
    unit_of_measure: 'Volts',
    is_passed: true,
    remarks: '',
  });

  // Worklog form
  const [worklogForm, setWorklogForm] = useState({
    hours_worked: 8,
    work_description: '',
  });

  // Material consumption form
  const [consumptionForm, setConsumptionForm] = useState({
    product_id: '',
    quantity_used: 1,
    serial_number_id: '',
    notes: '',
  });

  // Service Visit Completion Modal
  const [completingVisit, setCompletingVisit] = useState(null);
  const [visitForm, setVisitForm] = useState({
    findings: '',
    action_taken: '',
    parts_replaced: false,
    customer_present_name: '',
  });

  const loadTechnicianData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [schedRes, instRes, survRes, visitRes] = await Promise.allSettled([
        getMyInstallationSchedules(),
        getMyInstallations(),
        getMyAssignedSurveys(),
        getMyServiceVisits(),
      ]);

      if (schedRes.status === 'fulfilled') {
        const sItems = schedRes.value.data?.data?.items || schedRes.value.data?.items || [];
        setSchedules(sItems);
      }
      if (instRes.status === 'fulfilled') {
        const iItems = instRes.value.data?.data?.items || instRes.value.data?.items || [];
        setInstallations(iItems);
      }
      if (survRes.status === 'fulfilled') {
        const survItems = survRes.value.data?.data?.items || survRes.value.data?.items || [];
        setSurveys(survItems);
      }
      if (visitRes.status === 'fulfilled') {
        const vItems = visitRes.value.data?.data?.items || visitRes.value.data?.items || [];
        setServiceVisits(vItems);
      }
    } catch (err) {
      setError(err.message || 'Failed to aggregate technician workload');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTechnicianData();
  }, []);

  const openInstallationManager = async (instId) => {
    setSelectedInstId(instId);
    setActionLoading(true);
    try {
      const res = await getInstallation(instId);
      setInstallationDetail(res.data?.data || null);
    } catch (err) {
      alert('Failed to load installation QA details');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleChecklist = async (itemId, currentPassed) => {
    try {
      await updateChecklistItem(itemId, {
        is_passed: !currentPassed,
        remarks: !currentPassed ? 'Verified on-site by field technician' : 'Pending re-inspection',
      });
      // Refresh detail
      const res = await getInstallation(selectedInstId);
      setInstallationDetail(res.data?.data || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update checklist item');
    }
  };

  const handleRecordTest = async (e) => {
    e.preventDefault();
    if (!testForm.measured_value.trim()) {
      alert('Please enter a measured value');
      return;
    }
    setActionLoading(true);
    try {
      await submitInstallationTest(selectedInstId, {
        test_name: testForm.test_name,
        standard_value: testForm.standard_value,
        measured_value: testForm.measured_value,
        unit_of_measure: testForm.unit_of_measure,
        is_passed: testForm.is_passed,
        remarks: testForm.remarks,
      });
      alert('Electrical test result recorded successfully');
      setTestForm({ ...testForm, measured_value: '', remarks: '' });
      const res = await getInstallation(selectedInstId);
      setInstallationDetail(res.data?.data || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record test');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecordWorklog = async (e) => {
    e.preventDefault();
    if (!worklogForm.work_description.trim()) {
      alert('Please provide work description');
      return;
    }
    setActionLoading(true);
    try {
      await recordTechnicianWorklog(selectedInstId, {
        hours_worked: parseFloat(worklogForm.hours_worked),
        work_description: worklogForm.work_description,
      });
      alert('Technician worklog submitted');
      setWorklogForm({ hours_worked: 8, work_description: '' });
      const res = await getInstallation(selectedInstId);
      setInstallationDetail(res.data?.data || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit worklog');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteServiceVisit = async (e) => {
    e.preventDefault();
    if (!visitForm.findings.trim() || !visitForm.action_taken.trim()) {
      alert('Please enter on-site diagnostic findings and action taken');
      return;
    }
    setActionLoading(true);
    try {
      await completeTechnicianServiceVisit(completingVisit.id, {
        findings: visitForm.findings,
        action_taken: visitForm.action_taken,
        parts_replaced: visitForm.parts_replaced,
        customer_present_name: visitForm.customer_present_name,
      });
      alert('Service maintenance visit completed successfully');
      setCompletingVisit(null);
      setVisitForm({ findings: '', action_taken: '', parts_replaced: false, customer_present_name: '' });
      loadTechnicianData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to complete visit');
    } finally {
      setActionLoading(false);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const todaySchedules = schedules.filter((s) => s.scheduled_start_date === todayStr);

  return (
    <div className="space-y-6">
      {/* Top Mobile-First Hero Bar */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/50 rounded-2xl p-6 sm:p-8 text-white border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 mb-2">
              <Wrench className="w-3.5 h-3.5 text-amber-400" />
              <span>Field Technician Operations Command</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">My Active Field Tasks</h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-xl">
              Access your assigned rooftop solar surveys, site installation schedules, quality verification checklists, and breakdown maintenance visits.
            </p>
          </div>

          <button
            onClick={loadTechnicianData}
            className="self-start sm:self-auto p-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 transition flex items-center gap-2 text-xs font-semibold"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
            <span>Sync Workload</span>
          </button>
        </div>

        {/* Quick KPI Overview */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800 text-xs">
          <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 text-[11px] block">Assigned Surveys</span>
            <span className="text-xl font-black text-amber-400 font-mono">{surveys.length}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 text-[11px] block">Today's Visits</span>
            <span className="text-xl font-black text-emerald-400 font-mono">{todaySchedules.length}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 text-[11px] block">Installations Assigned</span>
            <span className="text-xl font-black text-white font-mono">{installations.length}</span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
            <span className="text-slate-400 text-[11px] block">Service Visits</span>
            <span className="text-xl font-black text-sky-400 font-mono">{serviceVisits.length}</span>
          </div>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs px-4 pt-2">
        <nav className="flex space-x-2 overflow-x-auto pb-2">
          {[
            { id: 'INSTALLATIONS', label: `Installation Jobs (${installations.length})`, icon: Wrench },
            { id: 'SURVEYS', label: `Site Feasibility Surveys (${surveys.length})`, icon: Compass },
            { id: 'SERVICE_VISITS', label: `Assigned Service Visits (${serviceVisits.length})`, icon: Activity },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-lg whitespace-nowrap transition ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200 flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
          <span className="text-sm font-semibold text-slate-600">Loading your assigned field tasks...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button
            onClick={loadTechnicianData}
            className="text-xs bg-rose-100 hover:bg-rose-200 text-rose-950 font-bold px-3 py-1.5 rounded-lg"
          >
            Retry
          </button>
        </div>
      ) : (
        <div>
          {/* TAB 1: INSTALLATION JOBS */}
          {activeTab === 'INSTALLATIONS' && (
            <div className="space-y-4">
              {installations.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <Wrench className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Installation Jobs Assigned</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    When the installation manager schedules a rooftop project and assigns you to the team, your checklist items will appear here.
                  </p>
                </div>
              ) : (
                installations.map((inst) => (
                  <div
                    key={inst.id}
                    className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">{inst.project_code || `INST-${inst.id}`}</span>
                          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                            {inst.status}
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-slate-900 mt-1">
                          {inst.customer_name || 'Rooftop Client'}
                        </h4>
                        <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          <span>{inst.site_address || 'Site Location'}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openInstallationManager(inst.id)}
                          className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5"
                        >
                          <CheckSquare className="w-4 h-4" />
                          <span>Launch QA Checklists & Tests</span>
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                      <div>
                        <span className="text-slate-400 text-[10px] block font-sans uppercase">Capacity</span>
                        <strong className="text-slate-900">{inst.system_capacity_kw} kW</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block font-sans uppercase">Panels</span>
                        <strong className="text-slate-900">{inst.total_panels_installed || 0} Modules</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block font-sans uppercase">Inverter</span>
                        <strong className="text-slate-900">{inst.inverter_make_model || 'Standard Inverter'}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block font-sans uppercase">Install Date</span>
                        <strong className="text-slate-900">{new Date(inst.installation_date).toLocaleDateString()}</strong>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 2: SITE FEASIBILITY SURVEYS */}
          {activeTab === 'SURVEYS' && (
            <div className="space-y-4">
              {surveys.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <Compass className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Assigned Surveys</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Site feasibility survey requests assigned to you by sales coordinators will be listed here.
                  </p>
                </div>
              ) : (
                surveys.map((surv) => (
                  <div
                    key={surv.id}
                    className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">{surv.survey_number}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          surv.status === 'APPROVED'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : surv.status === 'COMPLETED'
                            ? 'bg-blue-50 text-blue-800 border-blue-200'
                            : 'bg-amber-50 text-amber-800 border-amber-200'
                        }`}>
                          {surv.status}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-900">
                        {surv.customer_name || 'Customer Site'}
                      </h4>
                      <p className="text-xs text-slate-500 flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        <span>{surv.customer_phone || 'No phone'}</span> • <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{surv.site_address || surv.customer_city || 'Site Address'}</span>
                      </p>
                      <div className="text-xs text-slate-600 font-mono pt-1">
                        Proposed Capacity: <strong className="text-amber-700">{surv.proposed_capacity_kw} kW {surv.system_type}</strong> • Area: {surv.roof_area_sqft ? `${surv.roof_area_sqft} sq ft` : 'Pending measurement'}
                      </div>
                    </div>

                    <button
                      onClick={() => setSelectedSurvey(surv)}
                      className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 shrink-0"
                    >
                      <Compass className="w-4 h-4" />
                      <span>Record Roof Observations</span>
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 3: ASSIGNED SERVICE VISITS */}
          {activeTab === 'SERVICE_VISITS' && (
            <div className="space-y-4">
              {serviceVisits.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Service Visits Scheduled</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Maintenance visits and repair tickets assigned to you will appear here.
                  </p>
                </div>
              ) : (
                serviceVisits.map((v) => (
                  <div
                    key={v.id}
                    className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">{v.ticket_number || `Visit #${v.id}`}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {v.issue_category || 'MAINTENANCE'}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          v.visit_status === 'COMPLETED'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-amber-50 text-amber-800 border-amber-200'
                        }`}>
                          {v.visit_status}
                        </span>
                        {v.priority === 'CRITICAL' && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                            CRITICAL SLA
                          </span>
                        )}
                      </div>
                      <h4 className="text-base font-bold text-slate-900">
                        {v.customer_name || 'Customer'} • Project: {v.project_code || 'N/A'}
                      </h4>
                      <p className="text-xs text-slate-500 flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        <span>{v.customer_phone || 'N/A'}</span> • <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{v.site_address || 'Site Location'}</span>
                      </p>
                      <div className="text-xs text-slate-600 pt-1">
                        Scheduled Date: <strong className="text-slate-900">{new Date(v.scheduled_date).toLocaleDateString()}</strong>
                      </div>
                    </div>

                    {v.visit_status !== 'COMPLETED' && (
                      <button
                        onClick={() => {
                          setCompletingVisit(v);
                          setVisitForm({
                            findings: v.findings || '',
                            action_taken: v.action_taken || '',
                            parts_replaced: v.parts_replaced || false,
                            customer_present_name: v.customer_present_name || v.customer_name || '',
                          });
                        }}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 shrink-0"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Complete Visit & Diagnostic</span>
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* MODAL: SURVEY OBSERVATIONS */}
      {selectedSurvey && (
        <SurveyObservationModal
          isOpen={!!selectedSurvey}
          onClose={() => setSelectedSurvey(null)}
          onSuccess={() => {
            setSelectedSurvey(null);
            loadTechnicianData();
          }}
          survey={selectedSurvey}
        />
      )}

      {/* MODAL: INSTALLATION QA & CHECKLISTS MANAGER */}
      {selectedInstId && installationDetail && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-6 space-y-4 shadow-2xl border border-slate-200 my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-xs font-mono font-bold text-slate-500">{installationDetail.project_code}</span>
                <h3 className="text-base font-bold text-slate-900">Installation QA & Technician Field Tool</h3>
              </div>
              <button
                onClick={() => {
                  setSelectedInstId(null);
                  setInstallationDetail(null);
                }}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-tabs inside installation manager */}
            <div className="flex border-b border-slate-200 gap-4 text-xs font-bold">
              {[
                { id: 'checklists', label: `QA Checklists (${installationDetail.checklists?.length || 0})` },
                { id: 'tests', label: `Electrical Tests (${installationDetail.tests?.length || 0})` },
                { id: 'worklogs', label: `Work Hours (${installationDetail.worklogs?.length || 0})` },
              ].map((sub) => (
                <button
                  key={sub.id}
                  onClick={() => setInstModalTab(sub.id)}
                  className={`pb-2 transition border-b-2 ${
                    instModalTab === sub.id
                      ? 'border-amber-500 text-amber-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {sub.label}
                </button>
              ))}
            </div>

            {/* Tab 1: Checklists */}
            {instModalTab === 'checklists' && (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {(installationDetail.checklists || []).length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No checklist items generated yet.</p>
                ) : (
                  (installationDetail.checklists || []).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleToggleChecklist(item.id, item.is_passed)}
                      className={`p-3.5 rounded-xl border flex items-center justify-between gap-4 cursor-pointer transition ${
                        item.is_passed
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                          : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200">
                            {item.checklist_type}
                          </span>
                          <span className="text-xs font-bold">{item.item_name}</span>
                        </div>
                        <p className="text-[11px] text-slate-500">{item.remarks || 'Click to toggle pass/fail status'}</p>
                      </div>

                      <div className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                        item.is_passed ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-400'
                      }`}>
                        {item.is_passed && <Check className="w-4 h-4" />}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Tab 2: Electrical Testing Form & List */}
            {instModalTab === 'tests' && (
              <div className="space-y-4">
                <form onSubmit={handleRecordTest} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
                  <h5 className="font-bold text-slate-900 flex items-center gap-1.5">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span>Record Electrical Test Result</span>
                  </h5>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="font-bold text-slate-700 block mb-1">Test Type</label>
                      <select
                        value={testForm.test_name}
                        onChange={(e) => setTestForm({ ...testForm, test_name: e.target.value })}
                        className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white"
                      >
                        <option value="VOC_TEST">String Open Circuit (Voc)</option>
                        <option value="ISC_TEST">Short Circuit Current (Isc)</option>
                        <option value="EARTH_RESISTANCE">Earthing Resistance (&lt; 5&#8486;)</option>
                        <option value="GRID_SYNC">Grid Synchronization &amp; Anti-Islanding</option>
                        <option value="INSULATION_RESISTANCE">Insulation Resistance (Megger)</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-bold text-slate-700 block mb-1">Measured Value *</label>
                      <input
                        type="text"
                        value={testForm.measured_value}
                        onChange={(e) => setTestForm({ ...testForm, measured_value: e.target.value })}
                        placeholder="e.g. 580V, 1.8 Ohms..."
                        className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="font-bold text-slate-700 block mb-1">Standard / Benchmark</label>
                      <input
                        type="text"
                        value={testForm.standard_value}
                        onChange={(e) => setTestForm({ ...testForm, standard_value: e.target.value })}
                        className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={testForm.is_passed}
                        onChange={(e) => setTestForm({ ...testForm, is_passed: e.target.checked })}
                        className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span className="font-bold text-slate-800">Test Passed Benchmark</span>
                    </label>

                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-xs"
                    >
                      Save Test Measurement
                    </button>
                  </div>
                </form>

                {/* Test history */}
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {(installationDetail.tests || []).map((t) => (
                    <div key={t.id} className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-bold text-slate-900">{t.test_name}</span>
                        <div className="text-slate-500 text-[11px]">
                          Measured: <strong className="text-slate-900 font-mono">{t.measured_value} {t.unit_of_measure}</strong> (Target: {t.standard_value || 'N/A'})
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                        t.is_passed ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {t.is_passed ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab 3: Worklogs */}
            {instModalTab === 'worklogs' && (
              <div className="space-y-4">
                <form onSubmit={handleRecordWorklog} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
                  <h5 className="font-bold text-slate-900 flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-amber-500" />
                    <span>Submit Daily Installation Worklog</span>
                  </h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="font-bold text-slate-700 block mb-1">Hours Worked</label>
                      <input
                        type="number"
                        step="0.5"
                        min="0.5"
                        max="24"
                        value={worklogForm.hours_worked}
                        onChange={(e) => setWorklogForm({ ...worklogForm, hours_worked: e.target.value })}
                        className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="font-bold text-slate-700 block mb-1">Tasks Executed *</label>
                      <input
                        type="text"
                        value={worklogForm.work_description}
                        onChange={(e) => setWorklogForm({ ...worklogForm, work_description: e.target.value })}
                        placeholder="e.g. Structure assembly and inverter wiring..."
                        className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white"
                        required
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-1">
                    <button
                      type="submit"
                      disabled={actionLoading}
                      className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg shadow-xs"
                    >
                      Record Hours
                    </button>
                  </div>
                </form>

                {/* Worklog history */}
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {(installationDetail.worklogs || []).map((w) => (
                    <div key={w.id} className="p-3 bg-white rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-bold text-slate-900">{w.work_description}</span>
                        <div className="text-slate-500 text-[11px]">
                          Logged by: {w.employee_name || 'Technician'} • {new Date(w.work_date).toLocaleDateString()}
                        </div>
                      </div>
                      <span className="font-mono font-bold text-slate-900 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200">
                        {w.hours_worked} Hours
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: COMPLETE SERVICE VISIT */}
      {completingVisit && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Complete On-Site Service Visit</h3>
              <button onClick={() => setCompletingVisit(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCompleteServiceVisit} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Diagnostic Findings *</label>
                <textarea
                  rows={2}
                  value={visitForm.findings}
                  onChange={(e) => setVisitForm({ ...visitForm, findings: e.target.value })}
                  placeholder="Root cause identified (e.g. MC4 loose connection, blown fuse, inverter firmware error)..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Corrective Action Taken *</label>
                <textarea
                  rows={2}
                  value={visitForm.action_taken}
                  onChange={(e) => setVisitForm({ ...visitForm, action_taken: e.target.value })}
                  placeholder="Action taken on-site (e.g. Crimped new MC4 connector, rebooted inverter, verified 230V sync)..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Customer Name Present</label>
                  <input
                    type="text"
                    value={visitForm.customer_present_name}
                    onChange={(e) => setVisitForm({ ...visitForm, customer_present_name: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-200 rounded-lg"
                  />
                </div>
                <div className="flex items-center pt-5">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={visitForm.parts_replaced}
                      onChange={(e) => setVisitForm({ ...visitForm, parts_replaced: e.target.checked })}
                      className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                    />
                    <span className="font-bold text-slate-800">Hardware Parts Replaced</span>
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCompletingVisit(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-xs transition"
                >
                  {actionLoading ? 'Saving...' : 'Submit Completed Visit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
