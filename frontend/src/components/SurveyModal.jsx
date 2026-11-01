import React, { useState, useEffect } from 'react';
import { X, Calendar, User, FileText, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { scheduleSurvey, getActiveSurveyors, getEligibleEnquiries } from '../services/surveyApi';

export default function SurveyModal({ isOpen, onClose, onSuccess, preselectedEnquiry = null }) {
  const [enquiries, setEnquiries] = useState([]);
  const [surveyors, setSurveyors] = useState([]);
  const [loadingLookups, setLoadingLookups] = useState(false);

  const [enquiryId, setEnquiryId] = useState('');
  const [surveyorId, setSurveyorId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [remarks, setRemarks] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      // Default scheduled date to tomorrow at 10:00 AM
      const tmrw = new Date();
      tmrw.setDate(tmrw.getDate() + 1);
      tmrw.setHours(10, 0, 0, 0);
      const isoLocal = new Date(tmrw.getTime() - tmrw.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
      setScheduledAt(isoLocal);

      if (preselectedEnquiry) {
        setEnquiryId(String(preselectedEnquiry.id));
      } else {
        setEnquiryId('');
      }
      setSurveyorId('');
      setRemarks('');

      loadLookups();
    }
  }, [isOpen, preselectedEnquiry]);

  const loadLookups = async () => {
    setLoadingLookups(true);
    try {
      const [empRes, enqRes] = await Promise.all([
        getActiveSurveyors(),
        getEligibleEnquiries({ limit: 100 }),
      ]);
      if (empRes && empRes.data) {
        setSurveyors(empRes.data.items || []);
      }
      if (enqRes && enqRes.data) {
        // Filter out CANCELLED / LOST enquiries
        const eligible = (enqRes.data.items || []).filter(
          (e) => e.status !== 'CANCELLED' && e.status !== 'LOST'
        );
        setEnquiries(eligible);
      }
    } catch (err) {
      setError('Failed to load surveyors or enquiries: ' + (err.message || 'Error'));
    } finally {
      setLoadingLookups(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!enquiryId) {
      setError('Please select an eligible enquiry.');
      return;
    }
    if (!surveyorId) {
      setError('Please assign a surveyor employee.');
      return;
    }
    if (!scheduledAt) {
      setError('Please select a scheduled date and time.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        enquiry_id: parseInt(enquiryId, 10),
        surveyor_id: parseInt(surveyorId, 10),
        scheduled_at: new Date(scheduledAt).toISOString(),
        remarks: remarks.trim() || undefined,
      };

      await scheduleSurvey(payload);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to schedule site survey');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-amber-500" />
            <h3 className="font-bold text-base tracking-tight">Schedule Site Survey</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Enquiry Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Select Enquiry <span className="text-rose-500">*</span>
            </label>
            {preselectedEnquiry ? (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm">
                <span className="font-mono font-bold text-slate-900">{preselectedEnquiry.enquiry_number}</span>
                <span className="text-slate-500 ml-2">({preselectedEnquiry.customer_name || 'Customer'} • {preselectedEnquiry.proposed_capacity_kw} kW)</span>
              </div>
            ) : (
              <select
                value={enquiryId}
                onChange={(e) => setEnquiryId(e.target.value)}
                disabled={loadingLookups}
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                required
              >
                <option value="">-- Choose an Enquiry --</option>
                {enquiries.map((enq) => (
                  <option key={enq.id} value={enq.id}>
                    {enq.enquiry_number} - {enq.customer_name} ({enq.proposed_capacity_kw} kW) [{enq.status}]
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Surveyor Assignment */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Assign Surveyor Employee <span className="text-rose-500">*</span>
            </label>
            <select
              value={surveyorId}
              onChange={(e) => setSurveyorId(e.target.value)}
              disabled={loadingLookups}
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              required
            >
              <option value="">-- Choose Field Surveyor --</option>
              {surveyors.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.user?.full_name || emp.employee_code} ({emp.employee_code} - {emp.designation})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              Active technicians and engineering personnel available for field dispatch.
            </p>
          </div>

          {/* Scheduled Date & Time */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Scheduled Date & Time <span className="text-rose-500">*</span>
            </label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              required
            />
          </div>

          {/* Remarks */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Site Survey Notes / Instructions
            </label>
            <textarea
              rows={3}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="e.g. Roof access via terrace door, customer requested afternoon inspection..."
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
            />
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
              disabled={submitting || loadingLookups}
              className="px-5 py-2 rounded-lg text-sm font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Scheduling...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Schedule</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
