import React, { useState, useEffect } from 'react';
import {
  Search,
  Package,
  Layers,
  Edit2,
  Power,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  SlidersHorizontal,
  X,
  Zap,
  Tag,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { getProducts, updateProductStatus } from '../services/productApi';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'SOLAR_PANEL', label: 'Solar Panels' },
  { value: 'INVERTER', label: 'Solar Inverters' },
  { value: 'BATTERY', label: 'Batteries' },
  { value: 'STRUCTURE', label: 'Structures' },
  { value: 'CABLES', label: 'Solar Cables' },
  { value: 'DCDB', label: 'DCDB Boxes' },
  { value: 'ACDB', label: 'ACDB Boxes' },
  { value: 'LIGHTNING_ARRESTER', label: 'Lightning Arresters' },
  { value: 'EARTHING', label: 'Earthing Equipment' },
  { value: 'MISC', label: 'Miscellaneous' },
];

export default function ProductList({ canWrite, onOpenAdd, onOpenEdit, refreshKey }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [statusFilter, setStatusFilter] = useState(''); // '', 'true', 'false'
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Status toggle confirmation modal
  const [confirmToggleProduct, setConfirmToggleProduct] = useState(null);
  const [toggling, setToggling] = useState(false);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit: 15,
        search: search.trim() || undefined,
        category: category || undefined,
        is_active: statusFilter !== '' ? statusFilter === 'true' : undefined,
      };

      const res = await getProducts(params);
      if (res && res.data) {
        setProducts(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to load product catalog');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page, category, statusFilter, refreshKey]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const handleClearFilters = () => {
    setSearch('');
    setCategory('');
    setStatusFilter('');
    setPage(1);
  };

  const hasActiveFilters = search.trim() !== '' || category !== '' || statusFilter !== '';

  const handleExecuteStatusToggle = async () => {
    if (!confirmToggleProduct) return;
    setToggling(true);
    try {
      const targetState = !confirmToggleProduct.is_active;
      await updateProductStatus(confirmToggleProduct.id, targetState);
      setConfirmToggleProduct(null);
      fetchProducts();
    } catch (err) {
      alert(err.message || 'Failed to update product status');
    } finally {
      setToggling(false);
    }
  };

  const categoryBadge = (cat) => {
    switch (cat) {
      case 'SOLAR_PANEL':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'INVERTER':
        return 'bg-sky-100 text-sky-900 border-sky-300';
      case 'BATTERY':
        return 'bg-emerald-100 text-emerald-900 border-emerald-300';
      case 'STRUCTURE':
        return 'bg-purple-100 text-purple-900 border-purple-300';
      case 'CABLES':
        return 'bg-orange-100 text-orange-900 border-orange-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-4">
      {/* Search, Filter & Action Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search form */}
          <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by code, equipment name, brand, or model..."
                className="w-full text-xs pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2.5 text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white rounded-xl transition"
            >
              Search
            </button>
          </form>

          {/* Quick Dropdown Filters */}
          <div className="flex items-center gap-2">
            {/* Category Filter */}
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="text-xs font-semibold rounded-xl border border-slate-200 px-3 py-2.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>

            {/* Active Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs font-semibold rounded-xl border border-slate-200 px-3 py-2.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="">All Statuses</option>
              <option value="true">Active Only</option>
              <option value="false">Inactive Only</option>
            </select>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                title="Clear all search filters"
                className="px-3 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition flex items-center gap-1"
              >
                <X className="w-3.5 h-3.5" />
                <span>Clear</span>
              </button>
            )}

            {/* Refresh Button */}
            <button
              onClick={fetchProducts}
              title="Refresh Catalog"
              className="p-2.5 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Error Banner */}
        {error && (
          <div className="p-4 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchProducts}
              className="px-3 py-1 bg-white border border-rose-300 rounded-md font-bold text-rose-700 hover:bg-rose-100 transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && products.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-amber-500" />
            <p className="text-sm font-medium text-slate-500">Loading equipment master catalog...</p>
          </div>
        ) : products.length === 0 ? (
          /* Empty State */
          <div className="p-16 text-center text-slate-500 space-y-3">
            <Package className="w-12 h-12 stroke-[1.5] mx-auto text-slate-300" />
            <h4 className="text-base font-bold text-slate-800">No products found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {hasActiveFilters
                ? 'No equipment matched your active filter criteria. Try clearing search filters.'
                : 'The product catalog is currently empty. Add solar equipment to configure BOMs and quotations.'}
            </p>
            {canWrite && !hasActiveFilters && (
              <button
                onClick={onOpenAdd}
                className="mt-2 px-4 py-2 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm inline-flex items-center gap-1.5"
              >
                <Package className="w-4 h-4" />
                <span>Add First Product</span>
              </button>
            )}
          </div>
        ) : (
          /* Products Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Code / SKU</th>
                  <th className="py-3 px-4">Product Name & Specs</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Brand & Model</th>
                  <th className="py-3 px-4 text-right">Base Price (INR)</th>
                  <th className="py-3 px-4 text-center">GST Rate</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 transition">
                    {/* SKU Code */}
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-slate-900">{p.product_code}</div>
                      <div className="text-[10px] text-slate-400">UOM: {p.unit_of_measure}</div>
                    </td>

                    {/* Name & Capacity */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="font-bold text-slate-900 leading-snug">{p.name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                        {p.wattage_or_capacity && (
                          <span className="font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200/60 inline-flex items-center gap-0.5">
                            <Zap className="w-3 h-3 text-amber-500" />
                            {p.wattage_or_capacity}
                          </span>
                        )}
                        {p.is_serialized && (
                          <span className="text-[10px] font-medium text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
                            Serialized
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Category */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${categoryBadge(
                          p.category
                        )}`}
                      >
                        {p.category.replace(/_/g, ' ')}
                      </span>
                    </td>

                    {/* Brand & Model */}
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800">{p.brand || '—'}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{p.model_number || '—'}</div>
                    </td>

                    {/* Base Price */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="font-mono font-bold text-slate-900">
                        ₹{Number(p.base_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Min stock: {p.min_stock_alert} {p.unit_of_measure}
                      </div>
                    </td>

                    {/* Tax Rate */}
                    <td className="py-3.5 px-4 text-center font-mono font-semibold text-slate-700">
                      {p.tax_rate_percent}%
                    </td>

                    {/* Active Status */}
                    <td className="py-3.5 px-4 text-center">
                      {p.is_active ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-500 bg-slate-100 border border-slate-300 px-2.5 py-0.5 rounded-full">
                          <XCircle className="w-3.5 h-3.5 text-slate-400" />
                          <span>Inactive</span>
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        {canWrite ? (
                          <>
                            {/* Edit Button */}
                            <button
                              onClick={() => onOpenEdit(p)}
                              title="Edit Product Specs & Pricing"
                              className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>

                            {/* Activate / Deactivate Toggle Button */}
                            <button
                              onClick={() => setConfirmToggleProduct(p)}
                              title={p.is_active ? 'Deactivate Product' : 'Reactivate Product'}
                              className={`p-1.5 rounded-lg transition ${
                                p.is_active
                                  ? 'text-slate-400 hover:text-rose-600 hover:bg-rose-50'
                                  : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'
                              }`}
                            >
                              <Power className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <span className="text-[11px] text-slate-400 italic">Read-only</span>
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
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing <span className="font-semibold text-slate-800">{products.length}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> equipment items
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 rounded bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition font-medium"
              >
                Previous
              </button>
              <span className="font-semibold text-slate-800 font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1 rounded bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition font-medium"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Dialog for Activation/Deactivation */}
      {confirmToggleProduct && (
        <div className="fixed inset-0 z-60 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                  confirmToggleProduct.is_active
                    ? 'bg-rose-100 text-rose-700'
                    : 'bg-emerald-100 text-emerald-700'
                }`}
              >
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-base text-slate-900">
                  {confirmToggleProduct.is_active ? 'Deactivate Product?' : 'Reactivate Product?'}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  {confirmToggleProduct.is_active
                    ? 'Deactivating this equipment will hide it from future BOM and Quotation selections. Historical records remain fully preserved.'
                    : 'Reactivating this equipment makes it immediately available for new BOM templates and quotations.'}
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div>
                <span className="text-slate-400">SKU:</span>{' '}
                <span className="font-mono font-bold text-slate-800">{confirmToggleProduct.product_code}</span>
              </div>
              <div>
                <span className="text-slate-400">Name:</span>{' '}
                <span className="font-semibold text-slate-800">{confirmToggleProduct.name}</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setConfirmToggleProduct(null)}
                disabled={toggling}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteStatusToggle}
                disabled={toggling}
                className={`px-4 py-2 rounded-lg text-xs font-bold text-white transition shadow-sm ${
                  confirmToggleProduct.is_active
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : 'bg-emerald-600 hover:bg-emerald-500'
                }`}
              >
                {toggling
                  ? 'Updating...'
                  : confirmToggleProduct.is_active
                  ? 'Confirm Deactivation'
                  : 'Confirm Activation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
