import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Eye,
  CreditCard,
  DollarSign,
  ArrowRight
} from 'lucide-react';
import { getOrders, getOrder } from '../services/orderApi';
import OrderDetailModal from '../components/OrderDetailModal';
import ProjectDetailModal from '../components/ProjectDetailModal';
import { getProject } from '../services/projectApi';

const STATUS_BADGES = {
  PENDING_ADVANCE: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  CONFIRMED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  PROCESSING: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  COMPLETED: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function OrderManagementPage({ currentRole = 'SUPER_ADMIN' }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Modals
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, limit: 15 };
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;

      const res = await getOrders(params);
      const data = res.data?.data || {};
      setOrders(data.items || []);
      setTotalPages(data.pages || 1);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchOrders();
  };

  const handleOpenOrderDetail = async (orderId) => {
    try {
      const res = await getOrder(orderId);
      setSelectedOrder(res.data?.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to open order details');
    }
  };

  const handleOpenProjectDetail = async (projectId) => {
    try {
      const res = await getProject(projectId);
      setSelectedProject(res.data?.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to open project details');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Briefcase className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Customer Order Management</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Confirmed solar installations, contract amounts, advance receipts & operations handover
          </p>
        </div>

        <button
          onClick={fetchOrders}
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
              placeholder="Search by order #, customer name, or phone..."
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

        <div className="flex items-center gap-2">
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
            <option value="PENDING_ADVANCE">Pending Advance</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PROCESSING">Processing</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
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

      {/* Orders Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold">
              <tr>
                <th className="py-3 px-4">Order #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Quotation #</th>
                <th className="py-3 px-4">Order Date</th>
                <th className="py-3 px-4 text-right">Contract Total</th>
                <th className="py-3 px-4 text-right">Advance Paid</th>
                <th className="py-3 px-4 text-right">Balance</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-center">Handover</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-amber-500" />
                    <span>Loading customer orders...</span>
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-500 italic">
                    No orders matching criteria found.
                  </td>
                </tr>
              ) : (
                orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-white tracking-wide">
                      {ord.order_number}
                    </td>
                    <td className="py-3 px-4 text-white">
                      <span className="font-semibold block">{ord.customer?.full_name || 'Customer'}</span>
                      <span className="text-[10px] text-slate-400">{ord.customer?.phone}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-mono">
                      {ord.quotation?.quotation_number || '—'}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(ord.order_date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-white">
                      ₹{parseFloat(ord.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 font-semibold">
                      ₹{parseFloat(ord.advance_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right text-amber-400 font-semibold">
                      ₹{parseFloat(ord.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-[10px] px-2.5 py-0.5 rounded-full border font-semibold ${
                          STATUS_BADGES[ord.status] || 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {ord.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {ord.project ? (
                        <button
                          onClick={() => handleOpenProjectDetail(ord.project.id)}
                          className="text-[10px] px-2 py-0.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded font-semibold transition"
                        >
                          {ord.project.project_code}
                        </button>
                      ) : (
                        <span className="text-[10px] text-slate-500">Not Initiated</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenOrderDetail(ord.id)}
                        className="px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-xs font-semibold transition flex items-center gap-1 ml-auto"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View</span>
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
            <span>Showing page {page} of {totalPages} ({totalCount} total orders)</span>
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

      {/* Order Detail Modal */}
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onRefresh={async () => {
            fetchOrders();
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

      {/* Project Detail Modal */}
      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
          onRefresh={async () => {
            fetchOrders();
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
    </div>
  );
}
