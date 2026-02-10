import { useState, useEffect } from 'react';
import api from '../../lib/api';

const emptyForm = {
  program_key: '', name: '', menu_category: '', program_type: '', repair_tags: '',
  max_benefit: '', status_or_deadline: '', agency: '', phone: '', email: '', website: '',
  eligibility_summary: '', income_guidance: '', docs_checklist: '', priority_rank: 0,
};

export default function ProgramManagement() {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const fetchPrograms = () => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '200', active_only: 'false' });
    if (search) params.set('search', search);
    api.get(`/programs?${params.toString()}`)
      .then((res) => setPrograms(res.data))
      .catch(() => setPrograms([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchPrograms(); }, [search]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setShowModal(true);
  };

  const openEdit = (p) => {
    setEditing(p.program_key);
    setForm({
      program_key: p.program_key, name: p.name, menu_category: p.menu_category || '',
      program_type: p.program_type || '', repair_tags: p.repair_tags || '',
      max_benefit: p.max_benefit || '', status_or_deadline: p.status_or_deadline || '',
      agency: p.agency || '', phone: p.phone || '', email: p.email || '',
      website: p.website || '', eligibility_summary: p.eligibility_summary || '',
      income_guidance: p.income_guidance || '', docs_checklist: p.docs_checklist || '',
      priority_rank: p.priority_rank || 0,
    });
    setShowModal(true);
  };

  const save = async () => {
    setSaving(true);
    try {
      if (editing) {
        const { program_key, ...updates } = form;
        await api.patch(`/programs/${editing}`, updates);
      } else {
        await api.post('/programs', form);
      }
      setShowModal(false);
      fetchPrograms();
    } catch (err) {
      alert(err.response?.data?.detail || 'Save failed');
    }
    setSaving(false);
  };

  const deleteProgram = async (key) => {
    if (!confirm(`Deactivate program "${key}"?`)) return;
    try {
      await api.delete(`/programs/${key}`);
      fetchPrograms();
    } catch { /* ignore */ }
  };

  const field = (label, name, type = 'text') => (
    <div key={name}>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {type === 'textarea' ? (
        <textarea
          value={form[name]}
          onChange={(e) => setForm({ ...form, [name]: e.target.value })}
          rows={3}
          className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none resize-y"
        />
      ) : (
        <input
          type={type}
          value={form[name]}
          onChange={(e) => setForm({ ...form, [name]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
          className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
          readOnly={name === 'program_key' && !!editing}
        />
      )}
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f]">Program Management</h1>
        <button
          onClick={openCreate}
          className="px-4 py-2 bg-[#1e3a5f] text-white text-sm font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors border-none cursor-pointer"
        >
          + New Program
        </button>
      </div>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search programs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-gray-600">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Agency</th>
                  <th className="px-4 py-3 font-medium">Active</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {programs.map((p) => (
                  <tr key={p.program_key} className={`border-t border-gray-100 hover:bg-gray-50 ${!p.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3 font-medium text-[#1e3a5f]">{p.name}</td>
                    <td className="px-4 py-3 text-gray-600">{p.menu_category}</td>
                    <td className="px-4 py-3 text-gray-600">{p.agency || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`w-2 h-2 rounded-full inline-block ${p.is_active ? 'bg-emerald-500' : 'bg-red-400'}`} />
                    </td>
                    <td className="px-4 py-3 flex gap-3">
                      <button
                        onClick={() => openEdit(p)}
                        className="text-xs text-[#2d6a9f] hover:underline bg-transparent border-none cursor-pointer p-0"
                      >
                        Edit
                      </button>
                      {p.is_active && (
                        <button
                          onClick={() => deleteProgram(p.program_key)}
                          className="text-xs text-red-500 hover:underline bg-transparent border-none cursor-pointer p-0"
                        >
                          Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {programs.length === 0 && (
            <div className="p-8 text-center text-gray-500">No programs found.</div>
          )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-lg font-bold text-[#1e3a5f] mb-4">
              {editing ? 'Edit Program' : 'New Program'}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {field('Program Key', 'program_key')}
              {field('Name', 'name')}
              {field('Category', 'menu_category')}
              {field('Type', 'program_type')}
              {field('Repair Tags (semicolon-separated)', 'repair_tags')}
              {field('Max Benefit', 'max_benefit')}
              {field('Status / Deadline', 'status_or_deadline')}
              {field('Agency', 'agency')}
              {field('Phone', 'phone')}
              {field('Email', 'email')}
              {field('Website', 'website')}
              {field('Priority Rank', 'priority_rank', 'number')}
            </div>
            <div className="grid grid-cols-1 gap-3 mt-3">
              {field('Eligibility Summary', 'eligibility_summary', 'textarea')}
              {field('Income Guidance', 'income_guidance', 'textarea')}
              {field('Docs Checklist', 'docs_checklist', 'textarea')}
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors border border-gray-300 cursor-pointer bg-white"
              >
                Cancel
              </button>
              <button
                onClick={save}
                disabled={saving || !form.name || !form.program_key || !form.menu_category}
                className="px-4 py-2 text-sm text-white bg-[#1e3a5f] hover:bg-[#2d6a9f] rounded-lg transition-colors border-none cursor-pointer disabled:opacity-50"
              >
                {saving ? 'Saving...' : editing ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
