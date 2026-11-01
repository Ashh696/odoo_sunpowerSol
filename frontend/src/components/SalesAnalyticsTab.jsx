import React from 'react';
import {
  TrendingUp,
  Users,
  Award,
  FileText,
  DollarSign,
  Download,
  BarChart2,
  PieChart,
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

export default function SalesAnalyticsTab({ data, dateRange }) {
  if (!data) return null;

  const {
    total_enquiries,
    status_distribution,
    source_distribution,
    system_type_distribution,
    volume_over_time,
    reps_performance,
    quotations_metric,
  } = data;

  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  const stageColors = {
    NEW: 'bg-sky-50 text-sky-700 border-sky-200',
    CONTACTED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    SURVEY_REQUESTED: 'bg-amber-50 text-amber-800 border-amber-300 font-bold',
    QUOTED: 'bg-purple-50 text-purple-700 border-purple-200',
    WON: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold',
    LOST: 'bg-slate-100 text-slate-700 border-slate-300',
    CANCELLED: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  // Prepare Chart.js dataset for volume over time
  const chartLabels = (volume_over_time || []).map((v) => v.period);
  const chartTotalData = (volume_over_time || []).map((v) => v.count);
  const chartWonData = (volume_over_time || []).map((v) => v.won_count);

  const chartData = {
    labels: chartLabels.length > 0 ? chartLabels : ['No Data'],
    datasets: [
      {
        label: 'Total Enquiries',
        data: chartTotalData.length > 0 ? chartTotalData : [0],
        backgroundColor: 'rgba(245, 158, 11, 0.7)', // Amber
        borderRadius: 6,
      },
      {
        label: 'Won Orders',
        data: chartWonData.length > 0 ? chartWonData : [0],
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
        ticks: { precision: 0 },
      },
    },
  };

  return (
    <div className="space-y-8">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Sales Pipeline & Commercial Quotations</h3>
          <p className="text-xs text-slate-500">
            Track lead progression across all 7 lifecycle stages, commercial quotation acceptance, and sales rep performance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadAnalyticsCSV('sales_summary', dateRange)}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold px-3 py-1.5 rounded-lg text-xs border border-slate-200 shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" /> Export Enquiries CSV
          </button>
          <button
            onClick={() => downloadAnalyticsCSV('sales_reps', dateRange)}
            className="inline-flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5" /> Export Sales Reps CSV
          </button>
        </div>
      </div>

      {/* 7-Stage Lead Progression Funnel */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-500" />
            <span>Lead Funnel Stages</span>
          </h4>
          <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md">
            Total Pipeline: {total_enquiries} Leads
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
            const count = status_distribution?.[st.key] || 0;
            return (
              <div
                key={st.key}
                className={`p-3.5 rounded-xl border text-center transition ${
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

      {/* Quotation Acceptance & Monthly Trend Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quotation Acceptance KPI Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-4 h-4 text-purple-600" />
                <span>Quotation Conversion</span>
              </h4>
              <span className="text-xs font-bold bg-purple-50 text-purple-700 px-2 py-0.5 rounded-md border border-purple-200">
                Commercial
              </span>
            </div>
            <div className="mt-4 text-center p-4 bg-purple-50/50 rounded-xl border border-purple-100">
              <span className="text-xs font-semibold uppercase tracking-wider text-purple-800">
                Quotation Acceptance Rate
              </span>
              <div className="text-3xl font-black text-purple-900 mt-1">
                {quotations_metric.acceptance_rate_percentage}%
              </div>
              <span className="text-xs text-purple-700 mt-1 inline-block">
                {quotations_metric.accepted_quotations} accepted of {quotations_metric.total_commercial_quotations} sent proposals
              </span>
            </div>
            <div className="space-y-3 mt-4 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Average Proposal Gross:</span>
                <span className="font-bold text-slate-900">{formatCurrency(quotations_metric.average_quotation_gross)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Average Net Payable:</span>
                <span className="font-bold text-emerald-600">{formatCurrency(quotations_metric.average_quotation_net)}</span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 italic pt-2 border-t border-slate-100">
            *Draft quotations are excluded from the commercial acceptance denominator.
          </p>
        </div>

        {/* Lead Volume Over Time Chart */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-amber-500" />
              <span>Lead Acquisition & Won Trends</span>
            </h4>
            <span className="text-xs text-slate-400">Monthly progression</span>
          </div>
          <div className="h-56">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Sales Representative Leaderboard Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-500" />
            <span>Sales Representative Performance Leaderboard</span>
          </h4>
          <span className="text-xs text-slate-500">Traceable to customer orders</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Sales Representative</th>
                <th className="px-5 py-3 text-center">Assigned Leads</th>
                <th className="px-5 py-3 text-center">Won Leads</th>
                <th className="px-5 py-3 text-center">Conversion Rate</th>
                <th className="px-5 py-3 text-right">Won Order Value (INR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reps_performance && reps_performance.length > 0 ? (
                reps_performance.map((rep) => (
                  <tr key={rep.employee_id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-slate-900">{rep.employee_name}</div>
                      <div className="text-[11px] text-slate-400">{rep.email || 'No email registered'}</div>
                    </td>
                    <td className="px-5 py-3.5 text-center font-semibold text-slate-700">{rep.enquiries_assigned}</td>
                    <td className="px-5 py-3.5 text-center font-bold text-emerald-600">{rep.enquiries_won}</td>
                    <td className="px-5 py-3.5 text-center">
                      <span className="inline-block px-2.5 py-0.5 rounded-full font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {rep.conversion_rate_percentage}%
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-black text-slate-900">
                      {formatCurrency(rep.won_order_value)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-400 italic">
                    No active sales representatives or assigned leads found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
