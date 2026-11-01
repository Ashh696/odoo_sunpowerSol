import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, ShoppingCart, Calculator, AlertCircle, Check } from 'lucide-react';
import { createPurchaseOrder, updatePurchaseOrder } from '../services/procurementApi';
import { getSuppliers } from '../services/procurementApi';
import api from '../services/api';

export default function PurchaseOrderModal({ isOpen, onClose, po, onSuccess, defaultProjectId = null }) {
  const isEdit = Boolean(po);

  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loadingLookups, setLoadingLookups] = useState(false);

  const [supplierId, setSupplierId] = useState('');
  const [projectId, setProjectId] = useState(defaultProjectId || '');
  const [poDate, setPoDate] = useState(new Date().toISOString().split('T')[0]);
  const [expectedDate, setExpectedDate] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState([
    { product_id: '', ordered_quantity: 1, unit_price: 0, tax_rate_percent: 12 },
  ]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadLookups();
      if (po) {
        setSupplierId(po.supplier_id || '');
        setProjectId(po.project_id || '');
        setPoDate(po.po_date || new Date().toISOString().split('T')[0]);
        setExpectedDate(po.expected_delivery_date || '');
        setNotes(po.notes || '');
        if (po.items && po.items.length > 0) {
          setItems(
            po.items.map((it) => ({
              product_id: it.product_id,
              ordered_quantity: parseFloat(it.ordered_quantity),
              unit_price: parseFloat(it.unit_price),
              tax_rate_percent: parseFloat(it.tax_rate_percent),
            }))
          );
        }
      } else {
        setSupplierId('');
        setProjectId(defaultProjectId || '');
        setPoDate(new Date().toISOString().split('T')[0]);
        setExpectedDate('');
        setNotes('');
        setItems([
          { product_id: '', ordered_quantity: 1, unit_price: 0, tax_rate_percent: 12 },
        ]);
      }
      setError(null);
    }
  }, [isOpen, po, defaultProjectId]);

  const loadLookups = async () => {
    setLoadingLookups(true);
    try {
      const [suppRes, prodRes, projRes] = await Promise.all([
        getSuppliers({ is_active: true, page_size: 100 }),
        api.get('/api/v1/products', { params: { is_active: true, page_size: 200 } }),
        api.get('/api/v1/projects', { params: { page_size: 100 } }),
      ]);
      setSuppliers(suppRes.data?.data?.items || []);
      setProducts(prodRes.data?.data?.items || []);
      setProjects(projRes.data?.data?.items || []);
    } catch (err) {
      console.error('Error loading lookups for PO', err);
    } finally {
      setLoadingLookups(false);
    }
  };

  if (!isOpen) return null;

  const handleProductChange = (index, prodId) => {
    const selected = products.find((p) => p.id === parseInt(prodId, 10));
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        product_id: prodId,
        unit_price: selected ? parseFloat(selected.base_price || 0) : 0,
        tax_rate_percent: selected ? parseFloat(selected.tax_rate_percent || 12) : 12,
      };
      return updated;
    });
  };

  const handleItemChange = (index, field, value) => {
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        [field]: value,
      };
      return updated;
    });
  };

  const addItemRow = () => {
    setItems((prev) => [
      ...prev,
      { product_id: '', ordered_quantity: 1, unit_price: 0, tax_rate_percent: 12 },
    ]);
  };

  const removeItemRow = (index) => {
    if (items.length <= 1) return;
    setItems((prev) => prev.filter((_, idx) => idx !== index));
  };

  // Live financial totals calculation
  const calculations = items.map((it) => {
    const qty = parseFloat(it.ordered_quantity || 0);
    const price = parseFloat(it.unit_price || 0);
    const taxRate = parseFloat(it.tax_rate_percent || 0);
    const subtotal = Math.round(qty * price * 100) / 100;
    const tax = Math.round(subtotal * (taxRate / 100) * 100) / 100;
    const total = subtotal + tax;
    return { subtotal, tax, total };
  });

  const subtotalSum = calculations.reduce((acc, c) => acc + c.subtotal, 0);
  const taxSum = calculations.reduce((acc, c) => acc + c.tax, 0);
  const grandTotal = calculations.reduce((acc, c) => acc + c.total, 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!supplierId) {
      setError('Please select an active supplier');
      return;
    }

    if (items.some((it) => !it.product_id || it.ordered_quantity <= 0)) {
      setError('All PO lines must specify a product and positive ordered quantity');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        supplier_id: parseInt(supplierId, 10),
        project_id: projectId ? parseInt(projectId, 10) : null,
        po_date: poDate,
        expected_delivery_date: expectedDate || null,
        notes: notes.trim() || null,
        items: items.map((it) => ({
          product_id: parseInt(it.product_id, 10),
          ordered_quantity: parseFloat(it.ordered_quantity),
          unit_price: parseFloat(it.unit_price),
          tax_rate_percent: parseFloat(it.tax_rate_percent || 12),
        })),
      };

      if (isEdit) {
        await updatePurchaseOrder(po.id, payload);
      } else {
        await createPurchaseOrder(payload);
      }

      onSuccess();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error saving purchase order';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full shadow-2xl overflow-hidden my-8">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-bold text-white">
              {isEdit ? `Edit Purchase Order (${po.po_number})` : 'Create Purchase Order (DRAFT)'}
            </h2>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Equipment Supplier *
              </label>
              <select
                required
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">Select Supplier...</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.company_name} ({s.supplier_code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Link Project (Optional)
              </label>
              <select
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">General Warehouse Stock (No Project)</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.project_code} ({p.system_capacity_kw}kW)
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  PO Date *
                </label>
                <input
                  type="date"
                  required
                  value={poDate}
                  onChange={(e) => setPoDate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Expected Delivery
                </label>
                <input
                  type="date"
                  min={poDate}
                  value={expectedDate}
                  onChange={(e) => setExpectedDate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* Line items table */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Purchase Order Line Items
              </h3>
              <button
                type="button"
                onClick={addItemRow}
                className="px-2.5 py-1 text-xs font-semibold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30 transition flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="border border-slate-800 rounded-lg overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Product Catalog Item *</th>
                    <th className="py-2.5 px-3 w-28">Quantity *</th>
                    <th className="py-2.5 px-3 w-32">Unit Price (₹)</th>
                    <th className="py-2.5 px-3 w-24">Tax %</th>
                    <th className="py-2.5 px-3 w-32 text-right">Line Total (₹)</th>
                    <th className="py-2.5 px-3 w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {items.map((it, idx) => {
                    const calc = calculations[idx];
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3">
                          <select
                            required
                            value={it.product_id}
                            onChange={(e) => handleProductChange(idx, e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 font-sans"
                          >
                            <option value="">Select Product...</option>
                            {products.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name} ({p.product_code}) [{p.category}]
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            min="0.01"
                            step="any"
                            required
                            value={it.ordered_quantity}
                            onChange={(e) => handleItemChange(idx, 'ordered_quantity', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            required
                            value={it.unit_price}
                            onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={it.tax_rate_percent}
                            onChange={(e) => handleItemChange(idx, 'tax_rate_percent', e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3 text-right font-semibold text-slate-200">
                          ₹{calc?.total?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 px-3 text-center">
                          {items.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeItemRow(idx)}
                              className="text-slate-500 hover:text-rose-400 transition"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Totals Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Order Notes / Delivery Instructions
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Mention payment terms, transport carrier, or warehouse delivery gate..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-xs text-slate-400 font-mono">
                <span>Subtotal ({items.length} items):</span>
                <span>₹{subtotalSum.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-400 font-mono">
                <span>Total Tax Amount (GST):</span>
                <span>₹{taxSum.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="border-t border-slate-800 pt-2 flex justify-between text-base font-bold text-amber-400 font-mono">
                <span>Grand Total:</span>
                <span>₹{grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
            </div>
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
              disabled={submitting}
              className="px-5 py-2 rounded-lg text-sm font-semibold bg-amber-500 text-slate-950 hover:bg-amber-400 transition disabled:opacity-50 flex items-center gap-1.5 shadow-md shadow-amber-500/20"
            >
              {submitting ? (
                <span>Saving...</span>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>{isEdit ? 'Update Purchase Order' : 'Save as DRAFT'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
