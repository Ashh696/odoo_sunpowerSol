import React, { useState, useEffect } from 'react';
import { X, Inbox, User, Zap, AlertCircle } from 'lucide-react';
import { createEnquiry, updateEnquiry, getCustomers, getSalesEmployees } from '../services/crmApi';

export default function EnquiryModal({ isOpen, onClose, enquiry, defaultCustomer, onSuccess }) {
  const [formData, setFormData] = useState({
    customer_id: '',
    source: 'DIRECT',
    system_type: 'ON_GRID',
    proposed_capacity_kw: '3.0',
    monthly_electricity_bill: '',
    roof_type: 'RCC_FLAT',
    assigned_sales_id: '',
    notes: '',
  });

  const [customers, setCustomers] = useState([]);
  const [salesEmployees, setSalesEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      const loadOptions = async () => {
        try {
          const [cRes, eRes] = await Promise.all([
            getCustomers({ limit: 100, is_active: true }),
            getSalesEmployees(),
          ]);
          if (cRes && cRes.data && cRes.data.items) {
            setCustomers(cRes.data.items);
          }
          if (eRes && eRes.data && eRes.data.items) {
            setSalesEmployees(eRes.data.items);
          }
        } catch (err) {
          console.error('Error loading dropdown options', err);
        }
      };
      loadOptions();

      if (enquiry) {
        setFormData({
          customer_id: String(enquiry.customer_id || ''),
          source: enquiry.source || 'DIRECT',
          system_type: enquiry.system_type || 'ON_GRID',
          proposed_capacity_kw: String(enquiry.proposed_capacity_kw || '3.0'),
          monthly_electricity_bill: enquiry.monthly_electricity_bill ? String(enquiry.monthly_electricity_bill) : '',
          roof_type: enquiry.roof_type || 'RCC_FLAT',
          assigned_sales_id: enquiry.assigned_sales_id ? String(enquiry.assigned_sales_id) : '',
          notes: enquiry.notes || '',
        });
      } else if (defaultCustomer) {
        setFormData({
          customer_id: String(defaultCustomer.id),
          source: 'DIRECT',
          system_type: 'ON_GRID',
          proposed_capacity_kw: '3.0',
          monthly_electricity_bill: '',
          roof_type: 'RCC_FLAT',
          assigned_sales_id: '',
          notes: '',
        });
      } else {
        setFormData({
          customer_id: '',
          source: 'DIRECT',
          system_type: 'ON_GRID',
          proposed_capacity_kw: '3.0',
          monthly_electricity_bill: '',
          roof_type: 'RCC_FLAT',
          assigned_sales_id: '',
          notes: '',
        });
      }
      setError(null);
    }
  }, [isOpen, enquiry, defaultCustomer]);

  if (!isOpen) return null;

  // Determine customer type for capacity constraints
  const selectedCustomer =
    customers.find((c) => String(c.id) === String(formData.customer_id)) ||
    defaultCustomer ||
    (enquiry ? { customer_type: enquiry.customer_type || 'RESIDENTIAL' } : null);

  const customerType = selectedCustomer?.customer_type || 'RESIDENTIAL';
  const isResidential = customerType === 'RESIDENTIAL';
  const minCap = isResidential ? 1.0 : 0.1;
  const maxCap = isResidential ? 5.0 : 500.0;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id) {
      setError('Please select or register a customer for this enquiry');
      return;
    }

    const cap = parseFloat(formData.proposed_capacity_kw);
    if (isNaN(cap)) {
      setError('Please enter a valid numeric solar capacity in kW');
      return;
    }

    if (isResidential && (cap < 1.0 || cap > 5.0)) {
      setError(`Residential solar capacity must be between 1.0 kW and 5.0 kW. Provided: ${cap} kW`);
      return;
    }

    if (!isResidential && (cap <= 0.0 || cap > 500.0)) {
      setError(`${customerType} capacity must be greater than 0 kW and up to 500.0 kW. Provided: ${cap} kW`);
      return;
    }

    setLoading(true);
    setError(null);

    const payload = {
      customer_id: parseInt(formData.customer_id, 10),
      source: formData.source,
      system_type: formData.system_type,
      proposed_capacity_kw: cap,
      monthly_electricity_bill: formData.monthly_electricity_bill ? parseFloat(formData.monthly_electricity_bill) : null,
      roof_type: formData.roof_type,
      assigned_sales_id: formData.assigned_sales_id ? parseInt(formData.assigned_sales_id, 10) : null,
      notes: formData.notes ? formData.notes.trim() : null,
    };

    try {
      if (enquiry) {
        await updateEnquiry(enquiry.id, payload);
      } else {
        await createEnquiry(payload);
      }
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save enquiry');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-500/10 text-amber-600 rounded-lg">
              <Inbox className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {enquiry ? `Edit Enquiry (${enquiry.enquiry_number})` : 'New Solar Rooftop Enquiry'}
              </h3>
              <p className="text-xs text-slate-500">Record customer requirements and sizing for sales pipeline</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Customer *</label>
            <select
              name="customer_id"
              required
              disabled={!!enquiry || !!defaultCustomer}
              value={formData.customer_id}
              onChange={handleChange}
              className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:bg-slate-100"
            >
              <option value="">-- Select Customer --</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name} ({c.customer_type} • {c.phone} - {c.city})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">System Type *</label>
              <select
                name="system_type"
                value={formData.system_type}
                onChange={handleChange}
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="ON_GRID">On-Grid (Net Metered)</option>
                <option value="OFF_GRID">Off-Grid (Battery Backed)</option>
                <option value="HYBRID">Hybrid (Grid + Battery)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Proposed Capacity (kW) *</label>
              <input
                type="number"
                step="0.1"
                min={minCap}
                max={maxCap}
                name="proposed_capacity_kw"
                required
                value={formData.proposed_capacity_kw}
                onChange={handleChange}
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500 font-semibold"
              />
              <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
                {isResidential
                  ? 'Residential rooftop limits: 1.0 kW to 5.0 kW'
                  : `${customerType} limits: > 0 kW to 500.0 kW`}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Monthly Electricity Bill (₹)</label>
              <input
                type="number"
                step="1"
                min="0"
                name="monthly_electricity_bill"
                value={formData.monthly_electricity_bill}
                onChange={handleChange}
                placeholder="e.g. 3500"
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Roof Type</label>
              <select
                name="roof_type"
                value={formData.roof_type}
                onChange={handleChange}
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="RCC_FLAT">RCC Flat Slab</option>
                <option value="METAL_SHED">Industrial Metal Shed</option>
                <option value="TILED_ROOF">Tiled Sloped Roof</option>
                <option value="OTHER">Other / Complex</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Enquiry Source</label>
              <select
                name="source"
                value={formData.source}
                onChange={handleChange}
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="DIRECT">Direct Walk-in</option>
                <option value="WEBSITE">Website Form</option>
                <option value="WHATSAPP">WhatsApp Lead</option>
                <option value="REFERRAL">Customer Referral</option>
                <option value="CAMPAIGN">Marketing Campaign</option>
                <option value="PHONE">Inbound Phone Call</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Assign Sales Representative</label>
              <select
                name="assigned_sales_id"
                value={formData.assigned_sales_id}
                onChange={handleChange}
                className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="">-- Unassigned --</option>
                {salesEmployees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.user_full_name} ({emp.employee_code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Customer Requirements & Notes</label>
            <textarea
              name="notes"
              rows={2}
              value={formData.notes}
              onChange={handleChange}
              placeholder="e.g. Daytime load is high due to AC usage; requested quote for Tier-1 Mono PERC panels..."
              className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {loading ? 'Saving...' : enquiry ? 'Update Enquiry' : 'Create Enquiry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
