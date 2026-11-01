import React, { useState, useEffect } from 'react';
import { X, Package, CheckCircle2, AlertCircle, Clock, Layers } from 'lucide-react';
import { createProduct, updateProduct } from '../services/productApi';

const CATEGORIES = [
  { value: 'SOLAR_PANEL', label: 'Solar Panel (PV Module)' },
  { value: 'INVERTER', label: 'Solar Inverter (Grid-tie / Hybrid)' },
  { value: 'BATTERY', label: 'Battery Storage (LiFePO4 / Lead-Acid)' },
  { value: 'STRUCTURE', label: 'Mounting Structure (Elevated / Flush / Tin)' },
  { value: 'CABLES', label: 'Solar Cables (DC / AC)' },
  { value: 'DCDB', label: 'DC Distribution Box (DCDB)' },
  { value: 'ACDB', label: 'AC Distribution Box (ACDB)' },
  { value: 'LIGHTNING_ARRESTER', label: 'Lightning Arrester (LA)' },
  { value: 'EARTHING', label: 'Earthing Rods & Chemical Compound' },
  { value: 'MISC', label: 'Miscellaneous Hardware & Connectors' },
];

const UNITS = ['NOS', 'METERS', 'SETS', 'KG', 'FEET', 'ROLLS'];

export default function ProductModal({ isOpen, onClose, onSuccess, productToEdit = null }) {
  const isEditing = Boolean(productToEdit);

  const [productCode, setProductCode] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('SOLAR_PANEL');
  const [brand, setBrand] = useState('');
  const [modelNumber, setModelNumber] = useState('');
  const [wattageCapacity, setWattageCapacity] = useState('');
  const [unitOfMeasure, setUnitOfMeasure] = useState('NOS');
  const [isSerialized, setIsSerialized] = useState(false);
  const [basePrice, setBasePrice] = useState('');
  const [taxRatePercent, setTaxRatePercent] = useState('12');
  const [minStockAlert, setMinStockAlert] = useState('5');
  const [isActive, setIsActive] = useState(true);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (productToEdit) {
        setProductCode(productToEdit.product_code || '');
        setName(productToEdit.name || '');
        setCategory(productToEdit.category || 'SOLAR_PANEL');
        setBrand(productToEdit.brand || '');
        setModelNumber(productToEdit.model_number || '');
        setWattageCapacity(productToEdit.wattage_or_capacity || '');
        setUnitOfMeasure(productToEdit.unit_of_measure || 'NOS');
        setIsSerialized(Boolean(productToEdit.is_serialized));
        setBasePrice(productToEdit.base_price !== null && productToEdit.base_price !== undefined ? String(productToEdit.base_price) : '');
        setTaxRatePercent(productToEdit.tax_rate_percent !== null && productToEdit.tax_rate_percent !== undefined ? String(productToEdit.tax_rate_percent) : '12');
        setMinStockAlert(productToEdit.min_stock_alert !== null && productToEdit.min_stock_alert !== undefined ? String(productToEdit.min_stock_alert) : '5');
        setIsActive(productToEdit.is_active !== undefined ? productToEdit.is_active : true);
      } else {
        setProductCode('');
        setName('');
        setCategory('SOLAR_PANEL');
        setBrand('');
        setModelNumber('');
        setWattageCapacity('');
        setUnitOfMeasure('NOS');
        setIsSerialized(false);
        setBasePrice('');
        setTaxRatePercent('12');
        setMinStockAlert('5');
        setIsActive(true);
      }
    }
  }, [isOpen, productToEdit]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const cleanCode = productCode.trim().toUpperCase();
    const cleanName = name.trim();

    if (!cleanCode) {
      setError('Product code / SKU is required.');
      return;
    }
    if (!cleanName) {
      setError('Product name is required.');
      return;
    }

    const price = parseFloat(basePrice);
    if (isNaN(price) || price < 0) {
      setError('Base price must be zero or a positive number (>= ₹0.00).');
      return;
    }

    const tax = parseFloat(taxRatePercent);
    if (isNaN(tax) || tax < 0 || tax > 100) {
      setError('Tax rate percent must be between 0% and 100%.');
      return;
    }

    const minStock = parseFloat(minStockAlert);
    if (isNaN(minStock) || minStock < 0) {
      setError('Minimum stock alert threshold must be zero or positive (>= 0).');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        product_code: cleanCode,
        name: cleanName,
        category,
        brand: brand.trim() || undefined,
        model_number: modelNumber.trim() || undefined,
        wattage_or_capacity: wattageCapacity.trim() || undefined,
        unit_of_measure: unitOfMeasure,
        is_serialized: isSerialized,
        base_price: price,
        tax_rate_percent: tax,
        min_stock_alert: minStock,
        is_active: isActive,
      };

      if (isEditing) {
        await updateProduct(productToEdit.id, payload);
      } else {
        await createProduct(payload);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save product');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 flex items-center justify-center font-bold">
              <Package className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <h3 className="font-bold text-base tracking-tight">
                {isEditing ? 'Edit Catalog Product' : 'Add New Equipment / Product'}
              </h3>
              <p className="text-xs text-amber-400 font-mono">
                {isEditing ? productToEdit.product_code : 'Master Equipment Catalog'}
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

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Product Code */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Product Code / SKU <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={productCode}
                onChange={(e) => setProductCode(e.target.value.toUpperCase())}
                placeholder="e.g. MOD-550W-SP"
                className="w-full text-xs font-mono font-bold border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
              <p className="text-[10px] text-slate-400 mt-1">Unique equipment identifier.</p>
            </div>

            {/* Category */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Equipment Category <span className="text-rose-500">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full text-xs font-semibold border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                required
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Product Name */}
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Product Name / Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. 550W Mono PERC Half-Cut Dual Glass Solar Module"
                className="w-full text-xs font-medium border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>

            {/* Brand */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Manufacturer / Brand
              </label>
              <input
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="e.g. SunPower, Solis, Polycab"
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>

            {/* Model Number */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Model Number
              </label>
              <input
                type="text"
                value={modelNumber}
                onChange={(e) => setModelNumber(e.target.value)}
                placeholder="e.g. SP-550-MH"
                className="w-full text-xs font-mono border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>

            {/* Capacity / Wattage */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Capacity / Wattage Spec
              </label>
              <input
                type="text"
                value={wattageCapacity}
                onChange={(e) => setWattageCapacity(e.target.value)}
                placeholder="e.g. 550W, 5kW, 150Ah"
                className="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
            </div>

            {/* Unit of Measure */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Unit of Measure (UOM)
              </label>
              <select
                value={unitOfMeasure}
                onChange={(e) => setUnitOfMeasure(e.target.value)}
                className="w-full text-xs font-semibold border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              >
                {UNITS.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </div>

            {/* Base Price */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Base Unit Price (₹) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={basePrice}
                onChange={(e) => setBasePrice(e.target.value)}
                placeholder="0.00"
                className="w-full text-xs font-mono font-bold border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
              <p className="text-[10px] text-slate-400 mt-1">Catalog price before GST.</p>
            </div>

            {/* Tax Rate Percent */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                GST Tax Rate (%) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                required
                value={taxRatePercent}
                onChange={(e) => setTaxRatePercent(e.target.value)}
                placeholder="12.00"
                className="w-full text-xs font-mono border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
              <p className="text-[10px] text-slate-400 mt-1">Typical solar GST is 12% or 18%.</p>
            </div>

            {/* Min Stock Alert */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Min Stock Alert Level
              </label>
              <input
                type="number"
                step="1"
                min="0"
                value={minStockAlert}
                onChange={(e) => setMinStockAlert(e.target.value)}
                placeholder="5"
                className="w-full text-xs font-mono border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
              />
              <p className="text-[10px] text-slate-400 mt-1">Reorder threshold for warehouse.</p>
            </div>

            {/* Serialization and Active Flags */}
            <div className="flex flex-col justify-center space-y-2.5 pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
                <input
                  type="checkbox"
                  checked={isSerialized}
                  onChange={(e) => setIsSerialized(e.target.checked)}
                  className="rounded border-slate-300 text-amber-500 focus:ring-amber-500 w-4 h-4"
                />
                <span>Track Unique Serial Numbers (Panels / Inverters)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="rounded border-slate-300 text-amber-500 focus:ring-amber-500 w-4 h-4"
                />
                <span>Active in Catalog (Available for BOM / Quotation)</span>
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-lg text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{isEditing ? 'Save Changes' : 'Create Product'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
