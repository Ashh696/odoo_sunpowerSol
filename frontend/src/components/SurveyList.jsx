import React, { useState, useEffect } from 'react';
import {
  Search,
  Compass,
  Calendar,
  User,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Eye,
  Edit2,
  ShieldCheck,
  Filter,
  RefreshCw,
  AlertCircle,
  MapPin,
} from 'lucide-react';
import { getSurveys, getActiveSurveyors } from '../services/surveyApi';

export default function SurveyList({
  currentUser,
  onOpenDetail,
  onOpenEditObservations,
  onOpenApproval,
  refreshKey,
}) {
  const [surveys, setSurveys] = useState([]);
  const [surveyors, setSurveyors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [tabFilter, setTabFilter] = useState(''); // '', 'DRAFT', 'REVIEW_QUEUE', 'APPROVED', 'CORRECTION_REQUESTED', 'REJECTED'
  const [surveyorId, setSurveyorId] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchSurveys = async () => {
    setLoading(true);
    setError(null);
    try {
      let statusParam = undefined;
      if (tabFilter === 'REVIEW_QUEUE') {
        // Will match SUBMITTED on backend or we filter client-side/query
        statusParam = 'SUBMITTED';
      } else if (tabFilter) {
        statusParam = tabFilter;
      }

      const params = {
        page,
        limit: 15,
        status: statusParam,
        surveyor_id: surveyorId ? parseInt(surveyorId, 10) : undefined,
        search: search.trim() || undefined,
      };

      const res = await getSurveys(params);
      if (res && res.data) {
        setSurveys(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to load site surveys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSurveys();
  }, [page, tabFilter, surveyorId, refreshKey]);

  useEffect(() => {
    // Load surveyors for filter dropdown
    getActiveSurveyors()
      .then((res) => {
        if (res && res.data) setSurveyors(res.data.items || []);
      })
      .catch(() => {});
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchSurveys();
  };

  const roleSlug = currentUser?.role?.slug || '';
  const isSuperAdmin = roleSlug === 'SUPER_ADMIN';
  const isDirector = roleSlug === 'DIRECTOR';
  const isTechManager = roleSlug === 'TECHNICAL_MANAGER';
  const isTechnician = roleSlug === 'FIELD_TECHNICIAN';

  const statusBadge = (st) => {
    switch (st) {
      case 'DRAFT':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">Draft</span>;
      case 'SUBMITTED':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">Submitted</span>;
      case 'UNDER_REVIEW':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">Under Review</span>;
      case 'APPROVED':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Approved</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1"><XCircle className="w-3 h-3" /> Rejected</span>;
      case 'CORRECTION_REQUESTED':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Corrections</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">{st}</span>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Tab Filter Navigation */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-semibold">
        {[
          { key: '', label: 'All Surveys' },
          { key: 'DRAFT', label: 'Drafts' },
          { key: 'REVIEW_QUEUE', label: 'Review Queue' },
          { key: 'APPROVED', label: 'Approved' },
          { key: 'CORRECTION_REQUESTED', label: 'Corrections Requested' },
          { key: 'REJECTED', label: 'Rejected' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setTabFilter(tab.key);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg transition whitespace-nowrap ${
              tabFilter === tab.key
                ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search & Surveyor Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by survey #, customer name, phone, or city..."
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold transition shrink-0"
          >
            Search
          </button>
        </form>

        {/* Surveyor dropdown filter (For managers/admins/sales) */}
        {!isTechnician && (
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-slate-500 font-semibold whitespace-nowrap">Surveyor:</span>
            <select
              value={surveyorId}
              onChange={(e) => {
                setSurveyorId(e.target.value);
                setPage(1);
              }}
              className="border border-slate-300 rounded-lg px-2.5 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
            >
              <option value="">All Surveyors</option>
              {surveyors.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.user?.full_name || emp.employee_code} ({emp.employee_code})
                </option>
              ))}
            </select>
          </div>
        )}

        <button
          onClick={fetchSurveys}
          title="Refresh List"
          className="p-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition shrink-0 self-end md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Table / Cards */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <Clock className="w-6 h-6 animate-spin text-amber-500" />
            <span>Loading site surveys...</span>
          </div>
        ) : surveys.length === 0 ? (
          <div className="py-20 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <Compass className="w-10 h-10 text-slate-300 stroke-1" />
            <span className="font-semibold text-slate-600 text-sm">No site surveys found</span>
            <p className="max-w-sm text-slate-400">
              {tabFilter ? `No surveys currently matching filter '${tabFilter}'.` : 'No site surveys scheduled yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Survey #</th>
                  <th className="py-3 px-4">Customer & Enquiry</th>
                  <th className="py-3 px-4">Surveyor</th>
                  <th className="py-3 px-4">Scheduled Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Feasibility</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {surveys.map((srv) => {
                  const isAssignedTech = isTechnician; // In tech view, only assigned are returned
                  const isEditable = srv.status === 'DRAFT' || srv.status === 'CORRECTION_REQUESTED';
                  const canEdit = isEditable && (isSuperAdmin || isDirector || isTechManager || isAssignedTech);
                  const canReview = (isSuperAdmin || isDirector || isTechManager) && (srv.status === 'SUBMITTED' || srv.status === 'UNDER_REVIEW');

                  return (
                    <tr key={srv.id} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900 whitespace-nowrap">
                        <button
                          onClick={() => onOpenDetail(srv.id)}
                          className="hover:text-amber-600 hover:underline transition"
                        >
                          {srv.survey_number}
                        </button>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{srv.customer_name || 'N/A'}</div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                          <span className="font-mono text-amber-600 font-medium">{srv.enquiry_number}</span>
                          <span>•</span>
                          <span>{srv.proposed_capacity_kw ? `${srv.proposed_capacity_kw} kW` : 'Custom'}</span>
                          {srv.customer_city && (
                            <>
                              <span>•</span>
                              <span>{srv.customer_city}</span>
                            </>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="text-slate-800 font-semibold">{srv.surveyor_name || srv.surveyor_code}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{srv.surveyor_code}</div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="text-slate-800">
                          {srv.scheduled_at ? new Date(srv.scheduled_at).toLocaleDateString() : '—'}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {srv.scheduled_at ? new Date(srv.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </div>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        {statusBadge(srv.status)}
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`font-semibold ${srv.technical_feasibility === 'FEASIBLE' ? 'text-emerald-700' : srv.technical_feasibility === 'CONDITIONAL' ? 'text-amber-700' : 'text-rose-700'}`}>
                          {srv.technical_feasibility}
                        </span>
                        {srv.shadow_free_area_sqft !== null && (
                          <div className="text-[10px] text-slate-400">
                            {srv.shadow_free_area_sqft} sq ft usable
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* View Detail Button */}
                          <button
                            onClick={() => onOpenDetail(srv.id)}
                            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 rounded-md transition"
                            title="View Survey Details & Photos"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {/* Record / Edit Observations Button */}
                          {canEdit && (
                            <button
                              onClick={() => onOpenEditObservations(srv)}
                              className="px-2 py-1 text-[11px] font-bold rounded bg-slate-800 hover:bg-slate-700 text-white transition flex items-center gap-1 shadow-xs"
                              title="Record or Edit Measurements"
                            >
                              <Edit2 className="w-3 h-3" />
                              <span>Measure</span>
                            </button>
                          )}

                          {/* Technical Review Button */}
                          {canReview && (
                            <button
                              onClick={() => onOpenApproval(srv)}
                              className="px-2 py-1 text-[11px] font-bold rounded bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1 shadow-xs"
                              title="Review Feasibility & Sign-off"
                            >
                              <ShieldCheck className="w-3 h-3" />
                              <span>Review</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {total > 0 && (
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing <span className="font-semibold text-slate-800">{surveys.length}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> surveys
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 rounded bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition font-medium"
              >
                Previous
              </button>
              <span className="font-semibold text-slate-800 font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1 rounded bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition font-medium"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
