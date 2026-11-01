import React, { useState, useEffect } from 'react';
import {
  Layers,
  Plus,
  Briefcase,
  Search,
  SlidersHorizontal,
  X,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Zap,
  ShieldAlert,
  Power,
  Edit2,
  Eye,
  Info,
} from 'lucide-react';
import { getMe } from '../services/employeeApi';
import { getBomTemplates, updateBomTemplateStatus } from '../services/bomApi';
import BOMTemplateModal from '../components/BOMTemplateModal';
import BOMTemplateDetailModal from '../components/BOMTemplateDetailModal';
import ProjectBOMViewModal from '../components/ProjectBOMViewModal';

const SYSTEM_TYPES = [
  { value: '', label: 'All Architectures' },
  { value: 'ON_GRID', label: 'On-Grid (Net Metered)' },
  { value: 'OFF_GRID', label: 'Off-Grid (Battery Storage)' },
  { value: 'HYBRID', label: 'Hybrid' },
];

export default function BOMManagementPage() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Modals state
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateToEdit, setTemplateToEdit] = useState(null);
  const [detailTemplateId, setDetailTemplateId] = useState(null);
  const [showProjectBomModal, setShowProjectBomModal] = useState(false);

  // Status toggle confirmation modal
  const [confirmToggleTemplate, setConfirmToggleTemplate] = useState(null);
  const [toggling, setToggling] = useState(false);

  // Templates table state
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [systemType, setSystemType] = useState('');
  const [capacityKw, setCapacityKw] = useState('');
  const [statusFilter, setStatusFilter] = useState(''); // '', 'true', 'false'
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // KPI Metrics (accurately fetched from database counts)
  const [metrics, setMetrics] = useState({
    total: 0,
    active: 0,
    onGrid: 0,
    offGrid: 0,
  });

  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = () => setRefreshKey((k) => k + 1);

  // 1. Identify authenticated user & roles
  useEffect(() => {
    getMe()
      .then((res) => {
        if (res && res.data) setCurrentUser(res.data);
      })
      .catch(() => setCurrentUser(null))
      .finally(() => setLoadingUser(false));
  }, []);

  // 2. Fetch KPI Metrics
  useEffect(() => {
    Promise.all([
      getBomTemplates({ limit: 1 }),
      getBomTemplates({ is_active: true, limit: 1 }),
      getBomTemplates({ system_type: 'ON_GRID', limit: 1 }),
      getBomTemplates({ system_type: 'OFF_GRID', limit: 1 }),
    ])
      .then(([allRes, actRes, onGridRes, offGridRes]) => {
        setMetrics({
          total: allRes?.data?.total || 0,
          active: actRes?.data?.total || 0,
          onGrid: onGridRes?.data?.total || 0,
          offGrid: offGridRes?.data?.total || 0,
        });
      })
      .catch((err) => {
        console.error('Failed to load BOM summary metrics:', err);
      });
  }, [refreshKey]);

  // 3. Fetch Templates List
  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit: 15,
        search: search.trim() || undefined,
        system_type: systemType || undefined,
        capacity_kw: capacityKw ? parseFloat(capacityKw) : undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'true',
      };

      const res = await getBomTemplates(params);
      if (res && res.data) {
        setTemplates(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch BOM templates.');
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, [page, systemType, capacityKw, statusFilter, refreshKey]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTemplates();
  };

  const handleClearFilters = () => {
    setSearch('');
    setSystemType('');
    setCapacityKw('');
    setStatusFilter('');
    setPage(1);
  };

  // Status toggle handler
  const handleToggleConfirm = async () => {
    if (!confirmToggleTemplate) return;
    setToggling(true);
    try {
      const newStatus = !confirmToggleTemplate.is_active;
      await updateBomTemplateStatus(confirmToggleTemplate.id, newStatus);
      setConfirmToggleTemplate(null);
      triggerRefresh();
    } catch (err) {
      alert(err.message || 'Failed to toggle BOM template active status.');
    } finally {
      setToggling(false);
    }
  };

  // Role permissions evaluation matching Phase 5.3A backend
  const roleSlug = currentUser?.role?.slug || '';
  const canWrite = ['SUPER_ADMIN', 'TECHNICAL_MANAGER'].includes(roleSlug);
  const canRead = canWrite || ['DIRECTOR', 'WAREHOUSE_PROCUREMENT'].includes(roleSlug);

  // Unauthorized access block
  if (!loadingUser && !canRead) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-slate-900 text-lg">Access Restricted</h3>
        <p className="text-xs text-slate-500">
          The Bill of Materials (BOM) management module is restricted to Engineering Management, Technical Operations, and Warehouse Procurement personnel.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/40 p-6 rounded-2xl border border-slate-800 shadow-xl text-white">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Layers className="w-3.5 h-3.5 animate-pulse" /> Phase 5.3 BOM Module
          </div>
          <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
            Bill of Materials (BOM) Management
          </h2>
          <p className="text-xs text-slate-400 max-w-xl">
            Standardized technical sizing templates and project bill of materials tracking across On-Grid, Off-Grid, and Hybrid installations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setShowProjectBomModal(true)}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold px-4 py-2.5 rounded-xl text-xs shadow transition"
          >
            <Briefcase className="w-4 h-4 text-amber-400" />
            <span>Project BOM Inspector</span>
          </button>

          {canWrite && (
            <button
              type="button"
              onClick={() => {
                setTemplateToEdit(null);
                setShowTemplateModal(true);
              }}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-xs shadow-md shadow-amber-500/20 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Create Template</span>
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards (All Verified Counts) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Total Templates
            </span>
            <div className="text-2xl font-black text-slate-900 mt-1">{metrics.total}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Active Templates
            </span>
            <div className="text-2xl font-black text-emerald-600 mt-1">{metrics.active}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              On-Grid Standard
            </span>
            <div className="text-2xl font-black text-amber-600 mt-1">{metrics.onGrid}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Zap className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Off-Grid Storage
            </span>
            <div className="text-2xl font-black text-sky-600 mt-1">{metrics.offGrid}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Zap className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Search Box */}
          <div className="md:col-span-4 relative">
            <input
              type="text"
              placeholder="Search by template name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-amber-500 outline-none transition"
            />
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          </div>

          {/* System Type Filter */}
          <div className="md:col-span-3">
            <select
              value={systemType}
              onChange={(e) => {
                setSystemType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:ring-2 focus:ring-amber-500 outline-none transition"
            >
              {SYSTEM_TYPES.map((st) => (
                <option key={st.value} value={st.value}>
                  {st.label}
                </option>
              ))}
            </select>
          </div>

          {/* Capacity kW Filter */}
          <div className="md:col-span-2">
            <input
              type="number"
              step="0.1"
              min="0.1"
              placeholder="Capacity kW..."
              value={capacityKw}
              onChange={(e) => {
                setCapacityKw(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:ring-2 focus:ring-amber-500 outline-none transition"
            />
          </div>

          {/* Active Status Filter */}
          <div className="md:col-span-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:ring-2 focus:ring-amber-500 outline-none transition"
            >
              <option value="">All Statuses</option>
              <option value="true">Active Only</option>
              <option value="false">Inactive Only</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="md:col-span-1 flex items-center gap-1.5 justify-end">
            <button
              type="submit"
              className="p-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition"
              title="Apply Search"
            >
              <Search className="w-3.5 h-3.5" />
            </button>
            {(search || systemType || capacityKw || statusFilter) && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="p-2 border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-xl text-xs transition"
                title="Clear Filters"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Main Templates Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            Loading BOM master templates...
          </div>
        ) : error ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <AlertCircle className="w-5 h-5" />
            </div>
            <p className="text-sm font-semibold text-rose-900">{error}</p>
            <button
              onClick={fetchTemplates}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry Load
            </button>
          </div>
        ) : templates.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <Layers className="w-6 h-6" />
            </div>
            <h4 className="font-bold text-slate-900 text-sm">No BOM Templates Found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No matching bill of materials templates found for the current search and filter criteria.
            </p>
            {canWrite && (
              <button
                onClick={() => {
                  setTemplateToEdit(null);
                  setShowTemplateModal(true);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs transition"
              >
                <Plus className="w-4 h-4" /> Create First Template
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3.5 px-4">Template Specification</th>
                  <th className="py-3.5 px-3">Architecture</th>
                  <th className="py-3.5 px-3 text-right">Capacity (kW)</th>
                  <th className="py-3.5 px-3 text-center">Items</th>
                  <th className="py-3.5 px-3 text-center">Status</th>
                  <th className="py-3.5 px-3">Created By</th>
                  <th className="py-3.5 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {templates.map((tpl) => (
                  <tr key={tpl.id} className="hover:bg-slate-50/70 transition">
                    {/* Template Name & Description */}
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900 text-sm">{tpl.template_name}</div>
                      {tpl.description ? (
                        <div className="text-[11px] text-slate-400 truncate max-w-md mt-0.5">
                          {tpl.description}
                        </div>
                      ) : (
                        <div className="text-[10px] text-slate-300 italic mt-0.5">
                          No notes provided
                        </div>
                      )}
                    </td>

                    {/* Architecture */}
                    <td className="py-3.5 px-3">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide ${
                          tpl.system_type === 'ON_GRID'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : tpl.system_type === 'OFF_GRID'
                            ? 'bg-sky-50 text-sky-700 border border-sky-200'
                            : 'bg-purple-50 text-purple-700 border border-purple-200'
                        }`}
                      >
                        {tpl.system_type}
                      </span>
                    </td>

                    {/* Capacity */}
                    <td className="py-3.5 px-3 text-right font-black text-slate-900 text-sm font-mono">
                      {tpl.capacity_kw} kW
                    </td>

                    {/* Component Count */}
                    <td className="py-3.5 px-3 text-center font-bold text-slate-700">
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs">
                        {tpl.item_count} lines
                      </span>
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          tpl.is_active
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border-rose-200'
                        }`}
                      >
                        {tpl.is_active ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Active
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3 h-3 text-rose-600" /> Inactive
                          </>
                        )}
                      </span>
                    </td>

                    {/* Creator */}
                    <td className="py-3.5 px-3 text-slate-500 text-[11px]">
                      {tpl.creator_name || 'Administrator'}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {/* View Details */}
                        <button
                          type="button"
                          onClick={() => setDetailTemplateId(tpl.id)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition shadow-2xs"
                          title="View Component Lines"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Details</span>
                        </button>

                        {/* Edit Header */}
                        {canWrite && (
                          <button
                            type="button"
                            onClick={() => {
                              setTemplateToEdit(tpl);
                              setShowTemplateModal(true);
                            }}
                            className="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition"
                            title="Edit Template Header"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {/* Toggle Active Status */}
                        {canWrite && (
                          <button
                            type="button"
                            onClick={() => setConfirmToggleTemplate(tpl)}
                            className={`p-1.5 rounded-lg transition ${
                              tpl.is_active
                                ? 'text-slate-400 hover:text-rose-600 hover:bg-rose-50'
                                : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'
                            }`}
                            title={tpl.is_active ? 'Deactivate Template' : 'Activate Template'}
                          >
                            <Power className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {total > 0 && (
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
            <div>
              Showing <span className="font-bold">{templates.length}</span> of{' '}
              <span className="font-bold">{total}</span> master templates
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-lg font-semibold hover:bg-white transition disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-2 font-medium">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                className="px-3 py-1.5 border border-slate-300 rounded-lg font-semibold hover:bg-white transition disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Template Create / Edit Modal */}
      <BOMTemplateModal
        isOpen={showTemplateModal}
        onClose={() => {
          setShowTemplateModal(false);
          setTemplateToEdit(null);
        }}
        onSuccess={triggerRefresh}
        templateToEdit={templateToEdit}
      />

      {/* Template Detail View Modal */}
      <BOMTemplateDetailModal
        isOpen={Boolean(detailTemplateId)}
        onClose={() => setDetailTemplateId(null)}
        templateId={detailTemplateId}
        canWrite={canWrite}
        onUpdated={triggerRefresh}
      />

      {/* Project BOM View Modal */}
      <ProjectBOMViewModal
        isOpen={showProjectBomModal}
        onClose={() => setShowProjectBomModal(false)}
        canWrite={canWrite}
      />

      {/* Status Toggle Confirmation Modal */}
      {confirmToggleTemplate && (
        <div className="fixed inset-0 z-60 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full border border-slate-200 shadow-2xl space-y-4">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center mx-auto ${
                confirmToggleTemplate.is_active
                  ? 'bg-rose-50 text-rose-600'
                  : 'bg-emerald-50 text-emerald-600'
              }`}
            >
              <Power className="w-5 h-5" />
            </div>
            <div className="text-center space-y-1">
              <h4 className="font-bold text-slate-900 text-sm">
                {confirmToggleTemplate.is_active ? 'Deactivate Master Template?' : 'Activate Master Template?'}
              </h4>
              <p className="text-xs text-slate-500">
                Are you sure you want to {confirmToggleTemplate.is_active ? 'deactivate' : 'activate'}{' '}
                <span className="font-semibold">{confirmToggleTemplate.template_name}</span>?
              </p>
            </div>
            <p className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
              {confirmToggleTemplate.is_active
                ? 'Inactive templates cannot be selected for new project BOM generation.'
                : 'Active templates become immediately eligible for project BOM generation and sizing.'}
            </p>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setConfirmToggleTemplate(null)}
                disabled={toggling}
                className="flex-1 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleToggleConfirm}
                disabled={toggling}
                className={`flex-1 py-2 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50 ${
                  confirmToggleTemplate.is_active
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : 'bg-emerald-600 hover:bg-emerald-500'
                }`}
              >
                {toggling ? 'Updating...' : confirmToggleTemplate.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
