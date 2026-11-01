import React, { useState, useEffect } from 'react';
import {
  FileCheck,
  Building2,
  DollarSign,
  Search,
  RefreshCw,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  Upload,
  FileText,
  X,
  CreditCard,
  User,
} from 'lucide-react';
import {
  getSubsidyApplications,
  getSubsidyApplication,
  createSubsidyApplication,
  updateSubsidyStatus,
  uploadSubsidyDocument,
  verifySubsidyDocument,
  recordSubsidyDisbursement,
} from '../services/subsidyApi';
import { getProjects } from '../services/projectApi';

export default function SubsidyManagementPage() {
  const [applications, setApplications] = useState([]);
  const [projects, setProjects] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Modals
  const [newAppModal, setNewAppModal] = useState(false);
  const [selectedAppId, setSelectedAppId] = useState(null);
  const [appDetail, setAppDetail] = useState(null);
  const [uploadDocModal, setUploadDocModal] = useState(false);
  const [disburseModal, setDisburseModal] = useState(false);

  // Forms
  const [appForm, setAppForm] = useState({
    project_id: '',
    portal_registration_number: '',
    discom_name: 'MSEDCL (Maharashtra State Electricity Distribution)',
    sanctioned_capacity_kw: '3.00',
    eligible_subsidy_amount: '78000.00',
  });

  const [docForm, setDocForm] = useState({
    document_type: 'ELECTRICITY_BILL',
    file_name: '',
    remarks: '',
  });

  const [disburseForm, setDisburseForm] = useState({
    disbursed_amount: '',
    bank_reference_number: '',
    payment_reference: '',
    disbursement_date: new Date().toISOString().split('T')[0],
  });

  // KPIs
  const [kpis, setKpis] = useState({
    totalApplications: 0,
    totalDisbursed: 0,
    pendingInspections: 0,
    approved: 0,
  });

  const calculateSlab = (kw) => {
    const val = parseFloat(kw) || 0;
    if (val <= 0) return 0;
    if (val < 2.0) return val * 30000;
    if (val < 3.0) return 60000;
    return 78000;
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [appRes, projRes] = await Promise.all([
        getSubsidyApplications({ status: statusFilter || undefined, search: searchTerm || undefined }),
        getProjects({ page_size: 50 }),
      ]);

      const items = appRes.data?.data?.items || [];
      setApplications(items);
      setTotal(appRes.data?.data?.total || 0);
      setProjects(projRes.data?.data?.items || []);

      let sumDisbursed = 0;
      let pendingInsp = 0;
      let approvedCount = 0;

      items.forEach((a) => {
        if (a.status === 'SUBSIDY_DISBURSED') sumDisbursed += Number(a.eligible_subsidy_amount || 0);
        if (a.status === 'INSPECTION_SCHEDULED' || a.status === 'SUBMITTED_TO_DISCOM') pendingInsp++;
        if (a.status === 'APPROVED' || a.status === 'SUBSIDY_DISBURSED') approvedCount++;
      });

      setKpis({
        totalApplications: items.length,
        totalDisbursed: sumDisbursed,
        pendingInspections: pendingInsp,
        approved: approvedCount,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load subsidy applications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const viewDetail = async (id) => {
    setSelectedAppId(id);
    try {
      const res = await getSubsidyApplication(id);
      setAppDetail(res.data?.data || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load application details');
    }
  };

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    try {
      await createSubsidyApplication({
        project_id: parseInt(appForm.project_id),
        portal_registration_number: appForm.portal_registration_number || undefined,
        discom_name: appForm.discom_name,
        sanctioned_capacity_kw: parseFloat(appForm.sanctioned_capacity_kw),
        eligible_subsidy_amount: parseFloat(appForm.eligible_subsidy_amount),
      });
      setNewAppModal(false);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create subsidy application');
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    if (!selectedAppId) return;
    try {
      await updateSubsidyStatus(selectedAppId, {
        status: newStatus,
        comments: `Status updated to ${newStatus} by liaison officer`,
      });
      viewDetail(selectedAppId);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!selectedAppId) return;
    try {
      await uploadSubsidyDocument(selectedAppId, {
        document_type: docForm.document_type,
        file_name: docForm.file_name,
        remarks: docForm.remarks || undefined,
      });
      setUploadDocModal(false);
      setDocForm({ document_type: 'ELECTRICITY_BILL', file_name: '', remarks: '' });
      viewDetail(selectedAppId);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload document');
    }
  };

  const handleVerifyDocument = async (docId, status) => {
    try {
      await verifySubsidyDocument(docId, {
        verification_status: status,
        remarks: `Document ${status.toLowerCase()} by DISCOM verification officer`,
      });
      if (selectedAppId) viewDetail(selectedAppId);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to verify document');
    }
  };

  const handleDisbursePayment = async (e) => {
    e.preventDefault();
    if (!selectedAppId) return;
    try {
      await recordSubsidyDisbursement(selectedAppId, {
        disbursed_amount: parseFloat(disburseForm.disbursed_amount),
        bank_reference_number: disburseForm.bank_reference_number || undefined,
        payment_reference: disburseForm.payment_reference || undefined,
        disbursement_date: disburseForm.disbursement_date,
      });
      setDisburseModal(false);
      viewDetail(selectedAppId);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record disbursement');
    }
  };

  const renderStatusBadge = (st) => {
    switch (st) {
      case 'SUBSIDY_DISBURSED':
        return <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">DISBURSED</span>;
      case 'APPROVED':
        return <span className="bg-blue-500/10 text-blue-500 border border-blue-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">APPROVED</span>;
      case 'INSPECTION_SCHEDULED':
      case 'INSPECTION_COMPLETED':
        return <span className="bg-purple-500/10 text-purple-500 border border-purple-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">INSPECTION</span>;
      case 'REJECTED':
        return <span className="bg-rose-500/10 text-rose-500 border border-rose-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">REJECTED</span>;
      default:
        return <span className="bg-amber-500/10 text-amber-500 border border-amber-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">{st}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Building2 className="w-7 h-7 text-amber-500" />
            <span>PM Surya Ghar & DISCOM Subsidy Liaison</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Portal application tracking, DISCOM document filings, net meter joint inspections, and DBT direct disbursements
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setNewAppModal(true)}
            className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-lg text-xs font-bold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Subsidy Application</span>
          </button>
          <button
            onClick={loadData}
            className="p-1.5 bg-white border border-slate-200 text-slate-600 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Applications</span>
            <span className="p-1.5 bg-slate-100 text-slate-600 rounded-lg">
              <FileCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">{kpis.totalApplications}</div>
          <span className="text-[11px] text-slate-400">Rooftop subsidy filings</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Pending Inspections</span>
            <span className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-amber-600">{kpis.pendingInspections}</div>
          <span className="text-[11px] text-slate-400">Awaiting joint meter inspection</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Approved Subsidies</span>
            <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-blue-600">{kpis.approved}</div>
          <span className="text-[11px] text-slate-400">Feasibility & meter approved</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Disbursed</span>
            <span className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <DollarSign className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-emerald-600">
            ₹{kpis.totalDisbursed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Direct benefit transfers credited</span>
        </div>
      </div>

      {/* Filter and Applications List */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-slate-200 rounded-lg text-xs px-2.5 py-1.5"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="SUBMITTED_TO_DISCOM">SUBMITTED_TO_DISCOM</option>
              <option value="INSPECTION_SCHEDULED">INSPECTION_SCHEDULED</option>
              <option value="APPROVED">APPROVED</option>
              <option value="SUBSIDY_DISBURSED">SUBSIDY_DISBURSED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>
          <span className="text-xs text-slate-400">{applications.length} applications</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Application #</th>
                <th className="px-4 py-3">Customer & Project</th>
                <th className="px-4 py-3">DISCOM / Portal Ref</th>
                <th className="px-4 py-3 text-right">Capacity (kW)</th>
                <th className="px-4 py-3 text-right">Subsidy Amount</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-10 text-slate-400">
                    No subsidy applications found. Click "New Subsidy Application" to initiate filing.
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/70 transition">
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">{app.application_number}</td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{app.customer_name || 'Beneficiary'}</div>
                      <div className="text-[11px] text-slate-400">{app.project_code || `PRJ #${app.project_id}`}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{app.discom_name}</div>
                      <div className="font-mono text-[11px] text-slate-500">{app.portal_registration_number || 'Pending Reg #'}</div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-900">
                      {parseFloat(app.sanctioned_capacity_kw).toFixed(2)} kW
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-emerald-600">
                      ₹{Number(app.eligible_subsidy_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">{renderStatusBadge(app.status)}</td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => viewDetail(app.id)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg text-xs transition"
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Application Detail & DISCOM Liaison Modal */}
      {selectedAppId && appDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-amber-500" />
                  <span>Subsidy Application {appDetail.application_number}</span>
                  {renderStatusBadge(appDetail.status)}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{appDetail.project_code} • {appDetail.customer_name} ({appDetail.discom_name})</p>
              </div>
              <button onClick={() => { setSelectedAppId(null); setAppDetail(null); }} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Stepper Status Progression */}
            <div className="bg-slate-50 p-3 rounded-lg flex flex-wrap gap-2 text-xs items-center justify-between">
              <span className="font-bold text-slate-700">Quick Stage Actions:</span>
              <div className="flex gap-1.5 flex-wrap">
                <button
                  onClick={() => handleStatusUpdate('SUBMITTED_TO_DISCOM')}
                  className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded text-xs font-semibold"
                >
                  Mark Submitted
                </button>
                <button
                  onClick={() => handleStatusUpdate('INSPECTION_SCHEDULED')}
                  className="px-2.5 py-1 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 rounded text-xs font-semibold"
                >
                  Inspection Scheduled
                </button>
                <button
                  onClick={() => handleStatusUpdate('APPROVED')}
                  className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 rounded text-xs font-semibold"
                >
                  Net Meter Approved
                </button>
                {appDetail.status !== 'SUBSIDY_DISBURSED' && (
                  <button
                    onClick={() => {
                      setDisburseForm({
                        ...disburseForm,
                        disbursed_amount: appDetail.eligible_subsidy_amount,
                      });
                      setDisburseModal(true);
                    }}
                    className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded text-xs shadow-sm"
                  >
                    Record Disbursement
                  </button>
                )}
              </div>
            </div>

            {/* Documents Checklist Section */}
            <div className="space-y-2 border-t pt-3">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Required DISCOM Document Filings</h4>
                <button
                  onClick={() => setUploadDocModal(true)}
                  className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow-sm"
                >
                  <Upload className="w-3 h-3" />
                  <span>Upload Document</span>
                </button>
              </div>

              {appDetail.documents.length === 0 ? (
                <div className="text-xs text-slate-400 italic py-2">No documents uploaded for this application yet.</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {appDetail.documents.map((d) => (
                    <div key={d.id} className="border border-slate-200 rounded-lg p-2.5 text-xs bg-white space-y-1">
                      <div className="flex justify-between items-start font-semibold text-slate-800">
                        <span className="truncate">{d.document_type}</span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${d.verification_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {d.verification_status}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">{d.file_name}</div>
                      {d.verification_status === 'PENDING' && (
                        <div className="pt-1 flex gap-1 justify-end">
                          <button
                            onClick={() => handleVerifyDocument(d.id, 'VERIFIED')}
                            className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-bold"
                          >
                            Verify
                          </button>
                          <button
                            onClick={() => handleVerifyDocument(d.id, 'REJECTED')}
                            className="px-2 py-0.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-[10px] font-bold"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Disbursement Details */}
            {appDetail.payments.length > 0 && (
              <div className="space-y-2 border-t pt-3">
                <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Disbursement Record</h4>
                {appDetail.payments.map((p) => (
                  <div key={p.id} className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-3 text-xs space-y-1">
                    <div className="flex justify-between font-bold text-emerald-900">
                      <span>Ref: {p.payment_reference}</span>
                      <span className="font-mono text-sm">₹{Number(p.disbursed_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="text-emerald-700 text-[11px]">Date: {p.disbursement_date} • Bank Ref: {p.bank_reference_number || 'N/A'}</div>
                  </div>
                ))}
              </div>
            )}

            {/* History Trail */}
            <div className="space-y-1 border-t pt-3">
              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider mb-2">Audit & Status Progression History</h4>
              <div className="space-y-1.5 max-h-36 overflow-y-auto">
                {appDetail.history.map((h) => (
                  <div key={h.id} className="text-[11px] text-slate-600 flex justify-between border-b border-slate-100 pb-1">
                    <span>
                      <strong className="text-slate-800">{h.new_status}</strong>: {h.comments || 'Status updated'}
                    </span>
                    <span className="font-mono text-slate-400 whitespace-nowrap ml-2">
                      {new Date(h.action_date).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Application Modal */}
      {newAppModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-amber-500" />
                <span>Initiate PM Surya Ghar Subsidy</span>
              </h3>
              <button onClick={() => setNewAppModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateApplication} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Select Commissioned Project</label>
                <select
                  value={appForm.project_id}
                  onChange={(e) => {
                    const pId = e.target.value;
                    const p = projects.find((x) => x.id === parseInt(pId));
                    const cap = p ? (p.system_capacity_kw || p.system_size_kw || '3.00') : '3.00';
                    const slab = calculateSlab(cap);
                    setAppForm({
                      ...appForm,
                      project_id: pId,
                      sanctioned_capacity_kw: String(cap),
                      eligible_subsidy_amount: String(slab),
                    });
                  }}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                >
                  <option value="">Select Project...</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} — {p.customer_name || 'Project'} ({p.system_capacity_kw || p.system_size_kw || ''}kW)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">DISCOM Name</label>
                <input
                  type="text"
                  value={appForm.discom_name}
                  onChange={(e) => setAppForm({ ...appForm, discom_name: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">National Portal Application / Reg #</label>
                <input
                  type="text"
                  placeholder="e.g. PMSG-MH-2026-98124"
                  value={appForm.portal_registration_number}
                  onChange={(e) => setAppForm({ ...appForm, portal_registration_number: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sanctioned kW</label>
                  <input
                    type="number"
                    step="0.1"
                    value={appForm.sanctioned_capacity_kw}
                    onChange={(e) => {
                      const kw = e.target.value;
                      setAppForm({
                        ...appForm,
                        sanctioned_capacity_kw: kw,
                        eligible_subsidy_amount: String(calculateSlab(kw)),
                      });
                    }}
                    className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Estimated Subsidy (₹)</label>
                  <input
                    type="number"
                    value={appForm.eligible_subsidy_amount}
                    onChange={(e) => setAppForm({ ...appForm, eligible_subsidy_amount: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg p-2 font-mono font-bold text-emerald-600"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setNewAppModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  Create Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {uploadDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base">Upload DISCOM Filing</h3>
              <button onClick={() => setUploadDocModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadDocument} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Document Type</label>
                <select
                  value={docForm.document_type}
                  onChange={(e) => setDocForm({ ...docForm, document_type: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="ELECTRICITY_BILL">ELECTRICITY_BILL (Consumer No & Sanctioned Load)</option>
                  <option value="AADHAAR_CARD">AADHAAR_CARD (Identity & Address Proof)</option>
                  <option value="BANK_PASSBOOK">BANK_PASSBOOK (DBT Account Details & Cancelled Cheque)</option>
                  <option value="JOINT_INSPECTION_REPORT">JOINT_INSPECTION_REPORT (JIR Signed by DISCOM)</option>
                  <option value="NET_METER_INSTALL_REPORT">NET_METER_INSTALL_REPORT (Bi-directional Testing)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">File Name</label>
                <input
                  type="text"
                  placeholder="e.g. MSEDCL_Joint_Inspection_Report.pdf"
                  value={docForm.file_name}
                  onChange={(e) => setDocForm({ ...docForm, file_name: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Remarks</label>
                <textarea
                  placeholder="Notes for DISCOM portal officer..."
                  value={docForm.remarks}
                  onChange={(e) => setDocForm({ ...docForm, remarks: e.target.value })}
                  rows="2"
                  className="w-full border border-slate-200 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadDocModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  Upload & File
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Disbursement Recording Modal */}
      {disburseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base">Record DBT Disbursement</h3>
              <button onClick={() => setDisburseModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleDisbursePayment} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Disbursed Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={disburseForm.disbursed_amount}
                  onChange={(e) => setDisburseForm({ ...disburseForm, disbursed_amount: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono font-bold text-emerald-600"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Disbursement Date</label>
                <input
                  type="date"
                  value={disburseForm.disbursement_date}
                  onChange={(e) => setDisburseForm({ ...disburseForm, disbursement_date: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Bank / DBT UTR Reference</label>
                <input
                  type="text"
                  placeholder="e.g. DBT-SBIN-89127391"
                  value={disburseForm.bank_reference_number}
                  onChange={(e) => setDisburseForm({ ...disburseForm, bank_reference_number: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setDisburseModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg shadow-sm"
                >
                  Confirm Credit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
