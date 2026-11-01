import React, { useState } from 'react';
import {
  TrendingUp,
  Inbox,
  Users,
  Clock,
  Plus,
} from 'lucide-react';
import CRMPipelineDashboard from '../components/CRMPipelineDashboard';
import CustomerList from '../components/CustomerList';
import CustomerModal from '../components/CustomerModal';
import CustomerDetailModal from '../components/CustomerDetailModal';
import EnquiryList from '../components/EnquiryList';
import EnquiryModal from '../components/EnquiryModal';
import FollowupTracker from '../components/FollowupTracker';
import FollowupModal from '../components/FollowupModal';

export default function CRMManagementPage() {
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, enquiries, customers, followups

  // Customer Modals
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [detailCustomerId, setDetailCustomerId] = useState(null);
  const [showCustomerDetail, setShowCustomerDetail] = useState(false);

  // Enquiry Modals
  const [showEnquiryModal, setShowEnquiryModal] = useState(false);
  const [editingEnquiry, setEditingEnquiry] = useState(null);
  const [defaultEnquiryCustomer, setDefaultEnquiryCustomer] = useState(null);

  // Follow-up Modals
  const [showFollowupModal, setShowFollowupModal] = useState(false);
  const [targetFollowupEnquiry, setTargetFollowupEnquiry] = useState(null);
  const [followupToComplete, setFollowupToComplete] = useState(null);

  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  // Customer Handlers
  const handleOpenAddCustomer = () => {
    setEditingCustomer(null);
    setShowCustomerModal(true);
  };

  const handleOpenEditCustomer = (cust) => {
    setEditingCustomer(cust);
    setShowCustomerModal(true);
  };

  const handleOpenDetailCustomer = (custId) => {
    setDetailCustomerId(custId);
    setShowCustomerDetail(true);
  };

  // Enquiry Handlers
  const handleOpenAddEnquiry = () => {
    setEditingEnquiry(null);
    setDefaultEnquiryCustomer(null);
    setShowEnquiryModal(true);
  };

  const handleOpenAddEnquiryForCustomer = (cust) => {
    setEditingEnquiry(null);
    setDefaultEnquiryCustomer(cust);
    setShowEnquiryModal(true);
  };

  const handleOpenEditEnquiry = (enq) => {
    setEditingEnquiry(enq);
    setDefaultEnquiryCustomer(null);
    setShowEnquiryModal(true);
  };

  // Follow-up Handlers
  const handleScheduleFollowup = (enq) => {
    setTargetFollowupEnquiry(enq);
    setFollowupToComplete(null);
    setShowFollowupModal(true);
  };

  const handleCompleteFollowup = (f) => {
    setTargetFollowupEnquiry(null);
    setFollowupToComplete(f);
    setShowFollowupModal(true);
  };

  return (
    <div className="space-y-6">
      {/* Module Title & Tab Navigation Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-amber-500" />
            <span>CRM & Sales Pipeline</span>
          </h2>
          <p className="text-xs text-slate-500">
            Rooftop solar enquiries, customer registration, pipeline progression, and scheduled client touchpoints.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl self-stretch md:self-auto overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              activeTab === 'dashboard'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TrendingUp className="w-4 h-4 text-amber-500" />
            <span>Pipeline Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('enquiries')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              activeTab === 'enquiries'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Inbox className="w-4 h-4 text-amber-500" />
            <span>Solar Enquiries</span>
          </button>

          <button
            onClick={() => setActiveTab('customers')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              activeTab === 'customers'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Users className="w-4 h-4 text-amber-500" />
            <span>Customers</span>
          </button>

          <button
            onClick={() => setActiveTab('followups')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              activeTab === 'followups'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Clock className="w-4 h-4 text-amber-500" />
            <span>Follow-up Tracker</span>
          </button>
        </div>
      </div>

      {/* Tab Views */}
      <div>
        {activeTab === 'dashboard' && (
          <CRMPipelineDashboard
            onNavigateToEnquiries={() => setActiveTab('enquiries')}
            onNavigateToFollowups={() => setActiveTab('followups')}
            onSelectEnquiry={(enq) => {
              setActiveTab('enquiries');
              handleOpenEditEnquiry(enq);
            }}
          />
        )}

        {activeTab === 'enquiries' && (
          <EnquiryList
            onOpenAdd={handleOpenAddEnquiry}
            onOpenEdit={handleOpenEditEnquiry}
            onScheduleFollowup={handleScheduleFollowup}
            refreshKey={refreshKey}
          />
        )}

        {activeTab === 'customers' && (
          <CustomerList
            onOpenAdd={handleOpenAddCustomer}
            onOpenEdit={handleOpenEditCustomer}
            onOpenDetail={handleOpenDetailCustomer}
            refreshKey={refreshKey}
          />
        )}

        {activeTab === 'followups' && (
          <FollowupTracker
            onOpenSchedule={() => handleScheduleFollowup(null)}
            onOpenComplete={handleCompleteFollowup}
            refreshKey={refreshKey}
          />
        )}
      </div>

      {/* Modals */}
      <CustomerModal
        isOpen={showCustomerModal}
        onClose={() => setShowCustomerModal(false)}
        customer={editingCustomer}
        onSuccess={triggerRefresh}
      />

      <CustomerDetailModal
        isOpen={showCustomerDetail}
        onClose={() => setShowCustomerDetail(false)}
        customerId={detailCustomerId}
        onOpenNewEnquiry={handleOpenAddEnquiryForCustomer}
        onSelectEnquiry={(enq) => {
          setActiveTab('enquiries');
          handleOpenEditEnquiry(enq);
        }}
      />

      <EnquiryModal
        isOpen={showEnquiryModal}
        onClose={() => setShowEnquiryModal(false)}
        enquiry={editingEnquiry}
        defaultCustomer={defaultEnquiryCustomer}
        onSuccess={triggerRefresh}
      />

      <FollowupModal
        isOpen={showFollowupModal}
        onClose={() => setShowFollowupModal(false)}
        enquiry={targetFollowupEnquiry}
        followupToComplete={followupToComplete}
        onSuccess={triggerRefresh}
      />
    </div>
  );
}
