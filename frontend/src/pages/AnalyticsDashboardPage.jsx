import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  FolderKanban,
  Package,
  Receipt,
  Calendar,
  RefreshCw,
  AlertTriangle,
  Zap,
  Filter,
  Layers,
} from 'lucide-react';
import {
  getExecutiveAnalytics,
  getSalesAnalytics,
  getProjectAnalytics,
  getInventoryAnalytics,
  getFinanceAnalytics,
  getOperationsAnalytics,
} from '../services/analyticsApi';
import ExecutiveAnalyticsTab from '../components/ExecutiveAnalyticsTab';
import SalesAnalyticsTab from '../components/SalesAnalyticsTab';
import ProjectAnalyticsTab from '../components/ProjectAnalyticsTab';
import InventoryAnalyticsTab from '../components/InventoryAnalyticsTab';
import FinanceAnalyticsTab from '../components/FinanceAnalyticsTab';
import OperationsAnalyticsTab from '../components/OperationsAnalyticsTab';

export default function AnalyticsDashboardPage() {
  const [activeTab, setActiveTab] = useState('executive');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [appliedDateRange, setAppliedDateRange] = useState({ date_from: '', date_to: '' });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabData, setTabData] = useState(null);

  // Load analytics data for active tab
  const fetchTabData = async (tab, dateFilter = appliedDateRange) => {
    setLoading(true);
    setError(null);
    try {
      let res = null;
      const params = {};
      if (dateFilter.date_from) params.date_from = dateFilter.date_from;
      if (dateFilter.date_to) params.date_to = dateFilter.date_to;

      if (tab === 'executive') {
        res = await getExecutiveAnalytics(params);
      } else if (tab === 'sales') {
        res = await getSalesAnalytics(params);
      } else if (tab === 'projects') {
        res = await getProjectAnalytics(params);
      } else if (tab === 'inventory') {
        res = await getInventoryAnalytics(params);
      } else if (tab === 'finance') {
        res = await getFinanceAnalytics(params);
      } else if (tab === 'operations') {
        res = await getOperationsAnalytics();
      }

      if (res && res.data) {
        setTabData(res.data);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to aggregate analytics data';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTabData(activeTab, appliedDateRange);
  }, [activeTab, appliedDateRange]);

  const handleApplyFilter = (e) => {
    e.preventDefault();
    if (dateFrom && dateTo && dateTo < dateFrom) {
      alert('End Date cannot be earlier than Start Date.');
      return;
    }
    setAppliedDateRange({ date_from: dateFrom, date_to: dateTo });
  };

  const handleResetFilter = () => {
    setDateFrom('');
    setDateTo('');
    setAppliedDateRange({ date_from: '', date_to: '' });
  };

  const applyPreset = (presetKey) => {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const formatDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    const todayStr = formatDate(now);
    let fromStr = todayStr;
    let toStr = todayStr;

    if (presetKey === 'today') {
      fromStr = todayStr;
      toStr = todayStr;
    } else if (presetKey === 'this_week') {
      const day = now.getDay();
      const diffToMonday = day === 0 ? -6 : 1 - day;
      const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() + diffToMonday);
      fromStr = formatDate(monday);
      toStr = todayStr;
    } else if (presetKey === 'mtd') {
      const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      fromStr = formatDate(firstOfMonth);
      toStr = todayStr;
    } else if (presetKey === 'qtd') {
      const qMonth = Math.floor(now.getMonth() / 3) * 3;
      const firstOfQuarter = new Date(now.getFullYear(), qMonth, 1);
      fromStr = formatDate(firstOfQuarter);
      toStr = todayStr;
    } else if (presetKey === 'ytd') {
      const firstOfYear = new Date(now.getFullYear(), 0, 1);
      fromStr = formatDate(firstOfYear);
      toStr = todayStr;
    } else if (presetKey === 'last_30_days') {
      const thirtyDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 30);
      fromStr = formatDate(thirtyDaysAgo);
      toStr = todayStr;
    }

    setDateFrom(fromStr);
    setDateTo(toStr);
    setAppliedDateRange({ date_from: fromStr, date_to: toStr });
  };

  const tabs = [
    { id: 'executive', label: 'Executive Overview', icon: Zap },
    { id: 'operations', label: 'Operational Workflow', icon: Layers },
    { id: 'sales', label: 'Sales & CRM', icon: TrendingUp },
    { id: 'projects', label: 'Projects & Operations', icon: FolderKanban },
    { id: 'inventory', label: 'Inventory & Warehouse', icon: Package },
    { id: 'finance', label: 'Finance & Invoicing', icon: Receipt },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">Analytics & Business Intelligence</h2>
              <p className="text-xs text-slate-500">
                Live performance metrics, financial reconciliation, operations tracking, and Excel-compatible exports.
              </p>
            </div>
          </div>
        </div>

        {/* Global Date Filter Controls */}
        <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
          {/* Quick Date Presets */}
          <div className="flex flex-wrap items-center gap-1 bg-white p-1.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-bold text-slate-400 pl-1 pr-1 uppercase tracking-wider">Presets:</span>
            {[
              { id: 'today', label: 'Today' },
              { id: 'this_week', label: 'This Week' },
              { id: 'mtd', label: 'MTD' },
              { id: 'qtd', label: 'QTD' },
              { id: 'ytd', label: 'YTD' },
              { id: 'last_30_days', label: 'Last 30 Days' },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => applyPreset(p.id)}
                className="px-2 py-1 text-[11px] font-semibold rounded-lg bg-slate-50 hover:bg-amber-50 hover:text-amber-800 text-slate-700 border border-slate-200 transition"
              >
                {p.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleApplyFilter} className="flex flex-wrap items-center gap-2 bg-white p-2 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs text-slate-600 pl-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-semibold">Period:</span>
            </div>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
              title="Start Date"
            />
            <span className="text-slate-400 text-xs">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-2.5 py-1 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
              title="End Date"
            />
            <button
              type="submit"
              className="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg transition"
            >
              Apply
            </button>
            {(appliedDateRange.date_from || appliedDateRange.date_to) && (
              <button
                type="button"
                onClick={handleResetFilter}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold text-xs rounded-lg transition"
              >
                Reset
              </button>
            )}
          </form>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="border-b border-slate-200 bg-white rounded-t-2xl px-4 pt-2 shadow-xs">
        <nav className="flex space-x-2 overflow-x-auto pb-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl whitespace-nowrap transition ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 shadow-sm shadow-amber-500/20'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
          <span className="text-sm font-semibold text-slate-600">Aggregating analytical intelligence...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-600 shrink-0" />
            <div>
              <h4 className="text-sm font-bold">Analytics Authorization or Query Error</h4>
              <p className="text-xs text-rose-800 mt-0.5">{error}</p>
            </div>
          </div>
          <button
            onClick={() => fetchTabData(activeTab, appliedDateRange)}
            className="text-xs bg-rose-100 hover:bg-rose-200 text-rose-950 font-bold px-3 py-1.5 rounded-lg shrink-0 transition"
          >
            Retry
          </button>
        </div>
      ) : (
        <div>
          {activeTab === 'executive' && (
            <ExecutiveAnalyticsTab data={tabData} dateRange={appliedDateRange} />
          )}
          {activeTab === 'operations' && (
            <OperationsAnalyticsTab data={tabData} />
          )}
          {activeTab === 'sales' && (
            <SalesAnalyticsTab data={tabData} dateRange={appliedDateRange} />
          )}
          {activeTab === 'projects' && (
            <ProjectAnalyticsTab data={tabData} dateRange={appliedDateRange} />
          )}
          {activeTab === 'inventory' && (
            <InventoryAnalyticsTab data={tabData} dateRange={appliedDateRange} />
          )}
          {activeTab === 'finance' && (
            <FinanceAnalyticsTab data={tabData} dateRange={appliedDateRange} />
          )}
        </div>
      )}
    </div>
  );
}
