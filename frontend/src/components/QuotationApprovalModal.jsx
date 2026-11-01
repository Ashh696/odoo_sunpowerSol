import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { approveQuotation, rejectQuotation } from '../services/quotationApi';

export default function QuotationApprovalModal({
  isOpen,
  onClose,
  onSuccess,
  quotation,
  currentUser,
}) {
  const [decision, setDecision] = useState('APPROVE'); // 'APPROVE' or 'REJECT'
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !quotation) return null;

  const isCreator = quotation.created_by === currentUser?.id;
  const isSuperAdmin = currentUser?.role?.slug === 'SUPER_ADMIN';
  const isSelfApprovalBlocked = isCreator && !isSuperAdmin;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (isSelfApprovalBlocked && decision === 'APPROVE') {
      setError('You are the creator of this quotation. System separation-of-duties rules require another manager to approve.');
      return;
    }

    if (decision === 'REJECT' && (!comments || comments.trim().length < 3)) {
      setError('A mandatory reason (at least 3 characters) is required when rejecting a quotation.');
      return;
    }

    setSubmitting(true);
    try {
      if (decision === 'APPROVE') {
        await approveQuotation(quotation.id, { comments: comments.trim() || undefined });
      } else {
        await rejectQuotation(quotation.id, { comments: comments.trim() });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Action failed. Please check server validation details.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 text-white border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">Quotation Technical & Commercial Review</h3>
              <p className="text-xs text-slate-400 font-mono">{quotation.quotation_number} (v{quotation.version})</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Self-approval warning banner if applicable */}
        {isSelfApprovalBlocked && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2 text-amber-900 text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <span className="font-bold">Creator Separation-of-Duties:</span> You created this quotation. Only another authorized Technical Manager, Director, or Super Admin may approve it.
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Quotation Snapshot Info */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-500">Customer:</span>
              <span className="font-bold text-slate-900">{quotation.customer_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">System Spec:</span>
              <span className="font-semibold text-slate-800">{quotation.capacity_kw} kW {quotation.system_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Gross Amount:</span>
              <span className="font-mono font-bold text-slate-900">₹{quotation.gross_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-emerald-700">
              <span>Net Payable:</span>
              <span className="font-mono font-bold">₹{quotation.net_payable_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          {/* Decision Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
              Review Decision
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setDecision('APPROVE')}
                disabled={isSelfApprovalBlocked}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border text-xs font-bold transition disabled:opacity-40 ${
                  decision === 'APPROVE'
                    ? 'bg-blue-50 border-blue-500 text-blue-800 shadow-sm'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                <span>Approve Quotation</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('REJECT')}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border text-xs font-bold transition ${
                  decision === 'REJECT'
                    ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-sm'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <XCircle className="w-4 h-4 text-rose-600" />
                <span>Reject / Return</span>
              </button>
            </div>
          </div>

          {/* Review Comments */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {decision === 'REJECT' ? 'Mandatory Rejection Comments *' : 'Review / Approval Notes (Optional)'}
            </label>
            <textarea
              rows={3}
              placeholder={decision === 'REJECT' ? 'Enter exact reason for rejection...' : 'Verification comments (optional)...'}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-800 focus:ring-2 focus:ring-blue-500"
              required={decision === 'REJECT'}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || (isSelfApprovalBlocked && decision === 'APPROVE')}
              className={`px-5 py-2 rounded-xl text-xs font-bold text-white shadow-sm transition disabled:opacity-50 ${
                decision === 'APPROVE' ? 'bg-blue-600 hover:bg-blue-500' : 'bg-rose-600 hover:bg-rose-500'
              }`}
            >
              {submitting ? 'Submitting...' : decision === 'APPROVE' ? 'Confirm Approval' : 'Confirm Rejection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
