import React, { useState, useEffect } from 'react';
import {
  Sun,
  ShieldCheck,
  FileText,
  Receipt,
  LifeBuoy,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Calendar,
  User,
  Phone,
  Mail,
  MapPin,
  Zap,
  Layers,
  ArrowRight,
  RefreshCw,
  Plus,
  X,
  Printer,
  ChevronRight,
  Check,
  ThumbsUp,
  Landmark,
  Edit3,
  ClipboardList,
  Truck,
  Building,
} from 'lucide-react';
import {
  getMyCustomerProfile,
  updateMyCustomerProfile,
  getMyProjects,
  getMyQuotations,
  acceptQuotation,
  rejectQuotation,
  getMyInvoices,
  getMyPayments,
  getMyWarranties,
  getMyServiceTickets,
  createCustomerServiceTicket,
  submitCustomerAcceptance,
  getMySubsidyApplications,
  getMyEnquiries,
  createCustomerEnquiry,
  getMySurveys,
  getMyDispatches,
} from '../services/customerPortalApi';
import InvoicePrintModal from '../components/InvoicePrintModal';

const MILESTONES_ORDER = [
  'Engineering & Site Planning',
  'Procurement & Allocation',
  'Material Dispatch',
  'Civil & Structure Installation',
  'Panel & Inverter Mounting',
  'Electrical Wiring & Earthing',
  'Testing & Quality Commissioning',
  'DISCOM Net-Metering & Grid Sync',
  'Final Subsidy Release & Handover',
];

