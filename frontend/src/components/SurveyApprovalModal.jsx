import React, { useState, useEffect } from 'react';
import { X, ShieldCheck, CheckCircle2, AlertTriangle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { reviewSurvey } from '../services/surveyApi';

export default function SurveyApprovalModal({ isOpen, onClose, onSuccess, survey }) {
  const [action, setAction] = useState('APPROVED'); // APPROVED, CORRECTION_REQUESTED, REJECTED
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && survey) {
      setError(null);
      setAction('APPROVED');
      setComments('');
    }
  }, [isOpen, survey]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const cleanComments = comments.trim();
    if (!cleanComments) {
      setError('Please provide review comments.');
      return;
    }

    if ((action === 'REJECTED' || action === 'CORRECTION_REQUESTED') && cleanComments.length < 5) {
      setError(`Detailed comments (at least 5 characters) are required for decision '${action}'.`);
      return;
    }

    setSubmitting(true);
    try {
      await reviewSurvey(survey.id, {
        action,
        comments: cleanComments,
      });

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit technical approval decision');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen || !survey) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-amber-500" />
            <div>
              <h3 className="font-bold text-base tracking-tight">Technical Approval Review</h3>
              <p className="text-xs text-amber-400 font-mono">{survey.survey_number}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Survey Summary Banner */}
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-3 flex items-center justify-between text-xs">
          <div>
            <span className="text-slate-500">Surveyor:</span>{' '}
            <span className="font-semibold text-slate-800">{survey.surveyor_name || survey.surveyor_code}</span>
          </div>
          <div>
            <span className="text-slate-500">Usable Area:</span>{' '}
            <span className="font-semibold text-slate-800">{survey.shadow_free_area_sqft || 0} sq ft</span>
          </div>
          <div>
            <span className="text-slate-500">Feasibility:</span>{' '}
            <span className="font-semibold text-emerald-700">{survey.technical_feasibility}</span>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Decision Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Review Decision <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setAction('APPROVED')}
                className={`py-3 px-2 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                  action === 'APPROVED'
                    ? 'bg-emerald-50 border-emerald-500 text-emerald-900 shadow-sm ring-2 ring-emerald-500/20'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <CheckCircle2 className={`w-5 h-5 ${action === 'APPROVED' ? 'text-emerald-600' : 'text-slate-400'}`} />
                <span className="text-xs font-bold">Approve</span>
              </button>

              <button
                type="button"
                onClick={() => setAction('CORRECTION_REQUESTED')}
                className={`py-3 px-2 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                  action === 'CORRECTION_REQUESTED'
                    ? 'bg-amber-50 border-amber-500 text-amber-900 shadow-sm ring-2 ring-amber-500/20'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <AlertTriangle className={`w-5 h-5 ${action === 'CORRECTION_REQUESTED' ? 'text-amber-600' : 'text-slate-400'}`} />
                <span className="text-xs font-bold">Corrections</span>
              </button>

              <button
                type="button"
                onClick={() => setAction('REJECTED')}
                className={`py-3 px-2 rounded-xl border text-center transition flex flex-col items-center gap-1.5 ${
                  action === 'REJECTED'
                    ? 'bg-rose-50 border-rose-500 text-rose-900 shadow-sm ring-2 ring-rose-500/20'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <XCircle className={`w-5 h-5 ${action === 'REJECTED' ? 'text-rose-600' : 'text-slate-400'}`} />
                <span className="text-xs font-bold">Reject</span>
              </button>
            </div>
          </div>

          {/* Decision Notes */}
          {action === 'APPROVED' && (
            <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg text-xs text-emerald-800">
              Approving this survey verifies the rooftop feasibility and structural measurements. The parent enquiry will remain at <span className="font-semibold font-mono">SURVEY_REQUESTED</span> awaiting quotation preparation in Phase 5.
            </div>
          )}
          {action === 'CORRECTION_REQUESTED' && (
            <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs text-amber-800">
              The survey will be returned to the assigned field surveyor with your feedback. They can update measurements and resubmit for review.
            </div>
          )}
          {action === 'REJECTED' && (
            <div className="p-3 bg-rose-50/70 border border-rose-200 rounded-lg text-xs text-rose-800">
              Rejecting this survey permanently marks this site inspection as not feasible. It cannot be silently reopened or resubmitted.
            </div>
          )}

          {/* Comments */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Reviewer Engineering Comments <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={4}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder={
                action === 'APPROVED'
                  ? 'e.g. Shading analysis confirmed, 3.5 kW DC layout feasible with single-phase string inverter...'
                  : 'Specify exact reasons, missing information, or structural concerns...'
              }
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              required
            />
            <p className="text-[11px] text-slate-400 mt-1">
              {comments.length} characters • Minimum 5 characters required for corrections or rejection.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`px-5 py-2 rounded-lg text-sm font-bold text-white transition shadow-sm flex items-center gap-1.5 disabled:opacity-50 ${
                action === 'APPROVED'
                  ? 'bg-emerald-600 hover:bg-emerald-500'
                  : action === 'CORRECTION_REQUESTED'
                  ? 'bg-amber-600 hover:bg-amber-500'
                  : 'bg-rose-600 hover:bg-rose-500'
              }`}
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Submitting Review...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Record Decision</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
