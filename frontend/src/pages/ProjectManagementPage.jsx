import React, { useState, useEffect } from 'react';
import {
  Layers,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Eye,
  MapPin,
  Calendar,
  Briefcase
} from 'lucide-react';
import { getProjects, getProject } from '../services/projectApi';
import ProjectDetailModal from '../components/ProjectDetailModal';
import OrderDetailModal from '../components/OrderDetailModal';
import { getOrder } from '../services/orderApi';

const STATUS_BADGES = {
  INITIATED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  PROCUREMENT: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  DISPATCHED: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  INSTALLATION: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  COMMISSIONED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  HANDED_OVER: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  ON_HOLD: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function ProjectManagementPage({ currentRole = 'SUPER_ADMIN' }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [systemTypeFilter, setSystemTypeFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Modals
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, limit: 15 };
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;
      if (systemTypeFilter) params.system_type = systemTypeFilter;

      const res = await getProjects(params);
      const data = res.data?.data || {};
      setProjects(data.items || []);
      setTotalPages(data.pages || 1);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, statusFilter, systemTypeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProjects();
  };

  const handleOpenProjectDetail = async (projectId) => {
    try {
      const res = await getProject(projectId);
      setSelectedProject(res.data?.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to open project details');
    }
  };

  const handleOpenOrderDetail = async (orderId) => {
    try {
      const res = await getOrder(orderId);
      setSelectedOrder(res.data?.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to open order details');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Layers className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Solar Rooftop Execution Projects</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Operations tracking, Bill of Materials fulfillment, installation milestones & commissioning
          </p>
        </div>

        <button
          onClick={fetchProjects}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 bg-slate-900/60 border border-slate-800 rounded-xl p-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by project code, customer, or site address..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
          >
            <option value="">All Statuses</option>
            <option value="INITIATED">Initiated</option>
            <option value="PROCUREMENT">Procurement</option>
            <option value="DISPATCHED">Dispatched</option>
            <option value="INSTALLATION">Installation</option>
            <option value="COMMISSIONED">Commissioned</option>
            <option value="HANDED_OVER">Handed Over</option>
            <option value="ON_HOLD">On Hold</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <select
            value={systemTypeFilter}
            onChange={(e) => {
              setSystemTypeFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
          >
            <option value="">All System Types</option>
            <option value="ON_GRID">On-Grid</option>
            <option value="OFF_GRID">Off-Grid</option>
            <option value="HYBRID">Hybrid</option>
          </select>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-2.5 text-rose-400 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Projects Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold">
              <tr>
                <th className="py-3 px-4">Project Code</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">System Spec</th>
                <th className="py-3 px-4">Site Address</th>
                <th className="py-3 px-4">Timeline</th>
                <th className="py-3 px-4">Project Manager</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-amber-500" />
                    <span>Loading projects...</span>
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500 italic">
                    No execution projects matching filters.
                  </td>
                </tr>
              ) : (
                projects.map((proj) => (
                  <tr key={proj.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-white tracking-wide">
                      {proj.project_code}
                    </td>
                    <td className="py-3 px-4 text-white">
                      <span className="font-semibold block">{proj.customer?.full_name || 'Customer'}</span>
                      <span className="text-[10px] text-slate-400">{proj.customer?.city || 'Pune'}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-amber-400 block">{proj.system_capacity_kw} kW</span>
                      <span className="text-[10px] text-slate-400">{proj.system_type}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-[200px] truncate" title={proj.site_address}>
                      {proj.site_address}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      <div>Start: {proj.planned_start_date}</div>
                      <div className="text-[10px] text-slate-500">Target: {proj.planned_completion_date}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {proj.project_manager_name || <span className="text-slate-500 italic">Unassigned</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-[10px] px-2.5 py-0.5 rounded-full border font-semibold ${
                          STATUS_BADGES[proj.status] || 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {proj.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenProjectDetail(proj.id)}
                        className="px-2.5 py-1 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded text-xs font-semibold transition flex items-center gap-1 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Manage</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 text-xs text-slate-400 bg-slate-950/40">
            <span>Showing page {page} of {totalPages} ({totalCount} total projects)</span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded text-white font-medium transition"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 rounded text-white font-medium transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Project Detail Modal */}
      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
          onRefresh={async () => {
            fetchProjects();
            const res = await getProject(selectedProject.id);
            setSelectedProject(res.data?.data);
          }}
          currentRole={currentRole}
          onOpenOrder={(ordId) => {
            setSelectedProject(null);
            handleOpenOrderDetail(ordId);
          }}
        />
      )}

      {/* Order Detail Modal */}
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onRefresh={async () => {
            fetchProjects();
            const res = await getOrder(selectedOrder.id);
            setSelectedOrder(res.data?.data);
          }}
          currentRole={currentRole}
          onOpenProject={(projId) => {
            setSelectedOrder(null);
            handleOpenProjectDetail(projId);
          }}
        />
      )}
    </div>
  );
}
