import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  DollarSign,
  User,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  CreditCard,
  Briefcase,
  Layers,
  Receipt,
  Plus,
  Eye,
} from 'lucide-react';
import { recordOrderPayment, updateOrderStatus } from '../services/orderApi';
import { handoverProject } from '../services/projectApi';
import { getOrderInvoices } from '../services/financeApi';
import InvoiceCreateModal from './InvoiceCreateModal';
import InvoiceDetailModal from './InvoiceDetailModal';

const STATUS_COLORS = {
  PENDING_ADVANCE: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  CONFIRMED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  PROCESSING: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  COMPLETED: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function OrderDetailModal({
  order,
  onClose,
  onRefresh,
  currentRole = 'SUPER_ADMIN',
  onOpenProject = null,
}) {
  const [submittingPayment, setSubmittingPayment] = useState(false);
  const [submittingHandover, setSubmittingHandover] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [showHandoverForm, setShowHandoverForm] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Payment Form State
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState('UPI');
  const [payRef, setPayRef] = useState('');
  const [payNotes, setPayNotes] = useState('');

  // Handover Form State
  const [siteAddress, setSiteAddress] = useState(
    order?.customer ? `${order.customer.city || ''}, ${order.customer.state || ''}` : ''
  );
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [compDate, setCompDate] = useState(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [initialNotes, setInitialNotes] = useState('');

  // Invoices state
  const [orderInvoices, setOrderInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [showCreateInvoice, setShowCreateInvoice] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);

  const fetchInvoices = () => {
    if (!order?.id) return;
    setLoadingInvoices(true);
    getOrderInvoices(order.id)
      .then((res) => {
        setOrderInvoices(res.data || []);
      })
      .catch((err) => {
        console.warn('Failed to load order invoices:', err);
      })
      .finally(() => setLoadingInvoices(false));
  };

  useEffect(() => {
    fetchInvoices();
  }, [order?.id]);

  if (!order) return null;

  const canRecordPayment =
    currentRole === 'SUPER_ADMIN' ||
    currentRole === 'FINANCE_ACCOUNTS' ||
    currentRole === 'Finance & Accounts Manager' ||
    currentRole === 'Super Admin';

  const canHandover =
    currentRole === 'SUPER_ADMIN' ||
    currentRole === 'TECHNICAL_MANAGER' ||
    currentRole === 'Technical / Installation Manager' ||
    currentRole === 'Super Admin';

  const isEligibleForHandover =
    !order.project &&
    order.status !== 'CANCELLED' &&
    (order.status === 'CONFIRMED' || parseFloat(order.advance_paid) > 0);

  const handleRecordPaymentSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setSubmittingPayment(true);

    try {
      const parsedAmount = parseFloat(payAmount);
      if (isNaN(parsedAmount) || parsedAmount <= 0) {
        throw new Error('Please enter a valid positive payment amount');
      }

      const res = await recordOrderPayment(order.id, {
        amount: parsedAmount,
        payment_method: payMethod,
        transaction_reference: payRef.trim() || undefined,
        notes: payNotes.trim() || undefined,
      });

      setSuccessMsg(res.data?.message || 'Payment recorded successfully!');
      setShowPaymentForm(false);
      setPayAmount('');
      setPayRef('');
      setPayNotes('');
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to record payment');
    } finally {
      setSubmittingPayment(false);
    }
  };

  const handleHandoverSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setSubmittingHandover(true);

    try {
      const res = await handoverProject(order.id, {
        site_address: siteAddress.trim() || undefined,
        planned_start_date: startDate || undefined,
        planned_completion_date: compDate || undefined,
        initial_notes: initialNotes.trim() || undefined,
      });

      setSuccessMsg(res.data?.message || 'Project handover completed successfully!');
      setShowHandoverForm(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Handover failed');
    } finally {
      setSubmittingHandover(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white tracking-tight">{order.order_number}</h3>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${
                    STATUS_COLORS[order.status] || 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {order.status}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Created on {new Date(order.order_date).toLocaleDateString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-400 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Financial Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs font-medium text-slate-400 block mb-1">Total Contract Value</span>
              <span className="text-xl font-bold text-white">
                ₹{parseFloat(order.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs font-medium text-emerald-400 block mb-1">Advance Collected</span>
              <span className="text-xl font-bold text-emerald-400">
                ₹{parseFloat(order.advance_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
              <span className="text-xs font-medium text-amber-400 block mb-1">Balance Remaining</span>
              <span className="text-xl font-bold text-amber-400">
                ₹{parseFloat(order.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Customer & Quotation Context */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Customer Box */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-4 space-y-2">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                <User className="w-4 h-4 text-amber-400" />
                <span>Customer Details</span>
              </div>
              <div className="text-sm">
                <p className="font-semibold text-white">{order.customer?.full_name || 'Customer'}</p>
                <p className="text-slate-400 text-xs">Phone: {order.customer?.phone || 'N/A'}</p>
                <p className="text-slate-400 text-xs">Email: {order.customer?.email || 'N/A'}</p>
                <p className="text-slate-400 text-xs">
                  Location: {order.customer?.city || 'Pune'}, {order.customer?.state || 'Maharashtra'}
                </p>
              </div>
            </div>

            {/* Quotation Box */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-4 space-y-2">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                <FileText className="w-4 h-4 text-amber-400" />
                <span>Quotation Reference</span>
              </div>
              <div className="text-sm">
                <p className="font-semibold text-white">{order.quotation?.quotation_number || 'N/A'}</p>
                <p className="text-slate-400 text-xs">System: {order.quotation?.system_type} • {order.quotation?.capacity_kw} kW</p>
                <p className="text-slate-400 text-xs">
                  Net Payable: ₹{order.quotation?.net_payable_amount ? parseFloat(order.quotation.net_payable_amount).toLocaleString('en-IN') : 'N/A'}
                </p>
                <p className="text-slate-400 text-xs">Status: {order.quotation?.status}</p>
              </div>
            </div>
          </div>

          {/* Operations Handover / Project Section */}
          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-amber-400" />
                <h4 className="text-sm font-bold text-white">Sales-to-Operations Handover</h4>
              </div>

              {order.project && (
                <span className="text-xs px-2.5 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400 font-semibold">
                  Project Initialized: {order.project.project_code}
                </span>
              )}
            </div>

            {order.project ? (
              <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-lg p-3">
                <div>
                  <p className="text-sm font-semibold text-white">{order.project.project_code}</p>
                  <p className="text-xs text-slate-400">
                    Status: <span className="text-blue-400 font-medium">{order.project.status}</span> • Capacity: {order.project.system_capacity_kw} kW
                  </p>
                </div>
                {onOpenProject && (
                  <button
                    onClick={() => onOpenProject(order.project.id)}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1.5 shadow"
                  >
                    <span>View Project</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ) : (
              <div>
                {isEligibleForHandover ? (
                  <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800/80 rounded-lg p-3">
                    <div className="text-xs text-slate-300">
                      <p className="font-semibold text-white">Order is cleared for handover</p>
                      <p className="text-slate-400">Advance paid or order confirmed. Ready for Project & BOM generation.</p>
                    </div>
                    {canHandover && (
                      <button
                        onClick={() => setShowHandoverForm(!showHandoverForm)}
                        className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition shadow-md shadow-amber-500/10 flex items-center gap-1.5"
                      >
                        <Briefcase className="w-3.5 h-3.5" />
                        <span>{showHandoverForm ? 'Cancel' : 'Initialize Handover'}</span>
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3 flex items-start gap-2.5 text-xs text-amber-300/90">
                    <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-amber-400">Operations Handover Pending Advance</p>
                      <p className="text-slate-400 mt-0.5">
                        This order is in <span className="text-white font-medium">PENDING_ADVANCE</span> status with zero advance payment recorded. Record customer advance receipt to authorize project execution handover.
                      </p>
                    </div>
                  </div>
                )}

                {/* Handover Form */}
                {showHandoverForm && (
                  <form onSubmit={handleHandoverSubmit} className="mt-4 bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
                    <h5 className="text-xs font-bold text-white uppercase tracking-wider">Project Handover Details</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <label className="block text-slate-400 mb-1">Site Installation Address</label>
                        <input
                          type="text"
                          value={siteAddress}
                          onChange={(e) => setSiteAddress(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                          placeholder="Full installation site address"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-slate-400 mb-1">Start Date</label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-slate-400 mb-1">Target Completion</label>
                          <input
                            type="date"
                            value={compDate}
                            onChange={(e) => setCompDate(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                            required
                          />
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-slate-400 mb-1">Initial Technical Notes (Internal)</label>
                        <textarea
                          rows={2}
                          value={initialNotes}
                          onChange={(e) => setInitialNotes(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                          placeholder="e.g. Inverter location on west wall, structure tilt bracket required"
                        />
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        disabled={submittingHandover}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow"
                      >
                        {submittingHandover ? 'Initializing Project...' : 'Confirm Project Handover & BOM'}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </div>

          {/* Milestone Invoices Section */}
          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Receipt className="w-5 h-5 text-amber-400" />
                <h4 className="text-sm font-bold text-white">Commercial Milestone Invoices</h4>
              </div>
              {canRecordPayment && order.status !== 'CANCELLED' && (
                <button
                  onClick={() => setShowCreateInvoice(true)}
                  className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Generate Milestone Invoice</span>
                </button>
              )}
            </div>

            {loadingInvoices ? (
              <p className="text-xs text-slate-400 py-2">Loading invoices...</p>
            ) : orderInvoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2 px-3">Invoice #</th>
                      <th className="py-2 px-3">Type</th>
                      <th className="py-2 px-3">Due Date</th>
                      <th className="py-2 px-3 text-right">Total</th>
                      <th className="py-2 px-3 text-right">Paid</th>
                      <th className="py-2 px-3 text-right">Balance</th>
                      <th className="py-2 px-3 text-center">Status</th>
                      <th className="py-2 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {orderInvoices.map((inv) => (
                      <tr key={inv.id} className="hover:bg-slate-900/40">
                        <td className="py-2.5 px-3 font-mono font-semibold text-white">{inv.invoice_number}</td>
                        <td className="py-2.5 px-3 text-slate-300 font-medium">{inv.invoice_type.replace('_', ' ')}</td>
                        <td className="py-2.5 px-3 text-slate-400">{new Date(inv.due_date).toLocaleDateString()}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-white font-bold">
                          ₹{parseFloat(inv.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                          ₹{parseFloat(inv.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono text-amber-400 font-bold">
                          ₹{parseFloat(inv.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                            inv.payment_status === 'PAID'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          }`}>
                            {inv.payment_status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => setSelectedInvoiceId(inv.id)}
                            className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition"
                            title="View Invoice"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-2">No milestone tax invoices issued for this order yet.</p>
            )}
          </div>

          {/* Payments Section */}
          <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CreditCard className="w-5 h-5 text-emerald-400" />
                <h4 className="text-sm font-bold text-white">Payment Receipts & Allocations</h4>
              </div>
              {canRecordPayment && parseFloat(order.balance_amount) > 0 && (
                <button
                  onClick={() => setShowPaymentForm(!showPaymentForm)}
                  className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  <span>{showPaymentForm ? 'Cancel' : 'Record Payment'}</span>
                </button>
              )}
            </div>

            {/* Inline Payment Form */}
            {showPaymentForm && (
              <form onSubmit={handleRecordPaymentSubmit} className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
                <h5 className="text-xs font-bold text-white uppercase tracking-wider">Record Customer Payment</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Amount (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      max={parseFloat(order.balance_amount)}
                      value={payAmount}
                      onChange={(e) => setPayAmount(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                      placeholder={`Max: ${parseFloat(order.balance_amount)}`}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Payment Method</label>
                    <select
                      value={payMethod}
                      onChange={(e) => setPayMethod(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                    >
                      <option value="UPI">UPI / QR</option>
                      <option value="NEFT">NEFT / Bank Transfer</option>
                      <option value="RTGS">RTGS</option>
                      <option value="CHEQUE">Cheque</option>
                      <option value="CASH">Cash</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Transaction Reference</label>
                    <input
                      type="text"
                      value={payRef}
                      onChange={(e) => setPayRef(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                      placeholder="e.g. UTR / UPI Ref ID"
                    />
                  </div>
                  <div className="md:col-span-3">
                    <label className="block text-slate-400 mb-1">Notes / Remarks</label>
                    <input
                      type="text"
                      value={payNotes}
                      onChange={(e) => setPayNotes(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                      placeholder="e.g. 20% Booking Token Received"
                    />
                  </div>
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={submittingPayment}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow"
                  >
                    {submittingPayment ? 'Recording...' : 'Submit Payment Receipt'}
                  </button>
                </div>
              </form>
            )}

            {/* Payments List */}
            {order.payments && order.payments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2 px-3">Receipt #</th>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Method</th>
                      <th className="py-2 px-3">Reference</th>
                      <th className="py-2 px-3 text-right">Amount</th>
                      <th className="py-2 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {order.payments.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-900/40">
                        <td className="py-2.5 px-3 font-semibold text-white">{p.payment_number}</td>
                        <td className="py-2.5 px-3 text-slate-400">{new Date(p.payment_date).toLocaleDateString()}</td>
                        <td className="py-2.5 px-3 text-slate-300">{p.payment_method}</td>
                        <td className="py-2.5 px-3 text-slate-400">{p.transaction_reference || '—'}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                          ₹{parseFloat(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-2">No payment transactions recorded for this order yet.</p>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition"
          >
            Close
          </button>
        </div>
      </div>

      {showCreateInvoice && (
        <InvoiceCreateModal
          isOpen={showCreateInvoice}
          onClose={() => setShowCreateInvoice(false)}
          order={order}
          onSuccess={() => {
            fetchInvoices();
            if (onRefresh) onRefresh();
          }}
        />
      )}

      {selectedInvoiceId && (
        <InvoiceDetailModal
          isOpen={Boolean(selectedInvoiceId)}
          onClose={() => setSelectedInvoiceId(null)}
          invoiceId={selectedInvoiceId}
          currentUser={{ role: { slug: currentRole } }}
          onRefresh={() => {
            fetchInvoices();
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </div>
  );
}
