import React, { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  Building2,
  Zap,
  Award,
  Plus,
} from 'lucide-react';
import EmployeeDashboard from '../components/EmployeeDashboard';
import EmployeeList from '../components/EmployeeList';
import DepartmentView from '../components/DepartmentView';
import SkillsView from '../components/SkillsView';
import CertificationsView from '../components/CertificationsView';
import EmployeeModal from '../components/EmployeeModal';
import EmployeeDetailModal from '../components/EmployeeDetailModal';

export default function EmployeeManagementPage() {
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, employees, departments, skills, certifications

  // Modal controls
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);

  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);

  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  const handleOpenAdd = () => {
    setEditingEmployee(null);
    setShowEmployeeModal(true);
  };

  const handleOpenEdit = (emp) => {
    setEditingEmployee(emp);
    setShowEmployeeModal(true);
  };

  const handleOpenDetail = (empId) => {
    setSelectedEmployeeId(empId);
    setDetailModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Module Title & Tab Navigation Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-amber-500" />
            <span>Employee & Department Management</span>
          </h2>
          <p className="text-xs text-slate-500">
            Workforce roster, departmental structures, rooftop installation skills, and safety certification lifecycles.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex flex-wrap items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              activeTab === 'dashboard'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5 text-amber-500" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('employees')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              activeTab === 'employees'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-amber-500" />
            <span>Employees</span>
          </button>

          <button
            onClick={() => setActiveTab('departments')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              activeTab === 'departments'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-amber-500" />
            <span>Departments</span>
          </button>

          <button
            onClick={() => setActiveTab('skills')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              activeTab === 'skills'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>Skills Catalog</span>
          </button>

          <button
            onClick={() => setActiveTab('certifications')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              activeTab === 'certifications'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Award className="w-3.5 h-3.5 text-amber-500" />
            <span>Certifications</span>
          </button>
        </div>
      </div>

      {/* Main View Display */}
      <div key={refreshKey}>
        {activeTab === 'dashboard' && (
          <EmployeeDashboard
            onNavigate={(tab) => setActiveTab(tab)}
            onAddEmployee={handleOpenAdd}
            onViewEmployee={handleOpenDetail}
          />
        )}

        {activeTab === 'employees' && (
          <EmployeeList
            onAddEmployee={handleOpenAdd}
            onEditEmployee={handleOpenEdit}
            onViewEmployee={handleOpenDetail}
          />
        )}

        {activeTab === 'departments' && (
          <DepartmentView onViewEmployee={handleOpenDetail} />
        )}

        {activeTab === 'skills' && <SkillsView />}

        {activeTab === 'certifications' && (
          <CertificationsView onViewEmployee={handleOpenDetail} />
        )}
      </div>

      {/* Shared Modals */}
      <EmployeeModal
        isOpen={showEmployeeModal}
        onClose={() => setShowEmployeeModal(false)}
        employee={editingEmployee}
        onSaved={triggerRefresh}
      />

      <EmployeeDetailModal
        isOpen={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false);
          setSelectedEmployeeId(null);
        }}
        employeeId={selectedEmployeeId}
        onUpdated={triggerRefresh}
      />
    </div>
  );
}
