import React from 'react';
import {
  Package,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Truck,
  Download,
  Boxes,
} from 'lucide-react';
import { downloadAnalyticsCSV } from '../services/analyticsApi';

export default function InventoryAnalyticsTab({ data, dateRange }) {
  if (!data) return null;

  const {
    total_sku_count,
    total_quantity_on_hand,
    total_reserved_quantity,
    total_available_quantity,
    low_stock_sku_count,
    total_stock_valuation,
    total_dispatched_quantity,
    low_stock_items,
    top_stock_items,
  } = data;

  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  return (
    <div className="space-y-8">
      {/* Top Header & Export */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Warehouse Inventory & Stock Valuation</h3>
          <p className="text-xs text-slate-500">
            Authoritative component inventory balances, stock reservations, material valuation, and replenishment alerts.
          </p>
        </div>
        <button
          onClick={() => downloadAnalyticsCSV('inventory_stock', dateRange)}
          className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-3 py-1.5 rounded-lg text-xs shadow-sm transition"
        >
          <Download className="w-3.5 h-3.5" /> Export Inventory CSV
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Tracked SKUs</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{total_sku_count}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Catalog solar components</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
            <Boxes className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Stock on Hand</span>
            <div className="text-2xl font-black text-slate-900 mt-1">{total_quantity_on_hand}</div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {total_available_quantity} available | {total_reserved_quantity} reserved
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Package className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Low-Stock Alerts</span>
            <div className={`text-2xl font-black mt-1 ${low_stock_sku_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
              {low_stock_sku_count}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {low_stock_sku_count > 0 ? 'Items at or below reorder level' : 'All stock levels healthy'}
            </span>
          </div>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${low_stock_sku_count > 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Warehouse Valuation</span>
            <div className="text-2xl font-black text-emerald-600 mt-1">
              {formatCurrency(total_stock_valuation)}
            </div>
            <span className="text-xs text-slate-500 mt-1 inline-block">Based on weighted unit cost</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Low Stock Warning Callout if any */}
      {low_stock_items && low_stock_items.length > 0 && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wide">
              Critical Replenishment Required ({low_stock_items.length} SKUs)
            </h4>
            <p className="text-xs text-rose-800 mt-0.5">
              The following solar components are at or below their mandatory reorder threshold. Generate purchase orders to avert installation delays:
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {low_stock_items.map((it) => (
                <span
                  key={it.product_id}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white text-rose-950 font-bold rounded-lg border border-rose-300 text-xs shadow-xs"
                >
                  <span>{it.product_name}</span>
                  <span className="text-rose-600 font-black">({it.quantity_on_hand} left / min {it.reorder_level})</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Warehouse Stock Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Package className="w-4 h-4 text-emerald-600" />
            <span>Component Stock Ledger</span>
          </h4>
          <span className="text-xs text-slate-500">Live authoritative warehouse balance</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Product / SKU</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3 text-center">On Hand</th>
                <th className="px-5 py-3 text-center">Reserved</th>
                <th className="px-5 py-3 text-center">Available</th>
                <th className="px-5 py-3 text-center">Reorder Level</th>
                <th className="px-5 py-3 text-center">Status</th>
                <th className="px-5 py-3 text-right">Avg Unit Cost</th>
                <th className="px-5 py-3 text-right">Stock Valuation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {top_stock_items && top_stock_items.length > 0 ? (
                top_stock_items.map((it) => (
                  <tr key={it.product_id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-slate-900">{it.product_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{it.product_code}</div>
                    </td>
                    <td className="px-5 py-3.5 text-slate-600 font-medium">{it.category}</td>
                    <td className="px-5 py-3.5 text-center font-black text-slate-900">{it.quantity_on_hand}</td>
                    <td className="px-5 py-3.5 text-center text-slate-600">{it.reserved_quantity}</td>
                    <td className="px-5 py-3.5 text-center font-bold text-emerald-600">{it.quantity_available}</td>
                    <td className="px-5 py-3.5 text-center text-slate-500 font-semibold">{it.reorder_level}</td>
                    <td className="px-5 py-3.5 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full font-bold text-[11px] border ${
                          it.stock_status === 'LOW_STOCK'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {it.stock_status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-semibold text-slate-700">{formatCurrency(it.average_unit_cost)}</td>
                    <td className="px-5 py-3.5 text-right font-black text-slate-900">{formatCurrency(it.valuation)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="px-5 py-8 text-center text-slate-400 italic">
                    No inventory records found in warehouse.
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
