import React from 'react';
import {
  Truck,
  Wrench,
  ShieldCheck,
  Landmark,
  ShoppingCart,
  Boxes,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
} from 'lucide-react';

export default function OperationsAnalyticsTab({ data }) {
  if (!data) return null;

  const procurement = data.procurement || {};
  const dispatch = data.dispatch || {};
  const installation = data.installation || {};
  const service = data.service_warranty || {};
  const subsidy = data.subsidy || {};
  const pipelineStages = data.pipeline_stages || [];

  const formatINR = (val) => {
    const num = Number(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="space-y-6">
      {/* 1. Top Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Procurement Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-amber-300 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Procurement POs</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <ShoppingCart className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{procurement.total_purchase_orders || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            Total Value: <span className="font-bold text-slate-700">{formatINR(procurement.total_po_value)}</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-amber-600 font-semibold">{procurement.pending_receipt_pos_count || 0} Pending Receipt</span>
            <span className="text-slate-400">{procurement.goods_receipts_count || 0} GRNs</span>
          </div>
        </div>

        {/* Dispatch Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-amber-300 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Material Logistics</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Truck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{dispatch.total_dispatches || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            Tracked Serials: <span className="font-bold text-slate-700">{dispatch.total_serialized_items_tracked || 0}</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-blue-600 font-semibold">{dispatch.dispatches_in_transit || 0} In-Transit</span>
            <span className="text-emerald-600 font-semibold">{dispatch.dispatches_delivered || 0} Delivered</span>
          </div>
        </div>

        {/* Installations Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-amber-300 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Site Execution</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Wrench className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{installation.total_schedules || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            Tests Done: <span className="font-bold text-slate-700">{installation.tests_completed || 0}</span> | Worklogs: <span className="font-bold text-slate-700">{installation.worklogs_recorded || 0}</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-amber-600 font-semibold">{installation.active_installations || 0} In-Progress</span>
            <span className="text-emerald-600 font-semibold">{installation.completed_installations || 0} Completed</span>
          </div>
        </div>

        {/* PM Surya Ghar Subsidy Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-amber-300 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">PM Surya Ghar Subsidy</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <Landmark className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{subsidy.total_applications || 0}</div>
          <div className="text-xs text-slate-500 mt-1">
            Disbursed: <span className="font-bold text-emerald-600">{formatINR(subsidy.total_subsidy_disbursed)}</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-blue-600 font-semibold">{subsidy.submitted_applications || 0} In-DISCOM</span>
            <span className="text-emerald-600 font-semibold">{subsidy.approved_applications || 0} Approved</span>
          </div>
        </div>
      </div>

      {/* 2. Detailed Operations Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service & Warranty Operations */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-teal-50 text-teal-600">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-sm">After-Sales & Warranty Lifecycle</h3>
            </div>
            <span className="text-xs px-2.5 py-1 bg-teal-50 text-teal-700 font-bold rounded-lg">
              {service.active_warranties_count || 0} Active Warranties
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 block">Open Tickets</span>
              <span className="text-lg font-black text-slate-900">{service.open_service_tickets_count || 0}</span>
            </div>
            <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
              <span className="text-xs text-rose-600 block">Critical Tickets</span>
              <span className="text-lg font-black text-rose-900">{service.critical_tickets_count || 0}</span>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
              <span className="text-xs text-emerald-600 block">Resolved Tickets</span>
              <span className="text-lg font-black text-emerald-900">{service.resolved_tickets_count || 0}</span>
            </div>
            <div className="p-3 bg-indigo-50 rounded-xl border border-indigo-100">
              <span className="text-xs text-indigo-600 block">Technician Visits</span>
              <span className="text-lg font-black text-indigo-900">{service.technician_visits_completed || 0}</span>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl border border-purple-100">
              <span className="text-xs text-purple-600 block">Replacements</span>
              <span className="text-lg font-black text-purple-900">{service.components_replaced_count || 0}</span>
            </div>
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
              <span className="text-xs text-amber-600 block">Low Stock Alerts</span>
              <span className="text-lg font-black text-amber-900">{procurement.low_stock_alerts_count || 0}</span>
            </div>
          </div>
        </div>

        {/* Project Pipeline Stage Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900 text-sm">Solar Project Lifecycle Stages</h3>
            </div>
            <span className="text-xs text-slate-400">Total Stages: {pipelineStages.length}</span>
          </div>

          <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {pipelineStages.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">No active project pipeline data available.</p>
            ) : (
              pipelineStages.map((st, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl hover:bg-slate-100 transition">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                    <span className="text-xs font-bold text-slate-700">{st.stage.replace(/_/g, ' ')}</span>
                  </div>
                  <span className="px-2.5 py-0.5 bg-white border border-slate-200 text-xs font-black text-slate-900 rounded-lg">
                    {st.count} Projects
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
