import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';
import { createInvoice } from '../services/financeApi';
import { getProducts } from '../services/productApi';

export default function InvoiceCreateModal({ isOpen, onClose, order, onSuccess }) {
  const [invoiceType, setInvoiceType] = useState('ADVANCE');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState(
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [products, setProducts] = useState([]);
  const [items, setItems] = useState([
    { product_id: '', item_description: '', quantity: 1, unit_price: '', tax_rate_percent: 12 },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    setError(null);
    setInvoiceType('ADVANCE');
    setInvoiceDate(new Date().toISOString().split('T')[0]);
    setDueDate(new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);

    // Load active products
    getProducts({ limit: 50, is_active: true })
      .then((res) => {
        const prodList = res.data?.items || [];
        setProducts(prodList);
        if (prodList.length > 0) {
          setItems([
            {
              product_id: String(prodList[0].id),
              item_description: prodList[0].name,
              quantity: 1,
              unit_price: String(prodList[0].base_price || ''),
              tax_rate_percent: prodList[0].tax_rate_percent || 12,
            },
          ]);
        }
      })
      .catch((err) => {
        console.warn('Failed to load products for invoice line items:', err);
      });
  }, [isOpen, order]);

  if (!isOpen || !order) return null;

  const handleAddItem = () => {
    const defaultProd = products[0];
    setItems([
      ...items,
      {
        product_id: defaultProd ? String(defaultProd.id) : '',
        item_description: defaultProd ? defaultProd.name : '',
        quantity: 1,
        unit_price: defaultProd ? String(defaultProd.base_price || '') : '',
        tax_rate_percent: defaultProd ? defaultProd.tax_rate_percent : 12,
      },
    ]);
  };

  const handleRemoveItem = (index) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const handleItemChange = (index, field, value) => {
    const updated = [...items];
    updated[index][field] = value;

    if (field === 'product_id') {
      const prod = products.find((p) => String(p.id) === value);
      if (prod) {
        updated[index].item_description = prod.name;
        updated[index].unit_price = String(prod.base_price || '');
        updated[index].tax_rate_percent = prod.tax_rate_percent || 12;
      }
    }

    setItems(updated);
  };

  // Live calculation of totals
  let calculatedSubtotal = 0;
  let calculatedTax = 0;
  items.forEach((it) => {
    const q = parseFloat(it.quantity) || 0;
    const p = parseFloat(it.unit_price) || 0;
    const t = parseFloat(it.tax_rate_percent) || 0;
    const sub = q * p;
    const tax = sub * (t / 100);
    calculatedSubtotal += sub;
    calculatedTax += tax;
  });
  const calculatedTotal = calculatedSubtotal + calculatedTax;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      setError('Invoice must contain at least one line item.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload = {
      order_id: order.id,
      project_id: order.project?.id || null,
      invoice_type: invoiceType,
      invoice_date: invoiceDate,
      due_date: dueDate,
      items: items.map((it) => ({
        product_id: parseInt(it.product_id, 10),
        item_description: it.item_description,
        quantity: parseFloat(it.quantity),
        unit_price: parseFloat(it.unit_price),
        tax_rate_percent: parseFloat(it.tax_rate_percent),
      })),
    };

    try {
      await createInvoice(payload);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate invoice.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-6 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950 text-white">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-400" />
            <h3 className="font-bold text-sm">Generate Milestone Tax Invoice</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Context box */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">Billed Order:</span>
              <span className="font-mono font-bold text-white">{order.order_number}</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Customer: {order.customer?.full_name}</p>
            </div>
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Order Contract Value:</span>
              <span className="font-mono font-bold text-amber-400">
                ₹{parseFloat(order.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <p className="text-emerald-400 text-[11px] mt-0.5">
                Advance Collected: ₹{parseFloat(order.advance_paid).toLocaleString('en-IN')}
              </p>
            </div>
          </div>

          {/* Milestone Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Invoice Type / Milestone *</label>
              <select
                value={invoiceType}
                onChange={(e) => setInvoiceType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-white"
                required
              >
                <option value="ADVANCE">Advance / Booking (ADVANCE)</option>
                <option value="MILESTONE_DISPATCH">Pre-Dispatch Milestone (DISPATCH)</option>
                <option value="MILESTONE_INSTALLATION">Installation Milestone (INSTALLATION)</option>
                <option value="FINAL">Final Commissioning (FINAL)</option>
                <option value="SUBSIDY">DBT Subsidy Claim (SUBSIDY)</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Invoice Date *</label>
              <input
                type="date"
                value={invoiceDate}
                onChange={(e) => setInvoiceDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-white"
                required
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Due Date *</label>
              <input
                type="date"
                min={invoiceDate}
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-white"
                required
              />
            </div>
          </div>

          {/* Line items table */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Bill of Supply Line Items
              </label>
              <button
                type="button"
                onClick={handleAddItem}
                className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 font-semibold"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-2.5">
              {items.map((it, idx) => (
                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-400 text-[11px]">Item #{idx + 1}</span>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        className="text-slate-500 hover:text-rose-400 p-0.5"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div>
                      <label className="block text-slate-400 text-[11px] mb-0.5">Catalog Product *</label>
                      <select
                        value={it.product_id}
                        onChange={(e) => handleItemChange(idx, 'product_id', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-white text-xs"
                        required
                      >
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} ({p.product_code})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-slate-400 text-[11px] mb-0.5">Description</label>
                      <input
                        type="text"
                        value={it.item_description}
                        onChange={(e) => handleItemChange(idx, 'item_description', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-white text-xs"
                        placeholder="e.g. 550W Module Billing"
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-slate-400 text-[11px] mb-0.5">Quantity *</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={it.quantity}
                        onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-white text-xs font-mono"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 text-[11px] mb-0.5">Unit Price (₹) *</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={it.unit_price}
                        onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-white text-xs font-mono"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 text-[11px] mb-0.5">GST Rate (%)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={it.tax_rate_percent}
                        onChange={(e) => handleItemChange(idx, 'tax_rate_percent', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-white text-xs font-mono"
                        required
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Totals Preview */}
          <div className="flex justify-end pt-2">
            <div className="w-64 p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Subtotal:</span>
                <span className="font-mono text-white">₹{calculatedSubtotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>GST Tax:</span>
                <span className="font-mono text-white">₹{calculatedTax.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between font-bold text-amber-400 pt-1 border-t border-slate-800 text-sm">
                <span>Total Invoice:</span>
                <span className="font-mono">₹{calculatedTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow"
            >
              {submitting ? 'Generating...' : 'Confirm & Issue Invoice'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
