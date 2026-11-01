import React, { useState, useEffect } from 'react';
import {
  X,
  Layers,
  Plus,
  Trash2,
  Edit2,
  Check,
  AlertCircle,
  Package,
  CheckCircle2,
  XCircle,
  Info,
  Calendar,
  User,
  ShieldAlert,
} from 'lucide-react';
import {
  getBomTemplate,
  addBomTemplateItem,
  updateBomTemplateItem,
  deleteBomTemplateItem,
} from '../services/bomApi';
import { getProducts } from '../services/productApi';

export default function BOMTemplateDetailModal({
  isOpen,
  onClose,
  templateId,
  canWrite = false,
  onUpdated,
}) {
  const [template, setTemplate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add Item Subform state
  const [showAddForm, setShowAddForm] = useState(false);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [newQuantity, setNewQuantity] = useState('1');
  const [newMandatory, setNewMandatory] = useState(true);
  const [addItemError, setAddItemError] = useState(null);
  const [addingItem, setAddingItem] = useState(false);

  // Editing existing item inline
  const [editingItemId, setEditingItemId] = useState(null);
  const [editQuantity, setEditQuantity] = useState('');
  const [editMandatory, setEditMandatory] = useState(true);
  const [updatingItem, setUpdatingItem] = useState(false);

  // Delete item confirmation state
  const [itemToDelete, setItemToDelete] = useState(null);
  const [deletingItem, setDeletingItem] = useState(false);

  const fetchTemplateDetails = async () => {
    if (!templateId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getBomTemplate(templateId);
      setTemplate(res.data);
    } catch (err) {
      setError(err.message || 'Failed to load BOM template details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && templateId) {
      fetchTemplateDetails();
      setShowAddForm(false);
      setEditingItemId(null);
      setItemToDelete(null);
    }
  }, [isOpen, templateId]);

  // Load active products when opening add form
  const handleToggleAddForm = () => {
    if (!showAddForm && availableProducts.length === 0) {
      setLoadingProducts(true);
      getProducts({ is_active: true, limit: 100 })
        .then((res) => {
          setAvailableProducts(res?.data?.items || []);
        })
        .catch((err) => {
          console.error('Failed to load active catalog for BOM item add:', err);
        })
        .finally(() => setLoadingProducts(false));
    }
    setShowAddForm(!showAddForm);
    setSelectedProductId('');
    setNewQuantity('1');
    setNewMandatory(true);
    setAddItemError(null);
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    setAddItemError(null);

    if (!selectedProductId) {
      setAddItemError('Please select a product equipment.');
      return;
    }

    const prodIdNum = parseInt(selectedProductId, 10);
    const existing = template?.items?.find((it) => it.product_id === prodIdNum);
    if (existing) {
      setAddItemError(`Product already exists in this template (${existing.product_name}).`);
      return;
    }

    const qty = parseFloat(newQuantity);
    if (isNaN(qty) || qty <= 0) {
      setAddItemError('Quantity must be greater than 0.');
      return;
    }

    const prod = availableProducts.find((p) => p.id === prodIdNum);
    if (!prod) {
      setAddItemError('Selected product not found in active catalog.');
      return;
    }

    setAddingItem(true);
    try {
      const payload = {
        product_id: prod.id,
        item_category: prod.category,
        default_quantity: qty,
        unit_of_measure: prod.unit_of_measure || 'NOS',
        is_mandatory: newMandatory,
      };

      await addBomTemplateItem(templateId, payload);
      await fetchTemplateDetails();
      if (onUpdated) onUpdated();
      setShowAddForm(false);
    } catch (err) {
      setAddItemError(err.message || 'Failed to add component line to template.');
    } finally {
      setAddingItem(false);
    }
  };

  const handleStartEdit = (item) => {
    setEditingItemId(item.id);
    setEditQuantity(String(item.default_quantity));
    setEditMandatory(Boolean(item.is_mandatory));
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setEditQuantity('');
  };

  const handleSaveEdit = async (itemId) => {
    const qty = parseFloat(editQuantity);
    if (isNaN(qty) || qty <= 0) {
      alert('Quantity must be greater than 0.');
      return;
    }

    setUpdatingItem(true);
    try {
      await updateBomTemplateItem(templateId, itemId, {
        default_quantity: qty,
        is_mandatory: editMandatory,
      });
      await fetchTemplateDetails();
      if (onUpdated) onUpdated();
      setEditingItemId(null);
    } catch (err) {
      alert(err.message || 'Failed to update item quantity.');
    } finally {
      setUpdatingItem(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!itemToDelete) return;
    setDeletingItem(true);
    try {
      await deleteBomTemplateItem(templateId, itemToDelete.id);
      await fetchTemplateDetails();
      if (onUpdated) onUpdated();
      setItemToDelete(null);
    } catch (err) {
      alert(err.message || 'Failed to delete template component.');
    } finally {
      setDeletingItem(false);
    }
  };

  if (!isOpen) return null;

  const items = template?.items || [];
  const totalCost = items.reduce(
    (sum, it) => sum + (it.unit_price ? it.unit_price * it.default_quantity : 0),
    0
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-4xl w-full overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="bg-slate-900 px-6 py-4 flex items-center justify-between text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-lg leading-tight">
                  {template ? template.template_name : 'BOM Template Details'}
                </h3>
                {template && (
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      template.is_active
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    }`}
                  >
                    {template.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Master Bill of Materials Specification & Component Sizing
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

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-16 text-center text-slate-400 text-sm">
              <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              Loading template component specifications...
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <div>{error}</div>
            </div>
          ) : template ? (
            <>
              {/* Template Header Card */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Architecture
                    </span>
                    <span className="font-bold text-slate-900 text-sm">{template.system_type}</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      System Capacity
                    </span>
                    <span className="font-bold text-amber-600 text-sm">{template.capacity_kw} kW</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Component Lines
                    </span>
                    <span className="font-bold text-slate-900 text-sm">{items.length} items</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Estimated Cost
                    </span>
                    <span className="font-bold text-slate-900 text-sm">
                      ₹{totalCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {template.description && (
                  <div className="pt-3 border-t border-slate-200 text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold text-slate-700">Engineering Scope: </span>
                    {template.description}
                  </div>
                )}

                <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-2 border-t border-slate-200/60">
                  <span className="flex items-center gap-1">
                    <User className="w-3.5 h-3.5" /> Created by {template.creator_name || 'System Admin'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />{' '}
                    {template.created_at ? new Date(template.created_at).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Scope Notice */}
              <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-xl text-amber-900 text-xs flex items-start gap-2.5">
                <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Master Template Policy: </span>
                  Changes made here apply to future project BOM generation. Existing projects and customer quotations maintain their snapshot integrity.
                </div>
              </div>

              {/* Component Lines Table Header & Action */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                      <Package className="w-4 h-4 text-amber-500" /> Component Equipment Breakdown
                    </h4>
                    <p className="text-xs text-slate-400">
                      Standard hardware sized for {template.capacity_kw} kW {template.system_type}
                    </p>
                  </div>

                  {canWrite && (
                    <button
                      type="button"
                      onClick={handleToggleAddForm}
                      className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{showAddForm ? 'Cancel Add' : 'Add Component'}</span>
                    </button>
                  )}
                </div>

                {/* Add Component Line Subform */}
                {showAddForm && canWrite && (
                  <form
                    onSubmit={handleAddItem}
                    className="p-4 bg-amber-50/40 border border-amber-200 rounded-xl space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-950 uppercase tracking-wide">
                        Add Line to Master Template
                      </span>
                    </div>

                    {addItemError && (
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        <span>{addItemError}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                      <div className="md:col-span-6 space-y-1">
                        <label className="block text-[11px] font-bold text-slate-700">
                          Active Product Equipment
                        </label>
                        <select
                          value={selectedProductId}
                          onChange={(e) => {
                            setSelectedProductId(e.target.value);
                            setAddItemError(null);
                          }}
                          disabled={loadingProducts}
                          className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 outline-none transition"
                        >
                          <option value="">
                            {loadingProducts ? 'Loading active catalog...' : '-- Select Active Product --'}
                          </option>
                          {availableProducts.map((p) => (
                            <option key={p.id} value={p.id}>
                              [{p.product_code}] {p.name} ({p.category}) — {p.unit_of_measure}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="md:col-span-3 space-y-1">
                        <label className="block text-[11px] font-bold text-slate-700">
                          Default Quantity
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0.01"
                          required
                          value={newQuantity}
                          onChange={(e) => setNewQuantity(e.target.value)}
                          className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 outline-none transition"
                        />
                      </div>

                      <div className="md:col-span-1 flex items-center h-9">
                        <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={newMandatory}
                            onChange={(e) => setNewMandatory(e.target.checked)}
                            className="w-3.5 h-3.5 text-amber-600 rounded border-slate-300 focus:ring-amber-500"
                          />
                          <span className="text-[11px] font-medium">Req?</span>
                        </label>
                      </div>

                      <div className="md:col-span-2">
                        <button
                          type="submit"
                          disabled={addingItem}
                          className="w-full h-9 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition shadow-sm disabled:opacity-50 flex items-center justify-center gap-1"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>{addingItem ? 'Adding...' : 'Add Line'}</span>
                        </button>
                      </div>
                    </div>
                  </form>
                )}

                {/* Items Table */}
                {items.length === 0 ? (
                  <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400 text-xs">
                    This BOM template has no component lines configured.
                  </div>
                ) : (
                  <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-sm">
                    <table className="w-full text-left text-xs text-slate-700">
                      <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-3 px-3.5">Product Equipment</th>
                          <th className="py-3 px-3">Category</th>
                          <th className="py-3 px-3 text-right">Default Qty</th>
                          <th className="py-3 px-3">UOM</th>
                          <th className="py-3 px-3 text-center">Mandatory</th>
                          <th className="py-3 px-3 text-right">Catalog Price</th>
                          <th className="py-3 px-3 text-right">Line Total</th>
                          {canWrite && <th className="py-3 px-3 text-center">Actions</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {items.map((it) => {
                          const isEditingThis = editingItemId === it.id;
                          const lineTotal = it.unit_price ? it.unit_price * it.default_quantity : 0;

                          return (
                            <tr key={it.id} className="hover:bg-slate-50/70 transition">
                              <td className="py-3 px-3.5 font-medium text-slate-900">
                                <div>{it.product_name}</div>
                                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                                  {it.product_code}
                                  {it.brand ? ` • ${it.brand}` : ''}
                                </div>
                              </td>

                              <td className="py-3 px-3">
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                                  {it.item_category}
                                </span>
                              </td>

                              <td className="py-3 px-3 text-right font-bold text-slate-900">
                                {isEditingThis ? (
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={editQuantity}
                                    onChange={(e) => setEditQuantity(e.target.value)}
                                    className="w-20 px-2 py-1 bg-white border border-amber-400 rounded text-right text-xs focus:ring-1 focus:ring-amber-500 outline-none"
                                  />
                                ) : (
                                  it.default_quantity
                                )}
                              </td>

                              <td className="py-3 px-3 font-mono text-[11px] text-slate-500">
                                {it.unit_of_measure}
                              </td>

                              <td className="py-3 px-3 text-center">
                                {isEditingThis ? (
                                  <input
                                    type="checkbox"
                                    checked={editMandatory}
                                    onChange={(e) => setEditMandatory(e.target.checked)}
                                    className="w-4 h-4 text-amber-600 rounded border-slate-300"
                                  />
                                ) : it.is_mandatory ? (
                                  <span className="text-emerald-700 font-semibold text-[10px] bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                                    Yes
                                  </span>
                                ) : (
                                  <span className="text-slate-500 text-[10px] bg-slate-100 px-2 py-0.5 rounded-full">
                                    Optional
                                  </span>
                                )}
                              </td>

                              <td className="py-3 px-3 text-right text-slate-600 font-mono text-[11px]">
                                {it.unit_price !== null && it.unit_price !== undefined
                                  ? `₹${it.unit_price.toLocaleString('en-IN')}`
                                  : 'N/A'}
                              </td>

                              <td className="py-3 px-3 text-right font-bold text-slate-900 font-mono text-[11px]">
                                {lineTotal > 0
                                  ? `₹${lineTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
                                  : '—'}
                              </td>

                              {canWrite && (
                                <td className="py-3 px-3 text-center">
                                  {isEditingThis ? (
                                    <div className="flex items-center justify-center gap-1.5">
                                      <button
                                        type="button"
                                        onClick={() => handleSaveEdit(it.id)}
                                        disabled={updatingItem}
                                        className="text-emerald-600 hover:text-emerald-700 p-1 rounded hover:bg-emerald-50 transition"
                                        title="Save Quantity"
                                      >
                                        <Check className="w-4 h-4" />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={handleCancelEdit}
                                        disabled={updatingItem}
                                        className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-slate-100 transition"
                                        title="Cancel"
                                      >
                                        <X className="w-4 h-4" />
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="flex items-center justify-center gap-1">
                                      <button
                                        type="button"
                                        onClick={() => handleStartEdit(it)}
                                        className="text-slate-400 hover:text-amber-600 p-1 rounded hover:bg-amber-50 transition"
                                        title="Adjust Quantity"
                                      >
                                        <Edit2 className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => setItemToDelete(it)}
                                        className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition"
                                        title="Remove Component"
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  )}
                                </td>
                              )}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition shadow-sm"
          >
            Close Detail View
          </button>
        </div>
      </div>

      {/* Delete Item Confirmation Dialog */}
      {itemToDelete && (
        <div className="fixed inset-0 z-60 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full border border-slate-200 shadow-2xl space-y-4">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="w-5 h-5" />
            </div>
            <div className="text-center space-y-1">
              <h4 className="font-bold text-slate-900 text-sm">Remove Component Line?</h4>
              <p className="text-xs text-slate-500">
                Are you sure you want to remove <span className="font-semibold">{itemToDelete.product_name}</span> from this template?
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg text-[11px] text-slate-600 border border-slate-100">
              Note: This action affects future project BOM generation only and does not alter existing project BOMs or accepted quotations.
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setItemToDelete(null)}
                disabled={deletingItem}
                className="flex-1 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={deletingItem}
                className="flex-1 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
              >
                {deletingItem ? 'Removing...' : 'Confirm Remove'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
