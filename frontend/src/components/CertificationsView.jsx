import React, { useState, useEffect } from 'react';
import {
  Award,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Building2,
  User,
  ShieldAlert,
} from 'lucide-react';
import {
  fetchExpiringCertifications,
  updateCertification,
} from '../services/employeeApi';

export default function CertificationsView({ onViewEmployee }) {
  const [certifications, setCertifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [thresholdDays, setThresholdDays] = useState(60);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const loadCertifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchExpiringCertifications({
        days: thresholdDays,
        include_already_expired: true,
      });
      setCertifications(res?.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load expiring certifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCertifications();
  }, [thresholdDays]);

  const handleUpdateStatus = async (certId, newStatus) => {
    try {
      await updateCertification(certId, { verification_status: newStatus });
      loadCertifications();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const filteredCerts = certifications.filter((c) => {
    if (search.trim()) {
      const term = search.toLowerCase();
      const matchName = c.certification_name?.toLowerCase().includes(term);
      const matchEmp = c.employee_name?.toLowerCase().includes(term);
      const matchCode = c.employee_code?.toLowerCase().includes(term);
      const matchAuth = c.issuing_authority?.toLowerCase().includes(term);
      if (!matchName && !matchEmp && !matchCode && !matchAuth) return false;
    }
    if (statusFilter === 'expired' && !c.is_expired) return false;
    if (statusFilter === 'expiring' && (c.is_expired || c.days_to_expiry > 30)) return false;
    if (statusFilter === 'verified' && c.verification_status !== 'VERIFIED') return false;
    return true;
  });

  const expiredCount = certifications.filter((c) => c.is_expired).length;
  const imminentCount = certifications.filter((c) => !c.is_expired && c.days_to_expiry <= 30).length;

  return (
    <div className="space-y-6">
      {/* Top Banner with Alert metrics */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" /> Compliance & Safety Certification Tracking
            </h3>
            <p className="text-xs text-slate-500">
              Audit mandatory Rooftop Safety, Electrical License, and Manufacturer Accreditations across the team.
            </p>
          </div>

          <button
            onClick={loadCertifications}
            title="Refresh"
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs flex items-center gap-1.5 transition font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Audit</span>
          </button>
        </div>

        {/* Status Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100 text-xs">
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-between">
            <span className="font-semibold text-rose-900">Expired Certifications</span>
            <span className="font-extrabold text-rose-700 text-base">{expiredCount}</span>
          </div>
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-between">
            <span className="font-semibold text-amber-900">Expiring Within 30 Days</span>
            <span className="font-extrabold text-amber-700 text-base">{imminentCount}</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
            <span className="font-semibold text-slate-700">Total Monitored</span>
            <span className="font-extrabold text-slate-900 text-base">{certifications.length}</span>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by certification, technician, or certificate #..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <select
            value={thresholdDays}
            onChange={(e) => setThresholdDays(Number(e.target.value))}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
          >
            <option value={30}>Audit Window: 30 Days</option>
            <option value={60}>Audit Window: 60 Days</option>
            <option value={90}>Audit Window: 90 Days</option>
            <option value={180}>Audit Window: 180 Days</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Statuses</option>
            <option value="expired">Expired Only</option>
            <option value="expiring">Expiring Soon (≤30d)</option>
            <option value="verified">Verified Only</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {error}
        </div>
      )}

      {/* Certifications Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Running certification audit...</div>
        ) : filteredCerts.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No certifications found within the selected audit window.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Certification Title</th>
                  <th className="py-3 px-4">Employee / Technician</th>
                  <th className="py-3 px-4">Authority & Cert #</th>
                  <th className="py-3 px-4">Issue Date</th>
                  <th className="py-3 px-4">Expiry Date</th>
                  <th className="py-3 px-4">Audit Status</th>
                  <th className="py-3 px-4 text-right">Verification Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCerts.map((cert) => (
                  <tr key={cert.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-bold text-slate-900">
                      {cert.certification_name}
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-800">{cert.employee_name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {cert.employee_code} • {cert.department_name}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      <div>{cert.issuing_authority}</div>
                      {cert.certificate_number && (
                        <div className="text-[10px] text-slate-400 font-mono">
                          #{cert.certificate_number}
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-4 text-slate-600">{cert.issue_date}</td>

                    <td className="py-3 px-4 text-slate-600 font-medium">
                      {cert.expiry_date || 'Lifetime / No Expiry'}
                    </td>

                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          cert.is_expired
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : cert.days_to_expiry !== null && cert.days_to_expiry <= 30
                            ? 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        }`}
                      >
                        {cert.is_expired ? (
                          'EXPIRED'
                        ) : cert.days_to_expiry !== null && cert.days_to_expiry <= 30 ? (
                          <>
                            <Clock className="w-3 h-3" />
                            <span>{cert.days_to_expiry}d Remaining</span>
                          </>
                        ) : (
                          cert.verification_status
                        )}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        {cert.verification_status !== 'VERIFIED' && (
                          <button
                            onClick={() => handleUpdateStatus(cert.id, 'VERIFIED')}
                            className="px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-[11px] font-bold transition"
                          >
                            Verify
                          </button>
                        )}
                        <button
                          onClick={() => onViewEmployee && onViewEmployee(cert.employee_id)}
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition"
                        >
                          Profile
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
