import React, { useState, useEffect } from 'react';
import { X, Clock, CheckCircle2, Phone, Mail, Calendar, MessageSquare, AlertCircle } from 'lucide-react';
import { createFollowup, completeFollowup, getEnquiries } from '../services/crmApi';

export default function FollowupModal({ isOpen, onClose, enquiry, followupToComplete, onSuccess }) {
  // Mode: 'schedule' or 'complete'
  const mode = followupToComplete ? 'complete' : 'schedule';

  const [formData, setFormData] = useState({
    enquiry_id: '',
    followup_type: 'CALL',
    scheduled_at: '',
    discussion_summary: '',
    next_followup_at: '',
    update_enquiry_status: '',
  });

  const [enquiries, setEnquiries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      if (mode === 'schedule') {
        // Load active enquiries if not pre-provided
        if (!enquiry) {
          getEnquiries({ limit: 50 }).then((res) => {
            if (res && res.data && res.data.items) {
              setEnquiries(res.data.items);
            }
          }).catch(console.error);
        }

        // Set default scheduled time to 2 hours from now
        const now = new Date();
        now.setHours(now.getHours() + 2);
        const isoString = now.toISOString().slice(0, 16);

        setFormData({
          enquiry_id: enquiry ? String(enquiry.id) : '',
          followup_type: 'CALL',
          scheduled_at: isoString,
          discussion_summary: '',
          next_followup_at: '',
          update_enquiry_status: '',
        });
      } else if (followupToComplete) {
        setFormData({
          enquiry_id: String(followupToComplete.enquiry_id),
          followup_type: followupToComplete.followup_type || 'CALL',
          scheduled_at: followupToComplete.scheduled_at ? followupToComplete.scheduled_at.slice(0, 16) : '',
          discussion_summary: followupToComplete.discussion_summary || '',
          next_followup_at: '',
          update_enquiry_status: '',
        });
      }
      setError(null);
    }
  }, [isOpen, enquiry, followupToComplete, mode]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (mode === 'schedule') {
        const payload = {
          enquiry_id: parseInt(formData.enquiry_id, 10),
          followup_type: formData.followup_type,
          scheduled_at: new Date(formData.scheduled_at).toISOString(),
          discussion_summary: formData.discussion_summary ? formData.discussion_summary.trim() : null,
          next_followup_at: formData.next_followup_at ? new Date(formData.next_followup_at).toISOString() : null,
        };
        await createFollowup(payload);
      } else {
        const payload = {
          discussion_summary: formData.discussion_summary.trim(),
          completed_at: new Date().toISOString(),
          status: 'COMPLETED',
          next_followup_at: formData.next_followup_at ? new Date(formData.next_followup_at).toISOString() : null,
          update_enquiry_status: formData.update_enquiry_status || null,
        };
        await completeFollowup(followupToComplete.id, payload);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save follow-up touchpoint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-500/10 text-amber-600 rounded-lg">
              {mode === 'schedule' ? <Clock className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {mode === 'schedule' ? 'Schedule Sales Touchpoint' : 'Log Follow-up & Discussion Notes'}
              </h3>
              <p className="text-xs text-slate-500">
                {mode === 'schedule' ? 'Plan a customer call, site visit, or message' : 'Record client feedback and update enquiry progression'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {mode === 'schedule' && (
            <>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Target Enquiry *</label>
                {enquiry ? (
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-900">
                    {enquiry.enquiry_number} — {enquiry.customer_name} ({enquiry.proposed_capacity_kw} kW {enquiry.system_type})
                  </div>
                ) : (
                  <select
                    name="enquiry_id"
                    required
                    value={formData.enquiry_id}
                    onChange={handleChange}
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  >
                    <option value="">-- Select Enquiry --</option>
                    {enquiries.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.enquiry_number} - {e.customer_name} ({e.status})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Touchpoint Channel *</label>
                  <select
                    name="followup_type"
                    value={formData.followup_type}
                    onChange={handleChange}
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 font-medium"
                  >
                    <option value="CALL">Phone Call</option>
                    <option value="WHATSAPP">WhatsApp</option>
                    <option value="VISIT">In-Person Visit</option>
                    <option value="EMAIL">Email</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Scheduled Date & Time *</label>
                  <input
                    type="datetime-local"
                    name="scheduled_at"
                    required
                    value={formData.scheduled_at}
                    onChange={handleChange}
                    className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              {mode === 'schedule' ? 'Touchpoint Agenda / Pre-Notes' : 'Discussion Summary & Customer Response *'}
            </label>
            <textarea
              name="discussion_summary"
              required={mode === 'complete'}
              rows={3}
              value={formData.discussion_summary}
              onChange={handleChange}
              placeholder={
                mode === 'schedule'
                  ? 'e.g. Call to discuss monthly consumption and roof structure...'
                  : 'e.g. Spoke with client. Confirmed 4 kW On-Grid requirement. Roof is shade-free; requested site inspection.'
              }
              className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {mode === 'complete' && (
            <div className="space-y-4 pt-2 border-t border-slate-100">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Update Enquiry Stage (Optional)
                </label>
                <select
                  name="update_enquiry_status"
                  value={formData.update_enquiry_status}
                  onChange={handleChange}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 font-semibold text-amber-800"
                >
                  <option value="">-- Keep Current Status --</option>
                  <option value="CONTACTED">CONTACTED (Followed up)</option>
                  <option value="SURVEY_REQUESTED">SURVEY_REQUESTED (Qualify for Site Survey)</option>
                  <option value="QUOTED">QUOTED (Quotation discussed)</option>
                  <option value="WON">WON (Deal agreed)</option>
                  <option value="LOST">LOST (Dropped)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Schedule Next Follow-up (Optional)</label>
                <input
                  type="datetime-local"
                  name="next_followup_at"
                  value={formData.next_followup_at}
                  onChange={handleChange}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`px-5 py-2 text-xs font-bold rounded-lg shadow-sm transition disabled:opacity-50 ${
                mode === 'schedule'
                  ? 'bg-amber-500 hover:bg-amber-400 text-slate-950'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white'
              }`}
            >
              {loading ? 'Processing...' : mode === 'schedule' ? 'Schedule Touchpoint' : 'Complete & Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
