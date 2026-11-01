import React, { useState, useEffect } from 'react';
import { X, CreditCard, DollarSign, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { getPayments, allocatePaymentToInvoice } from '../services/financeApi';

export default function PaymentAllocationModal({ isOpen, onClose, invoice, onSuccess }) {
  const [payments, setPayments] = useState([]);
  const [selectedPaymentId, setSelectedPaymentId] = useState('');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    if (!isOpen || !invoice) return;

    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    setSelectedPaymentId('');
    setAmount('');

    // Fetch payments for this order/customer
    getPayments({ order_id: invoice.order_id, status: 'COMPLETED' })
      .then((res) => {
        const allPayments = res.data?.items || [];
        // Filter payments with positive unallocated amount
        const eligible = allPayments.filter((p) => parseFloat(p.unallocated_amount) > 0);
        setPayments(eligible);
        if (eligible.length > 0) {
          setSelectedPaymentId(String(eligible[0].id));
          // Pre-fill min(unallocated, invoice balance)
          const avail = parseFloat(eligible[0].unallocated_amount);
          const bal = parseFloat(invoice.balance_amount);
          setAmount(String(Math.min(avail, bal)));
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || err.message || 'Failed to retrieve order payments.');
      })
      .finally(() => setLoading(false));
  }, [isOpen, invoice]);

  if (!isOpen || !invoice) return null;

  const selectedPayment = payments.find((p) => String(p.id) === selectedPaymentId);
  const availableCash = selectedPayment ? parseFloat(selectedPayment.unallocated_amount) : 0;
  const invoiceBalance = parseFloat(invoice.balance_amount);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedPayment) {
      setError('Please select an eligible customer payment.');
      return;
    }

    const allocAmt = parseFloat(amount);
    if (!allocAmt || allocAmt <= 0) {
      setError('Allocation amount must be greater than zero.');
      return;
    }
    if (allocAmt > availableCash) {
      setError(`Amount cannot exceed available unallocated payment balance (₹${availableCash.toLocaleString('en-IN')}).`);
      return;
    }
    if (allocAmt > invoiceBalance) {
      setError(`Amount cannot exceed outstanding invoice balance (₹${invoiceBalance.toLocaleString('en-IN')}).`);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await allocatePaymentToInvoice(invoice.id, {
        payment_id: selectedPayment.id,
        allocated_amount: allocAmt,
      });
      setSuccessMsg(`₹${allocAmt.toLocaleString('en-IN')} allocated successfully.`);
      if (onSuccess) onSuccess();
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Payment allocation failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950 text-white">
          <div className="flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-sm">Allocate Existing Payment</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-emerald-400 text-xs">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Invoice Summary */}
          <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Target Invoice:</span>
              <span className="font-mono font-bold text-white">{invoice.invoice_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Milestone Type:</span>
              <span className="text-amber-400 font-semibold">{invoice.invoice_type}</span>
            </div>
            <div className="flex justify-between pt-1 border-t border-slate-800/80">
              <span className="text-slate-400 font-semibold">Outstanding Invoice Balance:</span>
              <span className="font-mono font-bold text-rose-400">
                ₹{invoiceBalance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-400">Loading eligible payments...</div>
          ) : payments.length === 0 ? (
            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-300 text-center">
              No completed payments with unallocated funds found for this order. Record a payment first to allocate funds.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Select Payment Receipt *
                </label>
                <select
                  value={selectedPaymentId}
                  onChange={(e) => {
                    setSelectedPaymentId(e.target.value);
                    const p = payments.find((item) => String(item.id) === e.target.value);
                    if (p) {
                      const avail = parseFloat(p.unallocated_amount);
                      setAmount(String(Math.min(avail, invoiceBalance)));
                    }
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  required
                >
                  {payments.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.payment_number} • ₹{parseFloat(p.amount).toLocaleString('en-IN')} ({p.payment_method}) — Unallocated: ₹{parseFloat(p.unallocated_amount).toLocaleString('en-IN')}
                    </option>
                  ))}
                </select>
              </div>

              {selectedPayment && (
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg">
                    <span className="text-slate-400 block text-[11px]">Available Unallocated:</span>
                    <span className="font-mono font-bold text-emerald-400">
                      ₹{availableCash.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg">
                    <span className="text-slate-400 block text-[11px]">Payment Date:</span>
                    <span className="text-white font-medium">
                      {new Date(selectedPayment.payment_date).toLocaleDateString('en-IN')}
                    </span>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Amount to Allocate (₹) *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-500 text-xs">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={Math.min(availableCash, invoiceBalance)}
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-7 pr-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
                    placeholder="Enter allocation amount"
                    required
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  Max allowable: ₹{Math.min(availableCash, invoiceBalance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-2">
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
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow"
                >
                  <ArrowRight className="w-4 h-4" />
                  <span>{submitting ? 'Allocating...' : 'Confirm Allocation'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
