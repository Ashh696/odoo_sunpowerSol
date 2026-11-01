import React, { useState } from 'react';
import {
  X,
  History,
  AlertCircle,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { reviseQuotation } from '../services/quotationApi';

export default function QuotationRevisionModal({
  isOpen,
  onClose,
  onSuccess,
  quotation,
}) {
  const [reason, setReason] = useState('');
  const [installationCost, setInstallationCost] = useState(
    quotation?.installation_cost ? String(quotation.installation_cost) : ''
  );
  const [terms, setTerms] = useState(quotation?.terms_and_conditions || '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !quotation) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!reason || reason.trim().length < 3) {
      setError('A mandatory reason for revision (at least 3 characters) is required.');
      return;
    }

    setSubmitting(true);
    try {
      await reviseQuotation(quotation.id, {
        reason_for_revision: reason.trim(),
        installation_cost: installationCost ? parseFloat(installationCost) : undefined,
        terms_and_conditions: terms.trim() || undefined,
      });

      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create revision. Please check server validation.');
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
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white">Create Quotation Revision</h3>
              <p className="text-xs text-slate-400 font-mono">
                {quotation.quotation_number} (v{quotation.version} $\to$ v{quotation.version + 1})
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

        {/* Informational banner */}
        <div className="mx-6 mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2 text-amber-900 text-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold">Version History Preservation:</span> Current version ({quotation.version}) and all line items will be immutably snapshotted to audit history. The active quotation will return to <strong>DRAFT</strong> at Version {quotation.version + 1} for commercial adjustments.
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Reason for Revision <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Customer requested changing module brand from 540W Mono PERC to TOPCon, or capacity upgraded from 3kW to 5kW..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Installation & Commissioning Cost (₹)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={installationCost}
              onChange={(e) => setInstallationCost(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Terms & Conditions
            </label>
            <textarea
              rows={3}
              value={terms}
              onChange={(e) => setTerms(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 font-mono"
            />
          </div>

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
              disabled={submitting}
              className="px-5 py-2 rounded-xl text-xs font-bold text-slate-950 bg-amber-500 hover:bg-amber-400 shadow-sm transition flex items-center gap-1.5"
            >
              {submitting ? 'Creating Revision...' : `Snapshot & Increment to v${quotation.version + 1}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
