import React, { useState, useEffect } from 'react';
import {
  X,
  Layers,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Package,
  Zap,
  Info,
} from 'lucide-react';
import { createBomTemplate, updateBomTemplate } from '../services/bomApi';
import { getProducts } from '../services/productApi';

const SYSTEM_TYPES = [
  { value: 'ON_GRID', label: 'On-Grid (Grid-Tied Net Metered)' },
  { value: 'OFF_GRID', label: 'Off-Grid (Battery Energy Storage)' },
  { value: 'HYBRID', label: 'Hybrid (Grid-Tied with Battery Backup)' },
];

export default function BOMTemplateModal({
  isOpen,
  onClose,
  onSuccess,
  templateToEdit = null,
}) {
  const isEditing = Boolean(templateToEdit);

  // Form states
  const [templateName, setTemplateName] = useState('');
  const [systemType, setSystemType] = useState('ON_GRID');
  const [capacityKw, setCapacityKw] = useState('3.0');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);

  // Item builder states (used during creation)
  const [items, setItems] = useState([]);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // New item selector states
  const [selectedProductId, setSelectedProductId] = useState('');
  const [itemQuantity, setItemQuantity] = useState('1');
  const [itemMandatory, setItemMandatory] = useState(true);
  const [itemError, setItemError] = useState(null);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Fetch active products on modal open
  useEffect(() => {
    if (isOpen) {
      setError(null);
      setItemError(null);

      // Load products for item builder
      setLoadingProducts(true);
      getProducts({ is_active: true, limit: 100 })
        .then((res) => {
          const prods = res?.data?.items || [];
          setAvailableProducts(prods);
        })
        .catch((err) => {
          console.error('Failed to load active products for BOM template builder:', err);
        })
        .finally(() => setLoadingProducts(false));

      if (templateToEdit) {
        setTemplateName(templateToEdit.template_name || '');
        setSystemType(templateToEdit.system_type || 'ON_GRID');
        setCapacityKw(
          templateToEdit.capacity_kw !== null && templateToEdit.capacity_kw !== undefined
            ? String(templateToEdit.capacity_kw)
            : '3.0'
        );
        setDescription(templateToEdit.description || '');
        setIsActive(templateToEdit.is_active !== undefined ? templateToEdit.is_active : true);
        setItems([]);
      } else {
        setTemplateName('');
        setSystemType('ON_GRID');
        setCapacityKw('3.0');
        setDescription('');
        setIsActive(true);
        setItems([]);
        setSelectedProductId('');
        setItemQuantity('1');
        setItemMandatory(true);
      }
    }
  }, [isOpen, templateToEdit]);

  // Handle adding an item to the local creation builder
  const handleAddItem = (e) => {
    if (e) e.preventDefault();
    setItemError(null);

    if (!selectedProductId) {
      setItemError('Please select a product equipment from the catalog.');
      return;
    }

    const prodIdNum = parseInt(selectedProductId, 10);
    const existing = items.find((it) => it.product_id === prodIdNum);
    if (existing) {
      setItemError(`This product is already added (${existing.product_name}).`);
      return;
    }

    const qty = parseFloat(itemQuantity);
    if (isNaN(qty) || qty <= 0) {
      setItemError('Default quantity must be a positive number greater than 0.');
      return;
    }

    const prod = availableProducts.find((p) => p.id === prodIdNum);
    if (!prod) {
      setItemError('Selected product not found in active catalog.');
      return;
    }

    const newItem = {
      product_id: prod.id,
      product_code: prod.product_code,
      product_name: prod.name,
      item_category: prod.category,
      unit_of_measure: prod.unit_of_measure || 'NOS',
      unit_price: prod.base_price !== null && prod.base_price !== undefined ? parseFloat(prod.base_price) : 0,
      default_quantity: qty,
      is_mandatory: itemMandatory,
    };

    setItems([...items, newItem]);
    setSelectedProductId('');
    setItemQuantity('1');
    setItemMandatory(true);
    setItemError(null);
  };

  const handleRemoveItem = (indexToRemove) => {
    setItems(items.filter((_, idx) => idx !== indexToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const cleanName = templateName.trim();
    if (!cleanName) {
      setError('Template name is required.');
      return;
    }

    const capNum = parseFloat(capacityKw);
    if (isNaN(capNum) || capNum <= 0) {
      setError('System capacity (kW) must be greater than 0.');
      return;
    }

    setSubmitting(true);
    try {
      if (isEditing) {
        const payload = {
          template_name: cleanName,
          system_type: systemType,
          capacity_kw: capNum,
          description: description.trim() || null,
          is_active: isActive,
        };
        await updateBomTemplate(templateToEdit.id, payload);
      } else {
        const payload = {
          template_name: cleanName,
          system_type: systemType,
          capacity_kw: capNum,
          description: description.trim() || null,
          is_active: isActive,
          items: items.map((it) => ({
            product_id: it.product_id,
            item_category: it.item_category,
            default_quantity: it.default_quantity,
            unit_of_measure: it.unit_of_measure,
            is_mandatory: it.is_mandatory,
          })),
        };
        await createBomTemplate(payload);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save BOM template. Please check the inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const totalEstimatedCost = items.reduce(
    (sum, it) => sum + (it.unit_price || 0) * (it.default_quantity || 0),
    0
  );

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-3xl w-full overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="bg-slate-900 px-6 py-4 flex items-center justify-between text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight">
                {isEditing ? 'Edit BOM Template' : 'Create Master BOM Template'}
              </h3>
              <p className="text-xs text-slate-400">
                {isEditing
                  ? `Update header parameters for ${templateToEdit.template_name}`
                  : 'Define standardized system architecture, capacity, and default bill of materials'}
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
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-600" />
              <div className="flex-1 font-medium">{error}</div>
            </div>
          )}

          {/* Section 1: Template Specification */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-amber-500" /> Master Architecture Parameters
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Template Name */}
              <div className="md:col-span-2 space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Template Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Residential 3kW Standard On-Grid System"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:bg-white outline-none transition"
                />
              </div>

              {/* System Type */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  System Architecture <span className="text-rose-500">*</span>
                </label>
                <select
                  value={systemType}
                  onChange={(e) => setSystemType(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:bg-white outline-none transition"
                >
                  {SYSTEM_TYPES.map((st) => (
                    <option key={st.value} value={st.value}>
                      {st.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Capacity kW */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Nominal Capacity (kW) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="100.0"
                  required
                  value={capacityKw}
                  onChange={(e) => setCapacityKw(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:bg-white outline-none transition"
                />
              </div>

              {/* Description */}
              <div className="md:col-span-2 space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  Engineering Notes & Scope
                </label>
                <textarea
                  rows="2"
                  placeholder="Optional technical notes, standard structural requirements, or warranty constraints..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 focus:bg-white outline-none transition"
                />
              </div>

              {/* Active Toggle */}
              <div className="md:col-span-2 flex items-center gap-3 pt-1">
                <input
                  type="checkbox"
                  id="tpl-active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 text-amber-600 rounded border-slate-300 focus:ring-amber-500 cursor-pointer"
                />
                <label
                  htmlFor="tpl-active"
                  className="text-sm font-semibold text-slate-800 cursor-pointer select-none"
                >
                  Template is Active for Project Deployment
                </label>
              </div>
            </div>
          </div>

          {/* Section 2: Component Items Builder (During Creation) */}
          {!isEditing && (
            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                    <Package className="w-3.5 h-3.5 text-amber-500" /> Bill of Materials Components ({items.length})
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Select equipment from the active product catalog and configure default quantities.
                  </p>
                </div>
                {totalEstimatedCost > 0 && (
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                    Est. Cost: ₹{totalEstimatedCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </span>
                )}
              </div>

              {itemError && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>{itemError}</span>
                </div>
              )}

              {/* Add Component Subform */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                  {/* Product Picker */}
                  <div className="md:col-span-6 space-y-1">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600">
                      Product Catalog Item
                    </label>
                    <select
                      value={selectedProductId}
                      onChange={(e) => {
                        setSelectedProductId(e.target.value);
                        setItemError(null);
                      }}
                      disabled={loadingProducts}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 outline-none transition"
                    >
                      <option value="">
                        {loadingProducts ? 'Loading active products...' : '-- Select Active Equipment --'}
                      </option>
                      {availableProducts.map((p) => (
                        <option key={p.id} value={p.id}>
                          [{p.product_code}] {p.name} ({p.category}) — {p.unit_of_measure}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Quantity */}
                  <div className="md:col-span-3 space-y-1">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600">
                      Default Qty
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={itemQuantity}
                      onChange={(e) => setItemQuantity(e.target.value)}
                      placeholder="Qty"
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-amber-500 outline-none transition"
                    />
                  </div>

                  {/* Mandatory Checkbox */}
                  <div className="md:col-span-1 flex items-center h-9">
                    <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={itemMandatory}
                        onChange={(e) => setItemMandatory(e.target.checked)}
                        className="w-3.5 h-3.5 text-amber-600 rounded border-slate-300 focus:ring-amber-500"
                      />
                      <span className="text-[11px] font-medium">Req?</span>
                    </label>
                  </div>

                  {/* Add Button */}
                  <div className="md:col-span-2">
                    <button
                      type="button"
                      onClick={handleAddItem}
                      className="w-full h-9 flex items-center justify-center gap-1 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-xs transition shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Line</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Items List Table */}
              {items.length === 0 ? (
                <div className="p-6 text-center border-2 border-dashed border-slate-200 rounded-xl text-slate-400 text-xs">
                  No components added yet. You may add components now or manage them in the detail view after creation.
                </div>
              ) : (
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Product / Equipment</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3 text-right">Default Qty</th>
                        <th className="py-2.5 px-3">UOM</th>
                        <th className="py-2.5 px-3 text-center">Mandatory</th>
                        <th className="py-2.5 px-3 text-right">Subtotal</th>
                        <th className="py-2.5 px-3 text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {items.map((it, idx) => (
                        <tr key={it.product_id} className="hover:bg-slate-50/60 transition">
                          <td className="py-2.5 px-3 font-medium text-slate-900">
                            <div>{it.product_name}</div>
                            <div className="text-[10px] text-slate-400 font-mono">{it.product_code}</div>
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                              {it.item_category}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                            {it.default_quantity}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">
                            {it.unit_of_measure}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {it.is_mandatory ? (
                              <span className="text-emerald-700 font-semibold text-[10px] bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                                Yes
                              </span>
                            ) : (
                              <span className="text-slate-500 text-[10px] bg-slate-100 px-2 py-0.5 rounded-full">
                                Optional
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium text-slate-700">
                            ₹{(it.unit_price * it.default_quantity).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveItem(idx)}
                              className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition"
                              title="Remove item from builder"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {isEditing && (
            <div className="p-3 bg-sky-50 border border-sky-200 rounded-xl text-sky-800 text-xs flex items-start gap-2.5">
              <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
              <div>
                Template component lines can be added, adjusted, or removed directly from the{' '}
                <span className="font-semibold">Template Detail View</span>.
              </div>
            </div>
          )}

          {/* Modal Footer Controls */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-sm font-semibold hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-xl text-sm font-bold shadow-md shadow-amber-500/20 transition flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create BOM Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
