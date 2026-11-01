import React, { useState, useEffect } from 'react';
import {
  Compass,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  ShieldCheck,
  FileText,
} from 'lucide-react';
import { getMe } from '../services/employeeApi';
import { getSurveys } from '../services/surveyApi';
import SurveyList from '../components/SurveyList';
import SurveyModal from '../components/SurveyModal';
import SurveyObservationModal from '../components/SurveyObservationModal';
import SurveyDetailModal from '../components/SurveyDetailModal';
import SurveyApprovalModal from '../components/SurveyApprovalModal';

export default function SurveyManagementPage() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Modals state
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showObservationModal, setShowObservationModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);

  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [selectedSurveyId, setSelectedSurveyId] = useState(null);

  // Metrics summary
  const [metrics, setMetrics] = useState({
    total: 0,
    drafts: 0,
    reviewQueue: 0,
    approved: 0,
    corrections: 0,
  });

  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = () => setRefreshKey((k) => k + 1);

  useEffect(() => {
    getMe()
      .then((res) => {
        if (res && res.data) setCurrentUser(res.data);
      })
      .catch(() => setCurrentUser(null))
      .finally(() => setLoadingUser(false));
  }, []);

  // Fetch summary counts
  useEffect(() => {
    Promise.all([
      getSurveys({ limit: 1 }),
      getSurveys({ status: 'DRAFT', limit: 1 }),
      getSurveys({ status: 'SUBMITTED', limit: 1 }),
      getSurveys({ status: 'APPROVED', limit: 1 }),
      getSurveys({ status: 'CORRECTION_REQUESTED', limit: 1 }),
    ])
      .then(([allRes, draftRes, subRes, appRes, corrRes]) => {
        setMetrics({
          total: allRes?.data?.total || 0,
          drafts: draftRes?.data?.total || 0,
          reviewQueue: subRes?.data?.total || 0,
          approved: appRes?.data?.total || 0,
          corrections: corrRes?.data?.total || 0,
        });
      })
      .catch(() => {});
  }, [refreshKey]);

  const roleSlug = currentUser?.role?.slug || '';
  const isCustomer = roleSlug === 'CUSTOMER';
  const isTechnician = roleSlug === 'FIELD_TECHNICIAN';

  // Can schedule if Sales, TM, Director, or Super Admin
  const canSchedule = !isCustomer && !isTechnician;

  // Handlers
  const handleOpenDetail = (srvId) => {
    setSelectedSurveyId(srvId);
    setShowDetailModal(true);
  };

  const handleOpenEditObservations = (srv) => {
    setSelectedSurvey(srv);
    setShowObservationModal(true);
  };

  const handleOpenApproval = (srv) => {
    setSelectedSurvey(srv);
    setShowApprovalModal(true);
  };

  if (!loadingUser && isCustomer) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-slate-900 text-lg">Access Restricted</h3>
        <p className="text-xs text-slate-500">
          Internal engineering site surveys and technical feasibility approvals are restricted to company staff.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Module Title & Action Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 flex items-center justify-center font-bold">
              <Compass className="w-5 h-5 stroke-[2.5]" />
            </div>
            <span>Site Surveys & Technical Approval</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Rooftop feasibility assessments, shading analysis, civil structure inspections, and technical sign-offs.
          </p>
        </div>

        {canSchedule && (
          <button
            onClick={() => setShowScheduleModal(true)}
            className="px-4 py-2.5 rounded-xl font-bold text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-sm flex items-center gap-2"
          >
            <Plus className="w-4 h-4 stroke-[3]" />
            <span>Schedule Site Survey</span>
          </button>
        )}
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Total Surveys</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">{metrics.total}</span>
          <span className="text-[10px] text-slate-500">All registered visits</span>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Draft Inspections</span>
          <span className="text-2xl font-black text-slate-700 mt-1 block">{metrics.drafts}</span>
          <span className="text-[10px] text-slate-400">Scheduled / measuring</span>
        </div>

        <div className="bg-white rounded-xl border border-blue-200 bg-blue-50/20 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider block">Review Queue</span>
          <span className="text-2xl font-black text-blue-900 mt-1 block">{metrics.reviewQueue}</span>
          <span className="text-[10px] text-blue-600 font-medium">Awaiting TM approval</span>
        </div>

        <div className="bg-white rounded-xl border border-amber-200 bg-amber-50/20 p-4 shadow-xs">
          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider block">Corrections</span>
          <span className="text-2xl font-black text-amber-900 mt-1 block">{metrics.corrections}</span>
          <span className="text-[10px] text-amber-600 font-medium">Returned to surveyor</span>
        </div>

        <div className="bg-white rounded-xl border border-emerald-200 bg-emerald-50/20 p-4 shadow-xs col-span-2 lg:col-span-1">
          <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">Approved Sites</span>
          <span className="text-2xl font-black text-emerald-900 mt-1 block">{metrics.approved}</span>
          <span className="text-[10px] text-emerald-600 font-medium">Ready for quotation</span>
        </div>
      </div>

      {/* Main Survey List */}
      <SurveyList
        currentUser={currentUser}
        onOpenDetail={handleOpenDetail}
        onOpenEditObservations={handleOpenEditObservations}
        onOpenApproval={handleOpenApproval}
        refreshKey={refreshKey}
      />

      {/* Modal 1: Schedule Survey */}
      <SurveyModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        onSuccess={triggerRefresh}
      />

      {/* Modal 2: Record / Edit Technical Observations */}
      <SurveyObservationModal
        isOpen={showObservationModal}
        onClose={() => {
          setShowObservationModal(false);
          setSelectedSurvey(null);
        }}
        onSuccess={triggerRefresh}
        survey={selectedSurvey}
      />

      {/* Modal 3: Detailed Survey View */}
      <SurveyDetailModal
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedSurveyId(null);
        }}
        surveyId={selectedSurveyId}
        currentUser={currentUser}
        onOpenEditObservations={handleOpenEditObservations}
        onOpenApprovalModal={handleOpenApproval}
        onRefreshList={triggerRefresh}
      />

      {/* Modal 4: Technical Approval & Review Decision */}
      <SurveyApprovalModal
        isOpen={showApprovalModal}
        onClose={() => {
          setShowApprovalModal(false);
          setSelectedSurvey(null);
        }}
        onSuccess={triggerRefresh}
        survey={selectedSurvey}
      />
    </div>
  );
}
