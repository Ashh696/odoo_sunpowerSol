import React, { useState, useEffect } from 'react';
import {
  X,
  Plus,
  Trash2,
  AlertCircle,
  FileText,
  Calculator,
  Zap,
  Package,
  Layers,
  Calendar,
  DollarSign,
  HelpCircle,
  ShieldAlert,
} from 'lucide-react';
import { createQuotation, updateQuotation } from '../services/quotationApi';
import { getEnquiries } from '../services/crmApi';
import { getSurveys } from '../services/surveyApi';
import { getProducts } from '../services/productApi';

export default function QuotationModal({
  isOpen,
  onClose,
  onSuccess,
  quotationToEdit = null,
  initialEnquiryId = null,
}) {
  const isEditing = Boolean(quotationToEdit);

  // Form State
  const [enquiryId, setEnquiryId] = useState('');
  const [surveyId, setSurveyId] = useState('');
  const [systemType, setSystemType] = useState('ON_GRID');
  const [capacityKw, setCapacityKw] = useState('');
  const [installationCost, setInstallationCost] = useState('0.00');
  const [subsidyEstimate, setSubsidyEstimate] = useState('');
  const [subsidyOverrideReason, setSubsidyOverrideReason] = useState('');
  const [validUntil, setValidUntil] = useState('');
  const [terms, setTerms] = useState(
    '1. 50% advance along with confirmed work order.\n2. 40% on dispatch of equipment to site.\n3. 10% on successful commissioning and net-metering synchronization.\n4. Comprehensive 5-year workmanship warranty and 25-year panel performance guarantee.'
  );

  // Line items state
  const [items, setItems] = useState([
    {
      product_id: '',
      item_description: '',
      quantity: 1,
      unit_price: '',
      discount_amount: '0.00',
      tax_rate_percent: '12.00',
    },
  ]);

  // Lookup Options
  const [enquiries, setEnquiries] = useState([]);
  const [approvedSurveys, setApprovedSurveys] = useState([]);
  const [products, setProducts] = useState([]);

  // UI state
  const [loadingLookups, setLoadingLookups] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 1. Load active products and enquiries when opened
  useEffect(() => {
    if (!isOpen) return;

    setLoadingLookups(true);
    setError(null);

    Promise.all([
      getProducts({ is_active: true, limit: 100 }),
      getEnquiries({ limit: 100 }),
    ])
      .then(([prodRes, enqRes]) => {
        if (prodRes?.data?.items) setProducts(prodRes.data.items);
        if (enqRes?.data?.items) setEnquiries(enqRes.data.items);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load reference equipment and enquiries.');
      })
      .finally(() => setLoadingLookups(false));

    // Calculate default valid_until (today + 30 days)
    const d = new Date();
    d.setDate(d.getDate() + 30);
    const defValid = d.toISOString().split('T')[0];

    if (quotationToEdit) {
      setEnquiryId(quotationToEdit.enquiry_id || '');
      setSurveyId(quotationToEdit.survey_id || '');
      setSystemType(quotationToEdit.system_type || 'ON_GRID');
      setCapacityKw(quotationToEdit.capacity_kw || '');
      setInstallationCost(quotationToEdit.installation_cost || '0.00');
      setSubsidyEstimate(quotationToEdit.subsidy_estimate || '');
      setValidUntil(quotationToEdit.valid_until || defValid);
      setTerms(quotationToEdit.terms_and_conditions || '');

      if (quotationToEdit.items && quotationToEdit.items.length > 0) {
        setItems(
          quotationToEdit.items.map((it) => ({
            product_id: it.product_id,
            item_description: it.item_description,
            quantity: it.quantity,
            unit_price: it.unit_price,
            discount_amount: it.discount_amount || '0.00',
            tax_rate_percent: it.tax_rate_percent || '12.00',
          }))
        );
      }
    } else {
      // New quotation
      setEnquiryId(initialEnquiryId ? String(initialEnquiryId) : '');
      setSurveyId('');
      setSystemType('ON_GRID');
      setCapacityKw('');
      setInstallationCost('0.00');
      setSubsidyEstimate('');
      setSubsidyOverrideReason('');
      setValidUntil(defValid);
      setItems([
        {
          product_id: '',
          item_description: '',
          quantity: 1,
          unit_price: '',
          discount_amount: '0.00',
          tax_rate_percent: '12.00',
        },
      ]);
    }
  }, [isOpen, quotationToEdit, initialEnquiryId]);

  // 2. Fetch approved surveys whenever enquiryId changes
  useEffect(() => {
    if (!enquiryId) {
      setApprovedSurveys([]);
      return;
    }

    getSurveys({ enquiry_id: parseInt(enquiryId, 10), status: 'APPROVED' })
      .then((res) => {
        const sList = res?.data?.items || [];
        setApprovedSurveys(sList);
        if (sList.length === 1 && !isEditing) {
          setSurveyId(sList[0].id);
        }
      })
      .catch((err) => {
        console.warn('Error loading approved surveys for enquiry:', err);
        setApprovedSurveys([]);
      });

    // If new quotation, also auto-fill spec from enquiry
    if (!isEditing && enquiries.length > 0) {
      const selectedEnq = enquiries.find((e) => e.id === parseInt(enquiryId, 10));
      if (selectedEnq) {
        if (selectedEnq.system_type) setSystemType(selectedEnq.system_type);
        if (selectedEnq.proposed_capacity_kw) setCapacityKw(selectedEnq.proposed_capacity_kw);
      }
    }
  }, [enquiryId, enquiries, isEditing]);

  // Line item handlers
  const handleProductChange = (index, prodIdStr) => {
    const prodId = parseInt(prodIdStr, 10);
    const prod = products.find((p) => p.id === prodId);
    const updated = [...items];
    if (prod) {
      updated[index] = {
        ...updated[index],
        product_id: prod.id,
        item_description: `${prod.name} (${prod.brand || 'Standard'} - ${prod.model_number || prod.product_code})`,
        unit_price: prod.base_price,
        tax_rate_percent: prod.tax_rate_percent,
      };
    } else {
      updated[index].product_id = '';
    }
    setItems(updated);
  };

  const handleItemFieldChange = (index, field, value) => {
    const updated = [...items];
    updated[index][field] = value;
    setItems(updated);
  };

  const handleAddItem = () => {
    setItems([
      ...items,
      {
        product_id: '',
        item_description: '',
        quantity: 1,
        unit_price: '',
        discount_amount: '0.00',
        tax_rate_percent: '12.00',
      },
    ]);
  };

  const handleRemoveItem = (index) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, idx) => idx !== index));
  };

  // Client-side instant preview calculation (server remains authoritative)
  const previewTotals = () => {
    let productBaseTotal = 0;
    let taxTotal = 0;

    items.forEach((it) => {
      const qty = parseFloat(it.quantity) || 0;
      const price = parseFloat(it.unit_price) || 0;
      const disc = parseFloat(it.discount_amount) || 0;
      const taxRate = parseFloat(it.tax_rate_percent) || 0;

      const base = Math.max(0, qty * price - disc);
      const tax = base * (taxRate / 100);
      productBaseTotal += base;
      taxTotal += tax;
    });

    const instCost = parseFloat(installationCost) || 0;
    const gross = productBaseTotal + taxTotal + instCost;
    const subEstimate = parseFloat(subsidyEstimate) || 0;
    const net = Math.max(0, gross - subEstimate);

    return {
      productBaseTotal: productBaseTotal.toFixed(2),
      taxTotal: taxTotal.toFixed(2),
      gross: gross.toFixed(2),
      net: net.toFixed(2),
    };
  };

  const totals = previewTotals();

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!enquiryId) {
      setError('Please select an eligible enquiry.');
      return;
    }
    if (!capacityKw || parseFloat(capacityKw) <= 0) {
      setError('System capacity (kW) must be strictly greater than zero.');
      return;
    }
    if (approvedSurveys.length > 0 && !surveyId) {
      setError('This enquiry has an approved site survey. You must select an approved survey.');
      return;
    }

    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      if (!it.product_id) {
        setError(`Line item #${i + 1} must select a product.`);
        return;
      }
      if (!it.quantity || parseFloat(it.quantity) <= 0) {
        setError(`Line item #${i + 1} quantity must be greater than zero.`);
        return;
      }
      if (parseFloat(it.discount_amount) < 0) {
        setError(`Line item #${i + 1} discount cannot be negative.`);
        return;
      }
    }

    setSubmitting(true);

    try {
      const formattedItems = items.map((it) => ({
        product_id: parseInt(it.product_id, 10),
        item_description: it.item_description.trim(),
        quantity: parseFloat(it.quantity),
        unit_price: parseFloat(it.unit_price),
        discount_amount: parseFloat(it.discount_amount || '0'),
        tax_rate_percent: parseFloat(it.tax_rate_percent || '12'),
      }));

      const payload = {
        enquiry_id: parseInt(enquiryId, 10),
        survey_id: surveyId ? parseInt(surveyId, 10) : undefined,
        system_type: systemType,
        capacity_kw: parseFloat(capacityKw),
        installation_cost: parseFloat(installationCost || '0'),
        subsidy_estimate: subsidyEstimate ? parseFloat(subsidyEstimate) : undefined,
        subsidy_override_reason: subsidyOverrideReason.trim() || undefined,
        valid_until: validUntil || undefined,
        terms_and_conditions: terms.trim() || undefined,
        items: formattedItems,
      };

      if (isEditing) {
        await updateQuotation(quotationToEdit.id, payload);
      } else {
        await createQuotation(payload);
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save quotation. Check server validation details.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950 text-white border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">
                {isEditing ? `Edit Quotation ${quotationToEdit?.quotation_number}` : 'Create New Quotation'}
              </h3>
              <p className="text-xs text-amber-300">
                {isEditing ? 'Update line items, pricing and terms' : 'DRAFT Status • 30-Day Validity Benchmark'}
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

        {/* Error Banner */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
            <div className="flex-1 font-medium">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Section 1: Enquiry & Survey Association */}
          <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200 space-y-4">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-amber-600" /> Lead & Technical Feasibility Association
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Enquiry Reference <span className="text-rose-500">*</span>
                </label>
                <select
                  disabled={isEditing || Boolean(initialEnquiryId)}
                  value={enquiryId}
                  onChange={(e) => setEnquiryId(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 disabled:bg-slate-100"
                  required
                >
                  <option value="">-- Select Customer Enquiry --</option>
                  {enquiries.map((enq) => (
                    <option key={enq.id} value={enq.id}>
                      {enq.enquiry_number} — {enq.customer_name} ({enq.proposed_capacity_kw}kW {enq.system_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Approved Site Survey {approvedSurveys.length > 0 && <span className="text-rose-500">*</span>}
                </label>
                <select
                  disabled={isEditing}
                  value={surveyId}
                  onChange={(e) => setSurveyId(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500"
                >
                  <option value="">
                    {approvedSurveys.length > 0 ? '-- Select Approved Survey --' : '(No approved survey required/found)'}
                  </option>
                  {approvedSurveys.map((srv) => (
                    <option key={srv.id} value={srv.id}>
                      {srv.survey_number} — Feasibility: {srv.technical_feasibility} (Approved)
                    </option>
                  ))}
                </select>
                {approvedSurveys.length === 0 && enquiryId && (
                  <p className="text-[11px] text-slate-500 mt-1 italic">
                    No approved survey recorded for this enquiry. Quotation will be created without site survey linkage.
                  </p>
                )}
              </div>
            </div>

            {/* Spec Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-200">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  System Architecture <span className="text-rose-500">*</span>
                </label>
                <select
                  value={systemType}
                  onChange={(e) => setSystemType(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500"
                >
                  <option value="ON_GRID">On-Grid (Net Metered)</option>
                  <option value="OFF_GRID">Off-Grid (Battery Bank)</option>
                  <option value="HYBRID">Hybrid (Grid + Storage)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Capacity (kW) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.1"
                  placeholder="e.g. 3.0"
                  value={capacityKw}
                  onChange={(e) => setCapacityKw(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Valid Until <span className="text-rose-500">*</span>
                </label>
                <input
                  type="date"
                  value={validUntil}
                  onChange={(e) => setValidUntil(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Section 2: Bill of Materials & Line Items */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Package className="w-4 h-4 text-amber-600" /> Quotation Bill of Materials Line Items
              </h4>
              <button
                type="button"
                onClick={handleAddItem}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-sm transition"
              >
                <Plus className="w-3.5 h-3.5" /> Add Component
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100/80 border-b border-slate-200 text-slate-600 font-bold">
                    <tr>
                      <th className="py-2.5 px-3 w-48">Catalog Product *</th>
                      <th className="py-2.5 px-3 min-w-[200px]">Description</th>
                      <th className="py-2.5 px-3 w-24">Qty *</th>
                      <th className="py-2.5 px-3 w-28">Price (₹)</th>
                      <th className="py-2.5 px-3 w-24">Disc (₹)</th>
                      <th className="py-2.5 px-3 w-20">GST %</th>
                      <th className="py-2.5 px-3 w-10 text-center"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((it, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3">
                          <select
                            value={it.product_id}
                            onChange={(e) => handleProductChange(idx, e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500"
                            required
                          >
                            <option value="">-- Choose Product --</option>
                            {products.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.product_code} ({p.name})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="text"
                            placeholder="Specification / description"
                            value={it.item_description}
                            onChange={(e) => handleItemFieldChange(idx, 'item_description', e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            step="0.01"
                            min="0.01"
                            value={it.quantity}
                            onChange={(e) => handleItemFieldChange(idx, 'quantity', e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500 text-right"
                            required
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            placeholder="Snapshot"
                            value={it.unit_price}
                            onChange={(e) => handleItemFieldChange(idx, 'unit_price', e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={it.discount_amount}
                            onChange={(e) => handleItemFieldChange(idx, 'discount_amount', e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="100"
                            value={it.tax_rate_percent}
                            onChange={(e) => handleItemFieldChange(idx, 'tax_rate_percent', e.target.value)}
                            className="w-full text-xs rounded border border-slate-300 p-1.5 bg-white text-slate-800 focus:ring-1 focus:ring-amber-500 text-right"
                          />
                        </td>
                        <td className="py-2 px-3 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveItem(idx)}
                            disabled={items.length <= 1}
                            className="text-slate-400 hover:text-rose-600 disabled:opacity-30 transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Section 3: Commercial Terms, Installation & Subsidy Override */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Installation, Mounting & Commissioning Cost (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={installationCost}
                  onChange={(e) => setInstallationCost(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 font-mono"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-slate-700">
                    DBT Subsidy Estimate (₹)
                  </label>
                  <span className="text-[10px] text-slate-400">Leave blank for standard PM Surya Ghar calculation</span>
                </div>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Auto-calculated by policy"
                  value={subsidyEstimate}
                  onChange={(e) => setSubsidyEstimate(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 font-mono"
                />
              </div>

              {subsidyEstimate && (
                <div>
                  <label className="block text-xs font-semibold text-amber-900 mb-1 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                    Subsidy Override Reason <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Mandatory justification (e.g. Discom transformer capacity limitation)"
                    value={subsidyOverrideReason}
                    onChange={(e) => setSubsidyOverrideReason(e.target.value)}
                    className="w-full text-xs rounded-lg border border-amber-300 px-3 py-2 bg-amber-50/50 text-slate-800 focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Standard Terms and Conditions
                </label>
                <textarea
                  rows={4}
                  value={terms}
                  onChange={(e) => setTerms(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 bg-white text-slate-800 focus:ring-2 focus:ring-amber-500 font-mono"
                />
              </div>
            </div>

            {/* Financial Summary Card */}
            <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-amber-950 p-5 rounded-2xl text-white shadow-lg flex flex-col justify-between border border-slate-800">
              <div>
                <div className="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
                  <h4 className="text-xs font-bold text-amber-400 tracking-wider uppercase flex items-center gap-1.5">
                    <Calculator className="w-4 h-4" /> Live Commercial Preview
                  </h4>
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                    Authoritative Backend Pricing
                  </span>
                </div>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between text-slate-300">
                    <span>Products Subtotal (Base - Disc):</span>
                    <span className="font-mono font-semibold">₹{Number(totals.productBaseTotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Total GST Taxes:</span>
                    <span className="font-mono font-semibold">₹{Number(totals.taxTotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Installation & Commissioning:</span>
                    <span className="font-mono font-semibold">₹{Number(installationCost || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>

                  <div className="border-t border-slate-700/80 pt-2 flex justify-between text-sm font-bold text-white">
                    <span>Gross Project Cost:</span>
                    <span className="font-mono text-amber-400">₹{Number(totals.gross).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>

                  <div className="flex justify-between text-emerald-400 text-xs">
                    <span>Estimated DBT Subsidy:</span>
                    <span className="font-mono">- ₹{Number(subsidyEstimate || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              <div className="border-t-2 border-amber-500/40 pt-3 mt-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-300">Net Customer Payable:</span>
                  <span className="text-xl font-black font-mono text-emerald-400">
                    ₹{Number(totals.net).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1 italic">
                  * Final decimal calculations, sequential numbers, and subsidy eligibility are authoritatively computed and committed by the server upon save.
                </p>
              </div>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl text-xs font-bold text-slate-950 bg-amber-500 hover:bg-amber-400 shadow-md shadow-amber-500/20 transition flex items-center gap-1.5"
            >
              {submitting ? 'Saving Quotation...' : isEditing ? 'Save Changes' : 'Generate Quotation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
