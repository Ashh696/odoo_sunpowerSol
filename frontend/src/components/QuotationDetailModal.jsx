import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  X,
  FileText,
  Calendar,
  User,
  Zap,
  Package,
  History,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Send,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  Building,
  Printer,
  Briefcase,
} from 'lucide-react';
import { getQuotation } from '../services/quotationApi';
import { createOrder } from '../services/orderApi';
import QuotationPrintModal from './QuotationPrintModal';

export default function QuotationDetailModal({
  isOpen,
  onClose,
  quotationId,
  onOpenApprove,
  onOpenRevise,
  onOpenSend,
  onOpenAccept,
  currentUser,
}) {
  const [quotation, setQuotation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRevision, setExpandedRevision] = useState(null);
  const [showPrintModal, setShowPrintModal] = useState(false);
  const [convertingOrder, setConvertingOrder] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [orderError, setOrderError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (!isOpen || !quotationId) return;

    setLoading(true);
    setError(null);
    setExpandedRevision(null);
    setOrderSuccess(null);
    setOrderError(null);

    getQuotation(quotationId)
      .then((res) => {
        if (res && res.data) setQuotation(res.data);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve quotation details.');
      })
      .finally(() => setLoading(false));
  }, [isOpen, quotationId]);

  if (!isOpen) return null;

  const roleSlug = currentUser?.role?.slug || '';
  const isSuperAdmin = roleSlug === 'SUPER_ADMIN';
  const isSales = roleSlug === 'SALES';
  const isDirector = roleSlug === 'DIRECTOR';
  const isTechManager = roleSlug === 'TECHNICAL_MANAGER';
  const isCustomer = roleSlug === 'CUSTOMER';

  const statusBadge = (st) => {
    switch (st) {
      case 'DRAFT':
        return <span className="bg-slate-100 text-slate-700 border border-slate-300 px-2.5 py-0.5 rounded-full text-xs font-bold">DRAFT</span>;
      case 'PENDING_APPROVAL':
        return <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"><Clock className="w-3 h-3 text-amber-600" /> PENDING REVIEW</span>;
      case 'APPROVED':
        return <span className="bg-blue-100 text-blue-800 border border-blue-300 px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-blue-600" /> APPROVED</span>;
      case 'SENT':
        return <span className="bg-purple-100 text-purple-800 border border-purple-300 px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"><Send className="w-3 h-3 text-purple-600" /> SENT TO CUSTOMER</span>;
      case 'ACCEPTED':
        return <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> ACCEPTED (WON)</span>;
      case 'REJECTED':
        return <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center gap-1"><XCircle className="w-3 h-3 text-rose-600" /> REJECTED</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs">{st}</span>;
    }
  };

  const handleConvertToOrder = async () => {
    if (!quotation) return;
    setConvertingOrder(true);
    setOrderError(null);
    setOrderSuccess(null);
    try {
      const res = await createOrder({ quotation_id: quotation.id });
      const order = res.data;
      setOrderSuccess(`Order ${order.order_number} created successfully in PENDING_ADVANCE status!`);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to convert quotation to order.';
      setOrderError(detail);
    } finally {
      setConvertingOrder(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950 text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-lg text-white font-mono">
                  {quotation?.quotation_number || 'Quotation Details'}
                </h3>
                {quotation && (
                  <span className="bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs px-2 py-0.5 rounded font-mono font-semibold">
                    v{quotation.version}
                  </span>
                )}
                {quotation && statusBadge(quotation.status)}
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                {quotation?.customer_name} • {quotation?.capacity_kw} kW {quotation?.system_type} Solar System
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {quotation && (
              <button
                type="button"
                onClick={() => setShowPrintModal(true)}
                title="Print Quotation / Save as PDF"
                className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5 text-xs font-semibold border border-slate-700/60 bg-slate-800/40"
              >
                <Printer className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline">Print / Save PDF</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-20 text-center text-slate-400">
              <Clock className="w-8 h-8 animate-spin mx-auto mb-2 text-amber-500" />
              <p className="text-xs">Loading quotation specification & revisions...</p>
            </div>
          ) : error ? (
            <div className="p-6 text-center">
              <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
              <p className="text-xs font-semibold text-rose-700">{error}</p>
            </div>
          ) : quotation ? (
            <>
              {/* Quick Info Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                <div>
                  <span className="text-slate-400 block font-medium">Customer & Enquiry</span>
                  <span className="font-bold text-slate-900 block mt-0.5">{quotation.customer_name}</span>
                  <span className="text-slate-500 block">Enquiry #{quotation.enquiry_number || quotation.enquiry_id}</span>
                  {quotation.customer_type && (
                    <span className="inline-block mt-1 text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-semibold">
                      {quotation.customer_type}
                    </span>
                  )}
                </div>

                <div>
                  <span className="text-slate-400 block font-medium">Technical Verification</span>
                  <span className="font-bold text-slate-900 block mt-0.5">
                    {quotation.capacity_kw} kW • {quotation.system_type}
                  </span>
                  <span className="text-slate-500 block">
                    {quotation.survey_number ? `Survey: ${quotation.survey_number} (Approved)` : 'No site survey attached'}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block font-medium">Validity & Authorship</span>
                  <span className="font-semibold text-slate-800 block mt-0.5">
                    Dated: {quotation.quotation_date}
                  </span>
                  <span className="text-amber-800 block font-medium">
                    Valid Until: {quotation.valid_until}
                  </span>
                  <span className="text-slate-400 block mt-0.5 text-[11px]">
                    Created by {quotation.creator_name || 'Staff'}
                  </span>
                </div>
              </div>

              {/* Line Items Table */}
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Package className="w-4 h-4 text-amber-600" /> Equipment & Bill of Materials Breakdown
                </h4>
                <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-100/80 border-b border-slate-200 text-slate-600 font-bold">
                      <tr>
                        <th className="py-2.5 px-3">#</th>
                        <th className="py-2.5 px-3">Component / Model</th>
                        <th className="py-2.5 px-3 text-right">Quantity</th>
                        <th className="py-2.5 px-3 text-right">Unit Price</th>
                        <th className="py-2.5 px-3 text-right">Discount</th>
                        <th className="py-2.5 px-3 text-right">GST %</th>
                        <th className="py-2.5 px-3 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {quotation.items && quotation.items.length > 0 ? (
                        quotation.items.map((it, idx) => (
                          <tr key={it.id || idx} className="hover:bg-slate-50/50">
                            <td className="py-2.5 px-3 text-slate-400 font-mono">{idx + 1}</td>
                            <td className="py-2.5 px-3">
                              <div className="font-semibold text-slate-900">{it.item_description}</div>
                              {it.product_code && (
                                <div className="text-[10px] text-slate-400 font-mono">
                                  {it.product_code} {it.brand ? `• ${it.brand}` : ''}
                                </div>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono font-medium">{it.quantity}</td>
                            <td className="py-2.5 px-3 text-right font-mono">₹{it.unit_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-3 text-right font-mono text-slate-500">
                              {it.discount_amount > 0 ? `₹${it.discount_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono">{it.tax_rate_percent}%</td>
                            <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                              ₹{it.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-slate-400 italic">
                            No component line items recorded.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Financial Summary & Terms */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                    Terms & Commercial Conditions
                  </h4>
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
                    {quotation.terms_and_conditions || 'Standard SunPower Solutions installation terms apply.'}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-slate-900 to-amber-950 p-5 rounded-2xl text-white shadow-md border border-slate-800 space-y-2.5 text-xs">
                  <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 mb-3">
                    Commercial Settlement Summary
                  </h4>

                  <div className="flex justify-between text-slate-300">
                    <span>Equipment Subtotal:</span>
                    <span className="font-mono font-semibold">₹{quotation.total_product_cost?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Applicable GST Taxes:</span>
                    <span className="font-mono font-semibold">₹{quotation.tax_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Installation & Commissioning:</span>
                    <span className="font-mono font-semibold">₹{quotation.installation_cost?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>

                  <div className="border-t border-slate-800 pt-2 flex justify-between font-bold text-sm text-white">
                    <span>Gross Quotation Amount:</span>
                    <span className="font-mono text-amber-400">₹{quotation.gross_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>

                  <div className="flex justify-between text-emerald-400 text-xs">
                    <span>Govt DBT Subsidy Estimate:</span>
                    <span className="font-mono">- ₹{quotation.subsidy_estimate?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>

                  <div className="border-t-2 border-amber-500/30 pt-3 mt-3 flex justify-between items-baseline">
                    <span className="text-xs font-bold uppercase text-amber-300">Net Customer Payable:</span>
                    <span className="text-xl font-black font-mono text-emerald-400">
                      ₹{quotation.net_payable_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Revision History Section */}
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <History className="w-4 h-4 text-amber-600" /> Immutable Version & Revision History
                </h4>

                {quotation.revisions && quotation.revisions.length > 0 ? (
                  <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 bg-white">
                    {quotation.revisions.map((rev) => {
                      const isExpanded = expandedRevision === rev.id;
                      return (
                        <div key={rev.id} className="p-3 text-xs">
                          <div
                            onClick={() => setExpandedRevision(isExpanded ? null : rev.id)}
                            className="flex items-center justify-between cursor-pointer hover:text-amber-600 transition"
                          >
                            <div className="flex items-center gap-2">
                              {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                              <span className="font-bold text-slate-900 font-mono">Revision #{rev.revision_number}</span>
                              <span className="text-slate-500 italic">"{rev.reason_for_revision}"</span>
                            </div>
                            <div className="text-[11px] text-slate-400 flex items-center gap-3">
                              <span>By {rev.revised_by_name || 'Staff'}</span>
                              <span>{new Date(rev.created_at).toLocaleString()}</span>
                            </div>
                          </div>

                          {isExpanded && rev.snapshot_data && (
                            <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 text-slate-600">
                              <div className="text-[11px] font-semibold text-slate-800">
                                Snapshot at Version #{rev.snapshot_data.version} ({rev.snapshot_data.status}):
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                                <div>Gross: ₹{rev.snapshot_data.gross_amount}</div>
                                <div>Net Payable: ₹{rev.snapshot_data.net_payable_amount}</div>
                                <div>Capacity: {rev.snapshot_data.capacity_kw} kW</div>
                                <div>Items: {rev.snapshot_data.items?.length || 0} lines</div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 italic text-center">
                    No prior revisions recorded. This quotation is currently at original Version 1.
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {orderSuccess && (
          <div className="mx-6 my-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{orderSuccess}</span>
            </div>
            <button
              type="button"
              onClick={() => {
                onClose();
                navigate('/orders');
              }}
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold ml-3"
            >
              View in Orders &rarr;
            </button>
          </div>
        )}
        {orderError && (
          <div className="mx-6 my-2 p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{orderError}</span>
            </div>
            <button
              type="button"
              onClick={() => setOrderError(null)}
              className="text-rose-500 hover:text-rose-700 ml-2"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 transition"
            >
              Close
            </button>
            {quotation && (
              <button
                type="button"
                onClick={() => setShowPrintModal(true)}
                title="Open print view & print or save as PDF"
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-800 bg-white border border-slate-300 hover:bg-slate-100 shadow-sm transition flex items-center gap-1.5"
              >
                <Printer className="w-4 h-4 text-slate-600" />
                <span>Print / Save PDF</span>
              </button>
            )}
          </div>

          {quotation && (
            <div className="flex items-center gap-2">
              {/* Review / Approval */}
              {quotation.status === 'PENDING_APPROVAL' && (isSuperAdmin || isDirector || isTechManager) && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenApprove(quotation);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 shadow-sm transition flex items-center gap-1.5"
                >
                  <ShieldCheck className="w-4 h-4" /> Review & Approve
                </button>
              )}

              {/* Send to Customer */}
              {quotation.status === 'APPROVED' && (isSuperAdmin || isSales) && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenSend(quotation);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-950 bg-amber-500 hover:bg-amber-400 shadow-md shadow-amber-500/20 transition flex items-center gap-1.5"
                >
                  <Send className="w-4 h-4" /> Send to Customer
                </button>
              )}

              {/* Revise */}
              {['APPROVED', 'SENT', 'REJECTED'].includes(quotation.status) && (isSuperAdmin || isSales) && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenRevise(quotation);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-800 bg-amber-100 hover:bg-amber-200 border border-amber-300 transition flex items-center gap-1.5"
                >
                  <History className="w-4 h-4" /> Create Revision
                </button>
              )}

              {/* Customer Acceptance */}
              {quotation.status === 'SENT' && (isCustomer || isSuperAdmin) && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenAccept(quotation);
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 shadow-sm transition flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {isSuperAdmin ? 'Admin Accept on Behalf' : 'Accept Quotation'}
                </button>
              )}

              {/* Convert to Order */}
              {quotation.status === 'ACCEPTED' && (isSuperAdmin || currentUser?.permissions?.includes('orders.create')) && (
                <button
                  type="button"
                  onClick={handleConvertToOrder}
                  disabled={convertingOrder}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-amber-600 hover:bg-amber-500 shadow-md shadow-amber-600/20 transition flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Briefcase className="w-4 h-4" />
                  <span>{convertingOrder ? 'Converting...' : 'Convert to Order'}</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {showPrintModal && quotation && (
        <QuotationPrintModal
          isOpen={showPrintModal}
          onClose={() => setShowPrintModal(false)}
          quotation={quotation}
        />
      )}
    </div>
  );
}
