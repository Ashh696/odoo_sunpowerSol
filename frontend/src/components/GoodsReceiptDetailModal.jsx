import React, { useState, useEffect } from 'react';
import { X, PackageCheck, Building2, Calendar, FileText, CheckCircle2, AlertTriangle, AlertCircle, ShoppingCart } from 'lucide-react';
import { getGoodsReceipt } from '../services/procurementApi';

const STATUS_COLORS = {
  ACCEPTED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  PARTIALLY_ACCEPTED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  REJECTED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function GoodsReceiptDetailModal({ grnId, isOpen, onClose }) {
  const [grn, setGrn] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && grnId) {
      loadData();
    }
  }, [isOpen, grnId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getGoodsReceipt(grnId);
      setGrn(res.data?.data || null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error loading goods receipt');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full shadow-2xl overflow-hidden my-8">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <PackageCheck className="w-5 h-5 text-amber-500" />
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>{grn?.grn_number || 'Goods Receipt Note'}</span>
                {grn && (
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                      STATUS_COLORS[grn.status] || 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {grn.status}
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

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading goods receipt details...</div>
        ) : !grn ? (
          <div className="p-12 text-center text-slate-400">Goods receipt not found</div>
        ) : (
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-amber-500" />
                  <span>Supplier</span>
                </div>
                <div className="text-sm font-semibold text-white">{grn.supplier_name}</div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <ShoppingCart className="w-3.5 h-3.5 text-blue-400" />
                  <span>Purchase Order</span>
                </div>
                <div className="text-sm font-mono font-semibold text-white">{grn.po_number}</div>
                <div className="text-xs text-slate-400 font-sans">Received by: {grn.receiver_name}</div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-1">
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Challan & Date</span>
                </div>
                <div className="text-sm font-mono text-slate-200">Date: {grn.received_date}</div>
                <div className="text-xs text-slate-400">
                  Challan: {grn.challan_number || 'N/A'} {grn.challan_date ? `(${grn.challan_date})` : ''}
                </div>
              </div>
            </div>

            {grn.inspection_remarks && (
              <div className="bg-slate-950/40 border border-slate-800 rounded-lg p-3 text-xs text-slate-300">
                <span className="font-semibold text-slate-400 block mb-1">Inspection Remarks:</span>
                {grn.inspection_remarks}
              </div>
            )}

            <div>
              <h3 className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">
                Inspected Items Breakdown
              </h3>
              <div className="border border-slate-800 rounded-lg overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300 font-mono text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3 font-sans">Product Name</th>
                      <th className="py-2.5 px-3 text-right">Physical Recv</th>
                      <th className="py-2.5 px-3 text-right text-emerald-400">Accepted (In Stock)</th>
                      <th className="py-2.5 px-3 text-right text-rose-400">Rejected</th>
                      <th className="py-2.5 px-3 font-sans">Rejection Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {(grn.items || []).map((it) => (
                      <tr key={it.id} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-sans">
                          <div className="font-semibold text-white">{it.product_name}</div>
                          <div className="text-xs text-slate-400 font-mono">{it.product_code}</div>
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-200">
                          {parseFloat(it.received_quantity)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                          {parseFloat(it.accepted_quantity)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-semibold text-rose-400">
                          {parseFloat(it.rejected_quantity)}
                        </td>
                        <td className="py-2.5 px-3 font-sans text-xs text-slate-300">
                          {it.rejection_reason || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
