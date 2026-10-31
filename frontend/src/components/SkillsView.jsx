import React, { useState, useEffect } from 'react';
import {
  Award,
  Plus,
  Edit2,
  Search,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Zap,
} from 'lucide-react';
import { fetchSkills, createSkill, updateSkill } from '../services/employeeApi';

const SKILL_CATEGORIES = [
  'ELECTRICAL',
  'MOUNTING',
  'SAFETY',
  'COMMISSIONING',
  'STORAGE',
  'TESTING',
  'SURVEY',
  'MAINTENANCE',
  'SERVICE',
];

export default function SkillsView() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('ELECTRICAL');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState(null);

  const loadSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (selectedCategory) params.category = selectedCategory;
      const res = await fetchSkills(params);
      setSkills(res?.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
  }, [selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadSkills();
  };

  const handleOpenCreate = () => {
    setEditingSkill(null);
    setName('');
    setCategory('ELECTRICAL');
    setDescription('');
    setIsActive(true);
    setModalError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (skill) => {
    setEditingSkill(skill);
    setName(skill.name || '');
    setCategory(skill.category || 'ELECTRICAL');
    setDescription(skill.description || '');
    setIsActive(skill.is_active);
    setModalError(null);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setModalLoading(true);
    setModalError(null);
    try {
      if (editingSkill) {
        await updateSkill(editingSkill.id, {
          name: name.trim(),
          category: category.trim().toUpperCase(),
          description: description.trim() || null,
          is_active: isActive,
        });
      } else {
        await createSkill({
          name: name.trim(),
          category: category.trim().toUpperCase(),
          description: description.trim() || null,
          is_active: isActive,
        });
      }
      setShowModal(false);
      loadSkills();
    } catch (err) {
      setModalError(err.message || 'Failed to save skill');
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Filter Controls */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" /> Technical Skills Catalog
            </h3>
            <p className="text-xs text-slate-500">
              Maintain standardized competency standards across rooftop solar mounting, electrical wiring, and commissioning.
            </p>
          </div>
          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition shadow-sm ml-auto sm:ml-0"
          >
            <Plus className="w-4 h-4" />
            <span>Register New Skill</span>
          </button>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search skills by title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-amber-500"
          >
            <option value="">All Categories</option>
            {SKILL_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <button
            type="submit"
            className="px-3.5 py-1.5 bg-slate-900 text-white hover:bg-slate-800 rounded-lg text-xs font-semibold"
          >
            Filter
          </button>
          <button
            type="button"
            onClick={loadSkills}
            title="Refresh"
            className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
          {error}
        </div>
      )}

      {/* Skills Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">Loading competency catalog...</div>
      ) : skills.length === 0 ? (
        <div className="p-12 text-center text-slate-500 text-xs">No skills matched your search.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {skills.map((skill) => (
            <div
              key={skill.id}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-amber-300 transition flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-start justify-between">
                  <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                    {skill.category}
                  </span>
                  <button
                    onClick={() => handleOpenEdit(skill)}
                    title="Edit skill"
                    className="text-slate-400 hover:text-slate-700 p-1 rounded"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h4 className="font-bold text-slate-900 text-sm mt-2">{skill.name}</h4>
                <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                  {skill.description || 'No description provided.'}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>Certified Workforce:</span>
                <span className="font-bold text-slate-800 font-mono">
                  {skill.employee_count} {skill.employee_count === 1 ? 'Tech' : 'Techs'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Skill Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">
                {editingSkill ? 'Update Skill Specification' : 'Register Technical Skill'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Skill Title *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Battery Inverter Synchronization"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Category *</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                >
                  {SKILL_CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detail scope, tooling, and safety prerequisites..."
                  className="w-full bg-slate-50 border border-slate-200 rounded px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  {modalLoading ? 'Saving...' : editingSkill ? 'Update' : 'Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
