import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function DiscoveryManagement() {
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [grants, setGrants] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(false);
  const [selectedGrant, setSelectedGrant] = useState(null);

  useEffect(() => {
    loadStats();
    loadRuns();
    loadGrants();
  }, [filter]);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/discovery/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadRuns = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/discovery/runs`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 10 }
      });
      setRuns(response.data);
    } catch (error) {
      console.error('Failed to load runs:', error);
    }
  };

  const loadGrants = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/discovery/grants`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { status: filter, limit: 50 }
      });
      setGrants(response.data);
    } catch (error) {
      console.error('Failed to load grants:', error);
    }
  };

  const runDiscovery = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/discovery/run`,
        { sources: ['rss_feed'], send_notification: false },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      alert('Discovery run started! Refresh in a few minutes to see results.');
      setTimeout(() => {
        loadStats();
        loadRuns();
      }, 2000);
    } catch (error) {
      alert('Failed to start discovery: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const approveGrant = async (grantId) => {
    if (!confirm('Approve this grant and create a Program?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/discovery/grants/${grantId}/approve`,
        { create_program: true },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      alert('Grant approved and Program created!');
      loadGrants();
      loadStats();
    } catch (error) {
      alert('Failed to approve: ' + error.message);
    }
  };

  const rejectGrant = async (grantId) => {
    const reason = prompt('Reason for rejection:');
    if (!reason) return;

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/discovery/grants/${grantId}/reject`,
        { reason },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      alert('Grant rejected');
      loadGrants();
    } catch (error) {
      alert('Failed to reject: ' + error.message);
    }
  };

  const markDuplicate = async (grantId) => {
    const programKey = prompt('Enter the program_key of the duplicate program:');
    if (!programKey) return;

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/discovery/grants/${grantId}/mark-duplicate`,
        { program_key: programKey },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      alert('Marked as duplicate');
      loadGrants();
    } catch (error) {
      alert('Failed to mark duplicate: ' + error.message);
    }
  };

  const getConfidenceBadge = (score) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">🔍 Discovery Management</h1>
        <button
          onClick={runDiscovery}
          disabled={loading}
          className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? '⏳ Running...' : '▶ Run Discovery Now'}
        </button>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Total Runs</div>
            <div className="text-2xl font-bold">{stats.total_runs}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Discovered</div>
            <div className="text-2xl font-bold">{stats.total_discovered}</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Pending Review</div>
            <div className="text-2xl font-bold">{stats.pending_review}</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600">Avg Confidence</div>
            <div className="text-2xl font-bold">{(stats.avg_confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      )}

      {/* Recent Runs */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Recent Discovery Runs</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sources</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Discovered</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duplicates</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Errors</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="px-6 py-4 text-sm">{new Date(run.started_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      run.status === 'completed' ? 'bg-green-100 text-green-800' :
                      run.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{run.sources_checked}</td>
                  <td className="px-6 py-4 text-sm font-semibold">{run.grants_discovered}</td>
                  <td className="px-6 py-4 text-sm">{run.duplicates_found}</td>
                  <td className="px-6 py-4 text-sm">{run.errors}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="mb-4 flex gap-2">
        {['pending', 'approved', 'rejected', 'duplicate'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg ${
              filter === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Discovered Grants */}
      <div>
        <h2 className="text-xl font-bold mb-4">Discovered Grants ({grants.length})</h2>
        <div className="space-y-4">
          {grants.map((grant) => (
            <div key={grant.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold mb-2">{grant.name}</h3>
                  <div className="flex gap-2 mb-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceBadge(grant.confidence_score)}`}>
                      {(grant.confidence_score * 100).toFixed(0)}% Confidence
                    </span>
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                      {grant.source_type}
                    </span>
                    {grant.jurisdiction && (
                      <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                        {grant.jurisdiction}
                      </span>
                    )}
                  </div>
                </div>
                {grant.review_status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => approveGrant(grant.id)}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => rejectGrant(grant.id)}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm"
                    >
                      ✗ Reject
                    </button>
                    <button
                      onClick={() => markDuplicate(grant.id)}
                      className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 text-sm"
                    >
                      🔄 Duplicate
                    </button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                {grant.agency && (
                  <div>
                    <span className="font-semibold">Agency:</span> {grant.agency}
                  </div>
                )}
                {grant.max_benefit && (
                  <div>
                    <span className="font-semibold">Benefit:</span> {grant.max_benefit}
                  </div>
                )}
                {grant.status_or_deadline && (
                  <div>
                    <span className="font-semibold">Deadline:</span> {grant.status_or_deadline}
                  </div>
                )}
                {grant.phone && (
                  <div>
                    <span className="font-semibold">Phone:</span> {grant.phone}
                  </div>
                )}
                {grant.email && (
                  <div>
                    <span className="font-semibold">Email:</span> {grant.email}
                  </div>
                )}
                {grant.website && (
                  <div className="col-span-2">
                    <span className="font-semibold">Website:</span>{' '}
                    <a href={grant.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {grant.website}
                    </a>
                  </div>
                )}
              </div>

              {grant.eligibility_summary && (
                <div className="mt-4 p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-700">{grant.eligibility_summary}</p>
                </div>
              )}

              <div className="mt-4 text-xs text-gray-500">
                Discovered: {new Date(grant.discovered_at).toLocaleString()}
                {grant.similarity_score && ` • Similarity: ${(grant.similarity_score * 100).toFixed(0)}%`}
                {grant.matched_program_key && ` • Matches: ${grant.matched_program_key}`}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
