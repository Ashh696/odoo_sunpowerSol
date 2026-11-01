import React from 'react';
import { X, Printer, FileText, CheckCircle2 } from 'lucide-react';

export default function InvoicePrintModal({ isOpen, onClose, invoice }) {
  if (!isOpen || !invoice) return null;

  const handlePrint = () => {
    window.print();
  };

  const formattedInvoiceDate = invoice.invoice_date
    ? new Date(invoice.invoice_date).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : 'N/A';

  const formattedDueDate = invoice.due_date
    ? new Date(invoice.due_date).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : 'N/A';

  const subtotal = parseFloat(invoice.subtotal || 0);
  const taxAmount = parseFloat(invoice.tax_amount || 0);
  const totalAmount = parseFloat(invoice.total_amount || 0);
  const paidAmount = parseFloat(invoice.paid_amount || 0);
  const balanceAmount = parseFloat(invoice.balance_amount || 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden my-6 flex flex-col max-h-[90vh]">
        {/* Modal Controls - Hidden during print */}
        <div className="no-print flex items-center justify-between px-6 py-4 bg-slate-900 text-white border-b border-slate-800">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-400" />
            <h3 className="font-bold text-sm">Tax Invoice Print & PDF View</h3>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Document Area */}
        <div className="p-8 overflow-y-auto text-slate-900 bg-white" id="printable-invoice">
          {/* Header */}
          <div className="flex justify-between items-start border-b border-slate-200 pb-6 mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center text-slate-950 font-black text-sm">
                  SP
                </div>
                <h1 className="text-xl font-black tracking-tight text-slate-900">SunPower Solutions</h1>
              </div>
              <p className="text-xs text-slate-600 font-medium">Solar Installation Management System (SIMS)</p>
              <p className="text-xs text-slate-500 mt-1">Pune, Maharashtra, India</p>
            </div>

            <div className="text-right">
              <span className="inline-block px-3 py-1 bg-slate-100 border border-slate-300 text-slate-800 text-xs font-black rounded-full uppercase tracking-wider mb-2">
                Tax Invoice • {invoice.invoice_type.replace('_', ' ')}
              </span>
              <h2 className="text-lg font-bold font-mono text-slate-900">{invoice.invoice_number}</h2>
              <div className="text-xs text-slate-600 space-y-0.5 mt-1">
                <p>Invoice Date: <span className="font-semibold text-slate-800">{formattedInvoiceDate}</span></p>
                <p>Due Date: <span className="font-semibold text-slate-800">{formattedDueDate}</span></p>
                <p>
                  Status:{' '}
                  <span className={`font-bold ${invoice.payment_status === 'PAID' ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {invoice.payment_status}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Customer & Order Context */}
          <div className="grid grid-cols-2 gap-6 p-4 bg-slate-50 rounded-xl border border-slate-200 mb-6 text-xs">
            <div>
              <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Billed To (Customer):</span>
              <p className="font-bold text-sm text-slate-900">{invoice.customer?.full_name || 'Customer'}</p>
              <p className="text-slate-600">Phone: {invoice.customer?.phone || 'N/A'}</p>
              {invoice.customer?.email && <p className="text-slate-600">Email: {invoice.customer.email}</p>}
              <p className="text-slate-600 mt-1">
                {invoice.customer?.address ? `${invoice.customer.address}, ` : ''}
                {invoice.customer?.city || 'Pune'}, {invoice.customer?.state || 'Maharashtra'} {invoice.customer?.pincode || ''}
              </p>
            </div>

            <div className="text-right">
              <span className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Commercial Reference:</span>
              <p className="text-slate-700">Order: <span className="font-mono font-bold text-slate-900">{invoice.order?.order_number || 'N/A'}</span></p>
              {invoice.project?.project_code && (
                <p className="text-slate-700">Project: <span className="font-mono font-bold text-slate-900">{invoice.project.project_code}</span></p>
              )}
              {invoice.project?.system_capacity_kw && (
                <p className="text-slate-700">System: {invoice.project.system_capacity_kw} kW {invoice.project.system_type}</p>
              )}
            </div>
          </div>

          {/* Line Items Table */}
          <table className="w-full text-left text-xs mb-6 border-collapse">
            <thead>
              <tr className="border-b-2 border-slate-300 text-slate-600 font-bold uppercase tracking-wider">
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3 text-right">Qty</th>
                <th className="py-2.5 px-3 text-right">Unit Price (₹)</th>
                <th className="py-2.5 px-3 text-right">GST Rate</th>
                <th className="py-2.5 px-3 text-right">Amount (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {invoice.items && invoice.items.length > 0 ? (
                invoice.items.map((it, idx) => (
                  <tr key={it.id || idx}>
                    <td className="py-2.5 px-3 text-slate-500">{idx + 1}</td>
                    <td className="py-2.5 px-3">
                      <p className="font-semibold text-slate-900">{it.item_description}</p>
                      {it.product_code && <span className="text-[10px] text-slate-500 font-mono">Code: {it.product_code}</span>}
                    </td>
                    <td className="py-2.5 px-3 text-right font-medium">{parseFloat(it.quantity).toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{parseFloat(it.unit_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="py-2.5 px-3 text-right font-mono">{parseFloat(it.tax_rate_percent).toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-900">{parseFloat(it.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-slate-400 italic">
                    Milestone billing item ({invoice.invoice_type.replace('_', ' ')})
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Financial Breakdown */}
          <div className="flex justify-end mb-8">
            <div className="w-72 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100 text-slate-600">
                <span>Subtotal (Base Value):</span>
                <span className="font-mono font-semibold text-slate-900">₹{subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 text-slate-600">
                <span>Applicable GST:</span>
                <span className="font-mono font-semibold text-slate-900">₹{taxAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between py-2 border-b-2 border-slate-300 font-bold text-sm text-slate-950">
                <span>Total Invoice Value:</span>
                <span className="font-mono text-amber-600">₹{totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between py-1 text-emerald-700">
                <span>Amount Paid / Allocated:</span>
                <span className="font-mono font-semibold">₹{paidAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between py-1.5 bg-slate-50 px-2 rounded-lg font-bold text-slate-900">
                <span>Outstanding Balance:</span>
                <span className={`font-mono ${balanceAmount > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  ₹{balanceAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>

          {/* Payment Allocations Table if present */}
          {invoice.allocations && invoice.allocations.length > 0 && (
            <div className="mb-6 border-t border-slate-200 pt-4">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Recorded Payment Allocations</h4>
              <div className="space-y-1.5">
                {invoice.allocations.map((al, idx) => (
                  <div key={al.id || idx} className="flex justify-between items-center text-xs p-2 bg-emerald-50/60 border border-emerald-100 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="font-mono font-semibold text-slate-800">{al.payment_number}</span>
                      <span className="text-slate-500 text-[11px]">• {new Date(al.allocated_at).toLocaleDateString('en-IN')}</span>
                    </div>
                    <span className="font-mono font-bold text-emerald-800">
                      ₹{parseFloat(al.allocated_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Commercial & Statutory Footer */}
          <div className="border-t border-slate-200 pt-6 text-[10px] text-slate-500 leading-relaxed">
            <p className="font-semibold text-slate-700 mb-1">Terms & Conditions:</p>
            <p>1. Please make all electronic remittances in favour of SunPower Solutions with order/invoice reference.</p>
            <p>2. Subject to Pune jurisdiction.</p>
            <p className="mt-2 text-right italic font-medium text-slate-400">
              This is an authentic system-generated document issued under SIMS commercial billing standards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
