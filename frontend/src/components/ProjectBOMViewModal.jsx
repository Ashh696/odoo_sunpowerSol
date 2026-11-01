import React, { useState, useEffect } from 'react';
import {
  X,
  Briefcase,
  Layers,
  Search,
  AlertCircle,
  CheckCircle2,
  Edit2,
  Check,
  Zap,
  Info,
  DollarSign,
  Package,
} from 'lucide-react';
import {
  getProjectBom,
  generateProjectBom,
  updateProjectBomItemQuantity,
  getBomTemplates,
} from '../services/bomApi';

export default function ProjectBOMViewModal({
  isOpen,
  onClose,
  canWrite = false,
  initialProjectId = '',
}) {
  const [projectIdInput, setProjectIdInput] = useState(initialProjectId ? String(initialProjectId) : '');
  const [activeProjectId, setActiveProjectId] = useState(initialProjectId ? String(initialProjectId) : '');

  const [projectBomData, setProjectBomData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Template selection for generation if empty
  const [activeTemplates, setActiveTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState(null);

  // Planned quantity edit state
  const [editingItemId, setEditingItemId] = useState(null);
  const [editPlannedQty, setEditPlannedQty] = useState('');
  const [updatingQty, setUpdatingQty] = useState(false);
  const [updateError, setUpdateError] = useState(null);

  const fetchProjectBom = async (projId) => {
    if (!projId) return;
    setLoading(true);
    setError(null);
    setGenerateError(null);
    setUpdateError(null);
    try {
      const res = await getProjectBom(projId);
      setProjectBomData(res.data);
      setActiveProjectId(String(projId));

      // If project has no items, load active templates for generation
      if (res.data?.items?.length === 0) {
        loadActiveTemplates(res.data.system_type, res.data.system_capacity_kw);
      }
    } catch (err) {
      setProjectBomData(null);
      setError(err.message || `Failed to load BOM for Project ID ${projId}`);
    } finally {
      setLoading(false);
    }
  };

  const loadActiveTemplates = async (projSysType, projCap) => {
    try {
      const res = await getBomTemplates({ is_active: true, limit: 100 });
      const tpls = res?.data?.items || [];
      setActiveTemplates(tpls);

      // Pre-select exact match if available
      if (projSysType && projCap) {
        const exactMatch = tpls.find(
          (t) =>
            t.system_type.toUpperCase() === projSysType.toUpperCase() &&
            parseFloat(t.capacity_kw) === parseFloat(projCap)
        );
        if (exactMatch) setSelectedTemplateId(String(exactMatch.id));
      }
    } catch (err) {
      console.error('Failed to load active templates for BOM generation:', err);
    }
  };

  useEffect(() => {
    if (isOpen) {
      if (initialProjectId) {
        setProjectIdInput(String(initialProjectId));
        fetchProjectBom(initialProjectId);
      } else {
        setProjectBomData(null);
        setError(null);
      }
      setEditingItemId(null);
    }
  }, [isOpen, initialProjectId]);

  const handleSearchProject = (e) => {
    e.preventDefault();
    const cleanId = projectIdInput.trim();
    if (!cleanId) return;
    fetchProjectBom(cleanId);
  };

  // Generate project BOM from selected template
  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!selectedTemplateId) {
      setGenerateError('Please select a compatible master BOM template.');
      return;
    }

    setGenerating(true);
    setGenerateError(null);
    try {
      const res = await generateProjectBom(activeProjectId, parseInt(selectedTemplateId, 10));
      setProjectBomData(res.data);
    } catch (err) {
      setGenerateError(err.message || 'Failed to generate project BOM.');
    } finally {
      setGenerating(false);
    }
  };

  // Adjust planned quantity
  const handleStartEditQty = (item) => {
    setEditingItemId(item.id);
    setEditPlannedQty(String(item.planned_quantity));
    setUpdateError(null);
  };

  const handleSaveQty = async (item) => {
    const newQty = parseFloat(editPlannedQty);
    if (isNaN(newQty) || newQty < 0) {
      setUpdateError('Planned quantity cannot be negative.');
      return;
    }

    if (newQty < item.allocated_quantity) {
      setUpdateError(
        `Planned quantity (${newQty}) cannot be less than already allocated stock (${item.allocated_quantity}).`
      );
      return;
    }

    setUpdatingQty(true);
    setUpdateError(null);
    try {
      await updateProjectBomItemQuantity(activeProjectId, item.id, newQty);
      await fetchProjectBom(activeProjectId);
      setEditingItemId(null);
    } catch (err) {
      setUpdateError(err.message || 'Failed to update planned quantity.');
    } finally {
      setUpdatingQty(false);
    }
  };

  if (!isOpen) return null;

  const items = projectBomData?.items || [];
  const hasItems = items.length > 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-4xl w-full overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="bg-slate-900 px-6 py-4 flex items-center justify-between text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight">Project BOM Inspector & Sizing</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Generate and monitor project bill of materials, stock allocation, and cost snapshot
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Project ID Input Form */}
          <form
            onSubmit={handleSearchProject}
            className="bg-slate-50 border border-slate-200 p-4 rounded-xl flex flex-col sm:flex-row items-center gap-3"
          >
            <div className="flex-1 w-full relative">
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                Project Record ID
              </label>
              <div className="relative">
                <input
                  type="number"
                  min="1"
                  required
                  placeholder="Enter Project ID (e.g. 1, 2...)"
                  value={projectIdInput}
                  onChange={(e) => setProjectIdInput(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 outline-none transition"
                />
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              </div>
            </div>
            <div className="w-full sm:w-auto sm:self-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-sm transition shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? 'Inspecting...' : 'Load Project BOM'}
              </button>
            </div>
          </form>

          {/* Feedback messages */}
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <div>{error}</div>
            </div>
          )}

          {updateError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <div>{updateError}</div>
            </div>
          )}

          {/* Project BOM Details */}
          {projectBomData && (
            <div className="space-y-6">
              {/* Project Metadata Banner */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Project Code
                    </span>
                    <span className="font-bold text-slate-900 text-sm font-mono">
                      {projectBomData.project_code}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Architecture
                    </span>
                    <span className="font-bold text-slate-900 text-sm">
                      {projectBomData.system_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Capacity Sizing
                    </span>
                    <span className="font-bold text-amber-600 text-sm">
                      {projectBomData.system_capacity_kw} kW
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Total Planned Cost
                    </span>
                    <span className="font-bold text-slate-900 text-sm">
                      ₹{projectBomData.total_estimated_cost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>

              {/* State 1: No BOM generated yet */}
              {!hasItems && (
                <div className="p-6 bg-amber-50/50 border border-amber-200 rounded-2xl space-y-4 text-center sm:text-left">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-amber-950 text-sm">
                        No BOM Generated for this Project
                      </h4>
                      <p className="text-xs text-amber-800 mt-1">
                        Select a compatible master BOM template matching{' '}
                        <span className="font-semibold">
                          {projectBomData.system_type} • {projectBomData.system_capacity_kw} kW
                        </span>{' '}
                        to clone component lines and lock base unit cost snapshots.
                      </p>
                    </div>
                  </div>

                  {generateError && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                      <span>{generateError}</span>
                    </div>
                  )}

                  {canWrite ? (
                    <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-3 pt-2">
                      <div className="flex-1">
                        <select
                          value={selectedTemplateId}
                          onChange={(e) => setSelectedTemplateId(e.target.value)}
                          className="w-full px-3.5 py-2.5 bg-white border border-amber-300 rounded-xl text-xs font-medium text-slate-800 focus:ring-2 focus:ring-amber-500 outline-none"
                        >
                          <option value="">-- Select Master BOM Template --</option>
                          {activeTemplates.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.template_name} ({t.system_type} • {t.capacity_kw} kW) — {t.item_count} items
                            </option>
                          ))}
                        </select>
                      </div>
                      <button
                        type="submit"
                        disabled={generating || !selectedTemplateId}
                        className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-xs shadow-md shadow-amber-500/20 transition disabled:opacity-50"
                      >
                        {generating ? 'Cloning & Generating...' : 'Generate Project BOM'}
                      </button>
                    </form>
                  ) : (
                    <div className="text-xs text-slate-500 italic">
                      Project BOM generation requires management authorization (Technical Manager or Super Admin).
                    </div>
                  )}
                </div>
              )}

              {/* State 2: BOM Items Table */}
              {hasItems && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                        <Package className="w-4 h-4 text-amber-500" /> Bill of Materials ({items.length} Component Lines)
                      </h4>
                      <p className="text-xs text-slate-400">
                        Tracks planned demand vs warehouse allocated, dispatched, and site installed quantities
                      </p>
                    </div>
                  </div>

                  <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-sm">
                    <table className="w-full text-left text-xs text-slate-700">
                      <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-3 px-3">Equipment</th>
                          <th className="py-3 px-2">Category</th>
                          <th className="py-3 px-2 text-right">Planned</th>
                          <th className="py-3 px-2 text-right">Allocated</th>
                          <th className="py-3 px-2 text-right">Dispatched</th>
                          <th className="py-3 px-2 text-right">Installed</th>
                          <th className="py-3 px-3 text-right">Unit Cost</th>
                          <th className="py-3 px-3 text-right">Total Planned</th>
                          {canWrite && <th className="py-3 px-2 text-center">Edit Qty</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {items.map((it) => {
                          const isEditingThis = editingItemId === it.id;

                          return (
                            <tr key={it.id} className="hover:bg-slate-50/70 transition">
                              <td className="py-3 px-3 font-medium text-slate-900">
                                <div>{it.product_name}</div>
                                <div className="text-[10px] text-slate-400 font-mono">
                                  {it.product_code}
                                  {it.brand ? ` • ${it.brand}` : ''}
                                </div>
                              </td>

                              <td className="py-3 px-2">
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                                  {it.item_category}
                                </span>
                              </td>

                              {/* Planned Quantity (Editable) */}
                              <td className="py-3 px-2 text-right font-bold text-slate-900">
                                {isEditingThis ? (
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={editPlannedQty}
                                    onChange={(e) => setEditPlannedQty(e.target.value)}
                                    className="w-16 px-1.5 py-1 bg-white border border-amber-400 rounded text-right text-xs focus:ring-1 focus:ring-amber-500 outline-none"
                                  />
                                ) : (
                                  it.planned_quantity
                                )}
                              </td>

                              {/* Allocated Stock (Read-Only) */}
                              <td className="py-3 px-2 text-right text-slate-600 font-mono">
                                {it.allocated_quantity}
                              </td>

                              {/* Dispatched Stock (Read-Only) */}
                              <td className="py-3 px-2 text-right text-slate-600 font-mono">
                                {it.dispatched_quantity}
                              </td>

                              {/* Installed Stock (Read-Only) */}
                              <td className="py-3 px-2 text-right text-slate-600 font-mono">
                                {it.installed_quantity}
                              </td>

                              {/* Unit Cost Snapshot */}
                              <td className="py-3 px-3 text-right text-slate-500 font-mono text-[11px]">
                                ₹{it.unit_cost_snapshot.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                              </td>

                              {/* Total Planned Cost */}
                              <td className="py-3 px-3 text-right font-bold text-slate-900 font-mono text-[11px]">
                                ₹{it.total_planned_cost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                              </td>

                              {canWrite && (
                                <td className="py-3 px-2 text-center">
                                  {isEditingThis ? (
                                    <div className="flex items-center justify-center gap-1">
                                      <button
                                        type="button"
                                        onClick={() => handleSaveQty(it)}
                                        disabled={updatingQty}
                                        className="text-emerald-600 hover:text-emerald-700 p-1 rounded hover:bg-emerald-50 transition"
                                        title="Confirm planned quantity"
                                      >
                                        <Check className="w-4 h-4" />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => setEditingItemId(null)}
                                        disabled={updatingQty}
                                        className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100 transition"
                                        title="Cancel"
                                      >
                                        <X className="w-4 h-4" />
                                      </button>
                                    </div>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={() => handleStartEditQty(it)}
                                      className="text-slate-400 hover:text-amber-600 p-1 rounded hover:bg-amber-50 transition"
                                      title="Adjust Planned Demand"
                                    >
                                      <Edit2 className="w-3.5 h-3.5" />
                                    </button>
                                  )}
                                </td>
                              )}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500 flex items-start gap-2">
                    <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-slate-700">Precedence Invariant: </span>
                      Planned Quantity must always satisfy <span className="font-mono">Planned ≥ Allocated ≥ Dispatched ≥ Installed</span>.
                      Allocated, Dispatched, Installed, and Unit Cost Snapshots are protected records and cannot be arbitrarily edited here.
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition shadow-sm"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
