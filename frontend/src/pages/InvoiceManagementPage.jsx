import React, { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Printer,
  Eye,
  Plus,
  CreditCard,
  Building,
} from 'lucide-react';
import { getInvoices } from '../services/financeApi';
import { getMe } from '../services/employeeApi';
import InvoiceDetailModal from '../components/InvoiceDetailModal';
import InvoicePrintModal from '../components/InvoicePrintModal';
import SupplierInvoicesTab from '../components/SupplierInvoicesTab';
import ProjectProfitabilityTab from '../components/ProjectProfitabilityTab';

export default function InvoiceManagementPage() {
  const [activeTab, setActiveTab] = useState('CUSTOMER_INVOICES');
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  // KPIs
  const [kpis, setKpis] = useState({
    totalBilled: 0,
    totalPaid: 0,
    totalOutstanding: 0,
  });

  // User
  const [currentUser, setCurrentUser] = useState(null);

  // Modals
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);
  const [invoiceToPrint, setInvoiceToPrint] = useState(null);

  const fetchCurrentUser = async () => {
    try {
      const res = await getMe();
      setCurrentUser(res.data);
    } catch {
      setCurrentUser(null);
    }
  };

  const fetchInvoicesList = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        limit,
        search: searchTerm.trim() || undefined,
        status: statusFilter || undefined,
        invoice_type: typeFilter || undefined,
      };
      const res = await getInvoices(params);
      const data = res.data;
      setInvoices(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
      setKpis({
        totalBilled: parseFloat(data.total_billed || 0),
        totalPaid: parseFloat(data.total_paid || 0),
        totalOutstanding: parseFloat(data.total_outstanding || 0),
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load invoices.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  useEffect(() => {
    fetchInvoicesList();
  }, [page, statusFilter, typeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchInvoicesList();
  };

  const statusBadge = (st) => {
    switch (st) {
      case 'PAID':
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">PAID</span>;
      case 'PARTIALLY_PAID':
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">PARTIAL</span>;
      case 'OVERDUE':
        return <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">OVERDUE</span>;
      default:
        return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full text-[11px] font-bold">PENDING</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-7 h-7 text-amber-500" />
            <span>Commercial Invoicing & Financial Operations</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage advance tokens, milestone billing, supplier AP bills, and project profitability analysis
          </p>
        </div>

        <button
          onClick={() => fetchInvoicesList()}
          disabled={loading}
          className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold shadow-sm transition flex items-center gap-1.5 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-500' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('CUSTOMER_INVOICES')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'CUSTOMER_INVOICES'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Customer Invoices (AR)</span>
        </button>
        <button
          onClick={() => setActiveTab('SUPPLIER_INVOICES')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'SUPPLIER_INVOICES'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Building className="w-4 h-4" />
          <span>Supplier Invoices (AP)</span>
        </button>
        <button
          onClick={() => setActiveTab('PROJECT_PROFITABILITY')}
          className={`pb-3 text-xs font-bold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'PROJECT_PROFITABILITY'
              ? 'border-amber-500 text-amber-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <CreditCard className="w-4 h-4" />
          <span>Project Profitability & Costs</span>
        </button>
      </div>

      {activeTab === 'SUPPLIER_INVOICES' && (
        <SupplierInvoicesTab currentUser={currentUser} />
      )}

      {activeTab === 'PROJECT_PROFITABILITY' && (
        <ProjectProfitabilityTab currentUser={currentUser} />
      )}

      {activeTab === 'CUSTOMER_INVOICES' && (
        <>
          {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Invoiced</span>
            <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg">
              <FileText className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-slate-900">
            ₹{kpis.totalBilled.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Total milestone bill of supply</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cash Collected / Allocated</span>
            <span className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-emerald-600">
            ₹{kpis.totalPaid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Total payments matched to invoices</span>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Outstanding Receivables</span>
            <span className="p-1.5 bg-amber-50 text-amber-600 rounded-lg">
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-black font-mono text-amber-600">
            ₹{kpis.totalOutstanding.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <span className="text-[11px] text-slate-400">Pending customer milestone balance</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by invoice number or customer name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-amber-500 bg-slate-50/50"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition shadow-sm"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Milestone Types</option>
            <option value="ADVANCE">Advance / Booking</option>
            <option value="MILESTONE_DISPATCH">Pre-Dispatch</option>
            <option value="MILESTONE_INSTALLATION">Installation</option>
            <option value="FINAL">Final Commissioning</option>
            <option value="SUBSIDY">DBT Subsidy</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Payment Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="PARTIALLY_PAID">Partially Paid</option>
            <option value="PAID">Paid</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        {error && (
          <div className="p-4 bg-rose-50 border-b border-rose-100 flex items-center gap-2 text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Customer & Order</th>
                <th className="py-3 px-4">Billing Date</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4 text-right">Total (₹)</th>
                <th className="py-3 px-4 text-right">Paid (₹)</th>
                <th className="py-3 px-4 text-right">Balance (₹)</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-amber-500 mb-2" />
                    <span>Loading invoices...</span>
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="font-semibold text-slate-600">No invoices found</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Generate a milestone invoice from an order or adjust your search filter.
                    </p>
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      {inv.invoice_number}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px] font-semibold border border-slate-200">
                        {inv.invoice_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <p className="font-semibold text-slate-900">{inv.customer?.full_name || 'N/A'}</p>
                      <span className="text-[11px] text-slate-400 font-mono">Order: {inv.order?.order_number || 'N/A'}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-medium">
                      {new Date(inv.invoice_date).toLocaleDateString('en-IN')}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-medium">
                      {new Date(inv.due_date).toLocaleDateString('en-IN')}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                      ₹{parseFloat(inv.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-emerald-600 font-semibold">
                      ₹{parseFloat(inv.paid_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold">
                      <span className={parseFloat(inv.balance_amount) > 0 ? 'text-amber-600' : 'text-slate-400'}>
                        ₹{parseFloat(inv.balance_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {statusBadge(inv.payment_status)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedInvoiceId(inv.id)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition flex items-center gap-1"
                          title="View Invoice & Allocations"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View</span>
                        </button>
                        <button
                          onClick={() => setInvoiceToPrint(inv)}
                          className="p-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg transition"
                          title="Print / PDF"
                        >
                          <Printer className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination footer */}
        {pages > 1 && (
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
            <span>Showing Page {page} of {pages} ({total} invoices total)</span>
            <div className="flex gap-1.5">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 bg-white border border-slate-200 rounded font-semibold disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                className="px-3 py-1 bg-white border border-slate-200 rounded font-semibold disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
      </>
      )}

      {/* Modals */}
      {selectedInvoiceId && (
        <InvoiceDetailModal
          isOpen={Boolean(selectedInvoiceId)}
          onClose={() => setSelectedInvoiceId(null)}
          invoiceId={selectedInvoiceId}
          currentUser={currentUser}
          onRefresh={() => fetchInvoicesList()}
        />
      )}

      {invoiceToPrint && (
        <InvoicePrintModal
          isOpen={Boolean(invoiceToPrint)}
          onClose={() => setInvoiceToPrint(null)}
          invoice={invoiceToPrint}
        />
      )}
    </div>
  );
}
