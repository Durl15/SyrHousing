import { useState, useEffect } from 'react';
import api from '../../lib/api';
import StatusBadge from '../../components/StatusBadge';

const STATUSES = ['', 'draft', 'submitted', 'under_review', 'approved', 'denied', 'withdrawn'];

export default function ApplicationManagement() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [changingId, setChangingId] = useState(null);

  const fetchApps = () => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '200' });
    if (statusFilter) params.set('status', statusFilter);
    api.get(`/admin/applications?${params.toString()}`)
      .then((res) => setApps(res.data))
      .catch(() => setApps([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchApps(); }, [statusFilter]);

  const changeStatus = async (appId, newStatus) => {
    setChangingId(appId);
    try {
      await api.post(`/admin/applications/${appId}/status`, { status: newStatus });
      fetchApps();
    } catch { /* ignore */ }
    setChangingId(null);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f] mb-6">All Applications</h1>

      <div className="mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none bg-white"
        >
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
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
                  <th className="px-4 py-3 font-medium">Program</th>
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app) => (
                  <tr key={app.id} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-[#1e3a5f]">{app.program_name}</td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{app.user_id.slice(0, 8)}...</td>
                    <td className="px-4 py-3"><StatusBadge status={app.status} /></td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{new Date(app.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <select
                        value={app.status}
                        onChange={(e) => changeStatus(app.id, e.target.value)}
                        disabled={changingId === app.id}
                        className="text-xs px-2 py-1 border border-gray-300 rounded bg-white"
                      >
                        {STATUSES.filter(Boolean).map((s) => (
                          <option key={s} value={s}>{s.replace('_', ' ')}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {apps.length === 0 && (
            <div className="p-8 text-center text-gray-500">No applications found.</div>
          )}
        </div>
      )}
    </div>
  );
}
