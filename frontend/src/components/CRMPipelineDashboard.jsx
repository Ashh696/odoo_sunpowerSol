import React, { useState, useEffect } from 'react';
import {
  Users,
  Inbox,
  CheckCircle2,
  AlertTriangle,
  Clock,
  TrendingUp,
  Zap,
  ArrowRight,
  Phone,
  Mail,
  Calendar,
  MessageSquare,
  RefreshCw,
  SunMedium
} from 'lucide-react';
import { getCRMDashboard } from '../services/crmApi';

export default function CRMPipelineDashboard({ onNavigateToEnquiries, onNavigateToFollowups, onSelectEnquiry }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCRMDashboard();
      if (res && res.data) {
        setMetrics(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load CRM dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-amber-500 mb-3" />
        <p className="text-sm text-slate-600 font-medium">Aggregating CRM sales pipeline & activities...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600" />
          <span className="text-sm font-semibold">{error}</span>
        </div>
        <button
          onClick={fetchDashboard}
          className="text-xs bg-rose-100 hover:bg-rose-200 text-rose-950 font-bold px-3 py-1.5 rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!metrics) return null;

  const stageColors = {
    NEW: 'bg-sky-50 text-sky-700 border-sky-200',
    CONTACTED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    SURVEY_REQUESTED: 'bg-amber-50 text-amber-800 border-amber-300 font-bold',
    QUOTED: 'bg-purple-50 text-purple-700 border-purple-200',
    WON: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold',
    LOST: 'bg-slate-100 text-slate-700 border-slate-300',
    CANCELLED: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Refresh */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Sales Pipeline & CRM Overview</h3>
          <p className="text-xs text-slate-500">Live operational snapshot of rooftop solar leads, qualified enquiries, and technician surveys.</p>
        </div>
        <button
          onClick={fetchDashboard}
          className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-1.5 rounded-lg text-xs font-semibold transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Data
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Pipeline Leads</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{metrics.total_enquiries}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Across all residential & commercial</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Inbox className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Survey Requested</span>
            <div className="text-2xl font-black text-amber-600 mt-1">
              {metrics.enquiries_by_status?.SURVEY_REQUESTED || 0}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Qualified for site feasibility</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <SunMedium className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Customers</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{metrics.active_customers}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Registered rooftop owners</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Overdue Follow-ups</span>
            <div className={`text-2xl font-black mt-1 ${metrics.overdue_followups_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
              {metrics.overdue_followups_count}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {metrics.scheduled_today_followups_count} scheduled today
            </span>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${metrics.overdue_followups_count > 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <Clock className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Pipeline Funnel Stage Cards */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-500" />
            <span>Pipeline Progression Stages</span>
          </h4>
          <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200" title="Formula: Won Enquiries / Total Enquiries (including all 7 stages) * 100">
            Overall Conversion (Won / All Leads): {metrics.conversion_rate_percentage}%
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { key: 'NEW', label: '1. New Enquiries' },
            { key: 'CONTACTED', label: '2. Contacted' },
            { key: 'SURVEY_REQUESTED', label: '3. Survey Req.' },
            { key: 'QUOTED', label: '4. Quoted' },
            { key: 'WON', label: '5. Won Orders' },
            { key: 'LOST', label: '6. Lost' },
            { key: 'CANCELLED', label: '7. Cancelled' },
          ].map((st) => {
            const count = metrics.enquiries_by_status?.[st.key] || 0;
            return (
              <div
                key={st.key}
                onClick={onNavigateToEnquiries}
                className={`p-3.5 rounded-xl border text-center cursor-pointer transition hover:scale-102 hover:shadow-sm ${
                  stageColors[st.key] || 'bg-slate-50 text-slate-800 border-slate-200'
                }`}
              >
                <div className="text-xs font-semibold opacity-80 uppercase tracking-tight">{st.label}</div>
                <div className="text-2xl font-black mt-1.5">{count}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two-Column Layout: Recent Enquiries & Pending Follow-ups */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Enquiries Box */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>Recent Solar Enquiries</span>
              </h4>
              <button
                onClick={onNavigateToEnquiries}
                className="text-xs font-bold text-amber-600 hover:text-amber-700 flex items-center gap-1"
              >
                View Pipeline <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100 mt-2">
              {metrics.recent_enquiries && metrics.recent_enquiries.length > 0 ? (
                metrics.recent_enquiries.map((enq) => (
                  <div
                    key={enq.id}
                    onClick={() => onSelectEnquiry && onSelectEnquiry(enq)}
                    className="py-3 flex items-center justify-between hover:bg-slate-50 rounded-lg px-2 cursor-pointer transition"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">{enq.enquiry_number}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${stageColors[enq.status] || 'bg-slate-100 text-slate-800'}`}>
                          {enq.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-600 mt-1">
                        <span className="font-medium text-slate-900">{enq.customer_name}</span> • {enq.customer_city || 'City'} • <span className="font-semibold text-amber-700">{enq.proposed_capacity_kw} kW {enq.system_type}</span>
                      </div>
                    </div>
                    <div className="text-right text-[11px] text-slate-400">
                      {new Date(enq.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              ) : (
                <p className="py-6 text-center text-xs text-slate-400">No enquiries recorded yet.</p>
              )}
            </div>
          </div>
        </div>

        {/* Pending Follow-ups Box */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                <span>Pending Touchpoints & Calls</span>
              </h4>
              <button
                onClick={onNavigateToFollowups}
                className="text-xs font-bold text-amber-600 hover:text-amber-700 flex items-center gap-1"
              >
                Follow-up Tracker <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100 mt-2">
              {metrics.pending_followups && metrics.pending_followups.length > 0 ? (
                metrics.pending_followups.map((f) => (
                  <div key={f.id} className="py-3 flex items-center justify-between hover:bg-slate-50 rounded-lg px-2">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center shrink-0 mt-0.5">
                        {f.followup_type === 'CALL' && <Phone className="w-4 h-4" />}
                        {f.followup_type === 'EMAIL' && <Mail className="w-4 h-4" />}
                        {f.followup_type === 'VISIT' && <Calendar className="w-4 h-4" />}
                        {f.followup_type === 'WHATSAPP' && <MessageSquare className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">{f.customer_name || f.enquiry_number}</span>
                          {f.is_overdue && (
                            <span className="text-[10px] font-black uppercase text-rose-600 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded">
                              Overdue
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Assigned to: <span className="font-medium text-slate-700">{f.conductor_name}</span>
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-[11px] text-slate-500">
                      {new Date(f.scheduled_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ))
              ) : (
                <p className="py-6 text-center text-xs text-slate-400">All scheduled follow-ups are up to date!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
