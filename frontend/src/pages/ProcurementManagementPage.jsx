import React, { useState, useEffect } from 'react';
import {
  ShoppingCart,
  PackageCheck,
  Building2,
  Boxes,
  Plus,
  Search,
  Filter,
  Eye,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  FileText,
  DollarSign,
  AlertCircle,
  Barcode,
  Send,
  Ban,
  Layers,
} from 'lucide-react';
import {
  getPurchaseOrders,
  getGoodsReceipts,
  getSuppliers,
  getWarehouseInventory,
  updateSupplierStatus,
  getProductStockMovements,
  getProductSerials,
  getProjectMaterialShortages,
} from '../services/procurementApi';
import api from '../services/api';
import SupplierModal from '../components/SupplierModal';
import PurchaseOrderModal from '../components/PurchaseOrderModal';
import PurchaseOrderDetailModal from '../components/PurchaseOrderDetailModal';
import GoodsReceiptModal from '../components/GoodsReceiptModal';
import GoodsReceiptDetailModal from '../components/GoodsReceiptDetailModal';

const PO_STATUS_COLORS = {
  DRAFT: 'bg-slate-700/80 text-slate-300 border-slate-600',
  ISSUED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  PARTIALLY_RECEIVED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  RECEIVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

const GRN_STATUS_COLORS = {
  ACCEPTED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  PARTIALLY_ACCEPTED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  REJECTED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function ProcurementManagementPage() {
  const [activeTab, setActiveTab] = useState('orders'); // 'orders' | 'receipts' | 'suppliers' | 'inventory'

  // Tab 1: Orders State
  const [orders, setOrders] = useState([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [orderStatusFilter, setOrderStatusFilter] = useState('');
  const [orderSearch, setOrderSearch] = useState('');

  // Tab 2: Goods Receipts State
  const [receipts, setReceipts] = useState([]);
  const [receiptsLoading, setReceiptsLoading] = useState(false);
  const [receiptSearch, setReceiptSearch] = useState('');

  // Tab 3: Suppliers State
  const [suppliers, setSuppliers] = useState([]);
  const [suppliersLoading, setSuppliersLoading] = useState(false);
  const [supplierSearch, setSupplierSearch] = useState('');
  const [supplierActiveFilter, setSupplierActiveFilter] = useState('');

  // Tab 4: Inventory State
  const [inventory, setInventory] = useState([]);
  const [inventorySummary, setInventorySummary] = useState(null);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventorySearch, setInventorySearch] = useState('');
  const [lowStockFilter, setLowStockFilter] = useState(false);

  // Sub-modal / Drawer state for Inventory movements & Serials
  const [selectedProductMovements, setSelectedProductMovements] = useState(null);
  const [movementsData, setMovementsData] = useState([]);
  const [movementsLoading, setMovementsLoading] = useState(false);

  const [selectedProductSerials, setSelectedProductSerials] = useState(null);
  const [serialsData, setSerialsData] = useState([]);
  const [serialsLoading, setSerialsLoading] = useState(false);

  // Project Shortage Tool State
  const [projectsList, setProjectsList] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [shortageResult, setShortageResult] = useState(null);
  const [shortageLoading, setShortageLoading] = useState(false);

  // Modals
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  const [poModalOpen, setPoModalOpen] = useState(false);
  const [editingPo, setEditingPo] = useState(null);

  const [poDetailModalOpen, setPoDetailModalOpen] = useState(false);
  const [selectedPoId, setSelectedPoId] = useState(null);

  const [grnModalOpen, setGrnModalOpen] = useState(false);
  const [grnTargetPo, setGrnTargetPo] = useState(null);

  const [grnDetailModalOpen, setGrnDetailModalOpen] = useState(false);
  const [selectedGrnId, setSelectedGrnId] = useState(null);

  useEffect(() => {
    if (activeTab === 'orders') fetchOrders();
    if (activeTab === 'receipts') fetchReceipts();
    if (activeTab === 'suppliers') fetchSuppliers();
    if (activeTab === 'inventory') {
      fetchInventory();
      loadProjectsForShortage();
    }
  }, [activeTab]);

  // Loaders
  const fetchOrders = async () => {
    setOrdersLoading(true);
    try {
      const params = { page_size: 100 };
      if (orderStatusFilter) params.status = orderStatusFilter;
      if (orderSearch) params.search = orderSearch;
      const res = await getPurchaseOrders(params);
      setOrders(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error fetching POs', err);
    } finally {
      setOrdersLoading(false);
    }
  };

  const fetchReceipts = async () => {
    setReceiptsLoading(true);
    try {
      const params = { page_size: 100 };
      if (receiptSearch) params.search = receiptSearch;
      const res = await getGoodsReceipts(params);
      setReceipts(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error fetching GRNs', err);
    } finally {
      setReceiptsLoading(false);
    }
  };

  const fetchSuppliers = async () => {
    setSuppliersLoading(true);
    try {
      const params = { page_size: 100 };
      if (supplierSearch) params.search = supplierSearch;
      if (supplierActiveFilter !== '') params.is_active = supplierActiveFilter === 'true';
      const res = await getSuppliers(params);
      setSuppliers(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error fetching suppliers', err);
    } finally {
      setSuppliersLoading(false);
    }
  };

  const fetchInventory = async () => {
    setInventoryLoading(true);
    try {
      const params = { page_size: 100 };
      if (inventorySearch) params.search = inventorySearch;
      if (lowStockFilter) params.low_stock_only = true;
      const res = await getWarehouseInventory(params);
      setInventory(res.data?.data?.items || []);
      setInventorySummary(res.data?.data?.summary || null);
    } catch (err) {
      console.error('Error fetching inventory', err);
    } finally {
      setInventoryLoading(false);
    }
  };

  const loadProjectsForShortage = async () => {
    try {
      const res = await api.get('/api/v1/projects', { params: { page_size: 100 } });
      setProjectsList(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error loading projects', err);
    }
  };

  const checkShortages = async (projId) => {
    setSelectedProjectId(projId);
    if (!projId) {
      setShortageResult(null);
      return;
    }
    setShortageLoading(true);
    try {
      const res = await getProjectMaterialShortages(projId);
      setShortageResult(res.data?.data || null);
    } catch (err) {
      console.error('Error calculating shortages', err);
    } finally {
      setShortageLoading(false);
    }
  };

  const handleToggleSupplierStatus = async (id, currentStatus) => {
    try {
      await updateSupplierStatus(id, !currentStatus);
      fetchSuppliers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error updating supplier status');
    }
  };

  const openMovementsModal = async (product) => {
    setSelectedProductMovements(product);
    setMovementsLoading(true);
    try {
      const res = await getProductStockMovements(product.product_id);
      setMovementsData(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error fetching movements', err);
    } finally {
      setMovementsLoading(false);
    }
  };

  const openSerialsModal = async (product) => {
    setSelectedProductSerials(product);
    setSerialsLoading(true);
    try {
      const res = await getProductSerials(product.product_id);
      setSerialsData(res.data?.data?.items || []);
    } catch (err) {
      console.error('Error fetching serials', err);
    } finally {
      setSerialsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 md:p-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
            <Boxes className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Procurement & Warehouse</h1>
            <p className="text-xs text-slate-400">
              Supplier directory, Purchase Orders, physical Goods Receipt Notes (GRN), and perpetual stock valuation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (activeTab === 'orders') fetchOrders();
              if (activeTab === 'receipts') fetchReceipts();
              if (activeTab === 'suppliers') fetchSuppliers();
              if (activeTab === 'inventory') fetchInventory();
            }}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Refresh current tab"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {activeTab === 'suppliers' && (
            <button
              onClick={() => {
                setSelectedSupplier(null);
                setSupplierModalOpen(true);
              }}
              className="px-4 py-2 rounded-lg text-sm font-semibold bg-amber-500 text-slate-950 hover:bg-amber-400 transition flex items-center gap-1.5 shadow-md shadow-amber-500/20"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>Add Supplier</span>
            </button>
          )}

          {activeTab === 'orders' && (
            <button
              onClick={() => {
                setEditingPo(null);
                setPoModalOpen(true);
              }}
              className="px-4 py-2 rounded-lg text-sm font-semibold bg-amber-500 text-slate-950 hover:bg-amber-400 transition flex items-center gap-1.5 shadow-md shadow-amber-500/20"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>Create Purchase Order</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="flex items-center space-x-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('orders')}
          className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'orders'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShoppingCart className="w-4 h-4" />
          <span>Purchase Orders</span>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {orders.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('receipts')}
          className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'receipts'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <PackageCheck className="w-4 h-4" />
          <span>Goods Receipts (GRN)</span>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {receipts.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('suppliers')}
          className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'suppliers'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Suppliers Directory</span>
          <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono">
            {suppliers.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('inventory')}
          className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
            activeTab === 'inventory'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Boxes className="w-4 h-4" />
          <span>Warehouse Stock Ledger</span>
          {inventorySummary && (
            <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full font-mono font-bold">
              ₹{Math.round(inventorySummary.total_valuation).toLocaleString('en-IN')}
            </span>
          )}
        </button>
      </div>

      {/* ============================================================ */}
      {/* TAB 1: PURCHASE ORDERS */}
      {/* ============================================================ */}
      {activeTab === 'orders' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search by PO # or vendor name..."
                value={orderSearch}
                onChange={(e) => setOrderSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchOrders()}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <select
                value={orderStatusFilter}
                onChange={(e) => {
                  setOrderStatusFilter(e.target.value);
                  setTimeout(fetchOrders, 0);
                }}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">All PO Statuses</option>
                <option value="DRAFT">DRAFT</option>
                <option value="ISSUED">ISSUED</option>
                <option value="PARTIALLY_RECEIVED">PARTIALLY_RECEIVED</option>
                <option value="RECEIVED">RECEIVED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>

              <button
                onClick={fetchOrders}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Apply Filter
              </button>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">PO Number</th>
                  <th className="py-3 px-4">Supplier</th>
                  <th className="py-3 px-4">Project Link</th>
                  <th className="py-3 px-4">Order Date</th>
                  <th className="py-3 px-4 text-center">Items</th>
                  <th className="py-3 px-4 text-right">Tax (₹)</th>
                  <th className="py-3 px-4 text-right">Grand Total (₹)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {ordersLoading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400">
                      Loading purchase orders...
                    </td>
                  </tr>
                ) : orders.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400 font-sans">
                      No purchase orders found. Click "Create Purchase Order" to issue new orders.
                    </td>
                  </tr>
                ) : (
                  orders.map((po) => (
                    <tr key={po.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-semibold text-amber-400">{po.po_number}</td>
                      <td className="py-3 px-4 font-sans">
                        <div className="font-semibold text-white">{po.supplier_name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{po.supplier_code}</div>
                      </td>
                      <td className="py-3 px-4 font-sans text-xs">
                        {po.project_code ? (
                          <span className="text-blue-400 font-mono font-medium">{po.project_code}</span>
                        ) : (
                          <span className="text-slate-500 italic">General Stock</span>
                        )}
                      </td>
                      <td className="py-3 px-4">{po.po_date}</td>
                      <td className="py-3 px-4 text-center">{po.items_count}</td>
                      <td className="py-3 px-4 text-right text-slate-400">
                        ₹{parseFloat(po.tax_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-100">
                        ₹{parseFloat(po.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                            PO_STATUS_COLORS[po.status] || 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {po.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <button
                          onClick={() => {
                            setSelectedPoId(po.id);
                            setPoDetailModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 2: GOODS RECEIPTS (GRN) */}
      {/* ============================================================ */}
      {activeTab === 'receipts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-lg p-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search by GRN # or Challan #..."
                value={receiptSearch}
                onChange={(e) => setReceiptSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchReceipts()}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>
            <button
              onClick={fetchReceipts}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
            >
              Refresh GRNs
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-sm text-slate-300 font-mono text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider border-b border-slate-800 font-sans">
                <tr>
                  <th className="py-3 px-4">GRN Number</th>
                  <th className="py-3 px-4">Purchase Order</th>
                  <th className="py-3 px-4">Supplier</th>
                  <th className="py-3 px-4">Receipt Date</th>
                  <th className="py-3 px-4">Challan / Invoice</th>
                  <th className="py-3 px-4">Received By</th>
                  <th className="py-3 px-4">Inspection Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {receiptsLoading ? (
                  <tr>
                    <td colSpan={8} className="text-center py-10 text-slate-400">
                      Loading goods receipts...
                    </td>
                  </tr>
                ) : receipts.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-10 text-slate-400 font-sans">
                      No Goods Receipt Notes recorded yet. Inward stock from an issued Purchase Order.
                    </td>
                  </tr>
                ) : (
                  receipts.map((grn) => (
                    <tr key={grn.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-semibold text-amber-400">{grn.grn_number}</td>
                      <td className="py-3 px-4 text-blue-400 font-medium">{grn.po_number}</td>
                      <td className="py-3 px-4 font-sans text-white">{grn.supplier_name}</td>
                      <td className="py-3 px-4">{grn.received_date}</td>
                      <td className="py-3 px-4">{grn.challan_number || '—'}</td>
                      <td className="py-3 px-4 font-sans">{grn.receiver_name || 'Staff'}</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                            GRN_STATUS_COLORS[grn.status] || 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {grn.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <button
                          onClick={() => {
                            setSelectedGrnId(grn.id);
                            setGrnDetailModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View GRN</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 3: SUPPLIERS DIRECTORY */}
      {/* ============================================================ */}
      {activeTab === 'suppliers' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search by vendor name, city, code..."
                value={supplierSearch}
                onChange={(e) => setSupplierSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchSuppliers()}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <select
                value={supplierActiveFilter}
                onChange={(e) => {
                  setSupplierActiveFilter(e.target.value);
                  setTimeout(fetchSuppliers, 0);
                }}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">All Vendors</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
              </select>

              <button
                onClick={fetchSuppliers}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Search
              </button>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-mono">Code</th>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Contact Person</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Phone</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4 font-mono">GST Number</th>
                  <th className="py-3 px-4 text-center">Active</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {suppliersLoading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400">
                      Loading supplier directory...
                    </td>
                  </tr>
                ) : suppliers.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400">
                      No suppliers registered. Click "Add Supplier" to register solar component vendors.
                    </td>
                  </tr>
                ) : (
                  suppliers.map((supp) => (
                    <tr key={supp.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono font-semibold text-amber-400">{supp.supplier_code}</td>
                      <td className="py-3 px-4 font-semibold text-white">{supp.company_name}</td>
                      <td className="py-3 px-4">{supp.contact_person}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono">{supp.email}</td>
                      <td className="py-3 px-4 font-mono">{supp.phone}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {supp.city}, {supp.state}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">{supp.gst_number || '—'}</td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleToggleSupplierStatus(supp.id, supp.is_active)}
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border transition ${
                            supp.is_active
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
                              : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                          }`}
                        >
                          {supp.is_active ? 'Active' : 'Inactive'}
                        </button>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedSupplier(supp);
                            setSupplierModalOpen(true);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 4: WAREHOUSE INVENTORY */}
      {/* ============================================================ */}
      {activeTab === 'inventory' && (
        <div className="space-y-6">
          {/* Inventory KPI Summary Cards */}
          {inventorySummary && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
                    Total Warehouse Valuation
                  </div>
                  <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                    ₹{parseFloat(inventorySummary.total_valuation).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Authoritative Moving Average Cost Basis</div>
                </div>
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                  <DollarSign className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
                    Low Stock Alerts
                  </div>
                  <div
                    className={`text-2xl font-bold font-mono mt-1 ${
                      inventorySummary.low_stock_count > 0 ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {inventorySummary.low_stock_count} SKUs
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">At or below reorder threshold</div>
                </div>
                <div className="w-12 h-12 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-500">
                  <AlertTriangle className="w-6 h-6" />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
                    Active Stock Records
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-1">
                    {inventorySummary.total_tracked_products}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Main Warehouse Bay Ledger</div>
                </div>
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Boxes className="w-6 h-6" />
                </div>
              </div>
            </div>
          )}

          {/* Project Shortage Checker Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-amber-500" />
                  <span>Project BOM Shortage Checker</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Compare unallocated project BOM requirements against unreserved warehouse stock to plan procurement
                </p>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={selectedProjectId}
                  onChange={(e) => checkShortages(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 font-sans"
                >
                  <option value="">Select Project to analyze BOM shortages...</option>
                  {projectsList.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} ({p.system_capacity_kw}kW - {p.status})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {shortageLoading && (
              <div className="text-xs text-slate-400 py-2">Analyzing material shortages against warehouse stock...</div>
            )}

            {shortageResult && (
              <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/60 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-amber-400">
                    Project: {shortageResult.project_code} ({shortageResult.system_capacity_kw} kW)
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded font-mono ${
                      shortageResult.shortage_items_count > 0
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    {shortageResult.shortage_items_count} Component Shortages Detected
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 pt-1 font-mono text-xs">
                  {shortageResult.items.map((it) => (
                    <div
                      key={it.bom_item_id}
                      className={`p-2 rounded border ${
                        it.has_shortage
                          ? 'bg-rose-500/5 border-rose-500/30 text-rose-300'
                          : 'bg-slate-900 border-slate-800 text-slate-300'
                      }`}
                    >
                      <div className="font-semibold text-white truncate font-sans">{it.product_name}</div>
                      <div className="text-[10px] text-slate-400">
                        Planned: {parseFloat(it.planned_quantity)} | Allocated: {parseFloat(it.allocated_quantity)}
                      </div>
                      <div className="flex justify-between items-center text-[11px] mt-1">
                        <span className="text-slate-400">Avail Stock: {parseFloat(it.quantity_available)}</span>
                        {it.has_shortage ? (
                          <span className="font-bold text-rose-400">
                            Shortage: -{parseFloat(it.shortage_quantity)} {it.unit_of_measure}
                          </span>
                        ) : (
                          <span className="text-emerald-400 font-semibold">Sufficient</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Inventory Table Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search stock by SKU, product name, brand..."
                value={inventorySearch}
                onChange={(e) => setInventorySearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchInventory()}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-300">
                <input
                  type="checkbox"
                  checked={lowStockFilter}
                  onChange={(e) => {
                    setLowStockFilter(e.target.checked);
                    setTimeout(fetchInventory, 0);
                  }}
                  className="rounded bg-slate-800 border-slate-700 text-amber-500 focus:ring-amber-500 w-3.5 h-3.5"
                />
                <span>Low Stock Only</span>
              </label>

              <button
                onClick={fetchInventory}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Search Stock
              </button>
            </div>
          </div>

          {/* Stock Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800 font-sans">
                <tr>
                  <th className="py-3 px-4">SKU / Item</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4 text-right">On Hand</th>
                  <th className="py-3 px-4 text-right">Reserved</th>
                  <th className="py-3 px-4 text-right text-emerald-400">Available</th>
                  <th className="py-3 px-4 text-right">Avg Unit Cost</th>
                  <th className="py-3 px-4 text-right">Valuation (₹)</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">History</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {inventoryLoading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400">
                      Loading stock balances...
                    </td>
                  </tr>
                ) : inventory.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-10 text-slate-400 font-sans">
                      No inventory records found. Inward goods receipts to populate warehouse stock.
                    </td>
                  </tr>
                ) : (
                  inventory.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-sans">
                        <div className="font-semibold text-white">{inv.product_name}</div>
                        <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                          <span>{inv.product_code}</span>
                          {inv.is_serialized && (
                            <span className="text-[10px] text-purple-400 font-semibold bg-purple-500/10 px-1 rounded">
                              SERIALIZED
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-sans text-xs text-slate-400">{inv.category}</td>
                      <td className="py-3 px-4 text-right text-white font-semibold">
                        {parseFloat(inv.quantity_on_hand)} {inv.unit_of_measure}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400">
                        {parseFloat(inv.reserved_quantity)} {inv.unit_of_measure}
                      </td>
                      <td className="py-3 px-4 text-right text-emerald-400 font-bold">
                        {parseFloat(inv.quantity_available)} {inv.unit_of_measure}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        ₹{parseFloat(inv.average_unit_cost).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-amber-400">
                        ₹{parseFloat(inv.total_valuation).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center font-sans">
                        {inv.is_low_stock ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            Low Stock
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            In Stock
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-sans space-x-1.5">
                        <button
                          onClick={() => openMovementsModal(inv)}
                          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium transition"
                          title="View Stock Movements Ledger"
                        >
                          Ledger
                        </button>
                        {inv.is_serialized && (
                          <button
                            onClick={() => openSerialsModal(inv)}
                            className="px-2 py-0.5 rounded bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 text-[11px] font-medium transition"
                            title="View Serial Numbers"
                          >
                            Serials
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* DRAWER / MODAL: STOCK MOVEMENTS LEDGER */}
      {/* ============================================================ */}
      {selectedProductMovements && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full shadow-2xl overflow-hidden my-8">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
              <div>
                <h3 className="text-base font-bold text-white">Stock Movement Audit Ledger</h3>
                <p className="text-xs text-slate-400 font-mono">
                  Product: {selectedProductMovements.product_name} ({selectedProductMovements.product_code})
                </p>
              </div>
              <button
                onClick={() => setSelectedProductMovements(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 max-h-[60vh] overflow-y-auto">
              {movementsLoading ? (
                <div className="text-center py-8 text-slate-400 text-sm">Loading ledger...</div>
              ) : movementsData.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm font-sans">
                  No stock movements recorded for this component yet.
                </div>
              ) : (
                <table className="w-full text-left text-xs font-mono text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Movement Type</th>
                      <th className="py-2.5 px-3 text-right">Qty</th>
                      <th className="py-2.5 px-3 text-right">Before</th>
                      <th className="py-2.5 px-3 text-right">After</th>
                      <th className="py-2.5 px-3">User</th>
                      <th className="py-2.5 px-3">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {movementsData.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-800/30">
                        <td className="py-2 px-3">{new Date(m.created_at).toLocaleDateString()}</td>
                        <td className="py-2 px-3">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {m.movement_type}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-bold text-emerald-400">
                          +{parseFloat(m.quantity)}
                        </td>
                        <td className="py-2 px-3 text-right text-slate-400">{parseFloat(m.quantity_before)}</td>
                        <td className="py-2 px-3 text-right text-white font-semibold">{parseFloat(m.quantity_after)}</td>
                        <td className="py-2 px-3 font-sans">{m.performer_name || 'Staff'}</td>
                        <td className="py-2 px-3 font-sans text-slate-400 truncate max-w-xs">{m.remarks || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="flex justify-end p-4 border-t border-slate-800">
              <button
                onClick={() => setSelectedProductMovements(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* DRAWER / MODAL: SERIAL NUMBERS */}
      {/* ============================================================ */}
      {selectedProductSerials && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden my-8">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Barcode className="w-5 h-5 text-purple-400" />
                  <span>Component Serial Numbers</span>
                </h3>
                <p className="text-xs text-slate-400 font-mono">
                  {selectedProductSerials.product_name} ({selectedProductSerials.product_code})
                </p>
              </div>
              <button
                onClick={() => setSelectedProductSerials(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 max-h-[60vh] overflow-y-auto">
              {serialsLoading ? (
                <div className="text-center py-8 text-slate-400 text-sm">Loading serials...</div>
              ) : serialsData.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm font-sans">
                  No serial numbers registered in warehouse for this component.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
                  {serialsData.map((sn) => (
                    <div
                      key={sn.id}
                      className="p-2.5 rounded-lg border border-slate-800 bg-slate-950/70 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-bold text-slate-200">{sn.serial_number}</div>
                        <div className="text-[10px] text-slate-500">
                          Recv: {sn.received_date} | Warranty: {sn.warranty_months}m
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {sn.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end p-4 border-t border-slate-800">
              <button
                onClick={() => setSelectedProductSerials(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modals Mounting */}
      <SupplierModal
        isOpen={supplierModalOpen}
        onClose={() => setSupplierModalOpen(false)}
        supplier={selectedSupplier}
        onSuccess={fetchSuppliers}
      />

      <PurchaseOrderModal
        isOpen={poModalOpen}
        onClose={() => setPoModalOpen(false)}
        po={editingPo}
        onSuccess={fetchOrders}
      />

      <PurchaseOrderDetailModal
        isOpen={poDetailModalOpen}
        poId={selectedPoId}
        onClose={() => setPoDetailModalOpen(false)}
        onRefresh={fetchOrders}
        onOpenEditModal={(po) => {
          setEditingPo(po);
          setPoModalOpen(true);
        }}
        onOpenGRNModal={(po) => {
          setGrnTargetPo(po);
          setGrnModalOpen(true);
        }}
      />

      <GoodsReceiptModal
        isOpen={grnModalOpen}
        onClose={() => setGrnModalOpen(false)}
        po={grnTargetPo}
        onSuccess={() => {
          fetchOrders();
          fetchReceipts();
        }}
      />

      <GoodsReceiptDetailModal
        isOpen={grnDetailModalOpen}
        grnId={selectedGrnId}
        onClose={() => setGrnDetailModalOpen(false)}
      />
    </div>
  );
}
