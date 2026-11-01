import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Printer,
  CreditCard,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  Calendar,
  User,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { getInvoice, recordDirectInvoicePayment } from '../services/financeApi';
import InvoicePrintModal from './InvoicePrintModal';
import PaymentAllocationModal from './PaymentAllocationModal';

export default function InvoiceDetailModal({ isOpen, onClose, invoiceId, currentUser, onRefresh }) {
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPrintModal, setShowPrintModal] = useState(false);
  const [showAllocModal, setShowAllocModal] = useState(false);

  // Direct Pay Form state
  const [showDirectPayForm, setShowDirectPayForm] = useState(false);
  const [directPayAmount, setDirectPayAmount] = useState('');
  const [directPayMethod, setDirectPayMethod] = useState('UPI');
  const [directPayRef, setDirectPayRef] = useState('');
  const [directPayNotes, setDirectPayNotes] = useState('');
  const [submittingPay, setSubmittingPay] = useState(false);
  const [paySuccessMsg, setPaySuccessMsg] = useState(null);

  const fetchInvoice = () => {
    if (!invoiceId) return;
    setLoading(true);
    setError(null);
    getInvoice(invoiceId)
      .then((res) => {
        setInvoice(res.data);
        if (res.data) {
          setDirectPayAmount(String(res.data.balance_amount));
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || err.message || 'Failed to load invoice details.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isOpen || !invoiceId) return;
    fetchInvoice();
    setShowDirectPayForm(false);
    setPaySuccessMsg(null);
  }, [isOpen, invoiceId]);

  if (!isOpen) return null;

  const roleSlug = currentUser?.role?.slug || '';
  const isFinance = roleSlug === 'FINANCE_ACCOUNTS' || roleSlug === 'SUPER_ADMIN';

  const handleDirectPaySubmit = async (e) => {
    e.preventDefault();
    if (!invoice) return;

    const amt = parseFloat(directPayAmount);
    if (!amt || amt <= 0) {
      setError('Payment amount must be greater than zero.');
      return;
    }
    if (amt > parseFloat(invoice.balance_amount)) {
      setError(`Payment cannot exceed outstanding balance (₹${parseFloat(invoice.balance_amount).toLocaleString('en-IN')}).`);
      return;
    }

    setSubmittingPay(true);
    setError(null);

    try {
      await recordDirectInvoicePayment(invoice.id, {
        amount: amt,
        payment_method: directPayMethod,
        transaction_reference: directPayRef.trim() || null,
        notes: directPayNotes.trim() || null,
      });
      setPaySuccessMsg(`Payment of ₹${amt.toLocaleString('en-IN')} recorded & allocated successfully!`);
      setShowDirectPayForm(false);
      fetchInvoice();
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Payment recording failed.');
    } finally {
      setSubmittingPay(false);
    }
  };

  const statusBadge = (st) => {
    switch (st) {
      case 'PAID':
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">PAID</span>;
      case 'PARTIALLY_PAID':
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">PARTIALLY PAID</span>;
      case 'OVERDUE':
        return <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">OVERDUE</span>;
      default:
        return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">PENDING</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-6 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950 text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm font-mono">{invoice?.invoice_number || 'Invoice Details'}</h3>
                {invoice && statusBadge(invoice.payment_status)}
              </div>
              <p className="text-xs text-slate-400">
                Milestone: <span className="text-white font-medium">{invoice?.invoice_type?.replace('_', ' ')}</span>
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition p-1.5 rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {paySuccessMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-emerald-400 text-xs">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{paySuccessMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading invoice details...</div>
          ) : invoice ? (
            <>
              {/* Financial KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl">
                  <span className="text-slate-400 text-[11px] block mb-0.5">Total Amount</span>
                  <span className="text-lg font-bold font-mono text-white">
                    ₹{parseFloat(invoice.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Base: ₹{parseFloat(invoice.subtotal).toLocaleString('en-IN')} + GST: ₹{parseFloat(invoice.tax_amount).toLocaleString('en-IN')}
                  </div>
                </div>

                <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl">
                  <span className="text-slate-400 text-[11px] block mb-0.5">Paid / Allocated</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">
                    ₹{parseFloat(invoice.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                  <div className="text-[10px] text-emerald-500/80 mt-1">
                    {invoice.allocations?.length || 0} allocation receipt(s)
                  </div>
                </div>

                <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl">
                  <span className="text-slate-400 text-[11px] block mb-0.5">Outstanding Balance</span>
                  <span className={`text-lg font-bold font-mono ${parseFloat(invoice.balance_amount) > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    ₹{parseFloat(invoice.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Due: {new Date(invoice.due_date).toLocaleDateString('en-IN')}
                  </div>
                </div>
              </div>

              {/* Context: Customer & Commercial */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Customer Info</span>
                  <p className="font-bold text-white">{invoice.customer?.full_name}</p>
                  <p className="text-slate-400 text-[11px]">Phone: {invoice.customer?.phone}</p>
                  <p className="text-slate-400 text-[11px]">Location: {invoice.customer?.city || 'Pune'}, {invoice.customer?.state || 'MH'}</p>
                </div>
                <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Order & Project</span>
                  <p className="text-slate-300">Order: <span className="font-mono font-bold text-white">{invoice.order?.order_number}</span></p>
                  {invoice.project?.project_code && (
                    <p className="text-slate-300">Project: <span className="font-mono font-bold text-white">{invoice.project.project_code}</span></p>
                  )}
                  <p className="text-slate-400 text-[11px]">Invoice Date: {new Date(invoice.invoice_date).toLocaleDateString('en-IN')}</p>
                </div>
              </div>

              {/* Line Items Table */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Bill of Supply Line Items</h4>
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/30">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 text-[11px]">
                      <tr>
                        <th className="py-2.5 px-3">Description</th>
                        <th className="py-2.5 px-3 text-right">Qty</th>
                        <th className="py-2.5 px-3 text-right">Unit Price</th>
                        <th className="py-2.5 px-3 text-right">GST %</th>
                        <th className="py-2.5 px-3 text-right">Amount (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80">
                      {invoice.items && invoice.items.length > 0 ? (
                        invoice.items.map((it) => (
                          <tr key={it.id}>
                            <td className="py-2 px-3">
                              <span className="font-semibold text-white">{it.item_description}</span>
                              {it.product_code && <span className="block text-[10px] text-slate-500 font-mono">{it.product_code}</span>}
                            </td>
                            <td className="py-2 px-3 text-right font-medium text-slate-300">{parseFloat(it.quantity).toFixed(2)}</td>
                            <td className="py-2 px-3 text-right font-mono text-slate-300">₹{parseFloat(it.unit_price).toLocaleString('en-IN')}</td>
                            <td className="py-2 px-3 text-right font-mono text-slate-400">{parseFloat(it.tax_rate_percent).toFixed(1)}%</td>
                            <td className="py-2 px-3 text-right font-mono font-bold text-white">₹{parseFloat(it.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="py-4 text-center text-slate-500 italic">No line items recorded.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Payment Allocations Section */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Payment Allocations</h4>
                  {isFinance && parseFloat(invoice.balance_amount) > 0 && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowAllocModal(true)}
                        className="px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                      >
                        <CreditCard className="w-3.5 h-3.5" />
                        <span>Allocate Payment</span>
                      </button>
                      <button
                        onClick={() => setShowDirectPayForm(!showDirectPayForm)}
                        className="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                      >
                        <DollarSign className="w-3.5 h-3.5" />
                        <span>{showDirectPayForm ? 'Cancel Pay' : 'Record Direct Payment'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Direct Pay Inline Form */}
                {showDirectPayForm && (
                  <form onSubmit={handleDirectPaySubmit} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-xs">
                    <h5 className="font-bold text-white uppercase text-[11px] tracking-wider text-emerald-400">Record Direct Payment Against Invoice</h5>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-slate-400 text-[11px] mb-1">Amount (₹) *</label>
                        <input
                          type="number"
                          step="0.01"
                          max={parseFloat(invoice.balance_amount)}
                          value={directPayAmount}
                          onChange={(e) => setDirectPayAmount(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 text-[11px] mb-1">Method *</label>
                        <select
                          value={directPayMethod}
                          onChange={(e) => setDirectPayMethod(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                        >
                          <option value="UPI">UPI / QR</option>
                          <option value="NEFT">NEFT / Bank</option>
                          <option value="RTGS">RTGS</option>
                          <option value="CHEQUE">Cheque</option>
                          <option value="CASH">Cash</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-400 text-[11px] mb-1">Transaction Ref</label>
                        <input
                          type="text"
                          value={directPayRef}
                          onChange={(e) => setDirectPayRef(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                          placeholder="e.g. UTR / UPI Ref"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end pt-1">
                      <button
                        type="submit"
                        disabled={submittingPay}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition text-xs shadow"
                      >
                        {submittingPay ? 'Recording...' : 'Submit & Allocate'}
                      </button>
                    </div>
                  </form>
                )}

                {invoice.allocations && invoice.allocations.length > 0 ? (
                  <div className="space-y-1.5">
                    {invoice.allocations.map((al) => (
                      <div key={al.id} className="flex justify-between items-center p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="font-mono font-bold text-white">{al.payment_number}</span>
                          <span className="text-slate-400 text-[11px]">• {new Date(al.allocated_at).toLocaleDateString('en-IN')}</span>
                        </div>
                        <span className="font-mono font-bold text-emerald-400">
                          ₹{parseFloat(al.allocated_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl text-xs text-slate-500 text-center italic">
                    No payment allocations recorded yet.
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950 flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
          >
            Close
          </button>
          {invoice && (
            <button
              onClick={() => setShowPrintModal(true)}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow"
            >
              <Printer className="w-4 h-4" />
              <span>Print Tax Invoice</span>
            </button>
          )}
        </div>
      </div>

      {showPrintModal && invoice && (
        <InvoicePrintModal
          isOpen={showPrintModal}
          onClose={() => setShowPrintModal(false)}
          invoice={invoice}
        />
      )}

      {showAllocModal && invoice && (
        <PaymentAllocationModal
          isOpen={showAllocModal}
          onClose={() => setShowAllocModal(false)}
          invoice={invoice}
          onSuccess={() => {
            fetchInvoice();
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </div>
  );
}
