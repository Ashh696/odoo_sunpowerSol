import React from 'react';
import {
  TrendingUp,
  Inbox,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Briefcase,
  FolderKanban,
  Receipt,
  DollarSign,
  Package,
  Download,
  Zap,
} from 'lucide-react';
import { downloadAnalyticsCSV } from '../services/analyticsApi';

export default function ExecutiveAnalyticsTab({ data, dateRange, onExport }) {
  if (!data) return null;

  const {
    as_of_date,
    enquiries,
    conversion,
    orders,
    projects,
    finance,
    inventory,
  } = data;

  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  const handleExport = (reportType) => {
    downloadAnalyticsCSV(reportType, dateRange);
  };

  return (
    <div className="space-y-8">
      {/* Top Banner with As-of Date & Export Action */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/40 rounded-2xl p-6 text-white border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Zap className="w-4 h-4" /> Executive Command Snapshot
          </div>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight">SunPower Solutions Business Overview</h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Consolidated operational, sales, and financial intelligence as of {as_of_date}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('sales_summary')}
            className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-2 rounded-xl text-xs transition shadow-md shadow-amber-500/20"
          >
            <Download className="w-3.5 h-3.5" /> Export Sales CSV
          </button>
          <button
            onClick={() => handleExport('finance_invoices')}
            className="inline-flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-3 py-2 rounded-xl text-xs border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5" /> Export Invoices CSV
          </button>
        </div>
      </div>

      {/* Row 1: High Level Executive Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Pipeline Leads */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Leads Pipeline</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{enquiries.total_enquiries}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              Won: {enquiries.won_enquiries} | Lost: {enquiries.lost_enquiries}
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Inbox className="w-6 h-6" />
          </div>
        </div>

        {/* Overall Conversion (Won / All Leads) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              {conversion.formula_label}
            </span>
            <div className="text-2xl font-black text-emerald-600 mt-1">
              {conversion.overall_conversion_percentage}%
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {conversion.won_leads_numerator} Won of {conversion.total_leads_denominator} Total Leads
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        {/* Active Projects */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Projects</span>
            <div className="text-2xl font-black text-sky-600 mt-1">{projects.active_projects}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {projects.delayed_projects > 0 ? (
                <span className="text-rose-600 font-bold">{projects.delayed_projects} delayed</span>
              ) : (
                <span className="text-emerald-600 font-medium">On schedule</span>
              )}{' '}
              | {projects.completed_projects} done
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        {/* Cash Collected */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Cash Collections</span>
            <div className="text-2xl font-black text-emerald-700 mt-1">
              {formatCurrency(finance.cash_collected)}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              Receivables: {formatCurrency(finance.outstanding_receivables)}
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Row 2: Contracts, Invoicing & Receivables Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Order Contracts Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-amber-500" />
              <span>Commercial Orders</span>
            </h4>
            <span className="text-xs font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded-md border border-amber-200">
              {orders.total_orders} Confirmed
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Total Contract Value:</span>
              <span className="font-bold text-slate-900">{formatCurrency(orders.contract_value)}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Advance Received:</span>
              <span className="font-bold text-emerald-600">{formatCurrency(orders.advance_collected)}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Balance Pending:</span>
              <span className="font-bold text-amber-600">{formatCurrency(orders.balance_due)}</span>
            </div>
            <div className="flex justify-between items-center text-xs pt-2 border-t border-slate-100">
              <span className="text-slate-500">Unbilled Contract Obligation:</span>
              <span className="font-bold text-indigo-600">{formatCurrency(finance.unbilled_order_obligation)}</span>
            </div>
          </div>
        </div>

        {/* Invoicing & Overdue Aging */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Receipt className="w-4 h-4 text-sky-500" />
              <span>Tax Invoicing & Aging</span>
            </h4>
            <span className="text-xs font-bold bg-sky-50 text-sky-800 px-2 py-0.5 rounded-md border border-sky-200">
              Billed Revenue
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Total Invoiced to Customers:</span>
              <span className="font-bold text-slate-900">{formatCurrency(finance.total_invoiced)}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Current Invoiced Outstanding:</span>
              <span className="font-bold text-amber-600">{formatCurrency(finance.outstanding_receivables)}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Overdue Receivables (Past Due):</span>
              <span className="font-bold text-rose-600">{formatCurrency(finance.overdue_receivables)}</span>
            </div>
            <div className="flex justify-between items-center text-xs pt-2 border-t border-slate-100">
              <span className="text-slate-500">Overdue Invoices Count:</span>
              <span className={`font-bold ${finance.overdue_invoices_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {finance.overdue_invoices_count} invoices
              </span>
            </div>
          </div>
        </div>

        {/* Project Capacity & Inventory Alerts */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-emerald-500" />
              <span>Projects & Warehouse</span>
            </h4>
            <span className="text-xs font-bold bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md border border-emerald-200">
              Operations
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Commissioned Rooftop Capacity:</span>
              <span className="font-bold text-slate-900">{projects.commissioned_capacity_kw} kW</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Tracked Component SKUs:</span>
              <span className="font-bold text-slate-900">{inventory.total_products_tracked} items</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Warehouse Stock on Hand:</span>
              <span className="font-bold text-slate-900">{inventory.total_quantity_on_hand} units</span>
            </div>
            <div className="flex justify-between items-center text-xs pt-2 border-t border-slate-100">
              <span className="text-slate-500">Low-Stock Reorder Alerts:</span>
              <span className={`font-bold ${inventory.low_stock_products_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {inventory.low_stock_products_count} items need restock
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
