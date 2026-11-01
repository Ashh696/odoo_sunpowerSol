import React, { useState, useEffect } from 'react';
import {
  Truck,
  CheckCircle2,
  AlertTriangle,
  Search,
  Plus,
  RefreshCw,
  Clock,
  ShieldCheck,
  Package,
  Calendar,
  Phone,
  User,
  MapPin,
  ExternalLink,
  X,
  FileCheck,
} from 'lucide-react';
import {
  getDispatches,
  getDispatch,
  createDispatch,
  updateDispatchStatus,
  confirmDelivery,
  getProjectMaterialReadiness,
  createStockReservation,
  releaseStockReservation,
} from '../services/dispatchApi';
import { getProjects } from '../services/projectApi';

export default function DispatchManagementPage() {
  const [activeTab, setActiveTab] = useState('dispatches'); // 'dispatches' | 'readiness'
  const [dispatches, setDispatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Selected Dispatch detail modal
  const [selectedDispatch, setSelectedDispatch] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Delivery confirmation modal
  const [confirmModalDispatch, setConfirmModalDispatch] = useState(null);
  const [confirmForm, setConfirmForm] = useState({
    confirmation_type: 'CUSTOMER_SIGN',
    recipient_name: '',
    recipient_phone: '',
    delivery_notes: '',
  });
  const [confirmSubmitting, setConfirmSubmitting] = useState(false);

  // Material Readiness state
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [readinessData, setReadinessData] = useState(null);
  const [readinessLoading, setReadinessLoading] = useState(false);

  // New Dispatch modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    project_id: '',
    dispatched_date: new Date().toISOString().split('T')[0],
    vehicle_number: '',
    driver_name: '',
    driver_phone: '',
    tracking_number: '',
    remarks: '',
    items: [],
  });
  const [createSubmitting, setCreateSubmitting] = useState(false);

  useEffect(() => {
    fetchDispatches();
    fetchProjectsList();
  }, [statusFilter]);

  const fetchDispatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (statusFilter) params.dispatch_status = statusFilter;
      if (search) params.search = search;
      const res = await getDispatches(params);
      if (res.data?.success) {
        setDispatches(res.data.data.items || []);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dispatches');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectsList = async () => {
    try {
      const res = await getProjects();
      if (res.data?.success) {
        setProjects(res.data.data.items || res.data.data || []);
      }
    } catch (err) {
      console.error('Failed to load projects list', err);
    }
  };

  const handleInspectReadiness = async (projectId) => {
    if (!projectId) return;
    setSelectedProjectId(projectId);
    setReadinessLoading(true);
    setError(null);
    try {
      const res = await getProjectMaterialReadiness(projectId);
      if (res.data?.success) {
        setReadinessData(res.data.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load readiness data');
    } finally {
      setReadinessLoading(false);
    }
  };

  const handleViewDetail = async (dispatchId) => {
    setDetailLoading(true);
    try {
      const res = await getDispatch(dispatchId);
      if (res.data?.success) {
        setSelectedDispatch(res.data.data);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to fetch dispatch detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleOpenDeliveryConfirm = (dispatch) => {
    setConfirmModalDispatch(dispatch);
    setConfirmForm({
      confirmation_type: 'CUSTOMER_SIGN',
      recipient_name: dispatch.customer_name || '',
      recipient_phone: '',
      delivery_notes: '',
    });
  };

  const handleSubmitDeliveryConfirm = async (e) => {
    e.preventDefault();
    if (!confirmModalDispatch) return;
    setConfirmSubmitting(true);
    try {
      const res = await confirmDelivery(confirmModalDispatch.id, confirmForm);
      if (res.data?.success) {
        alert('Delivery confirmation recorded successfully!');
        setConfirmModalDispatch(null);
        fetchDispatches();
        if (selectedDispatch?.id === confirmModalDispatch.id) {
          handleViewDetail(confirmModalDispatch.id);
        }
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to confirm delivery');
    } finally {
      setConfirmSubmitting(false);
    }
  };

  const handlePrepareDispatchForProject = (readiness) => {
    setSelectedProjectId(readiness.project_id);
    setCreateForm({
      project_id: readiness.project_id,
      dispatched_date: new Date().toISOString().split('T')[0],
      vehicle_number: '',
      driver_name: '',
      driver_phone: '',
      tracking_number: '',
      remarks: '',
      items: readiness.items.map((it) => ({
        product_id: it.product_id,
        product_name: it.product_name,
        category: it.category,
        is_serialized: it.is_serialized,
        dispatched_quantity: Math.min(Number(it.remaining_to_dispatch), Number(it.warehouse_available)),
        serial_number_ids: [],
      })),
    });
    setShowCreateModal(true);
  };

  const handleCreateDispatchSubmit = async (e) => {
    e.preventDefault();
    setCreateSubmitting(true);
    try {
      const payload = {
        project_id: Number(createForm.project_id),
        dispatched_date: createForm.dispatched_date,
        vehicle_number: createForm.vehicle_number,
        driver_name: createForm.driver_name,
        driver_phone: createForm.driver_phone,
        tracking_number: createForm.tracking_number,
        remarks: createForm.remarks,
        items: createForm.items
          .filter((it) => Number(it.dispatched_quantity) > 0)
          .map((it) => ({
            product_id: it.product_id,
            dispatched_quantity: Number(it.dispatched_quantity),
            serial_number_ids: it.serial_number_ids || [],
          })),
      };

      const res = await createDispatch(payload);
      if (res.data?.success) {
        alert('Dispatch created successfully! Stock decremented and serial numbers logged.');
        setShowCreateModal(false);
        fetchDispatches();
        if (selectedProjectId) {
          handleInspectReadiness(selectedProjectId);
        }
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create dispatch');
    } finally {
      setCreateSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Dispatch & Serial Logistics</h2>
              <p className="text-xs text-slate-500">
                Track project material readiness, staged dispatch notes, serial traceability, and delivery confirmations
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs font-medium">
            <button
              onClick={() => setActiveTab('dispatches')}
              className={`px-3 py-1.5 rounded-md transition ${
                activeTab === 'dispatches'
                  ? 'bg-white text-slate-900 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Dispatches & Tracking
            </button>
            <button
              onClick={() => setActiveTab('readiness')}
              className={`px-3 py-1.5 rounded-md transition ${
                activeTab === 'readiness'
                  ? 'bg-white text-slate-900 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Material Readiness Check
            </button>
          </div>

          <button
            onClick={() => {
              if (activeTab === 'dispatches') fetchDispatches();
              else if (selectedProjectId) handleInspectReadiness(selectedProjectId);
            }}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: DISPATCHES LIST */}
      {activeTab === 'dispatches' && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row gap-3 justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex flex-1 items-center gap-3">
              <div className="relative flex-1 max-w-sm">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search dispatch note, vehicle, driver..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchDispatches()}
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500"
              >
                <option value="">All Statuses</option>
                <option value="PREPARED">PREPARED</option>
                <option value="DISPATCHED">DISPATCHED</option>
                <option value="IN_TRANSIT">IN_TRANSIT</option>
                <option value="DELIVERED">DELIVERED</option>
                <option value="RETURNED">RETURNED</option>
              </select>
            </div>

            <button
              onClick={() => {
                setActiveTab('readiness');
              }}
              className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1.5 shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              <span>Create Dispatch via Readiness</span>
            </button>
          </div>

          {/* Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
                <span>Loading dispatch register...</span>
              </div>
            ) : dispatches.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No dispatches found. Select a project in the Material Readiness Check tab to dispatch staged materials.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-bold tracking-wider">
                      <th className="py-3 px-4">Dispatch #</th>
                      <th className="py-3 px-4">Project / Customer</th>
                      <th className="py-3 px-4">Date</th>
                      <th className="py-3 px-4">Transport</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Delivery</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {dispatches.map((d) => (
                      <tr key={d.id} className="hover:bg-slate-50/70 transition">
                        <td className="py-3 px-4 font-mono font-bold text-amber-700">
                          {d.dispatch_number}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900">{d.project_code}</div>
                          <div className="text-[11px] text-slate-500">{d.customer_name}</div>
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          {d.dispatched_date}
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-slate-800">{d.vehicle_number || 'N/A'}</div>
                          <div className="text-[11px] text-slate-500">{d.driver_name || 'Driver unassigned'}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide ${
                              d.dispatch_status === 'DELIVERED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : d.dispatch_status === 'IN_TRANSIT'
                                ? 'bg-blue-100 text-blue-800'
                                : d.dispatch_status === 'DISPATCHED'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-slate-100 text-slate-800'
                            }`}
                          >
                            {d.dispatch_status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {d.is_confirmed ? (
                            <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-amber-600 text-[11px]">
                              <Clock className="w-3.5 h-3.5" /> Awaiting POD
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right space-x-2">
                          <button
                            onClick={() => handleViewDetail(d.id)}
                            className="px-2 py-1 border border-slate-200 rounded hover:bg-slate-100 text-slate-700 font-medium"
                          >
                            View
                          </button>
                          {!d.is_confirmed && (
                            <button
                              onClick={() => handleOpenDeliveryConfirm(d)}
                              className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium shadow-xs"
                            >
                              Confirm POD
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: MATERIAL READINESS */}
      {activeTab === 'readiness' && (
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Select Solar Installation Project</h3>
                <p className="text-xs text-slate-500">
                  Verifies BOM item planned quantities against live warehouse inventory and reserve allocations.
                </p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <select
                  value={selectedProjectId}
                  onChange={(e) => handleInspectReadiness(e.target.value)}
                  className="w-full sm:w-72 text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 font-medium focus:outline-none focus:border-amber-500"
                >
                  <option value="">-- Select Active Project --</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} • {p.customer_name || 'Project'} ({p.status})
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => handleInspectReadiness(selectedProjectId)}
                  disabled={!selectedProjectId || readinessLoading}
                  className="px-3 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 disabled:opacity-50 transition"
                >
                  {readinessLoading ? 'Evaluating...' : 'Inspect'}
                </button>
              </div>
            </div>

            {readinessData && (
              <div className="pt-4 border-t border-slate-100 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Project Code</span>
                    <span className="font-bold text-slate-900 text-base">{readinessData.project_code}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Customer</span>
                    <span className="font-semibold text-slate-800 text-xs">{readinessData.customer_name}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Site Address</span>
                    <span className="font-medium text-slate-700 text-xs">{readinessData.site_address}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Overall Readiness</span>
                    {readinessData.all_ready_for_dispatch ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                        <CheckCircle2 className="w-3.5 h-3.5" /> 100% Ready to Dispatch
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                        <AlertTriangle className="w-3.5 h-3.5" /> Material Shortage in Warehouse
                      </span>
                    )}
                  </div>
                  <div>
                    <button
                      onClick={() => handlePrepareDispatchForProject(readinessData)}
                      className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs shadow-sm transition"
                    >
                      Stage Dispatch
                    </button>
                  </div>
                </div>

                {/* Readiness Items Table */}
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 uppercase font-bold tracking-wider">
                        <th className="py-2.5 px-3">Item / Product</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Serialized</th>
                        <th className="py-2.5 px-3 text-right">Planned BOM</th>
                        <th className="py-2.5 px-3 text-right">Dispatched</th>
                        <th className="py-2.5 px-3 text-right">Remaining</th>
                        <th className="py-2.5 px-3 text-right">Warehouse Avail</th>
                        <th className="py-2.5 px-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {readinessData.items.map((item) => (
                        <tr key={item.product_id} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-3">
                            <div className="font-semibold text-slate-900">{item.product_name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{item.product_code}</div>
                          </td>
                          <td className="py-2.5 px-3 text-slate-600">{item.category}</td>
                          <td className="py-2.5 px-3">
                            {item.is_serialized ? (
                              <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold">
                                SERIALIZED
                              </span>
                            ) : (
                              <span className="text-slate-400 text-[10px]">BULK</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium">{item.planned_quantity}</td>
                          <td className="py-2.5 px-3 text-right text-slate-600">{item.dispatched_quantity}</td>
                          <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                            {item.remaining_to_dispatch}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium text-emerald-700">
                            {item.warehouse_available}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {item.is_ready_for_dispatch ? (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                READY
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                                DEFICIT
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* DETAIL MODAL */}
      {selectedDispatch && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-4 border border-slate-200 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Dispatch Note: {selectedDispatch.dispatch_number}
                </h3>
                <p className="text-xs text-slate-500">
                  Project {selectedDispatch.project_code} • {selectedDispatch.customer_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedDispatch(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div>
                <span className="text-slate-500 block">Vehicle Number:</span>
                <span className="font-semibold text-slate-900">{selectedDispatch.vehicle_number || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Driver Name:</span>
                <span className="font-semibold text-slate-900">{selectedDispatch.driver_name || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Driver Phone:</span>
                <span className="font-semibold text-slate-900">{selectedDispatch.driver_phone || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Tracking Number:</span>
                <span className="font-semibold text-slate-900">{selectedDispatch.tracking_number || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Dispatched Date:</span>
                <span className="font-semibold text-slate-900">{selectedDispatch.dispatched_date}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Shipment Status:</span>
                <span className="font-bold text-amber-700">{selectedDispatch.dispatch_status}</span>
              </div>
            </div>

            {/* Line Items */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Dispatched Items & Serials</h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2 px-3">Product</th>
                      <th className="py-2 px-3 text-right">Quantity</th>
                      <th className="py-2 px-3">Serials Scanned</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {selectedDispatch.items?.map((it) => (
                      <tr key={it.id}>
                        <td className="py-2 px-3">
                          <div className="font-medium text-slate-900">{it.product_name}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{it.product_code}</div>
                        </td>
                        <td className="py-2 px-3 text-right font-bold text-slate-800">
                          {it.dispatched_quantity} {it.unit_of_measure}
                        </td>
                        <td className="py-2 px-3">
                          {it.serials && it.serials.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {it.serials.map((s, idx) => (
                                <span
                                  key={idx}
                                  className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] border border-slate-200"
                                >
                                  {s.serial_number || `SN-${s.serial_number_id}`}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-400 text-[10px]">Non-serialized</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Delivery Confirmation Info if present */}
            {selectedDispatch.delivery_confirmation && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl space-y-1 text-xs">
                <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                  <CheckCircle2 className="w-4 h-4" /> Delivery Confirmation
                </div>
                <div className="text-slate-700">
                  Received by: <span className="font-semibold">{selectedDispatch.delivery_confirmation.recipient_name}</span> ({selectedDispatch.delivery_confirmation.recipient_phone})
                </div>
                <div className="text-slate-500 text-[11px]">
                  Method: {selectedDispatch.delivery_confirmation.confirmation_type} • Date: {new Date(selectedDispatch.delivery_confirmation.confirmation_timestamp).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* DELIVERY CONFIRMATION MODAL */}
      {confirmModalDispatch && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleSubmitDeliveryConfirm}
            className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 border border-slate-200 shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                Confirm Delivery (POD)
              </h3>
              <button
                type="button"
                onClick={() => setConfirmModalDispatch(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Confirm on-site physical handover for dispatch note{' '}
              <span className="font-mono font-bold text-amber-600">
                {confirmModalDispatch.dispatch_number}
              </span>.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Confirmation Method</label>
                <select
                  value={confirmForm.confirmation_type}
                  onChange={(e) => setConfirmForm({ ...confirmForm, confirmation_type: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                >
                  <option value="CUSTOMER_SIGN">Customer Signature On-Site</option>
                  <option value="OTP">SMS / OTP Handover</option>
                  <option value="PHOTO">Delivery Photo Verification</option>
                  <option value="SUPERVISOR_VERIFY">Supervisor Verification</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Recipient Full Name *</label>
                <input
                  type="text"
                  required
                  value={confirmForm.recipient_name}
                  onChange={(e) => setConfirmForm({ ...confirmForm, recipient_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="e.g. Ramesh Patel"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Recipient Phone Number *</label>
                <input
                  type="tel"
                  required
                  value={confirmForm.recipient_phone}
                  onChange={(e) => setConfirmForm({ ...confirmForm, recipient_phone: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="e.g. 9876543210"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Delivery Notes (Optional)</label>
                <textarea
                  rows={2}
                  value={confirmForm.delivery_notes}
                  onChange={(e) => setConfirmForm({ ...confirmForm, delivery_notes: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="Condition of materials, site supervisor remarks..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setConfirmModalDispatch(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={confirmSubmitting}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs shadow-sm transition disabled:opacity-50"
              >
                {confirmSubmitting ? 'Recording...' : 'Confirm Delivery'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* CREATE DISPATCH MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateDispatchSubmit}
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-4 border border-slate-200 shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Stage New Dispatch Note</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Dispatched Date *</label>
                <input
                  type="date"
                  required
                  value={createForm.dispatched_date}
                  onChange={(e) => setCreateForm({ ...createForm, dispatched_date: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Vehicle Number</label>
                <input
                  type="text"
                  value={createForm.vehicle_number}
                  onChange={(e) => setCreateForm({ ...createForm, vehicle_number: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="e.g. KA-01-AB-1234"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Driver Name</label>
                <input
                  type="text"
                  value={createForm.driver_name}
                  onChange={(e) => setCreateForm({ ...createForm, driver_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="e.g. Ramesh Kumar"
                />
              </div>
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Driver Phone</label>
                <input
                  type="tel"
                  value={createForm.driver_phone}
                  onChange={(e) => setCreateForm({ ...createForm, driver_phone: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 focus:border-amber-500"
                  placeholder="e.g. 9876543210"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Select Quantities to Dispatch
              </label>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2 px-3">Product</th>
                      <th className="py-2 px-3">Type</th>
                      <th className="py-2 px-3 text-right">Qty to Dispatch</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {createForm.items.map((it, idx) => (
                      <tr key={it.product_id}>
                        <td className="py-2 px-3 font-medium text-slate-900">{it.product_name}</td>
                        <td className="py-2 px-3 text-slate-500">
                          {it.is_serialized ? 'Serialized' : 'Bulk'}
                        </td>
                        <td className="py-2 px-3 text-right">
                          <input
                            type="number"
                            min="0"
                            step="any"
                            value={it.dispatched_quantity}
                            onChange={(e) => {
                              const newItems = [...createForm.items];
                              newItems[idx].dispatched_quantity = Number(e.target.value);
                              setCreateForm({ ...createForm, items: newItems });
                            }}
                            className="w-24 text-right bg-slate-50 border border-slate-200 rounded p-1 font-mono"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createSubmitting}
                className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-xs shadow-sm transition disabled:opacity-50"
              >
                {createSubmitting ? 'Dispatching...' : 'Confirm Dispatch'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
