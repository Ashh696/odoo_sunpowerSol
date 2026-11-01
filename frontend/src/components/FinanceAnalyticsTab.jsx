import React from 'react';
import {
  DollarSign,
  Receipt,
  Clock,
  AlertTriangle,
  TrendingUp,
  Download,
  Info,
  Calendar,
  Layers,
} from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { downloadAnalyticsCSV } from '../services/analyticsApi';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function FinanceAnalyticsTab({ data, dateRange }) {
  if (!data) return null;

  const {
    total_invoiced,
    cash_collected,
    outstanding_receivables,
    overdue_receivables,
    overdue_invoices_count,
    unallocated_cash,
    allocated_cash,
    unbilled_order_obligation,
    aging_buckets,
    milestone_breakdown,
    cash_flow_trend,
    estimated_gross_margin,
    accounting_notes,
  } = data;

  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  // Cash flow trend chart
  const trendLabels = (cash_flow_trend || []).map((c) => c.month);
  const trendInvoiced = (cash_flow_trend || []).map((c) => parseFloat(c.invoiced_amount || 0));
  const trendCollected = (cash_flow_trend || []).map((c) => parseFloat(c.collected_amount || 0));

  const chartData = {
    labels: trendLabels.length > 0 ? trendLabels : ['No Data'],
    datasets: [
      {
        label: 'Invoiced Billed',
        data: trendInvoiced.length > 0 ? trendInvoiced : [0],
        backgroundColor: 'rgba(59, 130, 246, 0.7)', // Sky
        borderRadius: 6,
      },
      {
        label: 'Cash Collected',
        data: trendCollected.length > 0 ? trendCollected : [0],
        backgroundColor: 'rgba(16, 185, 129, 0.8)', // Emerald
        borderRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { font: { size: 11, weight: '600' } },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => `₹${value / 1000}k`,
        },
      },
    },
  };

  return (
    <div className="space-y-8">
      {/* Top Header & Export Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Financial Revenue, Collections & Receivables Aging</h3>
          <p className="text-xs text-slate-500">
            Reconciled tax invoices, cash collection receipts, unbilled contract obligations, and aging analysis.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => downloadAnalyticsCSV('finance_invoices', dateRange)}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-3 py-1.5 rounded-lg text-xs border border-slate-200 shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" /> Export Invoices CSV
          </button>
          <button
            onClick={() => downloadAnalyticsCSV('finance_payments', dateRange)}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-3 py-1.5 rounded-lg text-xs border border-slate-200 shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" /> Export Payments CSV
          </button>
          <button
            onClick={() => downloadAnalyticsCSV('receivables_aging', dateRange)}
            className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5" /> Export Aging CSV
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Invoiced</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{formatCurrency(total_invoiced)}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Tax invoices issued</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Receipt className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Cash Collected</span>
            <div className="text-2xl font-black text-emerald-600 mt-1">{formatCurrency(cash_collected)}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              Unallocated: {formatCurrency(unallocated_cash)}
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Receivables</span>
            <div className="text-2xl font-black text-amber-600 mt-1">{formatCurrency(outstanding_receivables)}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Uncollected invoice balance</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Overdue Receivables</span>
            <div className={`text-2xl font-black mt-1 ${parseFloat(overdue_receivables) > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
              {formatCurrency(overdue_receivables)}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {overdue_invoices_count} invoices past due date
            </span>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${parseFloat(overdue_receivables) > 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Row 2: Aging Receivables & Monthly Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Aging Buckets Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-500" />
              <span>Receivables Aging Buckets</span>
            </h4>
            <span className="text-xs font-semibold text-slate-500">By Due Date</span>
          </div>

          <div className="space-y-3">
            {(aging_buckets || []).map((b) => (
              <div key={b.bucket} className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-800">{b.bucket}</span>
                  <div className="text-[11px] text-slate-400">{b.count} invoices</div>
                </div>
                <div className={`text-sm font-black ${b.bucket === 'Current' ? 'text-slate-900' : 'text-rose-600'}`}>
                  {formatCurrency(b.amount)}
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs">
            <div className="flex justify-between items-center text-indigo-950 font-bold">
              <span>Unbilled Order Obligation:</span>
              <span>{formatCurrency(unbilled_order_obligation)}</span>
            </div>
            <p className="text-[11px] text-indigo-800 mt-1">
              Active customer contracts not yet billed into milestone invoices.
            </p>
          </div>
        </div>

        {/* Monthly Billing & Collection Chart */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <span>Billing vs Cash Collection Trend</span>
            </h4>
            <span className="text-xs text-slate-400">Monthly progression</span>
          </div>
          <div className="h-64">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Row 3: Milestone Breakdown Table & Estimated Gross Margin */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Milestone Invoices Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm lg:col-span-2 overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-600" />
              <span>Milestone Invoicing Breakdown</span>
            </h4>
            <span className="text-xs text-slate-500">Commercial billing milestones</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">Milestone Type</th>
                  <th className="px-5 py-3 text-center">Invoices</th>
                  <th className="px-5 py-3 text-right">Total Invoiced</th>
                  <th className="px-5 py-3 text-right">Paid</th>
                  <th className="px-5 py-3 text-right">Balance Due</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {milestone_breakdown && milestone_breakdown.length > 0 ? (
                  milestone_breakdown.map((m) => (
                    <tr key={m.invoice_type} className="hover:bg-slate-50/80 transition">
                      <td className="px-5 py-3.5 font-bold text-slate-900">{m.invoice_type}</td>
                      <td className="px-5 py-3.5 text-center font-semibold text-slate-700">{m.count}</td>
                      <td className="px-5 py-3.5 text-right font-semibold text-slate-900">{formatCurrency(m.total_amount)}</td>
                      <td className="px-5 py-3.5 text-right font-semibold text-emerald-600">{formatCurrency(m.paid_amount)}</td>
                      <td className="px-5 py-3.5 text-right font-black text-amber-600">{formatCurrency(m.balance_amount)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-400 italic">
                      No milestone invoices recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Estimated Gross Margin Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span>Estimated Gross Margin</span>
              </h4>
              <span className="text-xs font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded-md border border-amber-200">
                Estimate Only
              </span>
            </div>

            <div className="mt-4 text-center p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800">
                Estimated Gross Margin %
              </span>
              <div className="text-3xl font-black text-emerald-900 mt-1">
                {estimated_gross_margin.estimated_gross_margin_percentage}%
              </div>
              <span className="text-xs text-emerald-700 mt-1 inline-block font-bold">
                {formatCurrency(estimated_gross_margin.estimated_gross_margin)}
              </span>
            </div>

            <div className="space-y-2 mt-4 text-xs">
              <div className="flex justify-between items-center text-slate-600">
                <span>Contracted Revenue:</span>
                <span className="font-bold text-slate-900">{formatCurrency(estimated_gross_margin.contracted_revenue)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Estimated Product Cost:</span>
                <span className="font-semibold text-rose-600">-{formatCurrency(estimated_gross_margin.estimated_product_cost)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-600">
                <span>Estimated Installation Cost:</span>
                <span className="font-semibold text-rose-600">-{formatCurrency(estimated_gross_margin.estimated_installation_cost)}</span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-amber-50/80 rounded-xl border border-amber-200 text-[11px] text-amber-900 flex items-start gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>{estimated_gross_margin.disclosure_note}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
