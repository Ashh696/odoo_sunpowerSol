import React, { useState } from 'react';
import {
  X,
  Layers,
  Calendar,
  MapPin,
  User,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Briefcase,
  Plus,
  Lock,
  Globe,
  Sliders,
  CheckSquare
} from 'lucide-react';
import { updateProject, addProjectNote } from '../services/projectApi';
import ProjectBOMViewModal from './ProjectBOMViewModal';

const STATUS_COLORS = {
  INITIATED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  PROCUREMENT: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  DISPATCHED: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  INSTALLATION: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  COMMISSIONED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  HANDED_OVER: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  ON_HOLD: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

const VALID_STATUSES = [
  'INITIATED',
  'PROCUREMENT',
  'DISPATCHED',
  'INSTALLATION',
  'COMMISSIONED',
  'HANDED_OVER',
  'ON_HOLD',
  'CANCELLED',
];

export default function ProjectDetailModal({
  project,
  onClose,
  onRefresh,
  currentRole = 'SUPER_ADMIN',
  onOpenOrder = null,
}) {
  const [activeTab, setActiveTab] = useState('bom');
  const [submittingNote, setSubmittingNote] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [showBOMEditModal, setShowBOMEditModal] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New Note State
  const [noteType, setNoteType] = useState('GENERAL');
  const [noteContent, setNoteContent] = useState('');
  const [noteInternal, setNoteInternal] = useState(true);

  if (!project) return null;

  const canManageProject =
    currentRole === 'SUPER_ADMIN' ||
    currentRole === 'TECHNICAL_MANAGER' ||
    currentRole === 'Technical / Installation Manager' ||
    currentRole === 'Super Admin';

  const isCustomer =
    currentRole === 'CUSTOMER' ||
    currentRole === 'Customer';

  const handleStatusChange = async (newStatus) => {
    setError(null);
    setSuccessMsg(null);
    setUpdatingStatus(true);
    try {
      const res = await updateProject(project.id, { status: newStatus });
      setSuccessMsg(`Project status updated to ${newStatus}`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to update project status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!noteContent.trim()) return;

    setError(null);
    setSuccessMsg(null);
    setSubmittingNote(true);

    try {
      await addProjectNote(project.id, {
        note_type: noteType,
        content: noteContent.trim(),
        is_internal: isCustomer ? false : noteInternal,
      });

      setSuccessMsg('Note added successfully');
      setNoteContent('');
      if (onRefresh) onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to add project note');
    } finally {
      setSubmittingNote(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-5xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden my-6">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h3 className="text-lg font-bold text-white tracking-tight">{project.project_code}</h3>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${
                    STATUS_COLORS[project.status] || 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {project.status}
                </span>
                <span className="text-xs text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                  {project.system_capacity_kw} kW {project.system_type}
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                <span>{project.site_address}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {canManageProject && (
              <select
                disabled={updatingStatus}
                value={project.status}
                onChange={(e) => handleStatusChange(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-2.5 py-1.5 focus:ring-1 focus:ring-amber-500"
              >
                {VALID_STATUSES.map((st) => (
                  <option key={st} value={st}>
                    Update: {st}
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition p-1.5 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
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

          {/* Quick Context Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Timeline */}
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3.5 text-xs">
              <div className="flex items-center space-x-1.5 text-slate-400 font-semibold mb-2">
                <Calendar className="w-4 h-4 text-blue-400" />
                <span>Project Timeline</span>
              </div>
              <p className="text-slate-300">Start: <span className="text-white font-medium">{project.planned_start_date}</span></p>
              <p className="text-slate-300">Target Completion: <span className="text-white font-medium">{project.planned_completion_date}</span></p>
              {project.actual_completion_date && (
                <p className="text-emerald-400 font-medium">Completed: {project.actual_completion_date}</p>
              )}
            </div>

            {/* Customer */}
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3.5 text-xs">
              <div className="flex items-center space-x-1.5 text-slate-400 font-semibold mb-2">
                <User className="w-4 h-4 text-amber-400" />
                <span>Customer</span>
              </div>
              <p className="text-white font-semibold">{project.customer?.full_name || 'N/A'}</p>
              <p className="text-slate-400">{project.customer?.phone || '—'}</p>
              <p className="text-slate-400">{project.customer?.city || 'Pune'}, {project.customer?.state || 'Maharashtra'}</p>
            </div>

            {/* Order Reference */}
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3.5 text-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-1.5 text-slate-400 font-semibold mb-2">
                  <Briefcase className="w-4 h-4 text-emerald-400" />
                  <span>Order Contract</span>
                </div>
                <p className="text-white font-semibold">{project.order?.order_number || 'N/A'}</p>
                <p className="text-slate-400">
                  Total: ₹{project.order?.total_amount ? parseFloat(project.order.total_amount).toLocaleString('en-IN') : '—'}
                </p>
              </div>
              {onOpenOrder && project.order && (
                <button
                  onClick={() => onOpenOrder(project.order.id)}
                  className="mt-2 text-xs text-blue-400 hover:text-blue-300 font-semibold text-left transition"
                >
                  View Order Details →
                </button>
              )}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-4">
            <button
              onClick={() => setActiveTab('bom')}
              className={`pb-2.5 text-xs font-bold transition flex items-center gap-1.5 border-b-2 ${
                activeTab === 'bom'
                  ? 'border-amber-500 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sliders className="w-4 h-4" />
              <span>Project BOM ({project.bom_items?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab('notes')}
              className={`pb-2.5 text-xs font-bold transition flex items-center gap-1.5 border-b-2 ${
                activeTab === 'notes'
                  ? 'border-amber-500 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Globe className="w-4 h-4" />
              <span>Technical Notes ({project.notes?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`pb-2.5 text-xs font-bold transition flex items-center gap-1.5 border-b-2 ${
                activeTab === 'tasks'
                  ? 'border-amber-500 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckSquare className="w-4 h-4" />
              <span>Milestones & Setup Tasks ({project.tasks?.length || 0})</span>
            </button>
          </div>

          {/* Tab 1: Project BOM */}
          {activeTab === 'bom' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">Bill of Materials</h4>
                  <p className="text-xs text-slate-400">
                    Base BOM initialized from accepted quotation. Adjustable via Technical Management.
                  </p>
                </div>
                {canManageProject && (
                  <button
                    onClick={() => setShowBOMEditModal(true)}
                    className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
                  >
                    <Sliders className="w-3.5 h-3.5" />
                    <span>Manage / Adjust BOM</span>
                  </button>
                )}
              </div>

              {project.bom_items && project.bom_items.length > 0 ? (
                <div className="overflow-x-auto border border-slate-800 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400">
                      <tr>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Product Name</th>
                        <th className="py-2.5 px-3 text-right">Planned Qty</th>
                        <th className="py-2.5 px-3 text-right">Unit Snapshot</th>
                        <th className="py-2.5 px-3 text-right">Total Planned</th>
                        <th className="py-2.5 px-3 text-center">Fulfillment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {project.bom_items.map((it) => (
                        <tr key={it.id} className="hover:bg-slate-900/40">
                          <td className="py-2.5 px-3 font-medium text-amber-400">{it.item_category}</td>
                          <td className="py-2.5 px-3 text-white">
                            <span className="font-semibold block">{it.product_name}</span>
                            <span className="text-[10px] text-slate-400 font-mono">{it.product_code}</span>
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-white">
                            {parseFloat(it.planned_quantity)} {it.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-300">
                            ₹{parseFloat(it.unit_cost_snapshot).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                            ₹{parseFloat(it.total_planned_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-center text-[10px] text-slate-400">
                            Alloc: {parseFloat(it.allocated_quantity)} • Disp: {parseFloat(it.dispatched_quantity)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic py-3">No BOM component lines loaded for this project.</p>
              )}
            </div>
          )}

          {/* Tab 2: Technical Notes */}
          {activeTab === 'notes' && (
            <div className="space-y-4">
              {/* Add Note Form */}
              <form onSubmit={handleAddNote} className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">Add Site / Technical Note</span>
                  {!isCustomer && (
                    <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={noteInternal}
                        onChange={(e) => setNoteInternal(e.target.checked)}
                        className="rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
                      />
                      <span className="flex items-center gap-1">
                        {noteInternal ? <Lock className="w-3 h-3 text-amber-400" /> : <Globe className="w-3 h-3 text-slate-400" />}
                        <span>Internal Staff Only</span>
                      </span>
                    </label>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1">Note Type</label>
                    <select
                      value={noteType}
                      onChange={(e) => setNoteType(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                    >
                      <option value="GENERAL">General</option>
                      <option value="TECHNICAL">Technical</option>
                      <option value="SITE_ISSUE">Site Issue</option>
                      <option value="CUSTOMER_REQUEST">Customer Request</option>
                      <option value="SAFETY">Safety</option>
                    </select>
                  </div>
                  <div className="md:col-span-3">
                    <label className="block text-slate-400 mb-1">Note Content *</label>
                    <input
                      type="text"
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      placeholder="Add observation, technical remark, or milestone notes..."
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-white"
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={submittingNote}
                    className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold rounded-lg text-xs transition flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{submittingNote ? 'Saving...' : 'Post Note'}</span>
                  </button>
                </div>
              </form>

              {/* Notes List */}
              <div className="space-y-2.5">
                {project.notes && project.notes.length > 0 ? (
                  project.notes.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 rounded-lg border text-xs ${
                        n.is_internal
                          ? 'bg-amber-500/5 border-amber-500/20'
                          : 'bg-slate-950/40 border-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-white uppercase text-[10px] bg-slate-800 px-2 py-0.5 rounded">
                            {n.note_type}
                          </span>
                          {n.is_internal ? (
                            <span className="flex items-center gap-1 text-[10px] text-amber-400 font-medium">
                              <Lock className="w-3 h-3" /> Internal Staff
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
                              <Globe className="w-3 h-3" /> Visible to Customer
                            </span>
                          )}
                        </div>
                        <span className="text-slate-400 text-[10px]">
                          {new Date(n.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-slate-200 mt-1">{n.content}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic py-2">No notes added to this project yet.</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 3: Tasks */}
          {activeTab === 'tasks' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">Automated Execution Tasks</h4>
              {project.tasks && project.tasks.length > 0 ? (
                <div className="divide-y divide-slate-800/80 border border-slate-800 rounded-lg overflow-hidden">
                  {project.tasks.map((t) => (
                    <div key={t.id} className="p-3 bg-slate-950/50 flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-[10px] text-slate-400">{t.task_code}</span>
                          <span className="font-semibold text-white">{t.title}</span>
                          <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-300 rounded font-medium">
                            {t.task_type}
                          </span>
                        </div>
                        <p className="text-slate-400 text-[10px] mt-0.5">Priority: {t.priority} • Due: {t.due_date || '—'}</p>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {t.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic py-2">No tasks assigned to this project.</p>
              )}
            </div>
          )}
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

      {/* Embedded Project BOM Edit Modal */}
      {showBOMEditModal && (
        <ProjectBOMViewModal
          projectId={project.id}
          projectCode={project.project_code}
          onClose={() => {
            setShowBOMEditModal(false);
            if (onRefresh) onRefresh();
          }}
          userRole={currentRole}
        />
      )}
    </div>
  );
}
