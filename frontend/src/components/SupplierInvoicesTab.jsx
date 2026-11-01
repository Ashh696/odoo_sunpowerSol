import React, { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Plus,
  CreditCard,
  Building,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  X,
} from 'lucide-react';
import {
  getSupplierInvoices,
  directSupplierInvoicePayment,
} from '../services/supplierFinanceApi';

export default function SupplierInvoicesTab({ currentUser }) {
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  // Payment Modal
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMode, setPaymentMode] = useState('BANK_TRANSFER');
  const [paymentRef, setPaymentRef] = useState('');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [submittingPayment, setSubmittingPayment] = useState(false);

  // KPIs
  const [kpis, setKpis] = useState({
    totalInvoiced: 0,
    totalPaid: 0,
    totalOutstanding: 0,
  });

  const fetchInvoices = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: 20 };
      if (statusFilter) params.payment_status = statusFilter;

      const res = await getSupplierInvoices(params);
      const items = res.data?.data?.items || [];
      setInvoices(items);
      setTotal(res.data?.data?.total || 0);

      // Calculate KPIs
      let sumInvoiced = 0;
      let sumPaid = 0;
      let sumBalance = 0;
      items.forEach((i) => {
        sumInvoiced += Number(i.total_amount || 0);
        sumPaid += Number(i.paid_amount || 0);
        sumBalance += Number(i.balance_amount || 0);
      });
      setKpis({
        totalInvoiced: sumInvoiced,
        totalPaid: sumPaid,
        totalOutstanding: sumBalance,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load supplier invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [page, statusFilter]);

  const handleOpenPayment = (inv) => {
    setSelectedInvoice(inv);
    setPaymentAmount(inv.balance_amount);
    setPaymentRef('');
    setPaymentNotes('');
    setPaymentModalOpen(true);
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice || !paymentAmount) return;

    setSubmittingPayment(true);
    try {
      await directSupplierInvoicePayment(selectedInvoice.id, {
        amount: parseFloat(paymentAmount),
        payment_mode: paymentMode,
        payment_reference: paymentRef || undefined,
        notes: paymentNotes || undefined,
      });
      setPaymentModalOpen(false);
      fetchInvoices();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record supplier payment');
    } finally {
      setSubmittingPayment(false);
    }
  };

  const renderStatusBadge = (st) => {
    switch (st) {
      case 'PAID':
        return <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">PAID</span>;
      case 'PARTIALLY_PAID':
        return <span className="bg-blue-500/10 text-blue-500 border border-blue-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">PARTIAL</span>;
      default:
        return <span className="bg-amber-500/10 text-amber-500 border border-amber-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">{st}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total AP Invoiced</span>
            <span className="p-1.5 bg-slate-100 text-slate-600 rounded-lg">
              <FileText className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">
            ₹{kpis.totalInvoiced.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Total supplier purchase bills</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Supplier Payments Made</span>
            <span className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-emerald-600">
            ₹{kpis.totalPaid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Total settled disbursements</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Outstanding Accounts Payable</span>
            <span className="p-1.5 bg-rose-50 text-rose-600 rounded-lg">
              <TrendingDown className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-rose-600">
            ₹{kpis.totalOutstanding.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Pending payable to vendors</span>
        </div>
      </div>

      {/* Filter and Actions Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg text-xs px-3 py-1.5 focus:ring-2 focus:ring-amber-500/20"
          >
            <option value="">All Payment Statuses</option>
            <option value="PENDING">PENDING</option>
            <option value="PARTIALLY_PAID">PARTIALLY_PAID</option>
            <option value="PAID">PAID</option>
            <option value="OVERDUE">OVERDUE</option>
          </select>
          <button
            onClick={fetchInvoices}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
          </button>
        </div>
      </div>

      {/* Supplier Invoices Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Invoice # / PO #</th>
                <th className="px-4 py-3">Supplier & GSTIN</th>
                <th className="px-4 py-3">Invoice Date</th>
                <th className="px-4 py-3 text-right">Bill Total</th>
                <th className="px-4 py-3 text-right">PO Total</th>
                <th className="px-4 py-3 text-right">Variance</th>
                <th className="px-4 py-3 text-right">Paid / Balance</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
                    <span>Loading accounts payable invoices...</span>
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    No supplier invoices recorded yet.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/70 transition">
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{inv.invoice_number}</div>
                      <div className="text-[11px] text-slate-400">{inv.po_number || `PO #${inv.purchase_order_id}`}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{inv.supplier_name || `Supplier #${inv.supplier_id}`}</div>
                      <div className="text-[10px] font-mono text-slate-400">{inv.supplier_gstin || 'No GSTIN'}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600">
                      {inv.invoice_date}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-900">
                      ₹{Number(inv.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-500">
                      ₹{Number(inv.po_total || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {Number(inv.variance_amount) > 0 ? (
                        <span className="text-rose-600 font-semibold">+₹{Number(inv.variance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                      ) : Number(inv.variance_amount) < 0 ? (
                        <span className="text-emerald-600 font-semibold">-₹{Math.abs(Number(inv.variance_amount)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                      ) : (
                        <span className="text-slate-400">₹0.00</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="font-mono text-emerald-600 font-semibold">
                        ₹{Number(inv.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="font-mono text-slate-500 text-[11px]">
                        Bal: ₹{Number(inv.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {renderStatusBadge(inv.payment_status)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {Number(inv.balance_amount) > 0 ? (
                        <button
                          onClick={() => handleOpenPayment(inv)}
                          className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-lg text-xs font-bold transition flex items-center gap-1 mx-auto shadow-sm"
                        >
                          <CreditCard className="w-3 h-3" />
                          <span>Pay</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-600 font-semibold">Settled</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Modal */}
      {paymentModalOpen && selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-amber-500" />
                <span>Supplier Disbursement Payment</span>
              </h3>
              <button
                onClick={() => setPaymentModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg text-xs space-y-1">
              <div><span className="font-semibold text-slate-600">Invoice:</span> {selectedInvoice.invoice_number}</div>
              <div><span className="font-semibold text-slate-600">Supplier:</span> {selectedInvoice.supplier_name}</div>
              <div><span className="font-semibold text-slate-600">Remaining Balance:</span> ₹{Number(selectedInvoice.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
            </div>

            <form onSubmit={handleRecordPayment} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Disbursement Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  max={selectedInvoice.balance_amount}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payment Mode</label>
                <select
                  value={paymentMode}
                  onChange={(e) => setPaymentMode(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="BANK_TRANSFER">Bank Transfer (NEFT/RTGS)</option>
                  <option value="NEFT">NEFT</option>
                  <option value="RTGS">RTGS</option>
                  <option value="IMPS">IMPS</option>
                  <option value="UPI">UPI</option>
                  <option value="CHEQUE">Cheque</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payment / UTR Reference</label>
                <input
                  type="text"
                  placeholder="e.g. UTR-98231456"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes</label>
                <textarea
                  placeholder="Payment settlement details..."
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  rows="2"
                  className="w-full border border-slate-200 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setPaymentModalOpen(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingPayment}
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  {submittingPayment ? 'Processing...' : 'Confirm Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
