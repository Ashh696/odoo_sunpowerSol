import React from 'react';
import {
  FolderKanban,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  Sun,
  Download,
  Calendar,
} from 'lucide-react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { downloadAnalyticsCSV } from '../services/analyticsApi';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function ProjectAnalyticsTab({ data, dateRange }) {
  if (!data) return null;

  const {
    total_projects,
    active_projects,
    completed_projects,
    delayed_projects,
    cancelled_projects,
    status_distribution,
    average_completion_duration_days,
    capacity_distribution_by_type,
    project_managers_workload,
    schedule_workload,
  } = data;

  const statusColors = {
    INITIATED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    PROCUREMENT: 'bg-sky-50 text-sky-700 border-sky-200',
    DISPATCHED: 'bg-amber-50 text-amber-800 border-amber-300 font-bold',
    INSTALLATION: 'bg-purple-50 text-purple-700 border-purple-200',
    COMMISSIONED: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold',
    HANDED_OVER: 'bg-teal-50 text-teal-800 border-teal-300 font-bold',
    ON_HOLD: 'bg-slate-100 text-slate-700 border-slate-300',
    CANCELLED: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  // Doughnut chart for capacity by system type
  const typeLabels = Object.keys(capacity_distribution_by_type || {});
  const typeValues = Object.values(capacity_distribution_by_type || {}).map((v) => parseFloat(v || 0));

  const doughnutData = {
    labels: typeLabels.length > 0 ? typeLabels : ['No Projects'],
    datasets: [
      {
        data: typeValues.length > 0 ? typeValues : [1],
        backgroundColor: [
          'rgba(245, 158, 11, 0.8)', // Amber (ON_GRID)
          'rgba(14, 165, 233, 0.8)', // Sky (OFF_GRID)
          'rgba(139, 92, 246, 0.8)', // Purple (HYBRID)
        ],
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { font: { size: 11, weight: '600' } },
      },
    },
  };

  return (
    <div className="space-y-8">
      {/* Top Header & Export */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Project Operations & Installation Engineering</h3>
          <p className="text-xs text-slate-500">
            Lifecycle monitoring from technical handover to commissioning, turnaround times, and manager workloads.
          </p>
        </div>
        <button
          onClick={() => downloadAnalyticsCSV('projects_summary', dateRange)}
          className="inline-flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white font-bold px-3 py-1.5 rounded-lg text-xs shadow-sm transition"
        >
          <Download className="w-3.5 h-3.5" /> Export Projects CSV
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Work Orders</span>
            <div className="text-2xl font-black text-sky-600 mt-1">{active_projects}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">In engineering pipeline</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Completed & Handed Over</span>
            <div className="text-2xl font-black text-emerald-600 mt-1">{completed_projects}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Commissioned rooftop plants</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Delayed Work Orders</span>
            <div className={`text-2xl font-black mt-1 ${delayed_projects > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
              {delayed_projects}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {delayed_projects > 0 ? 'Past planned completion date' : 'All milestones on schedule'}
            </span>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${delayed_projects > 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Avg Completion Cycle</span>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {average_completion_duration_days !== null ? `${average_completion_duration_days} Days` : 'N/A'}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Planned start to commissioning</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Status Distribution Grid & Capacity Doughnut */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution Cards */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sun className="w-4 h-4 text-amber-500" />
              <span>Project Execution Stages</span>
            </h4>
            <span className="text-xs font-semibold text-slate-500">Total: {total_projects} Projects</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { key: 'INITIATED', label: '1. Initiated' },
              { key: 'PROCUREMENT', label: '2. Procurement' },
              { key: 'DISPATCHED', label: '3. Dispatched' },
              { key: 'INSTALLATION', label: '4. Installation' },
              { key: 'COMMISSIONED', label: '5. Commissioned' },
              { key: 'HANDED_OVER', label: '6. Handed Over' },
              { key: 'ON_HOLD', label: '7. On Hold' },
              { key: 'CANCELLED', label: '8. Cancelled' },
            ].map((st) => {
              const count = status_distribution?.[st.key] || 0;
              return (
                <div
                  key={st.key}
                  className={`p-3.5 rounded-xl border text-center transition ${
                    statusColors[st.key] || 'bg-slate-50 text-slate-800 border-slate-200'
                  }`}
                >
                  <div className="text-xs font-semibold opacity-80 uppercase tracking-tight">{st.label}</div>
                  <div className="text-2xl font-black mt-1.5">{count}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Capacity Distribution by System Type */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
              <Sun className="w-4 h-4 text-amber-500" />
              <span>Capacity by System Type (kW)</span>
            </h4>
            <div className="h-48 mt-3">
              <Doughnut data={doughnutData} options={doughnutOptions} />
            </div>
          </div>
          <div className="pt-2 border-t border-slate-100 space-y-1 text-xs">
            {typeLabels.map((t, idx) => (
              <div key={t} className="flex justify-between items-center text-slate-600">
                <span className="font-semibold">{t}:</span>
                <span className="font-black text-slate-900">{capacity_distribution_by_type[t]} kW</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Project Managers Workload Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-4 h-4 text-sky-600" />
            <span>Technical Managers Workload & Capacity Roster</span>
          </h4>
          <span className="text-xs text-slate-500">Assigned solar projects</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Project Manager</th>
                <th className="px-5 py-3 text-center">Active Projects</th>
                <th className="px-5 py-3 text-center">Completed</th>
                <th className="px-5 py-3 text-center">Delayed</th>
                <th className="px-5 py-3 text-right">Managed Capacity (kW)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {project_managers_workload && project_managers_workload.length > 0 ? (
                project_managers_workload.map((pm) => (
                  <tr key={pm.employee_id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-3.5 font-bold text-slate-900">{pm.employee_name}</td>
                    <td className="px-5 py-3.5 text-center font-bold text-sky-600">{pm.active_projects}</td>
                    <td className="px-5 py-3.5 text-center font-bold text-emerald-600">{pm.completed_projects}</td>
                    <td className="px-5 py-3.5 text-center">
                      {pm.delayed_projects > 0 ? (
                        <span className="inline-block px-2 py-0.5 rounded-full font-bold bg-rose-50 text-rose-700 border border-rose-200">
                          {pm.delayed_projects} delayed
                        </span>
                      ) : (
                        <span className="text-slate-400 font-medium">0</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right font-black text-slate-900">
                      {pm.total_capacity_kw} kW
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-400 italic">
                    No assigned technical project managers found.
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
