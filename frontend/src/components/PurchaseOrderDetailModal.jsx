import React, { useState, useEffect } from 'react';
import {
  X,
  ShoppingCart,
  Building2,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Send,
  Ban,
  PackageCheck,
  FileText,
  Clock,
  Layers,
} from 'lucide-react';
import {
  getPurchaseOrder,
  issuePurchaseOrder,
  cancelPurchaseOrder,
  getPOGoodsReceipts,
} from '../services/procurementApi';

const STATUS_COLORS = {
  DRAFT: 'bg-slate-700 text-slate-300 border-slate-600',
  ISSUED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  PARTIALLY_RECEIVED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  RECEIVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function PurchaseOrderDetailModal({
  poId,
  isOpen,
  onClose,
  onRefresh,
  onOpenGRNModal,
  onOpenEditModal,
}) {
  const [po, setPo] = useState(null);
  const [grns, setGrns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    if (isOpen && poId) {
      loadData();
    }
  }, [isOpen, poId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [poRes, grnRes] = await Promise.all([
        getPurchaseOrder(poId),
        getPOGoodsReceipts(poId),
      ]);
      setPo(poRes.data?.data || null);
      setGrns(grnRes.data?.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error loading purchase order');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleIssue = async () => {
    if (!window.confirm(`Are you sure you want to officially issue PO ${po?.po_number} to ${po?.supplier_name}?`)) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await issuePurchaseOrder(poId);
      setSuccessMsg('Purchase order issued successfully');
      loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error issuing purchase order');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm(`Are you sure you want to cancel PO ${po?.po_number}? This cannot be undone.`)) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await cancelPurchaseOrder(poId);
      setSuccessMsg('Purchase order cancelled successfully');
      loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error cancelling purchase order');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full shadow-2xl overflow-hidden my-8">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <ShoppingCart className="w-5 h-5 text-amber-500" />
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>{po?.po_number || 'Purchase Order'}</span>
                {po && (
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                      STATUS_COLORS[po.status] || 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {po.status}
                  </span>
                )}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading purchase order details...</div>
        ) : !po ? (
          <div className="p-12 text-center text-slate-400">Purchase order not found</div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Header Metadata Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-amber-500" />
                  <span>Supplier</span>
                </div>
                <div className="text-sm font-semibold text-white">{po.supplier_name}</div>
                <div className="text-xs text-slate-400 font-mono">{po.supplier_code}</div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-400" />
                  <span>Procurement Type</span>
                </div>
                <div className="text-sm font-semibold text-white">
                  {po.project_code ? `Project: ${po.project_code}` : 'General Warehouse Stock'}
                </div>
                <div className="text-xs text-slate-400">Created by: {po.creator_name || 'Admin'}</div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Dates</span>
                </div>
                <div className="text-sm font-mono text-slate-300">Order: {po.po_date}</div>
                <div className="text-xs font-mono text-slate-400">
                  Expected: {po.expected_delivery_date || 'Not specified'}
                </div>
              </div>
            </div>

            {/* Line Items Table */}
            <div>
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">
                Order Components & Quantities
              </h3>
              <div className="border border-slate-800 rounded-lg overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Item Name</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3 text-right">Ordered</th>
                      <th className="py-2.5 px-3 text-right">Received</th>
                      <th className="py-2.5 px-3 text-right">Unit Price</th>
                      <th className="py-2.5 px-3 text-right">Tax %</th>
                      <th className="py-2.5 px-3 text-right">Total (₹)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {(po.items || []).map((it) => {
                      const isComplete = parseFloat(it.received_quantity) >= parseFloat(it.ordered_quantity);
                      return (
                        <tr key={it.id} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-sans">
                            <div className="font-semibold text-white">{it.product_name}</div>
                            <div className="text-xs text-slate-400 font-mono">{it.product_code}</div>
                          </td>
                          <td className="py-2.5 px-3 font-sans text-xs text-slate-400">{it.category}</td>
                          <td className="py-2.5 px-3 text-right text-slate-200">
                            {parseFloat(it.ordered_quantity)} {it.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <span className={isComplete ? 'text-emerald-400 font-bold' : 'text-amber-400 font-medium'}>
                              {parseFloat(it.received_quantity)} {it.unit_of_measure}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-300">
                            ₹{parseFloat(it.unit_price).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-400">
                            {parseFloat(it.tax_rate_percent)}%
                          </td>
                          <td className="py-2.5 px-3 text-right font-semibold text-slate-100">
                            ₹{parseFloat(it.total_amount).toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Financial Summary & Notes */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
              <div>
                {po.notes && (
                  <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-300">
                    <span className="font-semibold text-slate-400 block mb-1">Notes:</span>
                    {po.notes}
                  </div>
                )}
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>Tax Amount (GST):</span>
                  <span>₹{parseFloat(po.tax_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="border-t border-slate-800 pt-2 flex justify-between text-base font-bold text-amber-400 font-mono">
                  <span>Grand Total Amount:</span>
                  <span>₹{parseFloat(po.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            {/* Goods Receipts Recorded */}
            {grns.length > 0 && (
              <div>
                <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">
                  Recorded Goods Receipt Notes (GRN)
                </h3>
                <div className="border border-slate-800 rounded-lg overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 font-mono">
                    <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                      <tr>
                        <th className="py-2 px-3">GRN Number</th>
                        <th className="py-2 px-3">Receipt Date</th>
                        <th className="py-2 px-3">Challan No</th>
                        <th className="py-2 px-3">Received By</th>
                        <th className="py-2 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {grns.map((g) => (
                        <tr key={g.id} className="hover:bg-slate-800/30">
                          <td className="py-2 px-3 font-semibold text-amber-400">{g.grn_number}</td>
                          <td className="py-2 px-3">{g.received_date}</td>
                          <td className="py-2 px-3">{g.challan_number || '—'}</td>
                          <td className="py-2 px-3 font-sans">{g.receiver_name || 'Staff'}</td>
                          <td className="py-2 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              {g.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2">
                {po.status === 'DRAFT' && (
                  <button
                    onClick={() => {
                      onClose();
                      onOpenEditModal(po);
                    }}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
                  >
                    Edit Draft
                  </button>
                )}
                {po.status !== 'CANCELLED' && po.status !== 'RECEIVED' && grns.length === 0 && (
                  <button
                    onClick={handleCancel}
                    disabled={actionLoading}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20 transition flex items-center gap-1.5"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Cancel PO</span>
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                {po.status === 'DRAFT' && (
                  <button
                    onClick={handleIssue}
                    disabled={actionLoading}
                    className="px-4 py-2 rounded-lg text-xs font-bold bg-blue-600 text-white hover:bg-blue-500 transition flex items-center gap-1.5 shadow-md shadow-blue-600/30"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Issue to Supplier</span>
                  </button>
                )}

                {(po.status === 'ISSUED' || po.status === 'PARTIALLY_RECEIVED') && (
                  <button
                    onClick={() => {
                      onClose();
                      onOpenGRNModal(po);
                    }}
                    className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-500 text-slate-950 hover:bg-amber-400 transition flex items-center gap-1.5 shadow-md shadow-amber-500/30"
                  >
                    <PackageCheck className="w-4 h-4" />
                    <span>Inward Physical Goods (GRN)</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
