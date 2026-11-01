import React, { useState, useEffect } from 'react';
import {
  Search,
  FileText,
  Calendar,
  User,
  Zap,
  CheckCircle2,
  Clock,
  Send,
  XCircle,
  Eye,
  Edit2,
  Trash2,
  History,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Filter,
  DollarSign,
  Printer,
} from 'lucide-react';
import {
  getQuotations,
  submitQuotation,
  sendQuotation,
  acceptQuotation,
  customerRejectQuotation,
  deleteQuotation,
} from '../services/quotationApi';
import QuotationPrintModal from './QuotationPrintModal';

const STATUS_TABS = [
  { value: '', label: 'All Quotations' },
  { value: 'DRAFT', label: 'Drafts' },
  { value: 'PENDING_APPROVAL', label: 'In Review' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'SENT', label: 'Sent to Customer' },
  { value: 'ACCEPTED', label: 'Accepted (Won)' },
  { value: 'REJECTED', label: 'Rejected' },
];

export default function QuotationList({
  currentUser,
  onOpenDetail,
  onOpenEdit,
  onOpenApproval,
  onOpenRevision,
  refreshKey,
}) {
  const [quotations, setQuotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Confirmation Modals State
  const [confirmAction, setConfirmAction] = useState(null); // { type, quotation }
  const [actionInput, setActionInput] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [printQuotationId, setPrintQuotationId] = useState(null);

  const roleSlug = currentUser?.role?.slug || '';
  const isSuperAdmin = roleSlug === 'SUPER_ADMIN';
  const isSales = roleSlug === 'SALES';
  const isDirector = roleSlug === 'DIRECTOR';
  const isTechManager = roleSlug === 'TECHNICAL_MANAGER';
  const isCustomer = roleSlug === 'CUSTOMER';

  const fetchQuotations = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit: 15,
        status: statusFilter || undefined,
        search: search.trim() || undefined,
      };

      const res = await getQuotations(params);
      if (res && res.data) {
        setQuotations(res.data.items || []);
        setTotalPages(res.data.pages || 1);
        setTotal(res.data.total || 0);
      }
    } catch (err) {
      setError(err.message || 'Failed to retrieve quotations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotations();
  }, [page, statusFilter, refreshKey]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchQuotations();
  };

  // Lifecycle Quick Actions
  const handleExecuteAction = async () => {
    if (!confirmAction) return;
    const { type, quotation } = confirmAction;

    setActionLoading(true);
    setActionError(null);

    try {
      if (type === 'SUBMIT') {
        await submitQuotation(quotation.id);
      } else if (type === 'SEND') {
        await sendQuotation(quotation.id);
      } else if (type === 'ACCEPT') {
        await acceptQuotation(quotation.id, { acceptance_notes: actionInput.trim() || undefined });
      } else if (type === 'REJECT_CUSTOMER') {
        if (!actionInput || actionInput.trim().length < 3) {
          setActionError('Please provide a mandatory reason for declining the quotation.');
          setActionLoading(false);
          return;
        }
        await customerRejectQuotation(quotation.id, { rejection_reason: actionInput.trim() });
      } else if (type === 'DELETE') {
        await deleteQuotation(quotation.id);
      }

      setConfirmAction(null);
      setActionInput('');
      fetchQuotations();
    } catch (err) {
      setActionError(err.message || 'Action failed. Please check server validation.');
    } finally {
      setActionLoading(false);
    }
  };

  const statusBadge = (st) => {
    switch (st) {
      case 'DRAFT':
        return <span className="bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded-full text-[11px] font-bold">DRAFT</span>;
      case 'PENDING_APPROVAL':
        return <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1"><Clock className="w-3 h-3 text-amber-600" /> REVIEW</span>;
      case 'APPROVED':
        return <span className="bg-blue-100 text-blue-800 border border-blue-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-blue-600" /> APPROVED</span>;
      case 'SENT':
        return <span className="bg-purple-100 text-purple-800 border border-purple-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1"><Send className="w-3 h-3 text-purple-600" /> SENT</span>;
      case 'ACCEPTED':
        return <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> WON</span>;
      case 'REJECTED':
        return <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1"><XCircle className="w-3 h-3 text-rose-600" /> REJECTED</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px]">{st}</span>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Status Tabs Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0 text-xs">
          {STATUS_TABS.map((tab) => {
            const active = statusFilter === tab.value;
            return (
              <button
                key={tab.value}
                onClick={() => {
                  setStatusFilter(tab.value);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg font-semibold transition shrink-0 ${
                  active
                    ? 'bg-amber-500 text-slate-950 shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 shrink-0">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search quotation #, customer..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 w-56 md:w-64"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-2 rounded-lg bg-slate-900 text-white font-semibold text-xs hover:bg-slate-800 transition shadow-sm"
          >
            Search
          </button>
        </form>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-2 text-amber-500" />
            <p className="text-xs">Loading quotations directory...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
            <p className="text-xs font-semibold text-rose-700">{error}</p>
          </div>
        ) : quotations.length === 0 ? (
          <div className="py-20 text-center text-slate-400">
            <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No quotations found</p>
            <p className="text-xs text-slate-400 mt-1">
              {statusFilter ? `No quotations in '${statusFilter}' status.` : 'Create a new quotation from the top action bar.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Quotation # & Date</th>
                  <th className="py-3 px-4">Customer & Enquiry</th>
                  <th className="py-3 px-4">System Spec</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Commercial Summary</th>
                  <th className="py-3 px-4">Valid Until</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {quotations.map((q) => (
                  <tr key={q.id} className="hover:bg-slate-50/60 transition">
                    {/* Quotation Number & Version */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-slate-900">{q.quotation_number}</span>
                        <span className="bg-slate-200 text-slate-700 text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold">
                          v{q.version}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Dated: {q.quotation_date}
                      </div>
                    </td>

                    {/* Customer & Enquiry */}
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{q.customer_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {q.enquiry_number ? `Enquiry: ${q.enquiry_number}` : `Enquiry #${q.enquiry_id}`}
                        {q.customer_type ? ` • ${q.customer_type}` : ''}
                      </div>
                    </td>

                    {/* Spec */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-amber-900 flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-amber-500" />
                        {q.capacity_kw} kW {q.system_type}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {q.survey_number ? `Survey: ${q.survey_number}` : 'Standard Feasibility'}
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-4">
                      {statusBadge(q.status)}
                    </td>

                    {/* Commercials */}
                    <td className="py-3 px-4 text-right font-mono">
                      <div className="font-bold text-emerald-700">
                        ₹{q.net_payable_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Gross: ₹{q.gross_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        {q.subsidy_estimate > 0 && ` • Subsidy: ₹${q.subsidy_estimate?.toLocaleString('en-IN')}`}
                      </div>
                    </td>

                    {/* Validity */}
                    <td className="py-3 px-4">
                      <div className="text-slate-800 font-medium">{q.valid_until}</div>
                      <div className="text-[10px] text-slate-400">By {q.creator_name || 'Staff'}</div>
                    </td>

                    {/* Action Controls */}
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        {/* 1. Detail View */}
                        <button
                          onClick={() => onOpenDetail(q.id)}
                          title="View Full Breakdown & Revision History"
                          className="p-1.5 text-slate-600 hover:text-amber-600 hover:bg-slate-100 rounded-lg transition"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* Print / Save PDF View */}
                        <button
                          onClick={() => setPrintQuotationId(q.id)}
                          title="Print Quotation / Save as PDF"
                          className="p-1.5 text-slate-600 hover:text-amber-600 hover:bg-slate-100 rounded-lg transition"
                        >
                          <Printer className="w-4 h-4" />
                        </button>

                        {/* 2. Edit (DRAFT only for Sales/SuperAdmin) */}
                        {q.status === 'DRAFT' && (isSuperAdmin || isSales) && (
                          <button
                            onClick={() => onOpenEdit(q)}
                            title="Edit Draft Quotation"
                            className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}

                        {/* 3. Submit for Review (DRAFT -> PENDING_APPROVAL) */}
                        {q.status === 'DRAFT' && (isSuperAdmin || isSales) && (
                          <button
                            onClick={() => setConfirmAction({ type: 'SUBMIT', quotation: q })}
                            title="Submit for Technical & Commercial Approval"
                            className="px-2 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-[11px] transition shadow-xs"
                          >
                            Submit
                          </button>
                        )}

                        {/* 4. Review / Approve / Reject (PENDING_APPROVAL) */}
                        {q.status === 'PENDING_APPROVAL' && (isSuperAdmin || isDirector || isTechManager) && (
                          <button
                            onClick={() => onOpenApproval(q)}
                            title="Technical Manager & Director Review"
                            className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded text-[11px] transition shadow-xs flex items-center gap-1"
                          >
                            <ShieldCheck className="w-3.5 h-3.5" /> Review
                          </button>
                        )}

                        {/* 5. Send to Customer (APPROVED -> SENT) */}
                        {q.status === 'APPROVED' && (isSuperAdmin || isSales) && (
                          <button
                            onClick={() => setConfirmAction({ type: 'SEND', quotation: q })}
                            title="Send Approved Quotation to Customer"
                            className="px-2 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded text-[11px] transition shadow-xs flex items-center gap-1"
                          >
                            <Send className="w-3.5 h-3.5" /> Send
                          </button>
                        )}

                        {/* 6. Customer Accept / Decline (SENT) */}
                        {q.status === 'SENT' && (isCustomer || isSuperAdmin) && (
                          <>
                            <button
                              onClick={() => setConfirmAction({ type: 'ACCEPT', quotation: q })}
                              title={isSuperAdmin ? 'Administrative Acceptance' : 'Accept Quotation & Win Project'}
                              className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[11px] transition shadow-xs"
                            >
                              {isSuperAdmin ? 'Admin Accept' : 'Accept'}
                            </button>
                            {isCustomer && (
                              <button
                                onClick={() => setConfirmAction({ type: 'REJECT_CUSTOMER', quotation: q })}
                                title="Decline Quotation"
                                className="px-2 py-1 bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold rounded text-[11px] transition"
                              >
                                Decline
                              </button>
                            )}
                          </>
                        )}

                        {/* 7. Revise (APPROVED, SENT, REJECTED) */}
                        {['APPROVED', 'SENT', 'REJECTED'].includes(q.status) && (isSuperAdmin || isSales) && (
                          <button
                            onClick={() => onOpenRevision(q)}
                            title="Create New Revision (Snapshot & Return to Draft)"
                            className="p-1.5 text-slate-600 hover:text-amber-600 hover:bg-slate-100 rounded-lg transition"
                          >
                            <History className="w-4 h-4" />
                          </button>
                        )}

                        {/* 8. Delete (DRAFT only) */}
                        {q.status === 'DRAFT' && (isSuperAdmin || isSales) && (
                          <button
                            onClick={() => setConfirmAction({ type: 'DELETE', quotation: q })}
                            title="Delete Draft"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
          <div>
            Showing <span className="font-bold text-slate-800">{quotations.length}</span> of <span className="font-bold text-slate-800">{total}</span> quotations
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-slate-700">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation & Action Dialog */}
      {confirmAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 max-w-md w-full space-y-4">
            <div className="flex items-start gap-3">
              <div className={`p-2.5 rounded-xl shrink-0 ${
                confirmAction.type === 'DELETE' || confirmAction.type === 'REJECT_CUSTOMER'
                  ? 'bg-rose-100 text-rose-600'
                  : confirmAction.type === 'ACCEPT'
                  ? 'bg-emerald-100 text-emerald-600'
                  : 'bg-amber-100 text-amber-600'
              }`}>
                {confirmAction.type === 'DELETE' || confirmAction.type === 'REJECT_CUSTOMER' ? (
                  <AlertTriangle className="w-5 h-5" />
                ) : confirmAction.type === 'ACCEPT' ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </div>
              <div>
                <h4 className="font-bold text-sm text-slate-900">
                  {confirmAction.type === 'SUBMIT' && 'Submit Quotation for Review'}
                  {confirmAction.type === 'SEND' && 'Send Quotation to Customer'}
                  {confirmAction.type === 'ACCEPT' && (isSuperAdmin ? 'Administrative Customer Acceptance' : 'Accept Quotation Proposal')}
                  {confirmAction.type === 'REJECT_CUSTOMER' && 'Decline Quotation Proposal'}
                  {confirmAction.type === 'DELETE' && 'Delete Draft Quotation'}
                </h4>
                <p className="text-xs text-slate-500 mt-1 font-mono">
                  {confirmAction.quotation.quotation_number} (v{confirmAction.quotation.version}) • {confirmAction.quotation.customer_name}
                </p>
              </div>
            </div>

            {actionError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg font-medium">
                {actionError}
              </div>
            )}

            <div className="text-xs text-slate-600 leading-relaxed">
              {confirmAction.type === 'SUBMIT' && (
                <p>This draft quotation will be transitioned to <strong>PENDING REVIEW</strong>. Managers will be notified to review technical and commercial feasibility.</p>
              )}
              {confirmAction.type === 'SEND' && (
                <p>Quotation will be marked <strong>SENT</strong> and dispatched to the customer. The associated sales enquiry will automatically advance to <strong>QUOTED</strong>.</p>
              )}
              {confirmAction.type === 'ACCEPT' && (
                <div className="space-y-2">
                  <p>Customer acceptance seals this quotation as <strong>ACCEPTED</strong> and legally binding. The sales pipeline deal will immediately update to <strong>WON</strong>.</p>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Optional Acceptance Notes:</label>
                    <input
                      type="text"
                      placeholder="e.g. Confirmed via email authorization..."
                      value={actionInput}
                      onChange={(e) => setActionInput(e.target.value)}
                      className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              )}
              {confirmAction.type === 'REJECT_CUSTOMER' && (
                <div className="space-y-2">
                  <p>Declining this proposal will mark the quotation as <strong>REJECTED</strong>. Sales will be alerted to propose a revision.</p>
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Mandatory Reason for Declining *</label>
                    <input
                      type="text"
                      placeholder="e.g. Budget constraints, preferred battery option..."
                      value={actionInput}
                      onChange={(e) => setActionInput(e.target.value)}
                      className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:ring-2 focus:ring-rose-500"
                      required
                    />
                  </div>
                </div>
              )}
              {confirmAction.type === 'DELETE' && (
                <p className="text-rose-700 font-medium">
                  Are you sure you want to permanently delete this draft quotation? This action cannot be undone.
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => {
                  setConfirmAction(null);
                  setActionInput('');
                  setActionError(null);
                }}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteAction}
                disabled={actionLoading}
                className={`px-4 py-2 rounded-xl text-xs font-bold text-white shadow-sm transition ${
                  confirmAction.type === 'DELETE' || confirmAction.type === 'REJECT_CUSTOMER'
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : confirmAction.type === 'ACCEPT'
                    ? 'bg-emerald-600 hover:bg-emerald-500'
                    : 'bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold'
                }`}
              >
                {actionLoading ? 'Executing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Printable Quotation Modal */}
      {printQuotationId && (
        <QuotationPrintModal
          isOpen={Boolean(printQuotationId)}
          onClose={() => setPrintQuotationId(null)}
          quotationId={printQuotationId}
        />
      )}
    </div>
  );
}
