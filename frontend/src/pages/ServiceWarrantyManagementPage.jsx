import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  LifeBuoy,
  Wrench,
  Search,
  RefreshCw,
  Plus,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Calendar,
  X,
  User,
  Star,
  FileCheck,
} from 'lucide-react';
import {
  getServiceTickets,
  getServiceTicket,
  createServiceTicket,
  updateServiceTicketStatus,
  scheduleServiceVisit,
  completeServiceVisit,
  replaceComponentUnderWarranty,
  confirmServiceTicketResolution,
  getWarrantyRecords,
  getWarrantyPolicies,
  registerProjectWarranties,
  getWarrantySLAMetrics,
} from '../services/warrantyApi';
import { getProjects } from '../services/projectApi';
import { fetchEmployees } from '../services/employeeApi';

export default function ServiceWarrantyManagementPage() {
  const [activeTab, setActiveTab] = useState('TICKETS');
  const [tickets, setTickets] = useState([]);
  const [warranties, setWarranties] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [projects, setProjects] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [slaMetrics, setSlaMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  // Modals
  const [newTicketModal, setNewTicketModal] = useState(false);
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [visitModal, setVisitModal] = useState(false);
  const [replaceModal, setReplaceModal] = useState(false);
  const [confirmModal, setConfirmModal] = useState(false);

  // Form states
  const [ticketForm, setTicketForm] = useState({
    project_id: '',
    issue_category: 'GENERAL',
    priority: 'MEDIUM',
    description: '',
  });

  const [visitForm, setVisitForm] = useState({
    technician_id: '',
    scheduled_date: new Date().toISOString().split('T')[0],
  });

  const [replaceForm, setReplaceForm] = useState({
    original_serial_id: '',
    replacement_serial_id: '',
    replacement_reason: '',
  });

  const [confirmForm, setConfirmForm] = useState({
    customer_rating: 5,
    customer_feedback: '',
    resolution_confirmed: true,
  });

  // KPIs
  const [kpis, setKpis] = useState({
    activeWarranties: 0,
    openTickets: 0,
    criticalTickets: 0,
    resolvedTickets: 0,
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [tRes, wRes, pRes, projRes, empRes, slaRes] = await Promise.all([
        getServiceTickets({ status: statusFilter || undefined, priority: priorityFilter || undefined }),
        getWarrantyRecords({ page_size: 50 }),
        getWarrantyPolicies(),
        getProjects({ page_size: 50 }),
        fetchEmployees({ page_size: 50 }).catch(() => ({ data: { data: { items: [] } } })),
        getWarrantySLAMetrics().catch(() => ({ data: { data: null } })),
      ]);

      const tItems = tRes.data?.data?.items || [];
      const wItems = wRes.data?.data?.items || [];
      setTickets(tItems);
      setWarranties(wItems);
      setPolicies(pRes.data?.data || []);
      setProjects(projRes.data?.data?.items || []);
      setEmployees(empRes.data?.data?.items || empRes.data?.items || []);
      if (slaRes?.data?.data) {
        setSlaMetrics(slaRes.data.data);
      }

      setKpis({
        activeWarranties: wItems.filter((w) => w.status === 'ACTIVE').length,
        openTickets: tItems.filter((t) => t.status === 'OPEN' || t.status === 'ASSIGNED').length,
        criticalTickets: tItems.filter((t) => t.priority === 'CRITICAL' || t.priority === 'HIGH').length,
        resolvedTickets: tItems.filter((t) => t.status === 'RESOLVED' || t.status === 'CLOSED').length,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load service & warranty data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, priorityFilter]);

  const viewTicketDetail = async (id) => {
    setSelectedTicketId(id);
    try {
      const res = await getServiceTicket(id);
      setTicketDetail(res.data?.data || null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load ticket detail');
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    try {
      await createServiceTicket({
        project_id: parseInt(ticketForm.project_id),
        issue_category: ticketForm.issue_category,
        priority: ticketForm.priority,
        description: ticketForm.description,
      });
      setNewTicketModal(false);
      setTicketForm({ project_id: '', issue_category: 'GENERAL', priority: 'MEDIUM', description: '' });
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create ticket');
    }
  };

  const handleScheduleVisit = async (e) => {
    e.preventDefault();
    if (!selectedTicketId) return;
    try {
      await scheduleServiceVisit(selectedTicketId, {
        technician_id: parseInt(visitForm.technician_id),
        scheduled_date: visitForm.scheduled_date,
      });
      setVisitModal(false);
      viewTicketDetail(selectedTicketId);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to schedule visit');
    }
  };

  const handleConfirmResolution = async (e) => {
    e.preventDefault();
    if (!selectedTicketId) return;
    try {
      await confirmServiceTicketResolution(selectedTicketId, {
        resolution_confirmed: confirmForm.resolution_confirmed,
        customer_rating: parseInt(confirmForm.customer_rating),
        customer_feedback: confirmForm.customer_feedback,
      });
      setConfirmModal(false);
      viewTicketDetail(selectedTicketId);
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to confirm resolution');
    }
  };

  const handleRegisterProjectWarranties = async (projId) => {
    try {
      await registerProjectWarranties(projId);
      alert('Warranty certificates registered successfully!');
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to register project warranties');
    }
  };

  const renderPriorityBadge = (prio) => {
    switch (prio) {
      case 'CRITICAL':
        return <span className="bg-rose-500/10 text-rose-500 border border-rose-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">CRITICAL</span>;
      case 'HIGH':
        return <span className="bg-amber-500/10 text-amber-500 border border-amber-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">HIGH</span>;
      default:
        return <span className="bg-slate-100 text-slate-600 border border-slate-200 px-2 py-0.5 rounded-full text-[10px] font-bold">{prio}</span>;
    }
  };

  const renderTicketStatusBadge = (st) => {
    switch (st) {
      case 'RESOLVED':
      case 'CLOSED':
        return <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">RESOLVED</span>;
      case 'IN_PROGRESS':
        return <span className="bg-blue-500/10 text-blue-500 border border-blue-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">IN PROGRESS</span>;
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
            <ShieldCheck className="w-7 h-7 text-amber-500" />
            <span>Warranty & Service Operations</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            AMC contracts, breakdown service tickets, SLA tracking, technician dispatch, and component replacement
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setNewTicketModal(true)}
            className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-lg text-xs font-bold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Service Ticket</span>
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

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Warranties</span>
            <span className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">{kpis.activeWarranties}</div>
          <span className="text-[11px] text-slate-400">Certificates under active period</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Open Tickets</span>
            <span className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <LifeBuoy className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-amber-600">{kpis.openTickets}</div>
          <span className="text-[11px] text-slate-400">Unresolved customer breakdown calls</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Critical / High SLA</span>
            <span className="p-1.5 bg-rose-50 text-rose-600 rounded-lg">
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-rose-600">{kpis.criticalTickets}</div>
          <span className="text-[11px] text-slate-400">Urgent inverter / grid outage</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Resolved Tickets</span>
            <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">{kpis.resolvedTickets}</div>
          <span className="text-[11px] text-slate-400">Confirmed customer resolution</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('TICKETS')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'TICKETS'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <LifeBuoy className="w-4 h-4" />
          <span>Service Tickets ({tickets.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('WARRANTY_RECORDS')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'WARRANTY_RECORDS'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Warranty Certificates ({warranties.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('SLA_DASHBOARD')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'SLA_DASHBOARD'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>SLA & Response Analytics</span>
        </button>
      </div>

      {/* TICKETS TAB */}
      {activeTab === 'TICKETS' && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-slate-200 rounded-lg text-xs px-2.5 py-1.5"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="border border-slate-200 rounded-lg text-xs px-2.5 py-1.5"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Ticket #</th>
                  <th className="px-4 py-3">Project & Customer</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3 text-center">Priority</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="text-center py-10 text-slate-400">
                      No service tickets found.
                    </td>
                  </tr>
                ) : (
                  tickets.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/70 transition">
                      <td className="px-4 py-3 font-bold font-mono text-slate-900">{t.ticket_number}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-800">{t.customer_name || 'Customer'}</div>
                        <div className="text-[11px] text-slate-400">{t.project_code || `PRJ #${t.project_id}`}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{t.issue_category}</td>
                      <td className="px-4 py-3 text-center">{renderPriorityBadge(t.priority)}</td>
                      <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{t.description}</td>
                      <td className="px-4 py-3 text-center">{renderTicketStatusBadge(t.status)}</td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => viewTicketDetail(t.id)}
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
      )}

      {/* WARRANTY RECORDS TAB */}
      {activeTab === 'WARRANTY_RECORDS' && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs text-slate-600">Register warranties for completed installations:</span>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                id="batchRegisterSelect"
                className="border border-slate-200 rounded-lg text-xs px-3 py-1.5 w-full sm:w-64"
                defaultValue=""
              >
                <option value="" disabled>Select Commissioned Project...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.project_code} — {p.customer_name || 'Project'}</option>
                ))}
              </select>
              <button
                onClick={() => {
                  const el = document.getElementById('batchRegisterSelect');
                  if (el && el.value) handleRegisterProjectWarranties(el.value);
                }}
                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs transition whitespace-nowrap shadow-sm"
              >
                Register Warranties
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Certificate #</th>
                    <th className="px-4 py-3">Equipment & Serial</th>
                    <th className="px-4 py-3">Customer / Project</th>
                    <th className="px-4 py-3">Policy & Coverage</th>
                    <th className="px-4 py-3">Valid Until</th>
                    <th className="px-4 py-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {warranties.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-10 text-slate-400">
                        No warranty records registered yet.
                      </td>
                    </tr>
                  ) : (
                    warranties.map((w) => (
                      <tr key={w.id} className="hover:bg-slate-50/70 transition">
                        <td className="px-4 py-3 font-mono font-bold text-slate-900">{w.certificate_number}</td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-800">{w.product_name || 'Product'}</div>
                          <div className="font-mono text-[11px] text-slate-500">{w.serial_number || `Serial #${w.serial_number_id}`}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-800">{w.customer_name || 'Customer'}</div>
                          <div className="text-[11px] text-slate-400">{w.project_code || `PRJ #${w.project_id}`}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-800">{w.policy_name || 'Standard Warranty'}</div>
                          <div className="text-[11px] text-slate-400">{w.warranty_period_months || 60} Months Coverage</div>
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-700">{w.warranty_end_date}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold">
                            {w.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SLA & RESPONSE ANALYTICS TAB */}
      {activeTab === 'SLA_DASHBOARD' && (
        <div className="space-y-6">
          {/* Key SLA Indicators */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">SLA Compliance Rate</span>
                <span className={`p-1.5 rounded-lg ${(slaMetrics?.sla_compliance_percentage ?? 100) >= 90 ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                  <CheckCircle2 className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black font-mono text-slate-900">
                {slaMetrics ? `${slaMetrics.sla_compliance_percentage.toFixed(1)}%` : '--'}
              </div>
              <span className="text-[11px] text-slate-400">Tickets resolved within priority targets</span>
            </div>

            <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Avg Resolution Time</span>
                <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
                  <Clock className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black font-mono text-slate-900">
                {slaMetrics?.average_resolution_hours ? `${slaMetrics.average_resolution_hours.toFixed(1)} hrs` : 'N/A'}
              </div>
              <span className="text-[11px] text-slate-400">From creation to verified resolution</span>
            </div>

            <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Approaching Deadline</span>
                <span className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
                  <AlertTriangle className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black font-mono text-amber-600">
                {slaMetrics?.approaching_deadline_count ?? 0}
              </div>
              <span className="text-[11px] text-slate-400">Tickets with &lt; 6 hours remaining</span>
            </div>

            <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Overdue Response</span>
                <span className="p-1.5 bg-rose-50 text-rose-600 rounded-lg">
                  <AlertTriangle className="w-4 h-4" />
                </span>
              </div>
              <div className="text-3xl font-black font-mono text-rose-600">
                {slaMetrics?.overdue_response_count ?? 0}
              </div>
              <span className="text-[11px] text-slate-400">Tickets that breached target SLA</span>
            </div>
          </div>

          {/* Aging Buckets & Target Policies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Open Tickets by SLA Aging</h3>
                  <p className="text-xs text-slate-500">Breakdown of pending service calls by time in queue</p>
                </div>
                <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-bold rounded-lg">
                  {slaMetrics?.total_open_tickets ?? 0} Active
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-3 text-center">
                  <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">&lt; 24 Hours</span>
                  <div className="text-2xl font-black font-mono text-emerald-800 my-1">
                    {slaMetrics?.open_tickets_by_sla_aging?.under_24h ?? 0}
                  </div>
                  <span className="text-[10px] text-emerald-600 font-medium">Standard Window</span>
                </div>

                <div className="bg-blue-50/50 border border-blue-200 rounded-xl p-3 text-center">
                  <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider">24 - 48 Hours</span>
                  <div className="text-2xl font-black font-mono text-blue-800 my-1">
                    {slaMetrics?.open_tickets_by_sla_aging?.["24_to_48h"] ?? 0}
                  </div>
                  <span className="text-[10px] text-blue-600 font-medium">Under Investigation</span>
                </div>

                <div className="bg-amber-50/50 border border-amber-200 rounded-xl p-3 text-center">
                  <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">48 - 72 Hours</span>
                  <div className="text-2xl font-black font-mono text-amber-800 my-1">
                    {slaMetrics?.open_tickets_by_sla_aging?.["48_to_72h"] ?? 0}
                  </div>
                  <span className="text-[10px] text-amber-600 font-medium">Escalation Window</span>
                </div>

                <div className="bg-rose-50/50 border border-rose-200 rounded-xl p-3 text-center">
                  <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider">&gt; 72 Hours</span>
                  <div className="text-2xl font-black font-mono text-rose-800 my-1">
                    {slaMetrics?.open_tickets_by_sla_aging?.over_72h ?? 0}
                  </div>
                  <span className="text-[10px] text-rose-600 font-medium">High Risk / Overdue</span>
                </div>
              </div>

              <div className="pt-2 text-xs text-slate-500 bg-slate-50 p-3 rounded-lg flex items-center justify-between">
                <span>Critical priorities require resolution within 24h; high priority within 48h.</span>
                <span className="font-semibold text-slate-700">MNRE Compliant</span>
              </div>
            </div>

            {/* SLA Policy Targets */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="border-b pb-3">
                <h3 className="text-sm font-bold text-slate-900">Standard Service Level Agreement Targets</h3>
                <p className="text-xs text-slate-500">Guaranteed turnaround by ticket priority tier</p>
              </div>

              <div className="space-y-3 pt-1">
                <div className="flex items-center justify-between p-2.5 bg-rose-50/60 border border-rose-200/80 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 bg-rose-500 text-white rounded text-[10px] font-black uppercase">CRITICAL</span>
                    <span className="text-xs font-bold text-slate-800">Total System Outage / Inverter Failure</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-rose-700">24 Hours Target</span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-amber-50/60 border border-amber-200/80 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 bg-amber-500 text-white rounded text-[10px] font-black uppercase">HIGH</span>
                    <span className="text-xs font-bold text-slate-800">Severe String Degradation / Grid Sync Drop</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-amber-700">48 Hours Target</span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-blue-50/60 border border-blue-200/80 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 bg-blue-500 text-white rounded text-[10px] font-black uppercase">MEDIUM</span>
                    <span className="text-xs font-bold text-slate-800">Monitoring Dongle / Minor Generation Drop</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-blue-700">72 Hours Target</span>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 bg-slate-400 text-white rounded text-[10px] font-black uppercase">LOW</span>
                    <span className="text-xs font-bold text-slate-800">General Inquiry / Scheduled Cleaning Visit</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-600">120 Hours Target</span>
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Resolution Trend */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="border-b pb-3">
              <h3 className="text-sm font-bold text-slate-900">Service Ticket Volume & Resolution History</h3>
              <p className="text-xs text-slate-500">Historical tickets opened vs resolved over recent calendar months</p>
            </div>

            {slaMetrics?.resolution_trend && slaMetrics.resolution_trend.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-2.5">Calendar Month</th>
                      <th className="px-4 py-2.5 text-center">Tickets Opened</th>
                      <th className="px-4 py-2.5 text-center">Tickets Resolved</th>
                      <th className="px-4 py-2.5 text-center">Clearance Ratio</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {slaMetrics.resolution_trend.map((trend, idx) => {
                      const ratio = trend.opened > 0 ? ((trend.resolved / trend.opened) * 100).toFixed(0) : 100;
                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 transition">
                          <td className="px-4 py-3 font-mono font-bold text-slate-900">{trend.month}</td>
                          <td className="px-4 py-3 text-center font-mono font-bold text-slate-700">{trend.opened}</td>
                          <td className="px-4 py-3 text-center font-mono font-bold text-emerald-600">{trend.resolved}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-black font-mono ${
                              Number(ratio) >= 80 ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-amber-50 text-amber-600 border border-amber-200'
                            }`}>
                              {ratio}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                No monthly historical ticket data recorded yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Ticket Details & Management Modal */}
      {selectedTicketId && ticketDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                  <LifeBuoy className="w-5 h-5 text-amber-500" />
                  <span>Ticket {ticketDetail.ticket_number}</span>
                  {renderPriorityBadge(ticketDetail.priority)}
                  {renderTicketStatusBadge(ticketDetail.status)}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{ticketDetail.project_code} • {ticketDetail.customer_name}</p>
              </div>
              <button
                onClick={() => { setSelectedTicketId(null); setTicketDetail(null); }}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg text-xs space-y-1">
              <div><span className="font-semibold text-slate-700">Issue Category:</span> {ticketDetail.issue_category}</div>
              <div><span className="font-semibold text-slate-700">Component Serial:</span> {ticketDetail.serial_number || 'None'}</div>
              <div><span className="font-semibold text-slate-700">Description:</span> {ticketDetail.description}</div>
            </div>

            {/* Visits Section */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Technician Service Visits</h4>
                <button
                  onClick={() => setVisitModal(true)}
                  className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow-sm"
                >
                  <Plus className="w-3 h-3" />
                  <span>Schedule Visit</span>
                </button>
              </div>

              {ticketDetail.visits.length === 0 ? (
                <div className="text-xs text-slate-400 italic py-2">No visits scheduled yet.</div>
              ) : (
                ticketDetail.visits.map((v) => (
                  <div key={v.id} className="border border-slate-200 rounded-lg p-3 text-xs space-y-1 bg-white">
                    <div className="flex justify-between font-bold text-slate-800">
                      <span>Visit #{v.visit_number} — {v.technician_name || `Technician #${v.technician_id}`}</span>
                      <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded font-mono">{v.visit_status}</span>
                    </div>
                    <div className="text-slate-500">Scheduled Date: {v.scheduled_date}</div>
                    {v.findings && <div><span className="font-semibold text-slate-700">Findings:</span> {v.findings}</div>}
                    {v.action_taken && <div><span className="font-semibold text-slate-700">Action:</span> {v.action_taken}</div>}
                  </div>
                ))
              )}
            </div>

            {/* Replacements Section */}
            <div className="space-y-2 border-t pt-3">
              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Component Replacements</h4>
              {ticketDetail.replacements.length === 0 ? (
                <div className="text-xs text-slate-400 italic">No warranty replacements logged on this ticket.</div>
              ) : (
                ticketDetail.replacements.map((r) => (
                  <div key={r.id} className="border border-slate-200 rounded-lg p-3 text-xs bg-emerald-50/50 space-y-1">
                    <div className="font-semibold text-emerald-800">
                      Replaced: {r.original_serial_number || r.original_serial_id} ➔ {r.replacement_serial_number || r.replacement_serial_id}
                    </div>
                    <div className="text-slate-600 text-[11px]">Reason: {r.replacement_reason} (Date: {r.replacement_date})</div>
                  </div>
                ))
              )}
            </div>

            {/* Customer Sign-off / Confirmation */}
            <div className="border-t pt-3 flex justify-between items-center">
              <div>
                {ticketDetail.confirmation ? (
                  <div className="text-xs text-emerald-600 font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Customer Sign-off Confirmed (Rating: {ticketDetail.confirmation.customer_rating}★)</span>
                  </div>
                ) : (
                  <span className="text-xs text-slate-400">Awaiting customer resolution sign-off</span>
                )}
              </div>

              {!ticketDetail.confirmation && (
                <button
                  onClick={() => setConfirmModal(true)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs shadow-sm flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Customer Sign-off</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* New Ticket Modal */}
      {newTicketModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <LifeBuoy className="w-5 h-5 text-amber-500" />
                <span>Create Service Ticket</span>
              </h3>
              <button onClick={() => setNewTicketModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project</label>
                <select
                  value={ticketForm.project_id}
                  onChange={(e) => setTicketForm({ ...ticketForm, project_id: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                >
                  <option value="">Select Project...</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.project_code} — {p.customer_name || 'Project'}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Issue Category</label>
                <select
                  value={ticketForm.issue_category}
                  onChange={(e) => setTicketForm({ ...ticketForm, issue_category: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="INVERTER_FAULT">INVERTER_FAULT (Tripping, Error Code, Inverter Dead)</option>
                  <option value="LOW_GENERATION">LOW_GENERATION (Generation Drop, Soiling, Shading)</option>
                  <option value="GRID_FAILURE">GRID_FAILURE (Phase Mismatch, DISCOM Disconnect)</option>
                  <option value="WIRING_ISSUE">WIRING_ISSUE (MC4 Connector, AC/DC DB, Earthing)</option>
                  <option value="PHYSICAL_DAMAGE">PHYSICAL_DAMAGE (Panel Crack, Structure Damage)</option>
                  <option value="GENERAL">GENERAL (Routine AMC / Periodic Check)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Priority / SLA Target</label>
                <select
                  value={ticketForm.priority}
                  onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="CRITICAL">CRITICAL (Total System Outage - 24h SLA)</option>
                  <option value="HIGH">HIGH (Major Generation Drop - 48h SLA)</option>
                  <option value="MEDIUM">MEDIUM (Standard Issue - 72h SLA)</option>
                  <option value="LOW">LOW (Informational / Minor - 7 Days SLA)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Detailed Description</label>
                <textarea
                  placeholder="Describe the issue reported by the client..."
                  value={ticketForm.description}
                  onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                  rows="3"
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setNewTicketModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  Create Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Visit Modal */}
      {visitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base">Schedule Field Visit</h3>
              <button onClick={() => setVisitModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleScheduleVisit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Assign Technician</label>
                <select
                  value={visitForm.technician_id}
                  onChange={(e) => setVisitForm({ ...visitForm, technician_id: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                >
                  <option value="">Select Technician...</option>
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.user?.full_name || e.employee_code} ({e.designation || 'Technician'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Scheduled Date</label>
                <input
                  type="date"
                  value={visitForm.scheduled_date}
                  onChange={(e) => setVisitForm({ ...visitForm, scheduled_date: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setVisitModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Sign-off Modal */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base">Customer Sign-off</h3>
              <button onClick={() => setConfirmModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmResolution} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Satisfaction Rating</label>
                <select
                  value={confirmForm.customer_rating}
                  onChange={(e) => setConfirmForm({ ...confirmForm, customer_rating: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="5">★★★★★ (5 Stars - Excellent)</option>
                  <option value="4">★★★★☆ (4 Stars - Good)</option>
                  <option value="3">★★★☆☆ (3 Stars - Satisfactory)</option>
                  <option value="2">★★☆☆☆ (2 Stars - Needs Improvement)</option>
                  <option value="1">★☆☆☆☆ (1 Star - Poor)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Customer Feedback Remarks</label>
                <textarea
                  placeholder="Feedback on technician punctuality and system generation..."
                  value={confirmForm.customer_feedback}
                  onChange={(e) => setConfirmForm({ ...confirmForm, customer_feedback: e.target.value })}
                  rows="3"
                  className="w-full border border-slate-200 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setConfirmModal(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg shadow-sm"
                >
                  Sign Off & Close
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
