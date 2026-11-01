import React, { useState, useEffect } from 'react';
import {
  Package,
  Plus,
  ShieldAlert,
  Zap,
  Sun,
  Layers,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { getMe } from '../services/employeeApi';
import { getProducts } from '../services/productApi';
import ProductList from '../components/ProductList';
import ProductModal from '../components/ProductModal';

export default function ProductManagementPage() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [productToEdit, setProductToEdit] = useState(null);

  // Metrics state
  const [metrics, setMetrics] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    panels: 0,
    inverters: 0,
  });

  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = () => setRefreshKey((k) => k + 1);

  useEffect(() => {
    getMe()
      .then((res) => {
        if (res && res.data) setCurrentUser(res.data);
      })
      .catch(() => setCurrentUser(null))
      .finally(() => setLoadingUser(false));
  }, []);

  // Fetch summary counts
  useEffect(() => {
    Promise.all([
      getProducts({ limit: 1 }),
      getProducts({ is_active: true, limit: 1 }),
      getProducts({ is_active: false, limit: 1 }),
      getProducts({ category: 'SOLAR_PANEL', limit: 1 }),
      getProducts({ category: 'INVERTER', limit: 1 }),
    ])
      .then(([allRes, actRes, inactRes, panRes, invRes]) => {
        setMetrics({
          total: allRes?.data?.total || 0,
          active: actRes?.data?.total || 0,
          inactive: inactRes?.data?.total || 0,
          panels: panRes?.data?.total || 0,
          inverters: invRes?.data?.total || 0,
        });
      })
      .catch(() => {});
  }, [refreshKey]);

  // Role permissions evaluation matching backend authorization
  const roleSlug = currentUser?.role?.slug || '';

  const canWrite = ['SUPER_ADMIN', 'TECHNICAL_MANAGER', 'WAREHOUSE_PROCUREMENT'].includes(roleSlug);
  const canRead = canWrite || ['DIRECTOR', 'SALES'].includes(roleSlug);

  const handleOpenAdd = () => {
    setProductToEdit(null);
    setShowModal(true);
  };

  const handleOpenEdit = (prod) => {
    setProductToEdit(prod);
    setShowModal(true);
  };

  // Unauthorized access block
  if (!loadingUser && !canRead) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-slate-900 text-lg">Access Restricted</h3>
        <p className="text-xs text-slate-500">
          The internal equipment and product catalog is restricted to engineering, inventory, management, and sales personnel.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Module Title & Action Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 flex items-center justify-center font-bold">
              <Package className="w-5 h-5 stroke-[2.5]" />
            </div>
            <span>Product Catalog</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Master equipment registry, specifications, base pricing, GST tax rates, and active catalog items.
          </p>
        </div>

        {canWrite && (
          <button
            onClick={handleOpenAdd}
            className="px-4 py-2.5 rounded-xl font-bold text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm flex items-center gap-2"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>Add Equipment</span>
          </button>
        )}
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Total Catalog</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">{metrics.total}</span>
          <span className="text-[10px] text-slate-500">All registered items</span>
        </div>

        <div className="bg-white rounded-xl border border-emerald-200 bg-emerald-50/20 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Active Equipment</span>
          <span className="text-2xl font-black text-emerald-900 mt-1 block">{metrics.active}</span>
          <span className="text-[10px] text-emerald-600 font-medium">BOM & quote ready</span>
        </div>

        <div className="bg-white rounded-xl border border-amber-200 bg-amber-50/20 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Solar Panels</span>
          <span className="text-2xl font-black text-amber-900 mt-1 block">{metrics.panels}</span>
          <span className="text-[10px] text-amber-600 font-medium">Mono PERC & TOPCon</span>
        </div>

        <div className="bg-white rounded-xl border border-sky-200 bg-sky-50/20 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-sky-700 uppercase tracking-wider block">Inverters</span>
          <span className="text-2xl font-black text-sky-900 mt-1 block">{metrics.inverters}</span>
          <span className="text-[10px] text-sky-600 font-medium">Grid-tie & hybrid</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs col-span-2 lg:col-span-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Archived / Inactive</span>
          <span className="text-2xl font-black text-slate-600 mt-1 block">{metrics.inactive}</span>
          <span className="text-[10px] text-slate-400">Legacy preserved</span>
        </div>
      </div>

      {/* Main Product List */}
      <ProductList
        canWrite={canWrite}
        onOpenAdd={handleOpenAdd}
        onOpenEdit={handleOpenEdit}
        refreshKey={refreshKey}
      />

      {/* Modal: Create / Edit Product */}
      <ProductModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setProductToEdit(null);
        }}
        onSuccess={triggerRefresh}
        productToEdit={productToEdit}
      />
    </div>
  );
}
