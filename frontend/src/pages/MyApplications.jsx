import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import StatusBadge from '../components/StatusBadge';

const TABS = [
  { key: '', label: 'All' },
  { key: 'draft', label: 'Draft' },
  { key: 'submitted', label: 'Submitted' },
  { key: 'under_review', label: 'Under Review' },
  { key: 'approved', label: 'Approved' },
  { key: 'denied', label: 'Denied' },
];

export default function MyApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('');

  const fetchApps = (status) => {
    setLoading(true);
    const params = status ? `?status=${status}` : '';
    api.get(`/applications${params}`)
      .then((res) => setApplications(res.data))
      .catch(() => setApplications([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchApps(activeTab);
  }, [activeTab]);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f]">My Applications</h1>
        <Link
          to="/programs"
          className="px-4 py-2 bg-[#1e3a5f] text-white text-sm font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
        >
          Browse Programs
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 mb-6 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors bg-transparent cursor-pointer ${
              activeTab === tab.key
                ? 'border-[#1e3a5f] text-[#1e3a5f]'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
        </div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <div className="text-4xl mb-4">📋</div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">No applications yet</h2>
          <p className="text-gray-500 mb-6">
            Start by browsing available programs and tracking your applications.
          </p>
          <Link
            to="/programs"
            className="px-6 py-2 bg-[#1e3a5f] text-white font-medium rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
          >
            Explore Programs
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Link
              key={app.id}
              to={`/applications/${app.id}`}
              className="block bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-5 no-underline"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-[#1e3a5f] truncate">
                    {app.program_name}
                  </h3>
                  {app.notes && (
                    <p className="text-sm text-gray-500 mt-1 truncate">{app.notes}</p>
                  )}
                  <div className="text-xs text-gray-400 mt-2">
                    Created {new Date(app.created_at).toLocaleDateString()}
                    {app.applied_at && ` · Applied ${new Date(app.applied_at).toLocaleDateString()}`}
                    {app.decided_at && ` · Decided ${new Date(app.decided_at).toLocaleDateString()}`}
                  </div>
                </div>
                <StatusBadge status={app.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
