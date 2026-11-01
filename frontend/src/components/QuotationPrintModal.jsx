import React, { useEffect, useState } from 'react';
import { Printer, X, ArrowLeft, Clock, AlertCircle } from 'lucide-react';
import QuotationPrintView from './QuotationPrintView';
import { getQuotation } from '../services/quotationApi';

export default function QuotationPrintModal({
  isOpen,
  onClose,
  quotation: initialQuotation = null,
  quotationId = null,
}) {
  const [quotation, setQuotation] = useState(initialQuotation);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    if (initialQuotation) {
      setQuotation(initialQuotation);
      setLoading(false);
      setError(null);
    } else if (quotationId) {
      setLoading(true);
      setError(null);
      getQuotation(quotationId)
        .then((res) => {
          if (res && res.data) setQuotation(res.data);
        })
        .catch((err) => {
          setError(err.message || 'Failed to load quotation for printing.');
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, initialQuotation, quotationId]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-slate-900/80 backdrop-blur-sm overflow-y-auto print-modal-overlay">
      {/* Print Preview Top Navigation Toolbar (Hidden during print) */}
      <div className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 text-white px-6 py-3.5 shadow-xl flex items-center justify-between no-print">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition flex items-center gap-1.5 border border-slate-700"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Details</span>
          </button>
          <div className="h-5 w-px bg-slate-700 hidden sm:block" />
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Print Preview</span>
              {quotation && (
                <span className="font-mono text-amber-400 text-xs font-semibold">
                  {quotation.quotation_number} (v{quotation.version})
                </span>
              )}
            </h2>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Review document before printing or exporting to PDF via native browser dialog.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handlePrint}
            disabled={loading || !quotation}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-950 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-amber-500/20 transition flex items-center gap-2"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save as PDF</span>
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Close Preview"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Document Viewport */}
      <div className="flex-1 p-4 sm:p-8 bg-slate-200/90 print:bg-white print:p-0 flex justify-center">
        {loading ? (
          <div className="py-24 text-center text-slate-600 no-print">
            <Clock className="w-8 h-8 animate-spin mx-auto mb-2 text-amber-600" />
            <p className="text-xs font-medium">Preparing printable quotation specification...</p>
          </div>
        ) : error ? (
          <div className="py-16 text-center text-rose-700 max-w-md mx-auto no-print">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
            <p className="text-xs font-semibold">{error}</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-1.5 rounded-lg text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100"
            >
              Close
            </button>
          </div>
        ) : quotation ? (
          <div className="w-full max-w-4xl bg-white shadow-2xl rounded-2xl print:shadow-none print:rounded-none overflow-hidden print-modal-content">
            <QuotationPrintView quotation={quotation} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
