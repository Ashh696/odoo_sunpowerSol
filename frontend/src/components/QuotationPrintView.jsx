import React from 'react';
import { Sun, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

/**
 * Standard Indian Rupee (INR) formatter with two decimal places.
 */
export const formatINR = (val) => {
  if (val === null || val === undefined || val === '') return '₹0.00';
  const num = typeof val === 'number' ? val : parseFloat(val);
  if (isNaN(num)) return '₹0.00';
  return (
    '₹' +
    num.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  );
};

export default function QuotationPrintView({ quotation }) {
  if (!quotation) return null;

  const items = quotation.items || [];

  return (
    <div className="printable-document bg-white text-slate-900 p-8 sm:p-10 max-w-4xl mx-auto font-sans leading-normal">
      {/* 1. Header / Branding */}
      <div className="border-b-2 border-slate-900 pb-5 mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-amber-500 flex items-center justify-center text-slate-950 font-bold shadow-md print:shadow-none">
            <Sun className="w-7 h-7 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 leading-none">
              SunPower Solutions
            </h1>
            <p className="text-xs text-amber-700 font-semibold tracking-wide uppercase mt-1">
              Solar Installation Management System (SIMS)
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Clean Energy • Engineering Excellence • Turnkey Solar Solutions
            </p>
          </div>
        </div>

        <div className="text-right">
          <div className="inline-block bg-slate-900 text-white font-black tracking-widest text-sm px-3 py-1 rounded">
            QUOTATION
          </div>
          <div className="text-xs font-mono font-bold text-slate-900 mt-1.5">
            {quotation.quotation_number}
            <span className="ml-1 text-[11px] font-semibold text-amber-700">
              (Rev {quotation.version})
            </span>
          </div>
          <div className="text-[11px] text-slate-600 mt-0.5">
            Status: <span className="font-semibold text-slate-900">{quotation.status}</span>
          </div>
        </div>
      </div>

      {/* 2. Quotation Metadata & Customer Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 text-xs">
        {/* Customer Information */}
        <div className="border border-slate-300 rounded-lg p-4 bg-slate-50/60 print:bg-transparent">
          <h2 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 border-b border-slate-200 pb-1">
            Customer Information
          </h2>
          <div className="space-y-1">
            <div className="text-sm font-bold text-slate-900">
              {quotation.customer_name || 'Customer Name On Record'}
            </div>
            {quotation.customer_type && (
              <div className="text-[11px] text-slate-600">
                <span className="font-semibold">Category:</span> {quotation.customer_type}
              </div>
            )}
            <div className="text-[11px] text-slate-500 italic pt-1">
              Customer Contact & Address: Registered on File
              <span className="block text-[10px] text-slate-400 not-italic">
                (Reference: Enquiry #{quotation.enquiry_number || quotation.enquiry_id})
              </span>
            </div>
          </div>
        </div>

        {/* Quotation & Project Details */}
        <div className="border border-slate-300 rounded-lg p-4 bg-slate-50/60 print:bg-transparent">
          <h2 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2 border-b border-slate-200 pb-1">
            Project & Quotation Details
          </h2>
          <div className="grid grid-cols-2 gap-y-1.5 text-[11px]">
            <div>
              <span className="text-slate-500 block">Date of Issue:</span>
              <span className="font-semibold text-slate-900">{quotation.quotation_date}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Valid Until:</span>
              <span className="font-semibold text-slate-900">{quotation.valid_until}</span>
            </div>
            <div>
              <span className="text-slate-500 block">System Type:</span>
              <span className="font-semibold text-slate-900">{quotation.system_type} Solar PV</span>
            </div>
            <div>
              <span className="text-slate-500 block">Proposed Capacity:</span>
              <span className="font-bold text-amber-700">{quotation.capacity_kw} kW</span>
            </div>
            <div>
              <span className="text-slate-500 block">Associated Enquiry:</span>
              <span className="font-mono text-slate-900">{quotation.enquiry_number || `#${quotation.enquiry_id}`}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Site Feasibility Survey:</span>
              <span className="font-mono text-slate-900">
                {quotation.survey_number ? `${quotation.survey_number} (Approved)` : 'Standard Engineering Feasibility'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Itemized Equipment Table */}
      <div className="mb-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-2 flex items-center justify-between">
          <span>Equipment & Bill of Materials Breakdown</span>
          <span className="text-[10px] font-normal text-slate-500">All prices in Indian Rupees (INR)</span>
        </h2>

        <div className="border border-slate-300 rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100 border-b border-slate-300 text-slate-700 font-bold">
              <tr>
                <th className="py-2.5 px-3 w-8 text-center border-r border-slate-200">#</th>
                <th className="py-2.5 px-3 border-r border-slate-200">Item Description & Specifications</th>
                <th className="py-2.5 px-3 text-right w-16 border-r border-slate-200">Qty</th>
                <th className="py-2.5 px-3 text-right w-24 border-r border-slate-200">Unit Price</th>
                <th className="py-2.5 px-3 text-right w-20 border-r border-slate-200">Discount</th>
                <th className="py-2.5 px-3 text-right w-16 border-r border-slate-200">GST %</th>
                <th className="py-2.5 px-3 text-right w-28">Line Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-800">
              {items.length > 0 ? (
                items.map((it, idx) => (
                  <tr key={it.id || idx} className="page-break-inside-avoid">
                    <td className="py-2.5 px-3 text-center text-slate-500 font-mono border-r border-slate-200">
                      {idx + 1}
                    </td>
                    <td className="py-2.5 px-3 border-r border-slate-200">
                      <div className="font-bold text-slate-900">{it.item_description}</div>
                      {(it.product_code || it.brand || it.model_number) && (
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {it.product_code && <span>Code: {it.product_code}</span>}
                          {it.brand && <span> • Brand: {it.brand}</span>}
                          {it.model_number && <span> • Model: {it.model_number}</span>}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium border-r border-slate-200 whitespace-nowrap">
                      {it.quantity} Nos.
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono border-r border-slate-200 whitespace-nowrap">
                      {formatINR(it.unit_price)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-slate-600 border-r border-slate-200 whitespace-nowrap">
                      {it.discount_amount > 0 ? formatINR(it.discount_amount) : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono border-r border-slate-200 whitespace-nowrap">
                      {it.tax_rate_percent}%
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900 whitespace-nowrap">
                      {formatINR(it.total_amount)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-500 italic">
                    No component line items recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Financial Summary & Terms */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 page-break-inside-avoid">
        {/* Commercial Terms & Conditions */}
        <div className="border border-slate-300 rounded-lg p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 mb-2 border-b border-slate-200 pb-1">
              Terms & Commercial Conditions
            </h3>
            <div className="text-[11px] text-slate-700 whitespace-pre-wrap leading-relaxed font-mono">
              {quotation.terms_and_conditions ||
                '1. 50% advance along with confirmed work order.\n2. 40% on dispatch of equipment to site.\n3. 10% on successful commissioning and net-metering synchronization.\n4. Comprehensive 5-year workmanship warranty and 25-year panel performance guarantee.'}
            </div>
          </div>
          <div className="mt-4 pt-2 border-t border-slate-200 text-[10px] text-slate-500 italic">
            * Validity: This quotation is valid until {quotation.valid_until}. Prices are subject to solar policy changes thereafter.
          </div>
        </div>

        {/* Commercial Settlement Summary Box */}
        <div className="border-2 border-slate-900 rounded-lg p-4 bg-slate-50/80 print:bg-transparent space-y-2 text-xs">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-slate-300 pb-1 mb-2">
            Commercial Settlement Summary
          </h3>

          <div className="flex justify-between text-slate-700">
            <span>Equipment Subtotal:</span>
            <span className="font-mono font-semibold">{formatINR(quotation.total_product_cost)}</span>
          </div>

          <div className="flex justify-between text-slate-700">
            <span>Applicable GST Taxes:</span>
            <span className="font-mono font-semibold">{formatINR(quotation.tax_amount)}</span>
          </div>

          <div className="flex justify-between text-slate-700">
            <span>Installation & Commissioning Charges:</span>
            <span className="font-mono font-semibold">{formatINR(quotation.installation_cost)}</span>
          </div>

          <div className="border-t border-slate-300 pt-2 flex justify-between font-bold text-slate-900">
            <span>Gross Quotation Amount:</span>
            <span className="font-mono text-sm">{formatINR(quotation.gross_amount)}</span>
          </div>

          <div className="flex justify-between text-emerald-800 font-medium">
            <span>Estimated Govt DBT Subsidy:</span>
            <span className="font-mono">- {formatINR(quotation.subsidy_estimate)}</span>
          </div>

          <div className="border-t-2 border-slate-900 pt-2.5 mt-2 flex justify-between items-baseline font-bold">
            <span className="text-xs uppercase text-slate-900">Net Customer Payable:</span>
            <span className="text-lg font-black font-mono text-slate-950">
              {formatINR(quotation.net_payable_amount)}
            </span>
          </div>
          <p className="text-[10px] text-slate-500 pt-1">
            * Direct Benefit Transfer (DBT) subsidy is subject to government verification and discom approval.
          </p>
        </div>
      </div>

      {/* 5. Signatory & Authorization Block */}
      <div className="border-t-2 border-slate-300 pt-6 mt-6 page-break-inside-avoid">
        <div className="grid grid-cols-2 gap-8 text-xs">
          {/* Company Signatory */}
          <div>
            <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              For SunPower Solutions
            </div>
            <p className="text-[11px] text-slate-500 mb-8">
              Prepared by: <span className="font-semibold text-slate-900">{quotation.creator_name || 'Authorized Technical Sales Staff'}</span>
            </p>
            <div className="border-t border-dashed border-slate-400 pt-1.5 w-48">
              <span className="text-[10px] text-slate-500 block uppercase font-medium">Authorized Signatory & Stamp</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Date: {quotation.quotation_date}</span>
            </div>
          </div>

          {/* Customer Acceptance Signatory */}
          <div>
            <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
              Customer Acceptance
            </div>
            <p className="text-[11px] text-slate-500 mb-8">
              Accepted by: <span className="font-semibold text-slate-900">{quotation.customer_name || 'Customer / Authorized Representative'}</span>
            </p>
            <div className="border-t border-dashed border-slate-400 pt-1.5 w-48">
              <span className="text-[10px] text-slate-500 block uppercase font-medium">Customer Signature</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Date: ____________________</span>
            </div>
          </div>
        </div>

        {/* Footer Notice */}
        <div className="mt-8 pt-3 border-t border-slate-200 text-center text-[10px] text-slate-400 flex items-center justify-between">
          <span>SunPower Solutions • Solar Installation Management System (SIMS)</span>
          <span>Computer-generated quotation • Document ID: {quotation.quotation_number}</span>
        </div>
      </div>
    </div>
  );
}
