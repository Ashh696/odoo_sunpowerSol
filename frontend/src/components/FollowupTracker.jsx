import React, { useState, useEffect } from 'react';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  Phone,
  Mail,
  Calendar,
  MessageSquare,
  Plus,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { getFollowups } from '../services/crmApi';

export default function FollowupTracker({ onOpenSchedule, onOpenComplete, refreshKey }) {
  const [followups, setFollowups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [activeTab, setActiveTab] = useState('ALL'); // ALL, OVERDUE, SCHEDULED, COMPLETED
  const [channelFilter, setChannelFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchFollowups = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit: 15,
        followup_type: channelFilter || undefined,
        status: activeTab === 'COMPLETED' ? 'COMPLETED' : activeTab === 'SCHEDULED' ? 'SCHEDULED' : undefined,
        overdue_only: activeTab === 'OVERDUE' ? true : undefined,
      };
      const res = await getFollowups(params);
      if (res && res.data) {
        setFollowups(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to load follow-ups');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFollowups();
  }, [page, activeTab, channelFilter, refreshKey]);

  const channelIcons = {
    CALL: <Phone className="w-3.5 h-3.5 text-blue-600" />,
    WHATSAPP: <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />,
    VISIT: <Calendar className="w-3.5 h-3.5 text-amber-600" />,
    EMAIL: <Mail className="w-3.5 h-3.5 text-purple-600" />,
  };

  return (
    <div className="space-y-4">
      {/* Tab Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-semibold">
          {[
            { key: 'ALL', label: 'All Activities' },
            { key: 'OVERDUE', label: '⚠️ Overdue Touchpoints' },
            { key: 'SCHEDULED', label: 'Scheduled / Upcoming' },
            { key: 'COMPLETED', label: 'Completed' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg border whitespace-nowrap transition ${
                activeTab === tab.key
                  ? tab.key === 'OVERDUE'
                    ? 'bg-rose-500 text-white border-rose-500 shadow-sm'
                    : 'bg-amber-500 text-slate-950 border-amber-500 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={channelFilter}
            onChange={(e) => {
              setChannelFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs rounded-lg border border-slate-200 px-3 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All Channels</option>
            <option value="CALL">Phone Calls</option>
            <option value="WHATSAPP">WhatsApp</option>
            <option value="VISIT">Site Visits</option>
            <option value="EMAIL">Emails</option>
          </select>

          <button
            onClick={onOpenSchedule}
            className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3.5 py-1.5 rounded-lg text-xs shadow-sm transition shrink-0"
          >
            <Plus className="w-4 h-4" /> Schedule Touchpoint
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
            <span className="text-xs">Loading sales activities...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center">
            <AlertCircle className="w-6 h-6 text-rose-500 mx-auto mb-2" />
            <p className="text-xs text-rose-700 font-semibold">{error}</p>
          </div>
        ) : followups.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-semibold text-slate-600">No activities found</p>
            <p className="text-xs text-slate-400 mt-1">Schedule a customer follow-up to track communications.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Channel & Time</th>
                  <th className="py-3 px-4">Customer & Enquiry</th>
                  <th className="py-3 px-4">Conducted By</th>
                  <th className="py-3 px-4">Discussion / Agenda</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {followups.map((f) => (
                  <tr key={f.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 font-bold text-slate-900">
                        {channelIcons[f.followup_type] || <Clock className="w-3.5 h-3.5" />}
                        <span>{f.followup_type}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {new Date(f.scheduled_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{f.customer_name || 'Customer'}</div>
                      <div className="font-mono text-[11px] text-amber-700">{f.enquiry_number}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-900">{f.conductor_name}</div>
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      {f.discussion_summary ? (
                        <p className="text-slate-700 line-clamp-2">{f.discussion_summary}</p>
                      ) : (
                        <span className="text-slate-400 italic">No notes logged</span>
                      )}
                      {f.next_followup_at && (
                        <div className="text-[10px] text-slate-400 mt-1">
                          Next planned: {new Date(f.next_followup_at).toLocaleDateString()}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {f.is_overdue ? (
                        <span className="text-[10px] font-black uppercase text-rose-700 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-rose-500" /> Overdue
                        </span>
                      ) : f.status === 'COMPLETED' ? (
                        <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Done
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                          Scheduled
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {f.status === 'SCHEDULED' ? (
                        <button
                          onClick={() => onOpenComplete(f)}
                          className="px-2.5 py-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-md transition"
                        >
                          Log Notes
                        </button>
                      ) : (
                        <span className="text-slate-400 text-xs">Completed</span>
                      )}
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
              Showing {followups.length} of {total} activities
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