export default function CustomerPortalPage() {
  const [activeTab, setActiveTab] = useState('PROJECTS');
  const [profile, setProfile] = useState(null);
  const [projects, setProjects] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [warranties, setWarranties] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [subsidyApps, setSubsidyApps] = useState([]);
  const [enquiries, setEnquiries] = useState([]);
  const [surveys, setSurveys] = useState([]);
  const [dispatches, setDispatches] = useState([]);
  const [dispatchForbidden, setDispatchForbidden] = useState(false);
  const [dispatchError, setDispatchError] = useState(null);
  const [dispatchLoading, setDispatchLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals & Action States
  const [editProfileModal, setEditProfileModal] = useState(false);
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    alternate_phone: '',
    address: '',
    city: '',
    state: '',
    pincode: '',
    electricity_consumer_number: '',
  });
  const [submittingProfile, setSubmittingProfile] = useState(false);

  const [newEnquiryModal, setNewEnquiryModal] = useState(false);
  const [enquiryForm, setEnquiryForm] = useState({
    system_type: 'ON_GRID',
    proposed_capacity_kw: 3.0,
    monthly_electricity_bill: '',
    roof_type: 'RCC_FLAT',
    notes: '',
  });
  const [submittingEnquiry, setSubmittingEnquiry] = useState(false);

  const [newTicketModal, setNewTicketModal] = useState(false);
  const [ticketForm, setTicketForm] = useState({
    project_id: '',
    issue_category: 'GENERAL',
    priority: 'MEDIUM',
    description: '',
  });
  const [submittingTicket, setSubmittingTicket] = useState(false);

  const [rejectModal, setRejectModal] = useState(false);
  const [selectedQuoteId, setSelectedQuoteId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const [printInvoice, setPrintInvoice] = useState(null);

  const [acceptanceModal, setAcceptanceModal] = useState(false);
  const [selectedInstallationId, setSelectedInstallationId] = useState(null);
  const [acceptanceNotes, setAcceptanceNotes] = useState('');
  const [signatureName, setSignatureName] = useState('');

  const loadAllCustomerData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        profRes,
        projRes,
        qRes,
        invRes,
        payRes,
        warRes,
        tickRes,
        subRes,
        enqRes,
        survRes,
        dispRes,
      ] = await Promise.allSettled([
        getMyCustomerProfile(),
        getMyProjects(),
        getMyQuotations(),
        getMyInvoices(),
        getMyPayments(),
        getMyWarranties(),
        getMyServiceTickets(),
        getMySubsidyApplications(),
        getMyEnquiries(),
        getMySurveys(),
        getMyDispatches(),
      ]);

      if (profRes.status === 'fulfilled') {
        const pData = profRes.value?.data?.data || profRes.value?.data || profRes.value;
        if (pData && (pData.id || pData.full_name)) {
          setProfile(pData);
        }
      }
      if (projRes.status === 'fulfilled') {
        const pItems = projRes.value?.data?.items || projRes.value?.data?.data?.items || projRes.value?.items || projRes.value?.data || [];
        setProjects(Array.isArray(pItems) ? pItems : []);
      }
      if (qRes.status === 'fulfilled') {
        const qItems = qRes.value?.data?.items || qRes.value?.data?.data?.items || qRes.value?.items || qRes.value?.data || [];
        setQuotations(Array.isArray(qItems) ? qItems : []);
      }
      if (invRes.status === 'fulfilled') {
        const iItems = invRes.value?.data?.items || invRes.value?.data?.data?.items || invRes.value?.items || invRes.value?.data || [];
        setInvoices(Array.isArray(iItems) ? iItems : []);
      }
      if (payRes.status === 'fulfilled') {
        const payItems = payRes.value?.data?.items || payRes.value?.data?.data?.items || payRes.value?.items || payRes.value?.data || [];
        setPayments(Array.isArray(payItems) ? payItems : []);
      }
      if (warRes.status === 'fulfilled') {
        const wItems = warRes.value?.data?.items || warRes.value?.data?.data?.items || warRes.value?.items || warRes.value?.data || [];
        setWarranties(Array.isArray(wItems) ? wItems : []);
      }
      if (tickRes.status === 'fulfilled') {
        const tItems = tickRes.value?.data?.items || tickRes.value?.data?.data?.items || tickRes.value?.items || tickRes.value?.data || [];
        setTickets(Array.isArray(tItems) ? tItems : []);
      }
      if (subRes.status === 'fulfilled') {
        const sItems = subRes.value?.data?.items || subRes.value?.data?.data?.items || subRes.value?.items || subRes.value?.data || [];
        setSubsidyApps(Array.isArray(sItems) ? sItems : []);
      }
      if (enqRes.status === 'fulfilled') {
        const eItems = enqRes.value?.data?.items || enqRes.value?.data?.data?.items || enqRes.value?.items || enqRes.value?.data || [];
        setEnquiries(Array.isArray(eItems) ? eItems : []);
      }
      if (survRes.status === 'fulfilled') {
        const suItems = survRes.value?.data?.items || survRes.value?.data?.data?.items || survRes.value?.items || survRes.value?.data || [];
        setSurveys(Array.isArray(suItems) ? suItems : []);
      }
      if (dispRes.status === 'fulfilled') {
        const dItems = dispRes.value?.data?.items || dispRes.value?.data?.data?.items || dispRes.value?.items || dispRes.value?.data || [];
        setDispatches(Array.isArray(dItems) ? dItems : []);
        setDispatchForbidden(false);
        setDispatchError(null);
      } else {
        const status = dispRes.reason?.response?.status;
        if (status === 403) {
          setDispatchForbidden(true);
          setDispatchError(null);
          setDispatches([]);
        } else {
          setDispatchForbidden(false);
          setDispatchError(dispRes.reason?.response?.data?.detail || dispRes.reason?.message || 'Failed to load dispatch details');
          setDispatches([]);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load customer portal data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllCustomerData();
  }, []);

  const handleRetryDispatches = async () => {
    setDispatchLoading(true);
    setDispatchError(null);
    try {
      const res = await getMyDispatches();
      const dItems = res?.data?.items || res?.data?.data?.items || res?.items || res?.data || [];
      setDispatches(Array.isArray(dItems) ? dItems : []);
      setDispatchForbidden(false);
    } catch (err) {
      if (err.response?.status === 403) {
        setDispatchForbidden(true);
        setDispatchError(null);
      } else {
        setDispatchForbidden(false);
        setDispatchError(err.response?.data?.detail || err.message || 'Failed to load dispatch details');
      }
    } finally {
      setDispatchLoading(false);
    }
  };

  const openEditProfile = () => {
    setProfileForm({
      full_name: profile?.full_name || '',
      alternate_phone: profile?.alternate_phone || '',
      address: profile?.address || '',
      city: profile?.city || '',
      state: profile?.state || '',
      pincode: profile?.pincode || '',
      electricity_consumer_number: profile?.electricity_consumer_number || profile?.consumer_number || '',
    });
    setEditProfileModal(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSubmittingProfile(true);
    try {
      const res = await updateMyCustomerProfile(profileForm);
      const updated = res?.data?.data || res?.data || res;
      setProfile(updated);
      setEditProfileModal(false);
      alert('Your customer profile details have been updated successfully.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to update profile');
    } finally {
      setSubmittingProfile(false);
    }
  };

  const handleCreateEnquiry = async (e) => {
    e.preventDefault();
    setSubmittingEnquiry(true);
    try {
      await createCustomerEnquiry({
        system_type: enquiryForm.system_type,
        proposed_capacity_kw: parseFloat(enquiryForm.proposed_capacity_kw),
        monthly_electricity_bill: enquiryForm.monthly_electricity_bill ? parseFloat(enquiryForm.monthly_electricity_bill) : null,
        roof_type: enquiryForm.roof_type,
        notes: enquiryForm.notes,
        customer_id: profile?.id || 0,
      });
      setNewEnquiryModal(false);
      setEnquiryForm({
        system_type: 'ON_GRID',
        proposed_capacity_kw: 3.0,
        monthly_electricity_bill: '',
        roof_type: 'RCC_FLAT',
        notes: '',
      });
      alert('Your solar requirement enquiry has been submitted. Our sales engineering team will review it.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to submit enquiry');
    } finally {
      setSubmittingEnquiry(false);
    }
  };

  const handleAcceptQuote = async (quoteId) => {
    if (!window.confirm('Are you sure you wish to accept this quotation proposal? This will confirm your selection.')) return;
    setActionLoading(true);
    try {
      await acceptQuotation(quoteId);
      alert('Quotation accepted successfully! Our project engineering team will initiate your solar setup.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to accept quotation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectQuote = async (e) => {
    e.preventDefault();
    if (!rejectionReason.trim()) {
      alert('Please provide a reason for declining the proposal.');
      return;
    }
    setActionLoading(true);
    try {
      await rejectQuotation(selectedQuoteId, rejectionReason);
      setRejectModal(false);
      setRejectionReason('');
      setSelectedQuoteId(null);
      alert('Quotation proposal status updated.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to decline quotation');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!ticketForm.project_id) {
      alert('Please select your project.');
      return;
    }
    if (!ticketForm.description.trim()) {
      alert('Please enter a description of the issue.');
      return;
    }
    setSubmittingTicket(true);
    try {
      await createCustomerServiceTicket({
        project_id: parseInt(ticketForm.project_id),
        issue_category: ticketForm.issue_category,
        priority: ticketForm.priority,
        description: ticketForm.description,
      });
      setNewTicketModal(false);
      setTicketForm({ project_id: '', issue_category: 'GENERAL', priority: 'MEDIUM', description: '' });
      alert('Your service ticket has been registered. A SunPower technician will be assigned.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to create service ticket');
    } finally {
      setSubmittingTicket(false);
    }
  };

  const handleCustomerAcceptance = async (e) => {
    e.preventDefault();
    if (!signatureName.trim()) {
      alert('Please enter your full name as signature.');
      return;
    }
    setActionLoading(true);
    try {
      await submitCustomerAcceptance(selectedInstallationId, {
        customer_name: signatureName,
        customer_signature: signatureName,
        acceptance_notes: acceptanceNotes,
        rating_overall: 5,
        is_accepted: true,
      });
      setAcceptanceModal(false);
      setAcceptanceNotes('');
      setSignatureName('');
      setSelectedInstallationId(null);
      alert('Thank you! Customer handover acceptance signed successfully.');
      loadAllCustomerData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Failed to submit acceptance');
    } finally {
      setActionLoading(false);
    }
  };

  const formatCurrency = (val) => {
    const num = parseFloat(val || 0);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num);
  };

  const primaryProject = projects[0] || null;
  const consumerNumber = profile?.electricity_consumer_number || profile?.consumer_number;

  return (
    <div className="space-y-6">
      {/* 1. Welcome & Customer Profile Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-amber-950/60 rounded-2xl p-6 sm:p-8 text-white border border-slate-800 shadow-xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span>SunPower Solar Rooftop Portal</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Welcome, {profile?.full_name || 'Valued Customer'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Track your rooftop solar system installation, view approved engineering quotes, review milestone invoices, and manage service warranties.
            </p>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700/80 text-xs space-y-2 min-w-[260px]">
            <div className="flex items-center justify-between border-b border-slate-700/60 pb-1.5">
              <div className="flex items-center gap-1.5 text-slate-400">
                <User className="w-3.5 h-3.5 text-amber-400" />
                <span>Customer #{profile?.id || '---'}</span>
              </div>
              <button
                onClick={openEditProfile}
                className="inline-flex items-center gap-1 text-[11px] text-amber-400 hover:text-amber-300 font-bold"
              >
                <Edit3 className="w-3 h-3" />
                <span>Edit Profile</span>
              </button>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <Phone className="w-3.5 h-3.5 text-amber-400" />
              <span>{profile?.phone || 'No phone recorded'}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Mail className="w-3.5 h-3.5 text-amber-400" />
              <span>{profile?.email || 'No email recorded'}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400 text-[11px]">
              <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span className="truncate max-w-[200px]">
                {profile?.address ? `${profile.address}, ${profile.city || ''}` : 'Address recorded'}
              </span>
            </div>
            {consumerNumber && (
              <div className="flex items-center gap-2 text-amber-300 font-mono text-[11px] pt-1.5 border-t border-slate-700">
                <Zap className="w-3.5 h-3.5" />
                <span>DISCOM Meter: {consumerNumber}</span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Highlights Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 text-[11px] block">Rooftop Projects</span>
            <span className="text-lg font-black text-amber-400 font-mono">{projects.length}</span>
          </div>
          <div>
            <span className="text-slate-400 text-[11px] block">Installed Capacity</span>
            <span className="text-lg font-black text-white font-mono">
              {primaryProject?.system_capacity_kw ? `${primaryProject.system_capacity_kw} kW` : '---'}
            </span>
          </div>
          <div>
            <span className="text-slate-400 text-[11px] block">Active Warranties</span>
            <span className="text-lg font-black text-emerald-400 font-mono">{warranties.length}</span>
          </div>
          <div>
            <span className="text-slate-400 text-[11px] block">Open Tickets</span>
            <span className="text-lg font-black text-rose-400 font-mono">
              {tickets.filter((t) => t.status !== 'RESOLVED' && t.status !== 'CLOSED').length}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Navigation Tabs Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs px-4 pt-2">
        <nav className="flex space-x-2 overflow-x-auto pb-2">
          {[
            { id: 'PROJECTS', label: 'My Rooftop Project', icon: Sun },
            { id: 'ENQUIRIES', label: `Solar Requests & Surveys (${enquiries.length + surveys.length})`, icon: ClipboardList },
            { id: 'QUOTATIONS', label: `Quotations (${quotations.length})`, icon: FileText },
            { id: 'INVOICES', label: `Invoices & Payments (${invoices.length})`, icon: Receipt },
            { id: 'EQUIPMENT', label: `Equipment & Delivery (${warranties.length + dispatches.length})`, icon: ShieldCheck },
            { id: 'TICKETS', label: `Service Helpdesk (${tickets.length})`, icon: LifeBuoy },
            { id: 'SUBSIDY', label: `PM Surya Ghar Subsidy (${subsidyApps.length})`, icon: Landmark },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-lg whitespace-nowrap transition ${
                  isActive
                    ? 'bg-amber-500 text-slate-950 shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* 3. Content Area */}
      {loading ? (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200 flex flex-col items-center justify-center gap-3">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
          <span className="text-sm font-semibold text-slate-600">Retrieving your solar rooftop records...</span>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button
            onClick={loadAllCustomerData}
            className="text-xs bg-rose-100 hover:bg-rose-200 text-rose-950 font-bold px-3 py-1.5 rounded-lg"
          >
            Retry
          </button>
        </div>
      ) : (
        <div>
          {/* TAB 1: MY ROOFTOP PROJECT & TIMELINE */}
          {activeTab === 'PROJECTS' && (
            <div className="space-y-6">
              {projects.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <Sun className="w-12 h-12 text-amber-400 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Active Installation Project Yet</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Once you approve a quotation proposal, our operations team will initialize your project and milestone tracking will appear here.
                  </p>
                </div>
              ) : (
                projects.map((proj) => {
                  const activeMilestoneIndex = MILESTONES_ORDER.findIndex(
                    (m) => m.toLowerCase() === (proj.current_stage || '').toLowerCase()
                  );
                  const isCompleted = proj.status === 'COMPLETED' || proj.status === 'HANDED_OVER';

                  return (
                    <div key={proj.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-bold text-slate-900">Rooftop Solar Project: {proj.project_code}</h3>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                              {proj.status}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            <span>{proj.site_address || profile?.site_address || 'Rooftop Site Location'}</span>
                          </p>
                        </div>

                        <div className="flex items-center gap-4 text-xs font-mono">
                          <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                            <span className="text-slate-400 text-[10px] block uppercase font-sans">Capacity</span>
                            <span className="font-bold text-slate-900">{proj.system_capacity_kw || '---'} kW {proj.system_type || ''}</span>
                          </div>
                          <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                            <span className="text-slate-400 text-[10px] block uppercase font-sans">Target Handover</span>
                            <span className="font-bold text-slate-900">
                              {proj.planned_completion_date ? new Date(proj.planned_completion_date).toLocaleDateString() : 'TBD'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* 9-Stage Milestone Progress Bar */}
                      <div>
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-1.5">
                          <Clock className="w-4 h-4 text-amber-500" />
                          <span>Installation Milestone Progression</span>
                        </h4>

                        <div className="relative">
                          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-2">
                            {MILESTONES_ORDER.map((stageName, idx) => {
                              const isPast = isCompleted || (activeMilestoneIndex !== -1 && idx < activeMilestoneIndex);
                              const isCurrent = !isCompleted && idx === activeMilestoneIndex;

                              return (
                                <div
                                  key={stageName}
                                  className={`p-3 rounded-xl border text-center transition ${
                                    isPast
                                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                                      : isCurrent
                                      ? 'bg-amber-500 text-slate-950 font-bold border-amber-600 shadow-sm'
                                      : 'bg-slate-50 border-slate-200 text-slate-500 opacity-70'
                                  }`}
                                >
                                  <div className="flex items-center justify-center mb-1.5">
                                    {isPast ? (
                                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                                    ) : (
                                      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                        isCurrent ? 'bg-slate-950 text-amber-400' : 'bg-slate-200 text-slate-600'
                                      }`}>
                                        {idx + 1}
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-[11px] font-semibold leading-tight block">
                                    {stageName}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>

                      {/* Customer Handover Acceptance Action */}
                      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div>
                          <h5 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-emerald-600" />
                            <span>System Commissioning & Customer Handover</span>
                          </h5>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            Once installation and electrical testing are complete, provide your customer sign-off here.
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            setSelectedInstallationId(proj.id);
                            setSignatureName(profile?.full_name || '');
                            setAcceptanceModal(true);
                          }}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center gap-1.5 shrink-0"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>Customer Acceptance Sign-Off</span>
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* TAB 2: ENQUIRIES & SITE SURVEYS */}
          {activeTab === 'ENQUIRIES' && (
            <div className="space-y-6">
              {/* Enquiries Section */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-slate-100">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <ClipboardList className="w-4 h-4 text-amber-500" />
                      <span>Submitted Solar Enquiries & Lead Status</span>
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Review your initial solar requirement requests and track engineering team status updates.
                    </p>
                  </div>
                  <button
                    onClick={() => setNewEnquiryModal(true)}
                    className="px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-xl text-xs font-bold shadow-xs transition flex items-center gap-1.5 shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Submit New Solar Requirement</span>
                  </button>
                </div>

                {enquiries.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No solar enquiries submitted yet.</p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {enquiries.map((enq) => (
                      <div key={enq.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-900">{enq.enquiry_number}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                              {enq.system_type}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                              enq.status === 'WON'
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                : enq.status === 'LOST' || enq.status === 'CANCELLED'
                                ? 'bg-rose-50 text-rose-800 border-rose-200'
                                : 'bg-amber-50 text-amber-800 border-amber-200'
                            }`}>
                              {enq.status}
                            </span>
                          </div>
                          <div className="text-slate-500 text-[11px]">
                            Proposed Capacity: <strong className="text-slate-700">{enq.proposed_capacity_kw} kW</strong> • Roof Type: <span className="font-semibold">{enq.roof_type || 'RCC'}</span> • Submitted: {new Date(enq.created_at).toLocaleDateString()}
                          </div>
                          {enq.monthly_electricity_bill && (
                            <div className="text-slate-400 text-[11px]">
                              Current Monthly Electricity Bill: <span className="font-mono text-slate-700">{formatCurrency(enq.monthly_electricity_bill)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Site Surveys Section */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div>
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-emerald-600" />
                    <span>Site Technical Surveys</span>
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Engineering rooftop measurements, shadow analyses, and feasibility evaluations for your location.
                  </p>
                </div>

                {surveys.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No site surveys scheduled or conducted yet.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {surveys.map((surv) => (
                      <div key={surv.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-slate-900">{surv.survey_number}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            surv.status === 'APPROVED'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-amber-50 text-amber-800 border-amber-200'
                          }`}>
                            {surv.status}
                          </span>
                        </div>
                        <div className="text-slate-600">
                          Scheduled: <strong className="text-slate-800">{surv.scheduled_at ? new Date(surv.scheduled_at).toLocaleDateString() : 'Pending'}</strong>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-slate-200">
                          <div>
                            <span className="text-slate-400 block">Roof Area</span>
                            <span className="font-mono font-bold text-slate-800">{surv.roof_area_sqft || '---'} sq ft</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block">Shadow-Free Area</span>
                            <span className="font-mono font-bold text-emerald-700">{surv.shadow_free_area_sqft || '---'} sq ft</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block">Tilt & Direction</span>
                            <span className="font-bold text-slate-800">{surv.roof_tilt_degrees ? `${surv.roof_tilt_degrees}°` : '---'} {surv.roof_orientation || ''}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block">Assigned Surveyor</span>
                            <span className="font-bold text-slate-800">{surv.surveyor_name || 'Technical Surveyor'}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: QUOTATIONS & PROPOSALS */}
          {activeTab === 'QUOTATIONS' && (
            <div className="space-y-4">
              {quotations.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Quotations Generated Yet</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Our sales engineers will prepare your customized proposal after evaluating your rooftop survey.
                  </p>
                </div>
              ) : (
                quotations.map((q) => {
                  const isSent = q.status === 'SENT';
                  const isAccepted = q.status === 'ACCEPTED';
                  const isRejected = q.status === 'REJECTED';

                  return (
                    <div key={q.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-3">
                          <h4 className="text-base font-bold text-slate-900 font-mono">{q.quotation_number}</h4>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${
                            isAccepted
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : isRejected
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : 'bg-amber-50 text-amber-800 border-amber-200'
                          }`}>
                            {q.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600">
                          Capacity: <span className="font-semibold text-slate-900">{q.capacity_kw} kW {q.system_type}</span> • Validity: {q.valid_until ? new Date(q.valid_until).toLocaleDateString() : '30 Days'}
                        </p>
                        <div className="flex flex-wrap items-center gap-4 text-xs pt-1 text-slate-600">
                          <span>Gross Cost: <strong className="text-slate-900">{formatCurrency(q.gross_amount)}</strong></span>
                          <span>MNRE Subsidy: <strong className="text-emerald-700">-{formatCurrency(q.subsidy_estimate)}</strong></span>
                          <span>Net Payable: <strong className="text-amber-600 text-sm">{formatCurrency(q.net_payable_amount)}</strong></span>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-2">
                        {isSent && (
                          <>
                            <button
                              onClick={() => handleAcceptQuote(q.id)}
                              disabled={actionLoading}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-sm transition flex items-center gap-1.5"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Accept Proposal</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedQuoteId(q.id);
                                setRejectModal(true);
                              }}
                              disabled={actionLoading}
                              className="px-3 py-2 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition"
                            >
                              Decline
                            </button>
                          </>
                        )}
                        {isAccepted && (
                          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                            <CheckCircle2 className="w-4 h-4" /> Proposal Accepted
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* TAB 4: INVOICES & PAYMENTS */}
          {activeTab === 'INVOICES' && (
            <div className="space-y-6">
              {/* Invoices List */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-amber-500" />
                  <span>Milestone Tax Invoices</span>
                </h4>

                {invoices.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No invoices issued for your account yet.</p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {invoices.map((inv) => (
                      <div key={inv.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-slate-900">{inv.invoice_number}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                              {inv.invoice_type}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                              inv.payment_status === 'PAID'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-amber-50 text-amber-800 border-amber-200'
                            }`}>
                              {inv.payment_status}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 mt-1">
                            Date: {new Date(inv.invoice_date).toLocaleDateString()} • Due: {new Date(inv.due_date).toLocaleDateString()}
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-xs font-bold text-slate-900">{formatCurrency(inv.total_amount)}</div>
                            <div className="text-[11px] text-slate-400">
                              Balance: <span className="font-semibold text-rose-600">{formatCurrency(inv.balance_amount)}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => setPrintInvoice(inv)}
                            className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition"
                            title="View / Print Tax Invoice"
                          >
                            <Printer className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Completed Payments */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Payment Receipts</span>
                </h4>

                {payments.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No payment receipts recorded yet.</p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {payments.map((p) => (
                      <div key={p.id} className="py-2.5 flex items-center justify-between text-xs">
                        <div>
                          <div className="font-mono font-bold text-slate-900">{p.payment_number || `Receipt #${p.id}`}</div>
                          <div className="text-slate-500 text-[11px]">
                            {new Date(p.payment_date).toLocaleDateString()} • {p.payment_method} • Ref: {p.transaction_reference || 'N/A'}
                          </div>
                        </div>
                        <span className="font-mono font-bold text-emerald-700 text-sm">
                          {formatCurrency(p.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: INSTALLED EQUIPMENT & MATERIAL DISPATCHES */}
          {activeTab === 'EQUIPMENT' && (
            <div className="space-y-6">
              {/* Material Dispatches & Logistics */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Truck className="w-4 h-4 text-amber-500" />
                    <span>Material Dispatch & Site Deliveries</span>
                  </h4>
                  {dispatchLoading && (
                    <span className="text-xs text-slate-400 animate-pulse">Loading updates...</span>
                  )}
                </div>

                {dispatchForbidden ? (
                  <div className="rounded-xl bg-amber-50/70 border border-amber-200/80 p-4 text-xs text-amber-900 flex items-start gap-3">
                    <Truck className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <p className="font-semibold text-amber-950">Centralized Warehouse Logistics</p>
                      <p className="text-amber-800 leading-relaxed">
                        Material dispatches and transit manifests are managed directly by our central warehouse and logistics operations team. Delivery schedules and driver contacts will be communicated directly via SMS/phone or updated by your assigned project manager before on-site delivery.
                      </p>
                    </div>
                  </div>
                ) : dispatchError ? (
                  <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 text-xs text-rose-800 flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-rose-900">Unable to load dispatch status</p>
                      <p className="text-rose-700 mt-0.5">{dispatchError}</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleRetryDispatches}
                      disabled={dispatchLoading}
                      className="px-3 py-1.5 rounded-lg bg-white border border-rose-300 font-semibold text-rose-700 hover:bg-rose-50 transition-colors shadow-xs shrink-0"
                    >
                      {dispatchLoading ? 'Retrying...' : 'Retry'}
                    </button>
                  </div>
                ) : dispatches.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">No material dispatches dispatched for your project yet.</p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {dispatches.map((d) => (
                      <div key={d.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-900">{d.dispatch_number}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                              {d.dispatch_status}
                            </span>
                          </div>
                          <div className="text-slate-500 text-[11px] mt-0.5">
                            Dispatched on: {d.dispatched_date ? new Date(d.dispatched_date).toLocaleDateString() : 'Pending'} • Tracking: <span className="font-mono">{d.tracking_number || 'N/A'}</span>
                          </div>
                        </div>
                        <div className="text-slate-600 text-[11px]">
                          Vehicle: <strong className="text-slate-800">{d.vehicle_number || 'N/A'}</strong> • Driver: {d.driver_name || 'Assigned Driver'} ({d.driver_phone || 'N/A'})
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Warranties & Components List */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Installed Hardware Component Warranties</span>
                </h4>

                {warranties.length === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">Component warranty certificates and manufacturer policies are registered upon commissioning.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {warranties.map((w) => (
                      <div key={w.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900">{w.product_name || 'Solar Hardware'}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {w.status}
                          </span>
                        </div>
                        <div className="text-xs text-slate-600 font-mono">
                          Serial: <strong className="text-slate-900">{w.serial_number || 'N/A'}</strong>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Certificate: <span className="font-mono">{w.certificate_number}</span>
                        </div>
                        <div className="pt-2 border-t border-slate-100 text-xs flex justify-between text-slate-600">
                          <span>Valid From: {new Date(w.warranty_start_date).toLocaleDateString()}</span>
                          <span>Expires: <strong className="text-slate-900">{new Date(w.warranty_end_date).toLocaleDateString()}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 6: SERVICE HELPDESK & TICKETS */}
          {activeTab === 'TICKETS' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Customer Support & Breakdown Helpdesk</h4>
                  <p className="text-xs text-slate-500">Log service requests for solar generation issues, inverter alerts, or scheduled maintenance.</p>
                </div>
                <button
                  onClick={() => setNewTicketModal(true)}
                  className="px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-xl text-xs font-bold shadow-xs transition flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Raise Service Ticket</span>
                </button>
              </div>

              {tickets.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <LifeBuoy className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Service Tickets Logged</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Your rooftop system is running normally. If you ever observe an issue, use the button above to lodge a ticket.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {tickets.map((t) => (
                    <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">{t.ticket_number}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                            {t.issue_category}
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            t.status === 'RESOLVED' || t.status === 'CLOSED'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : 'bg-amber-50 text-amber-800 border-amber-200'
                          }`}>
                            {t.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 font-medium">{t.description}</p>
                        <span className="text-[11px] text-slate-400 block">
                          Reported on: {new Date(t.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <div className="text-right text-xs">
                        <span className={`font-semibold px-2 py-1 rounded-md text-[11px] ${
                          t.priority === 'CRITICAL' ? 'bg-rose-50 text-rose-700' : 'bg-slate-50 text-slate-700'
                        }`}>
                          Priority: {t.priority}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 7: SUBSIDY & DISCOM NET-METERING */}
          {activeTab === 'SUBSIDY' && (
            <div className="space-y-4">
              {subsidyApps.length === 0 ? (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                  <Landmark className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-900">No Subsidy Applications On File</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                    Your DISCOM net-metering and PM Surya Ghar subsidy application will be filed by our liaison team upon project commencement.
                  </p>
                </div>
              ) : (
                subsidyApps.map((sub) => (
                  <div key={sub.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-mono text-xs font-bold text-slate-900">{sub.application_number}</span>
                        <h4 className="text-sm font-bold text-slate-800 mt-0.5">PM Surya Ghar Yojana Application</h4>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                        {sub.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-2 border-t border-slate-100">
                      <div>
                        <span className="text-slate-400 text-[11px] block">Portal Reg Number</span>
                        <span className="font-mono font-bold text-slate-900">{sub.portal_registration_number || 'Pending'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block">DISCOM Provider</span>
                        <span className="font-bold text-slate-900">{sub.discom_name || 'State DISCOM'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block">Eligible Subsidy</span>
                        <span className="font-bold text-emerald-700">{formatCurrency(sub.eligible_subsidy_amount)}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px] block">Sanctioned kW</span>
                        <span className="font-bold text-slate-900">{sub.sanctioned_capacity_kw || '---'} kW</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* MODAL: EDIT CUSTOMER PROFILE */}
      {editProfileModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-amber-500" />
                <span>Update Contact & Site Address Details</span>
              </h3>
              <button onClick={() => setEditProfileModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Alternate Phone</label>
                  <input
                    type="text"
                    value={profileForm.alternate_phone}
                    onChange={(e) => setProfileForm({ ...profileForm, alternate_phone: e.target.value })}
                    placeholder="Optional backup phone"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Installation Site Address *</label>
                <input
                  type="text"
                  value={profileForm.address}
                  onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                  placeholder="House/Plot number, Street, Landmark"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">City *</label>
                  <input
                    type="text"
                    value={profileForm.city}
                    onChange={(e) => setProfileForm({ ...profileForm, city: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">State *</label>
                  <input
                    type="text"
                    value={profileForm.state}
                    onChange={(e) => setProfileForm({ ...profileForm, state: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Pincode *</label>
                  <input
                    type="text"
                    value={profileForm.pincode}
                    onChange={(e) => setProfileForm({ ...profileForm, pincode: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">DISCOM Electricity Meter Consumer Number</label>
                <input
                  type="text"
                  value={profileForm.electricity_consumer_number}
                  onChange={(e) => setProfileForm({ ...profileForm, electricity_consumer_number: e.target.value })}
                  placeholder="e.g. 10023456789"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500 font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditProfileModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingProfile}
                  className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-xs transition"
                >
                  {submittingProfile ? 'Saving...' : 'Save Profile Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: SUBMIT NEW SOLAR REQUIREMENT */}
      {newEnquiryModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ClipboardList className="w-4 h-4 text-amber-500" />
                <span>Submit Solar Rooftop Requirement</span>
              </h3>
              <button onClick={() => setNewEnquiryModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateEnquiry} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">System Type *</label>
                  <select
                    value={enquiryForm.system_type}
                    onChange={(e) => setEnquiryForm({ ...enquiryForm, system_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  >
                    <option value="ON_GRID">On-Grid (Net-Metered)</option>
                    <option value="HYBRID">Hybrid (Grid + Battery)</option>
                    <option value="OFF_GRID">Off-Grid (Standalone)</option>
                  </select>
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Proposed Capacity (kW) *</label>
                  <input
                    type="number"
                    step="0.5"
                    min="1.0"
                    max="5.0"
                    value={enquiryForm.proposed_capacity_kw}
                    onChange={(e) => setEnquiryForm({ ...enquiryForm, proposed_capacity_kw: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                  <span className="text-[10px] text-slate-400">Residential standard range: 1.0 - 5.0 kW</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Approx. Monthly Bill (₹)</label>
                  <input
                    type="number"
                    value={enquiryForm.monthly_electricity_bill}
                    onChange={(e) => setEnquiryForm({ ...enquiryForm, monthly_electricity_bill: e.target.value })}
                    placeholder="e.g. 3500"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Rooftop Type</label>
                  <select
                    value={enquiryForm.roof_type}
                    onChange={(e) => setEnquiryForm({ ...enquiryForm, roof_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  >
                    <option value="RCC_FLAT">RCC Flat Roof</option>
                    <option value="TIN_SHED">Metal / Tin Sheet</option>
                    <option value="TILED">Clay Tile Slanted</option>
                    <option value="OTHER">Other Rooftop Surface</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Specific Requirements or Notes</label>
                <textarea
                  rows={2}
                  value={enquiryForm.notes}
                  onChange={(e) => setEnquiryForm({ ...enquiryForm, notes: e.target.value })}
                  placeholder="e.g. Seeking high-efficiency bifacial panels with micro-inverters..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setNewEnquiryModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingEnquiry}
                  className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-xs transition"
                >
                  {submittingEnquiry ? 'Submitting...' : 'Submit Enquiry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 1: RAISE SERVICE TICKET */}
      {newTicketModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Raise Service / Maintenance Ticket</h3>
              <button onClick={() => setNewTicketModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Select Project *</label>
                <select
                  value={ticketForm.project_id}
                  onChange={(e) => setTicketForm({ ...ticketForm, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                >
                  <option value="">-- Choose your project --</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} ({p.system_capacity_kw} kW)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Issue Category *</label>
                <select
                  value={ticketForm.issue_category}
                  onChange={(e) => setTicketForm({ ...ticketForm, issue_category: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="GENERAL">General Maintenance Inquiry</option>
                  <option value="INVERTER_FAULT">Inverter Error / Red Light</option>
                  <option value="LOW_GENERATION">Low Energy Generation</option>
                  <option value="PHYSICAL_DAMAGE">Panel or Structure Damage</option>
                  <option value="GRID_FAILURE">Net-Metering / Grid Connection</option>
                  <option value="WIRING_ISSUE">Wiring / Conduits</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Priority</label>
                <select
                  value={ticketForm.priority}
                  onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="LOW">Low (Routine Checkup)</option>
                  <option value="MEDIUM">Medium (Minor Issue)</option>
                  <option value="HIGH">High (Reduced Output)</option>
                  <option value="CRITICAL">Critical (Complete System Down)</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Description of Issue *</label>
                <textarea
                  rows={3}
                  value={ticketForm.description}
                  onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                  placeholder="Please describe what you are observing on your inverter readout or generation app..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setNewTicketModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingTicket}
                  className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-xs transition"
                >
                  {submittingTicket ? 'Submitting...' : 'Submit Service Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: DECLINE QUOTATION REASON */}
      {rejectModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Decline Proposal</h3>
            <p className="text-xs text-slate-500">Please let our engineering team know what adjustments would better match your requirements.</p>
            <form onSubmit={handleRejectQuote} className="space-y-3 text-xs">
              <textarea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Reason (e.g. Budget constraints, requesting different panel brand, alternative capacity)..."
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRejectModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold"
                >
                  {actionLoading ? 'Declining...' : 'Confirm Decline'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: CUSTOMER ACCEPTANCE SIGN-OFF */}
      {acceptanceModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Sign Customer Acceptance</h3>
            <p className="text-xs text-slate-500">
              Confirm that your solar installation has been commissioned, grid-synced, and demonstrated to your satisfaction.
            </p>
            <form onSubmit={handleCustomerAcceptance} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Your Full Name (Digital Signature) *</label>
                <input
                  type="text"
                  value={signatureName}
                  onChange={(e) => setSignatureName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>
              <div>
                <label className="font-bold text-slate-700 block mb-1">Feedback / Acceptance Notes</label>
                <textarea
                  rows={2}
                  value={acceptanceNotes}
                  onChange={(e) => setAcceptanceNotes(e.target.value)}
                  placeholder="System tested and handed over in satisfactory working condition..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAcceptanceModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {actionLoading ? 'Signing...' : 'Sign Handover'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PRINT INVOICE MODAL */}
      {printInvoice && (
        <InvoicePrintModal
          invoice={printInvoice}
          onClose={() => setPrintInvoice(null)}
        />
      )}
    </div>
  );
}
