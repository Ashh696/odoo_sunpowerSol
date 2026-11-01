import React, { useState, useEffect } from 'react';
import {
  X,
  Compass,
  Zap,
  MapPin,
  Calendar,
  User,
  ShieldCheck,
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Download,
  AlertCircle,
  FileCheck,
  Paperclip,
  Check,
} from 'lucide-react';
import { getSurvey, submitSurvey, uploadSurveyAttachment } from '../services/surveyApi';

export default function SurveyDetailModal({
  isOpen,
  onClose,
  surveyId,
  currentUser,
  onOpenEditObservations,
  onOpenApprovalModal,
  onRefreshList,
}) {
  const [survey, setSurvey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Attachment upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Submit survey confirmation state
  const [confirmSubmitOpen, setConfirmSubmitOpen] = useState(false);
  const [submittingSurvey, setSubmittingSurvey] = useState(false);

  const fetchDetail = async () => {
    if (!surveyId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getSurvey(surveyId);
      if (res && res.data) {
        setSurvey(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load survey details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && surveyId) {
      fetchDetail();
      setSelectedFile(null);
      setUploadError(null);
      setUploadSuccess(false);
      setConfirmSubmitOpen(false);
    }
  }, [isOpen, surveyId]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    // Client-side file size check (10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setUploadError('File size exceeds 10 MB limit.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);
    try {
      await uploadSurveyAttachment(survey.id, selectedFile);
      setUploadSuccess(true);
      setSelectedFile(null);
      // Refresh details to display new attachment
      fetchDetail();
      if (onRefreshList) onRefreshList();
    } catch (err) {
      setUploadError(err.message || 'Failed to upload attachment');
    } finally {
      setUploading(false);
    }
  };

  const handleConfirmSubmit = async () => {
    setSubmittingSurvey(true);
    setError(null);
    try {
      await submitSurvey(survey.id);
      setConfirmSubmitOpen(false);
      fetchDetail();
      if (onRefreshList) onRefreshList();
    } catch (err) {
      setError(err.message || 'Failed to submit survey');
      setConfirmSubmitOpen(false);
    } finally {
      setSubmittingSurvey(false);
    }
  };

  if (!isOpen) return null;

  // Role permissions helpers
  const roleSlug = currentUser?.role?.slug || '';
  const isSuperAdmin = roleSlug === 'SUPER_ADMIN';
  const isDirector = roleSlug === 'DIRECTOR';
  const isTechManager = roleSlug === 'TECHNICAL_MANAGER';
  const isTechnician = roleSlug === 'FIELD_TECHNICIAN';

  // Can review if TM, Director, or Admin and survey is SUBMITTED or UNDER_REVIEW
  const canReview = (isSuperAdmin || isDirector || isTechManager) && (survey?.status === 'SUBMITTED' || survey?.status === 'UNDER_REVIEW');

  // Can edit observations if DRAFT or CORRECTION_REQUESTED and (technician or manager/admin)
  const isEditable = survey?.status === 'DRAFT' || survey?.status === 'CORRECTION_REQUESTED';
  const canEdit = isEditable && (isSuperAdmin || isDirector || isTechManager || isTechnician);

  // Can submit if DRAFT or CORRECTION_REQUESTED and assigned technician or admin
  const canSubmit = isEditable && (isTechnician || isSuperAdmin);

  const statusBadge = (st) => {
    switch (st) {
      case 'DRAFT':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">Draft</span>;
      case 'SUBMITTED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">Submitted</span>;
      case 'UNDER_REVIEW':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">Under Review</span>;
      case 'APPROVED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Approved</span>;
      case 'REJECTED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> Rejected</span>;
      case 'CORRECTION_REQUESTED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Corrections Requested</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">{st}</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-bold">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base tracking-tight font-mono">{survey?.survey_number || 'Loading...'}</h3>
                {survey && statusBadge(survey.status)}
              </div>
              <p className="text-xs text-slate-400">
                Enquiry: <span className="font-mono text-amber-400">{survey?.enquiry_number}</span> • Customer: {survey?.customer_name}
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

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm flex flex-col items-center gap-2">
              <Clock className="w-6 h-6 animate-spin text-amber-500" />
              <span>Loading technical survey details...</span>
            </div>
          ) : survey ? (
            <>
              {/* Revision / Correction Alert if applicable */}
              {survey.status === 'CORRECTION_REQUESTED' && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-sm space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-amber-950">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    <span>Corrections Requested by Technical Reviewer</span>
                  </div>
                  <p className="text-xs text-amber-800">
                    {survey.latest_approval_comments || 'Please revise physical roof measurements or shading profile and resubmit.'}
                  </p>
                </div>
              )}

              {/* Grid 1: Customer & Site Assignment */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Customer Information Card */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-slate-600">
                    <User className="w-3.5 h-3.5 text-amber-600" /> Customer & Site Location
                  </h4>
                  <div className="text-xs space-y-1 text-slate-700">
                    <p><span className="font-semibold text-slate-900">Name:</span> {survey.customer_name || 'N/A'}</p>
                    <p><span className="font-semibold text-slate-900">Phone:</span> {survey.customer_phone || 'N/A'}</p>
                    <p><span className="font-semibold text-slate-900">Address:</span> {survey.customer_address || 'N/A'}</p>
                    <p><span className="font-semibold text-slate-900">City / State:</span> {survey.customer_city || 'N/A'}</p>
                  </div>
                </div>

                {/* Survey Logistics Card */}
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-slate-600">
                    <Calendar className="w-3.5 h-3.5 text-amber-600" /> Logistics & Assignment
                  </h4>
                  <div className="text-xs space-y-1 text-slate-700">
                    <p><span className="font-semibold text-slate-900">Assigned Surveyor:</span> {survey.surveyor_name || survey.surveyor_code} ({survey.surveyor_code})</p>
                    <p><span className="font-semibold text-slate-900">Scheduled Visit:</span> {survey.scheduled_at ? new Date(survey.scheduled_at).toLocaleString() : 'N/A'}</p>
                    <p><span className="font-semibold text-slate-900">Conducted At:</span> {survey.conducted_at ? new Date(survey.conducted_at).toLocaleString() : 'Not Yet Recorded'}</p>
                    <p><span className="font-semibold text-slate-900">Proposed Capacity:</span> {survey.proposed_capacity_kw ? `${survey.proposed_capacity_kw} kW` : 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Grid 2: Physical & Technical Measurements */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-amber-600">
                  <Compass className="w-4 h-4" /> Technical Rooftop Specifications
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Total Roof Area</span>
                    <span className="text-sm font-bold text-slate-900">{survey.roof_area_sqft !== null ? `${survey.roof_area_sqft} sq ft` : '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Shadow-Free Area</span>
                    <span className="text-sm font-bold text-emerald-700">{survey.shadow_free_area_sqft !== null ? `${survey.shadow_free_area_sqft} sq ft` : '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Roof Orientation</span>
                    <span className="text-sm font-bold text-slate-900">{survey.roof_orientation || '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Roof Pitch / Tilt</span>
                    <span className="text-sm font-bold text-slate-900">{survey.roof_tilt_degrees !== null ? `${survey.roof_tilt_degrees}°` : '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Structure Type</span>
                    <span className="text-sm font-bold text-slate-900">{survey.roof_structure_type || '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Electrical Phase</span>
                    <span className="text-sm font-bold text-slate-900">{survey.existing_phase || '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Sanctioned Load</span>
                    <span className="text-sm font-bold text-slate-900">{survey.sanctioned_load_kw !== null ? `${survey.sanctioned_load_kw} kW` : '—'}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <span className="text-slate-500 block mb-0.5">Feasibility</span>
                    <span className={`text-sm font-bold ${survey.technical_feasibility === 'FEASIBLE' ? 'text-emerald-700' : survey.technical_feasibility === 'CONDITIONAL' ? 'text-amber-700' : 'text-rose-700'}`}>
                      {survey.technical_feasibility}
                    </span>
                  </div>
                </div>

                {/* GPS and Remarks */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs border-t border-slate-100">
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">GPS Coordinates</span>
                    <span className="font-mono text-slate-800">
                      {survey.gps_latitude && survey.gps_longitude ? `${survey.gps_latitude}, ${survey.gps_longitude}` : 'Not Captured'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">Surveyor Notes & Observations</span>
                    <p className="text-slate-700 whitespace-pre-wrap">{survey.remarks || 'No remarks recorded.'}</p>
                  </div>
                </div>
              </div>

              {/* Section 3: Attachments Gallery */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-amber-600">
                    <Paperclip className="w-4 h-4" /> Site Photographs & Technical Documents ({survey.attachments?.length || 0})
                  </h4>
                </div>

                {/* Inline Upload Form (Only for editable surveys) */}
                {isEditable && (
                  <form onSubmit={handleFileUpload} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                    <span className="text-xs font-semibold text-slate-700 block">Upload Site Image or Drawing (JPEG, PNG, WEBP, PDF &le; 10MB)</span>
                    <div className="flex flex-col sm:flex-row items-center gap-2">
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp,application/pdf"
                        onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                        className="text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-200 file:text-slate-700 hover:file:bg-slate-300 w-full sm:w-auto"
                      />
                      <button
                        type="submit"
                        disabled={!selectedFile || uploading}
                        className="w-full sm:w-auto px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-40"
                      >
                        {uploading ? (
                          <>
                            <Clock className="w-3.5 h-3.5 animate-spin" />
                            <span>Uploading...</span>
                          </>
                        ) : (
                          <>
                            <UploadCloud className="w-3.5 h-3.5" />
                            <span>Upload File</span>
                          </>
                        )}
                      </button>
                    </div>
                    {uploadError && <p className="text-xs text-rose-600 mt-1">{uploadError}</p>}
                    {uploadSuccess && <p className="text-xs text-emerald-600 mt-1">Attachment uploaded successfully!</p>}
                  </form>
                )}

                {/* Attachment list */}
                {survey.attachments && survey.attachments.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {survey.attachments.map((att) => (
                      <div key={att.id} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                        <div className="overflow-hidden pr-2">
                          <p className="font-semibold text-slate-900 truncate">{att.file_name}</p>
                          <p className="text-[10px] text-slate-400">
                            {(att.file_size_bytes / 1024).toFixed(1)} KB • By {att.uploader_name || 'Staff'} • {new Date(att.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="shrink-0 px-2 py-1 rounded bg-slate-200 text-slate-700 text-[10px] font-mono">
                          {att.mime_type.includes('image') ? 'IMAGE' : 'PDF'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No photographs or technical files attached yet.</p>
                )}
              </div>

              {/* Section 4: Technical Review & Revision History */}
              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 text-amber-600">
                  <ShieldCheck className="w-4 h-4" /> Technical Approval & Revision History
                </h4>

                {survey.approvals && survey.approvals.length > 0 ? (
                  <div className="space-y-2.5">
                    {survey.approvals.map((app) => (
                      <div key={app.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">Revision #{app.revision_number}</span>
                            {statusBadge(app.action)}
                          </div>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {new Date(app.reviewed_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-slate-700 font-medium whitespace-pre-wrap">{app.comments}</p>
                        <p className="text-[10px] text-slate-400">
                          Reviewed by: <span className="font-semibold text-slate-600">{app.reviewer_name || 'Technical Reviewer'}</span> ({app.reviewer_role || 'Manager'})
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No review decisions recorded yet. Pending surveyor completion and submission.</p>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-200 transition"
          >
            Close
          </button>

          <div className="flex items-center gap-2.5">
            {/* Record / Edit Observations Button */}
            {canEdit && (
              <button
                onClick={() => {
                  onClose();
                  if (onOpenEditObservations) onOpenEditObservations(survey);
                }}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white transition flex items-center gap-1.5 shadow-sm"
              >
                <Compass className="w-4 h-4" />
                <span>Record / Edit Observations</span>
              </button>
            )}

            {/* Submit for Review Button */}
            {canSubmit && (
              <button
                onClick={() => setConfirmSubmitOpen(true)}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition flex items-center gap-1.5 shadow-sm"
              >
                <Check className="w-4 h-4" />
                <span>Submit for Review</span>
              </button>
            )}

            {/* Technical Review Button */}
            {canReview && (
              <button
                onClick={() => {
                  onClose();
                  if (onOpenApprovalModal) onOpenApprovalModal(survey);
                }}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 shadow-sm"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Technical Review</span>
              </button>
            )}
          </div>
        </div>

        {/* Confirmation Dialog for Submission */}
        {confirmSubmitOpen && (
          <div className="fixed inset-0 z-60 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in zoom-in-95">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 shrink-0">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-base text-slate-900">Submit Survey for Review?</h4>
                  <p className="text-xs text-slate-500">This will lock observation editing and notify the Technical Manager for formal engineering review.</p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setConfirmSubmitOpen(false)}
                  disabled={submittingSurvey}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmSubmit}
                  disabled={submittingSurvey}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 flex items-center gap-1.5 shadow-sm"
                >
                  {submittingSurvey ? (
                    <>
                      <Clock className="w-3.5 h-3.5 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Yes, Submit Survey</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
