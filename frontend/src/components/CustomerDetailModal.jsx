import React, { useState, useEffect } from 'react';
import { X, User, Phone, Mail, MapPin, Zap, Plus, Inbox, Clock, RefreshCw } from 'lucide-react';
import { getCustomer, getEnquiries } from '../services/crmApi';

export default function CustomerDetailModal({ isOpen, onClose, customerId, onOpenNewEnquiry, onSelectEnquiry }) {
  const [customer, setCustomer] = useState(null);
  const [enquiries, setEnquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCustomerData = async () => {
    if (!customerId) return;
    setLoading(true);
    setError(null);
    try {
      const [custRes, enqRes] = await Promise.all([
        getCustomer(customerId),
        getEnquiries({ customer_id: customerId }),
      ]);
      const custData = custRes?.data?.data ? custRes.data.data : (custRes?.data ? custRes.data : custRes);
      if (custData) {
        setCustomer(custData);
      }
      const enqData = enqRes?.data?.data ? enqRes.data.data : (enqRes?.data ? enqRes.data : enqRes);
      if (enqData && enqData.items) {
        setEnquiries(enqData.items);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch customer details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && customerId) {
      fetchCustomerData();
    }
  }, [isOpen, customerId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">{customer ? customer.full_name : 'Customer Details'}</h3>
              <p className="text-xs text-slate-500">
                {customer?.customer_type} • ID: #{customer?.id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-500" />
              <span className="text-xs">Loading customer record & history...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 text-rose-800 text-xs rounded-xl border border-rose-200">
              {error}
            </div>
          ) : customer ? (
            <>
              {/* Contact & Location Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200/80">
                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-slate-700">
                    <Phone className="w-4 h-4 text-slate-400" />
                    <span className="font-semibold text-slate-900">{customer.phone}</span>
                    {customer.alternate_phone && (
                      <span className="text-slate-500">/ {customer.alternate_phone}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-slate-700">
                    <Mail className="w-4 h-4 text-slate-400" />
                    <span>{customer.email || 'No email registered'}</span>
                  </div>
                  <div className="flex items-start gap-2 text-slate-700">
                    <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                    <span>
                      {customer.address}, {customer.city}, {customer.state} - {customer.pincode}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-xs sm:border-l sm:border-slate-200 sm:pl-4">
                  <div className="flex items-center gap-2 text-slate-700">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span className="text-slate-500">Electricity Meter No:</span>
                    <span className="font-mono font-bold text-slate-900">
                      {customer.electricity_consumer_number || 'Not provided'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-700">
                    <span className="text-slate-500">Sanctioned Load:</span>
                    <span className="font-bold text-slate-900">
                      {customer.sanctioned_load_kw ? `${customer.sanctioned_load_kw} kW` : 'Not specified'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-700">
                    <span className="text-slate-500">Created:</span>
                    <span>{new Date(customer.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Enquiry History Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <Inbox className="w-4 h-4 text-amber-500" /> Solar Enquiries ({enquiries.length})
                  </h4>
                  <button
                    onClick={() => {
                      onClose();
                      if (onOpenNewEnquiry) onOpenNewEnquiry(customer);
                    }}
                    className="inline-flex items-center gap-1 text-xs font-bold text-amber-600 hover:text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-3 py-1.5 rounded-lg transition"
                  >
                    <Plus className="w-3.5 h-3.5" /> New Enquiry
                  </button>
                </div>

                {enquiries.length > 0 ? (
                  <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                    {enquiries.map((enq) => (
                      <div
                        key={enq.id}
                        onClick={() => {
                          onClose();
                          if (onSelectEnquiry) onSelectEnquiry(enq);
                        }}
                        className="p-3.5 flex items-center justify-between hover:bg-slate-50 cursor-pointer transition"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-slate-900">{enq.enquiry_number}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                              {enq.status}
                            </span>
                          </div>
                          <div className="text-xs text-slate-600 mt-1">
                            <span className="font-semibold text-amber-700">{enq.proposed_capacity_kw} kW {enq.system_type}</span> • {enq.roof_type || 'Roof'} • Source: {enq.source}
                          </div>
                        </div>
                        <div className="text-right text-xs text-slate-400">
                          {new Date(enq.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center border border-dashed border-slate-200 rounded-xl">
                    <p className="text-xs text-slate-400">No solar enquiries logged for this customer yet.</p>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 text-right">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
