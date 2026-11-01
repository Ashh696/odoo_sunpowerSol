import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Inbox,
  Search,
  Plus,
  Phone,
  Calendar,
  CheckCircle2,
  Clock,
  User,
  Zap,
  Edit2,
  ArrowRight,
  Filter,
  RefreshCw,
  AlertCircle,
  Compass,
  FileText
} from 'lucide-react';
import { getEnquiries, updateEnquiryStatus } from '../services/crmApi';

export default function EnquiryList({ onOpenAdd, onOpenEdit, onScheduleFollowup, refreshKey }) {
  const [enquiries, setEnquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [systemType, setSystemType] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Inline status update state
  const [updatingId, setUpdatingId] = useState(null);

  const fetchEnquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit: 15,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        system_type: systemType || undefined,
      };
      const res = await getEnquiries(params);
      if (res && res.data) {
        setEnquiries(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to load enquiries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnquiries();
  }, [page, statusFilter, systemType, refreshKey]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchEnquiries();
  };

  const handleQuickStatusChange = async (enquiryId, newStatus) => {
    setUpdatingId(enquiryId);
    try {
      await updateEnquiryStatus(enquiryId, newStatus, `Stage updated to ${newStatus}`);
      fetchEnquiries();
    } catch (err) {
      alert(err.message || 'Failed to update enquiry status');
    } finally {
      setUpdatingId(null);
    }
  };

  const stageBadgeClasses = {
    NEW: 'bg-sky-50 text-sky-700 border-sky-200',
    CONTACTED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    SURVEY_REQUESTED: 'bg-amber-100 text-amber-900 border-amber-300 font-bold',
    QUOTED: 'bg-purple-50 text-purple-700 border-purple-200',
    WON: 'bg-emerald-100 text-emerald-900 border-emerald-300 font-bold',
    LOST: 'bg-slate-100 text-slate-700 border-slate-300',
    CANCELLED: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  return (
    <div className="space-y-4">
      {/* Stage Tab Filters */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-semibold">
        {[
          { key: '', label: 'All Pipeline' },
          { key: 'NEW', label: 'New' },
          { key: 'CONTACTED', label: 'Contacted' },
          { key: 'SURVEY_REQUESTED', label: 'Survey Requested' },
          { key: 'QUOTED', label: 'Quoted' },
          { key: 'WON', label: 'Won' },
          { key: 'LOST', label: 'Lost' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setStatusFilter(tab.key);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg border whitespace-nowrap transition ${
              statusFilter === tab.key
                ? 'bg-amber-500 text-slate-950 border-amber-500 shadow-sm'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search & Actions Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by enquiry #, customer name, phone, city, notes..."
              className="w-full text-xs pl-9 pr-4 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-2">
          <select
            value={systemType}
            onChange={(e) => {
              setSystemType(e.target.value);
              setPage(1);
            }}
            className="text-xs rounded-lg border border-slate-200 px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All System Types</option>
            <option value="ON_GRID">On-Grid</option>
            <option value="OFF_GRID">Off-Grid</option>
            <option value="HYBRID">Hybrid</option>
          </select>

          <button
            onClick={onOpenAdd}
            className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3.5 py-2 rounded-lg text-xs shadow-sm transition shrink-0"
          >
            <Plus className="w-4 h-4" /> New Enquiry
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
            <span className="text-xs">Loading sales pipeline...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center">
            <AlertCircle className="w-6 h-6 text-rose-500 mx-auto mb-2" />
            <p className="text-xs text-rose-700 font-semibold">{error}</p>
          </div>
        ) : enquiries.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <Inbox className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-semibold text-slate-600">No enquiries found</p>
            <p className="text-xs text-slate-400 mt-1">Create an enquiry or adjust the stage filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Enquiry # & Date</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">System Spec</th>
                  <th className="py-3 px-4">Sales Stage</th>
                  <th className="py-3 px-4">Assigned Rep</th>
                  <th className="py-3 px-4 text-center">Touchpoints</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {enquiries.map((enq) => (
                  <tr key={enq.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4">
                      <div className="font-mono font-bold text-slate-900">{enq.enquiry_number}</div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(enq.created_at).toLocaleDateString()} • {enq.source}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{enq.customer_name}</div>
                      <div className="text-[11px] text-slate-500">
                        {enq.customer_phone} {enq.customer_city ? `• ${enq.customer_city}` : ''}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-amber-800 flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-amber-500" /> {enq.proposed_capacity_kw} kW {enq.system_type}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {enq.roof_type || 'RCC'} {enq.monthly_electricity_bill ? `• ₹${enq.monthly_electricity_bill}/mo` : ''}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <select
                        disabled={updatingId === enq.id}
                        value={enq.status}
                        onChange={(e) => handleQuickStatusChange(enq.id, e.target.value)}
                        className={`text-[11px] font-bold px-2 py-1 rounded-lg border focus:outline-none cursor-pointer ${
                          stageBadgeClasses[enq.status] || 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}
                      >
                        <option value="NEW">NEW</option>
                        <option value="CONTACTED">CONTACTED</option>
                        <option value="SURVEY_REQUESTED">SURVEY_REQUESTED</option>
                        <option value="QUOTED">QUOTED</option>
                        <option value="WON">WON</option>
                        <option value="LOST">LOST</option>
                        <option value="CANCELLED">CANCELLED</option>
                      </select>
                    </td>
                    <td className="py-3 px-4">
                      {enq.assigned_sales_name ? (
                        <div className="font-medium text-slate-900">{enq.assigned_sales_name}</div>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                      {enq.assigned_sales_code && (
                        <div className="text-[10px] text-slate-400">{enq.assigned_sales_code}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="inline-flex items-center gap-1 text-slate-600 font-semibold bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{enq.followup_count}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        {['CONTACTED', 'SURVEY_REQUESTED'].includes(enq.status) && (
                          <Link
                            to="/surveys"
                            title="Go to Site Surveys to schedule or view"
                            className="px-2 py-1 text-[11px] font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-md transition flex items-center gap-1"
                          >
                            <Compass className="w-3 h-3" /> Survey
                          </Link>
                        )}
                        {!['CANCELLED', 'LOST'].includes(enq.status) && (
                          <Link
                            to={`/quotations?enquiry_id=${enq.id}&open_create=true`}
                            title="Generate Quotation for this Enquiry"
                            className="px-2 py-1 text-[11px] font-bold text-amber-900 bg-amber-100/80 hover:bg-amber-200 border border-amber-300 rounded-md transition flex items-center gap-1"
                          >
                            <FileText className="w-3 h-3 text-amber-700" /> Quote
                          </Link>
                        )}
                        <button
                          onClick={() => onScheduleFollowup(enq)}
                          title="Schedule Follow-up Call / Visit"
                          className="px-2 py-1 text-[11px] font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-md transition flex items-center gap-1"
                        >
                          <Phone className="w-3 h-3" /> Follow-up
                        </button>
                        <button
                          onClick={() => onOpenEdit(enq)}
                          title="Edit Enquiry"
                          className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {total > 0 && (
          <div className="p-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 bg-slate-50/50">
            <div>
              Showing {enquiries.length} of {total} enquiries
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 border border-slate-200 rounded hover:bg-white disabled:opacity-40"
              >
                Previous
              </button>
              <span className="font-semibold text-slate-700">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 border border-slate-200 rounded hover:bg-white disabled:opacity-40"
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
