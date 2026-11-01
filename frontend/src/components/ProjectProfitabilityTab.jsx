import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  DollarSign,
  PieChart,
  RefreshCw,
  FolderKanban,
  Plus,
  X,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { getProjects } from '../services/projectApi';
import {
  getProjectProfitability,
  getProjectCosts,
  createProjectCost,
} from '../services/supplierFinanceApi';

export default function ProjectProfitabilityTab({ currentUser }) {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [profitability, setProfitability] = useState(null);
  const [costs, setCosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Add Cost Modal
  const [costModalOpen, setCostModalOpen] = useState(false);
  const [costCategory, setCostCategory] = useState('LABOR');
  const [costAmount, setCostAmount] = useState('');
  const [costRefType, setCostRefType] = useState('WAGES');
  const [submittingCost, setSubmittingCost] = useState(false);

  useEffect(() => {
    // Load available projects
    const loadProjects = async () => {
      try {
        const res = await getProjects({ page_size: 50 });
        const items = res.data?.data?.items || [];
        setProjects(items);
        if (items.length > 0) {
          setSelectedProjectId(items[0].id);
        }
      } catch (err) {
        console.error('Failed to load projects list', err);
      }
    };
    loadProjects();
  }, []);

  const fetchProjectFinancials = async (projId) => {
    if (!projId) return;
    setLoading(true);
    setError(null);
    try {
      const [profRes, costsRes] = await Promise.all([
        getProjectProfitability(projId),
        getProjectCosts(projId),
      ]);
      setProfitability(profRes.data?.data || null);
      setCosts(costsRes.data?.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load project financials');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectFinancials(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleAddCost = async (e) => {
    e.preventDefault();
    if (!selectedProjectId || !costAmount) return;

    setSubmittingCost(true);
    try {
      await createProjectCost(selectedProjectId, {
        cost_category: costCategory,
        cost_amount: parseFloat(costAmount),
        source_reference_type: costRefType || undefined,
      });
      setCostModalOpen(false);
      setCostAmount('');
      fetchProjectFinancials(selectedProjectId);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record project cost');
    } finally {
      setSubmittingCost(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Project Selector Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <FolderKanban className="w-5 h-5 text-amber-500" />
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Select Project:</span>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="border border-slate-200 rounded-lg text-xs px-3 py-1.5 focus:ring-2 focus:ring-amber-500/20 font-semibold text-slate-900"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_code} — {p.customer_name || 'Project'} ({p.system_capacity_kw || p.system_size_kw || ''}kW)
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCostModalOpen(true)}
            className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Direct Cost</span>
          </button>
          <button
            onClick={() => fetchProjectFinancials(selectedProjectId)}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-500' : ''}`} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
          <span>Calculating project cost and margin breakdown...</span>
        </div>
      ) : profitability ? (
        <>
          {/* Profitability KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Contract Revenue</span>
              <div className="text-2xl font-black font-mono text-slate-900 mt-1">
                ₹{Number(profitability.contract_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-400">Order Net Payable Total</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Incurred Cost</span>
              <div className="text-2xl font-black font-mono text-rose-600 mt-1">
                ₹{Number(profitability.total_incurred_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-400">Material + Labor + Site</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gross Profit</span>
              <div className={`text-2xl font-black font-mono mt-1 ${Number(profitability.gross_profit) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                ₹{Number(profitability.gross_profit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-400">Revenue minus Costs</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Gross Margin %</span>
              <div className={`text-2xl font-black font-mono mt-1 ${Number(profitability.gross_margin_percentage) >= 15 ? 'text-emerald-600' : 'text-amber-600'}`}>
                {Number(profitability.gross_margin_percentage).toFixed(2)}%
              </div>
              <span className="text-[11px] text-slate-400">Target Benchmark: &gt;20%</span>
            </div>
          </div>

          {/* Cost Allocation Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <PieChart className="w-4 h-4 text-amber-500" />
                <span>Cost Structure Analysis</span>
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Procured Materials Cost (BOM):</span>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{Number(profitability.material_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Direct Labor & Installation:</span>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{Number(profitability.labor_installation_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Transport & Other Incurred Costs:</span>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{Number(profitability.other_direct_costs).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-2 font-bold bg-slate-50 px-2 rounded-lg text-slate-900">
                  <span>Total Incurred Execution Cost:</span>
                  <span className="font-mono text-rose-600">
                    ₹{Number(profitability.total_incurred_cost).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-500" />
                <span>Customer Cash Realization</span>
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Total Invoiced to Customer:</span>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{Number(profitability.total_invoiced).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Total Customer Cash Collected:</span>
                  <span className="font-mono font-bold text-emerald-600">
                    ₹{Number(profitability.total_collected).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-600">Uncollected Customer Receivables:</span>
                  <span className="font-mono font-bold text-amber-600">
                    ₹{Number(profitability.total_invoiced - profitability.total_collected).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Direct Costs Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Direct Project Cost Ledger</h4>
              <span className="text-xs text-slate-500">{costs.length} recorded line items</span>
            </div>
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Category</th>
                  <th className="px-4 py-2.5">Reference Type</th>
                  <th className="px-4 py-2.5">Recorded By</th>
                  <th className="px-4 py-2.5 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {costs.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center py-6 text-slate-400">
                      No direct project costs logged yet. Click "Add Direct Cost" to record labor, freight, or permits.
                    </td>
                  </tr>
                ) : (
                  costs.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-2.5 font-bold text-slate-900">{c.cost_category}</td>
                      <td className="px-4 py-2.5 text-slate-500">{c.source_reference_type || 'DIRECT'}</td>
                      <td className="px-4 py-2.5 text-slate-600">{c.recorder_name || `User #${c.recorded_by}`}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-bold text-slate-900">
                        ₹{Number(c.cost_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400">
          Select a project above to analyze financial profitability.
        </div>
      )}

      {/* Add Direct Cost Modal */}
      {costModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <Plus className="w-5 h-5 text-amber-500" />
                <span>Record Direct Project Cost</span>
              </h3>
              <button
                onClick={() => setCostModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddCost} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Cost Category</label>
                <select
                  value={costCategory}
                  onChange={(e) => setCostCategory(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2"
                >
                  <option value="LABOR">LABOR (Installation / Technician Wages)</option>
                  <option value="CIVIL_WORK">CIVIL_WORK (Foundation / Structure)</option>
                  <option value="TRANSPORT">TRANSPORT (Logistics & Freight)</option>
                  <option value="PERMITS_DISCOM">PERMITS_DISCOM (Net Metering / Inspection)</option>
                  <option value="EQUIPMENT_RENTAL">EQUIPMENT_RENTAL (Crane / Scaffold)</option>
                  <option value="MISCELLANEOUS">MISCELLANEOUS</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Cost Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 15000.00"
                  value={costAmount}
                  onChange={(e) => setCostAmount(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Reference / Note</label>
                <input
                  type="text"
                  placeholder="e.g. Contractor Daily Wages / Net Metering Fee"
                  value={costRefType}
                  onChange={(e) => setCostRefType(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCostModalOpen(false)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCost}
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg shadow-sm"
                >
                  {submittingCost ? 'Recording...' : 'Record Cost'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
