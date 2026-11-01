import React, { useState, useEffect } from 'react';
import {
  X,
  PackageCheck,
  AlertCircle,
  CheckCircle2,
  Calendar,
  FileText,
  Barcode,
  Building2,
  Info,
} from 'lucide-react';
import { createGoodsReceipt } from '../services/procurementApi';

export default function GoodsReceiptModal({ isOpen, onClose, po, onSuccess }) {
  const [receivedDate, setReceivedDate] = useState(new Date().toISOString().split('T')[0]);
  const [challanNumber, setChallanNumber] = useState('');
  const [challanDate, setChallanDate] = useState('');
  const [inspectionRemarks, setInspectionRemarks] = useState('');

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && po) {
      setReceivedDate(new Date().toISOString().split('T')[0]);
      setChallanNumber('');
      setChallanDate('');
      setInspectionRemarks('');
      setError(null);

      // Initialize lines with remaining quantities
      const initialItems = (po.items || []).map((it) => {
        const remaining = Math.max(0, parseFloat(it.ordered_quantity) - parseFloat(it.received_quantity));
        return {
          po_item_id: it.id,
          product_id: it.product_id,
          product_name: it.product_name,
          product_code: it.product_code,
          category: it.category,
          unit_of_measure: it.unit_of_measure || 'NOS',
          is_serialized: it.is_serialized || false,
          ordered_quantity: parseFloat(it.ordered_quantity),
          previous_received: parseFloat(it.received_quantity),
          remaining_unreceived: remaining,
          // Defaults: pre-fill accepted with remaining
          received_quantity: remaining,
          accepted_quantity: remaining,
          rejected_quantity: 0,
          rejection_reason: '',
          serial_numbers_raw: '', // comma or newline separated
        };
      });

      setItems(initialItems);
    }
  }, [isOpen, po]);

  if (!isOpen || !po) return null;

  const handleQtyChange = (index, field, value) => {
    setItems((prev) => {
      const updated = [...prev];
      const item = { ...updated[index] };
      const val = parseFloat(value) || 0;
      item[field] = val;

      if (field === 'accepted_quantity') {
        item.received_quantity = val + parseFloat(item.rejected_quantity || 0);
      } else if (field === 'rejected_quantity') {
        item.received_quantity = parseFloat(item.accepted_quantity || 0) + val;
      } else if (field === 'received_quantity') {
        item.accepted_quantity = val;
        item.rejected_quantity = 0;
      }

      updated[index] = item;
      return updated;
    });
  };

  const handleTextChange = (index, field, value) => {
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [field]: value,
      };
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate lines
    for (const it of items) {
      const recv = parseFloat(it.received_quantity || 0);
      const acc = parseFloat(it.accepted_quantity || 0);
      const rej = parseFloat(it.rejected_quantity || 0);

      if (recv !== acc + rej) {
        setError(`Product '${it.product_name}': Received quantity (${recv}) must equal accepted (${acc}) + rejected (${rej})`);
        return;
      }

      if (acc > it.remaining_unreceived) {
        setError(`Product '${it.product_name}': Accepted quantity (${acc}) exceeds remaining unreceived on PO (${it.remaining_unreceived})`);
        return;
      }

      if (rej > 0 && (!it.rejection_reason || !it.rejection_reason.trim())) {
        setError(`Product '${it.product_name}': Rejection reason is mandatory when rejected quantity is greater than zero`);
        return;
      }

      if (it.is_serialized && acc > 0) {
        const serials = it.serial_numbers_raw
          .split(/[\n,]/)
          .map((s) => s.trim())
          .filter((s) => s.length > 0);

        if (serials.length !== Math.floor(acc)) {
          setError(
            `Serialized product '${it.product_name}' requires exactly ${Math.floor(acc)} serial numbers (entered ${serials.length})`
          );
          return;
        }

        const uniqueSerials = new Set(serials);
        if (uniqueSerials.size !== serials.length) {
          setError(`Product '${it.product_name}': Duplicate serial numbers found in your entry`);
          return;
        }
      }
    }

    const totalInward = items.reduce((acc, it) => acc + parseFloat(it.received_quantity || 0), 0);
    if (totalInward <= 0) {
      setError('At least one item must have a received quantity greater than zero');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        purchase_order_id: po.id,
        received_date: receivedDate,
        challan_number: challanNumber.trim() || null,
        challan_date: challanDate || null,
        inspection_remarks: inspectionRemarks.trim() || null,
        items: items
          .filter((it) => parseFloat(it.received_quantity) > 0)
          .map((it) => {
            const serials = it.is_serialized && parseFloat(it.accepted_quantity) > 0
              ? it.serial_numbers_raw
                  .split(/[\n,]/)
                  .map((s) => s.trim())
                  .filter((s) => s.length > 0)
              : [];

            return {
              po_item_id: it.po_item_id,
              product_id: it.product_id,
              received_quantity: parseFloat(it.received_quantity),
              accepted_quantity: parseFloat(it.accepted_quantity),
              rejected_quantity: parseFloat(it.rejected_quantity || 0),
              rejection_reason: parseFloat(it.rejected_quantity) > 0 ? it.rejection_reason.trim() : null,
              serial_numbers: serials,
            };
          }),
      };

      await createGoodsReceipt(payload);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error recording goods receipt');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-5xl w-full shadow-2xl overflow-hidden my-8">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2">
            <PackageCheck className="w-5 h-5 text-amber-500" />
            <div>
              <h2 className="text-lg font-bold text-white">Record Goods Receipt Note (GRN)</h2>
              <p className="text-xs text-slate-400 font-mono">
                Receiving stock against {po.po_number} from {po.supplier_name}
              </p>
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

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Header Metadata Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Receipt Date *
              </label>
              <input
                type="date"
                required
                value={receivedDate}
                onChange={(e) => setReceivedDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Challan / Invoice No
              </label>
              <input
                type="text"
                placeholder="e.g. DC-2026-991"
                value={challanNumber}
                onChange={(e) => setChallanNumber(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Challan Date
              </label>
              <input
                type="date"
                value={challanDate}
                onChange={(e) => setChallanDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Quality Inspection Status
              </label>
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Physical Inward Verification</span>
              </div>
            </div>
          </div>

          {/* Physical Inspection Grid */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs uppercase tracking-wider text-slate-300 font-semibold">
                Line-by-Line Quantity Inspection & Acceptance
              </h3>
              <span className="text-xs text-slate-400">
                Rule: Received = Accepted + Rejected
              </span>
            </div>

            <div className="border border-slate-800 rounded-lg overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Product Item</th>
                    <th className="py-2.5 px-3 w-24 text-right">Remaining</th>
                    <th className="py-2.5 px-3 w-28 text-right">Physical Recv</th>
                    <th className="py-2.5 px-3 w-28 text-right text-emerald-400">Accepted *</th>
                    <th className="py-2.5 px-3 w-28 text-right text-rose-400">Rejected</th>
                    <th className="py-2.5 px-3">Rejection Reason / Serials</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {items.map((it, idx) => {
                    const parsedSerials = (it.serial_numbers_raw || '')
                      .split(/[\n,]/)
                      .map((s) => s.trim())
                      .filter((s) => s.length > 0);
                    const serialCountMatch = parsedSerials.length === Math.floor(it.accepted_quantity);

                    return (
                      <tr key={it.po_item_id} className="hover:bg-slate-800/30 align-top">
                        <td className="py-3 px-3 font-sans">
                          <div className="font-semibold text-white">{it.product_name}</div>
                          <div className="text-xs text-slate-400 font-mono">{it.product_code}</div>
                          {it.is_serialized && (
                            <span className="inline-flex items-center gap-1 mt-1 text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-1.5 py-0.5 rounded">
                              <Barcode className="w-3 h-3" />
                              <span>Serialized Product</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-right text-slate-400">
                          {it.remaining_unreceived} {it.unit_of_measure}
                        </td>
                        <td className="py-3 px-3">
                          <input
                            type="number"
                            min="0"
                            step="any"
                            value={it.received_quantity}
                            onChange={(e) => handleQtyChange(idx, 'received_quantity', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 text-right"
                          />
                        </td>
                        <td className="py-3 px-3">
                          <input
                            type="number"
                            min="0"
                            max={it.remaining_unreceived}
                            step="any"
                            value={it.accepted_quantity}
                            onChange={(e) => handleQtyChange(idx, 'accepted_quantity', e.target.value)}
                            className="w-full bg-slate-800 border border-emerald-500/50 rounded px-2 py-1.5 text-xs text-emerald-300 font-bold focus:outline-none focus:border-emerald-400 text-right"
                          />
                        </td>
                        <td className="py-3 px-3">
                          <input
                            type="number"
                            min="0"
                            step="any"
                            value={it.rejected_quantity}
                            onChange={(e) => handleQtyChange(idx, 'rejected_quantity', e.target.value)}
                            className="w-full bg-slate-800 border border-rose-500/50 rounded px-2 py-1.5 text-xs text-rose-300 font-semibold focus:outline-none focus:border-rose-400 text-right"
                          />
                        </td>
                        <td className="py-3 px-3 space-y-2 font-sans">
                          {it.rejected_quantity > 0 && (
                            <div>
                              <input
                                type="text"
                                placeholder="Rejection reason (Required) *"
                                value={it.rejection_reason}
                                onChange={(e) => handleTextChange(idx, 'rejection_reason', e.target.value)}
                                className="w-full bg-slate-800 border border-rose-500/40 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-rose-400 placeholder-slate-500"
                              />
                            </div>
                          )}

                          {it.is_serialized && it.accepted_quantity > 0 && (
                            <div>
                              <div className="flex items-center justify-between text-[11px] mb-1">
                                <span className="text-slate-400">Scan / Enter Serial Numbers:</span>
                                <span
                                  className={`px-1.5 py-0.5 rounded font-mono font-bold text-[10px] ${
                                    serialCountMatch
                                      ? 'bg-emerald-500/20 text-emerald-300'
                                      : 'bg-amber-500/20 text-amber-300'
                                  }`}
                                >
                                  {parsedSerials.length} / {Math.floor(it.accepted_quantity)} Serials
                                </span>
                              </div>
                              <textarea
                                rows={2}
                                placeholder="Enter comma or newline separated serial numbers..."
                                value={it.serial_numbers_raw}
                                onChange={(e) => handleTextChange(idx, 'serial_numbers_raw', e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-purple-400 font-mono"
                              />
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              General Inspection Remarks / Notes
            </label>
            <textarea
              rows={2}
              value={inspectionRemarks}
              onChange={(e) => setInspectionRemarks(e.target.value)}
              placeholder="e.g. Unloaded safely at main warehouse bay 3. Inspected by QA team."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-lg text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-500 transition disabled:opacity-50 flex items-center gap-1.5 shadow-md shadow-emerald-600/30"
            >
              <PackageCheck className="w-4 h-4" />
              <span>{loading ? 'Processing Receipt...' : 'Confirm Inward Stock (GRN)'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
