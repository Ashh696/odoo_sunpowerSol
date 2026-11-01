import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  FileText,
  Plus,
  RefreshCw,
  Clock,
  Send,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { getMe } from '../services/employeeApi';
import { getQuotations } from '../services/quotationApi';
import QuotationList from '../components/QuotationList';
import QuotationModal from '../components/QuotationModal';
import QuotationDetailModal from '../components/QuotationDetailModal';
import QuotationApprovalModal from '../components/QuotationApprovalModal';
import QuotationRevisionModal from '../components/QuotationRevisionModal';

export default function QuotationManagementPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryEnquiryId = searchParams.get('enquiry_id');
  const queryOpenCreate = searchParams.get('open_create');

  const [currentUser, setCurrentUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Modals state
  const [showQuotationModal, setShowQuotationModal] = useState(false);
  const [quotationToEdit, setQuotationToEdit] = useState(null);
  const [detailQuotationId, setDetailQuotationId] = useState(null);
  const [approvalQuotation, setApprovalQuotation] = useState(null);
  const [revisionQuotation, setRevisionQuotation] = useState(null);

  // KPI Metrics
  const [metrics, setMetrics] = useState({
    total: 0,
    inReview: 0,
    sent: 0,
    won: 0,
  });

  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = () => setRefreshKey((k) => k + 1);

  // 1. Identify user
  useEffect(() => {
    getMe()
      .then((res) => {
        if (res && res.data) setCurrentUser(res.data);
      })
      .catch(() => setCurrentUser(null))
      .finally(() => setLoadingUser(false));
  }, []);

  // 2. Fetch KPI Metrics
  useEffect(() => {
    Promise.all([
      getQuotations({ limit: 1 }),
      getQuotations({ status: 'PENDING_APPROVAL', limit: 1 }),
      getQuotations({ status: 'SENT', limit: 1 }),
      getQuotations({ status: 'ACCEPTED', limit: 1 }),
    ])
      .then(([allRes, reviewRes, sentRes, wonRes]) => {
        setMetrics({
          total: allRes?.data?.total || 0,
          inReview: reviewRes?.data?.total || 0,
          sent: sentRes?.data?.total || 0,
          won: wonRes?.data?.total || 0,
        });
      })
      .catch((err) => {
        console.warn('Failed to load quotation summary metrics:', err);
      });
  }, [refreshKey]);

  // 3. Handle incoming query param for CRM enquiry quotation creation
  useEffect(() => {
    if (queryOpenCreate === 'true' && queryEnquiryId) {
      setQuotationToEdit(null);
      setShowQuotationModal(true);
    }
  }, [queryOpenCreate, queryEnquiryId]);

  const roleSlug = currentUser?.role?.slug || '';
  const isSuperAdmin = roleSlug === 'SUPER_ADMIN';
  const isSales = roleSlug === 'SALES';
  const isDirector = roleSlug === 'DIRECTOR';
  const isTechManager = roleSlug === 'TECHNICAL_MANAGER';
  const isCustomer = roleSlug === 'CUSTOMER';

  const isBlockedRole = [
    'WAREHOUSE_PROCUREMENT',
    'FIELD_TECHNICIAN',
    'FINANCE_ACCOUNTS',
  ].includes(roleSlug);

  if (loadingUser) {
    return (
      <div className="py-24 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-amber-500" />
        <p className="text-xs">Authenticating SIMS quotation engine session...</p>
      </div>
    );
  }

  if (isBlockedRole) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-14 h-14 bg-rose-100 rounded-2xl flex items-center justify-center mx-auto text-rose-600 shadow-sm">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Quotation Engine Access Restricted</h2>
        <p className="text-xs text-slate-600 leading-relaxed max-w-md mx-auto">
          Your role (<span className="font-mono font-bold text-rose-700">{roleSlug}</span>) does not have authorization to view or manage commercial customer quotations and pricing.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <FileText className="w-7 h-7 text-amber-500" />
              Quotations & Commercial Engine
            </h1>
            <span className="bg-amber-100 border border-amber-300 text-amber-900 text-xs px-2.5 py-0.5 rounded-full font-bold">
              Phase 5.4 Active
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Create, review, approve, dispatch, and revise solar installation proposals with snapshotted pricing and DBT subsidy estimates.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={triggerRefresh}
            title="Refresh Quotations"
            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition shadow-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {(isSuperAdmin || isSales) && (
            <button
              onClick={() => {
                setQuotationToEdit(null);
                setShowQuotationModal(true);
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition shrink-0"
            >
              <Plus className="w-4 h-4" /> New Quotation
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Row */}
      {!isCustomer && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Total Quotations
            </span>
            <div className="text-2xl font-black text-slate-900 mt-1">{metrics.total}</div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Pipeline proposals</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider block flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> In Review
            </span>
            <div className="text-2xl font-black text-amber-700 mt-1">{metrics.inReview}</div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Pending Manager Approval</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-purple-600 uppercase tracking-wider block flex items-center gap-1">
              <Send className="w-3.5 h-3.5" /> Dispatched
            </span>
            <div className="text-2xl font-black text-purple-700 mt-1">{metrics.sent}</div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Sent to Customers</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider block flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Accepted (Won)
            </span>
            <div className="text-2xl font-black text-emerald-700 mt-1">{metrics.won}</div>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Customer Confirmed</span>
          </div>
        </div>
      )}

      {/* Main Quotation List */}
      <QuotationList
        currentUser={currentUser}
        refreshKey={refreshKey}
        onOpenDetail={(id) => setDetailQuotationId(id)}
        onOpenEdit={(q) => {
          setQuotationToEdit(q);
          setShowQuotationModal(true);
        }}
        onOpenApproval={(q) => setApprovalQuotation(q)}
        onOpenRevision={(q) => setRevisionQuotation(q)}
      />

      {/* Modal: Create & Edit Quotation */}
      <QuotationModal
        isOpen={showQuotationModal}
        onClose={() => {
          setShowQuotationModal(false);
          setQuotationToEdit(null);
          // Clear query params if any
          if (queryEnquiryId) {
            setSearchParams({});
          }
        }}
        onSuccess={() => {
          triggerRefresh();
        }}
        quotationToEdit={quotationToEdit}
        initialEnquiryId={queryEnquiryId ? parseInt(queryEnquiryId, 10) : null}
      />

      {/* Modal: Detail View */}
      <QuotationDetailModal
        isOpen={Boolean(detailQuotationId)}
        onClose={() => setDetailQuotationId(null)}
        quotationId={detailQuotationId}
        currentUser={currentUser}
        onOpenApprove={(q) => setApprovalQuotation(q)}
        onOpenRevise={(q) => setRevisionQuotation(q)}
        onOpenSend={(q) => {
          // Re-render list with trigger or direct action
          triggerRefresh();
        }}
        onOpenAccept={(q) => {
          triggerRefresh();
        }}
      />

      {/* Modal: Approval / Rejection */}
      <QuotationApprovalModal
        isOpen={Boolean(approvalQuotation)}
        onClose={() => setApprovalQuotation(null)}
        onSuccess={() => triggerRefresh()}
        quotation={approvalQuotation}
        currentUser={currentUser}
      />

      {/* Modal: Revision Creation */}
      <QuotationRevisionModal
        isOpen={Boolean(revisionQuotation)}
        onClose={() => setRevisionQuotation(null)}
        onSuccess={() => triggerRefresh()}
        quotation={revisionQuotation}
      />
    </div>
  );
}
