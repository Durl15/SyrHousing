import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  LineChart, Line,
  AreaChart, Area,
} from 'recharts';

const COLORS = ['#1e3a5f', '#2d6a9f', '#4a9eda', '#c9a84c', '#059669', '#d97706'];
const STATUS_COLORS = {
  Draft: '#9ca3af',
  Submitted: '#2d6a9f',
  'Under Review': '#d97706',
  Approved: '#059669',
  Denied: '#dc2626',
  Withdrawn: '#6b7280',
};

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [recentApps, setRecentApps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/admin/stats'),
      api.get('/admin/applications?limit=10'),
      api.get('/admin/chart-data').catch(() => ({ data: null })),
    ])
      .then(([statsRes, appsRes, chartRes]) => {
        setStats(statsRes.data);
        setRecentApps(appsRes.data);
        setChartData(chartRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f] mb-6">Admin Dashboard</h1>

      {stats && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Total Users', value: stats.total_users, color: 'bg-[#1e3a5f]' },
              { label: 'Applications', value: stats.total_applications, color: 'bg-[#2d6a9f]' },
              { label: 'Active Programs', value: stats.active_programs, color: 'bg-emerald-600' },
              { label: 'New Users (30d)', value: stats.recent_registrations, color: 'bg-[#c9a84c]' },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-xl shadow-md overflow-hidden">
                <div className={`${s.color} h-1.5`} />
                <div className="p-5">
                  <div className="text-3xl font-bold text-[#1e3a5f]">{s.value}</div>
                  <div className="text-sm text-gray-500 mt-1">{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Charts */}
      {chartData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Registration Trend */}
          {chartData.registration_trend?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">User Registrations (12 weeks)</h2>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData.registration_trend} margin={{ left: -10 }}>
                  <defs>
                    <linearGradient id="regGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#1e3a5f" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#1e3a5f" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                  <Area type="monotone" dataKey="users" stroke="#1e3a5f" strokeWidth={2} fill="url(#regGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Application Trend */}
          {chartData.application_trend?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Applications (12 weeks)</h2>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData.application_trend} margin={{ left: -10 }}>
                  <defs>
                    <linearGradient id="appGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#059669" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                  <Area type="monotone" dataKey="applications" stroke="#059669" strokeWidth={2} fill="url(#appGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Applications by Status */}
          {chartData.apps_by_status?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Applications by Status</h2>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={chartData.apps_by_status}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    label={({ name, count }) => `${count}`}
                    labelLine={false}
                  >
                    {chartData.apps_by_status.map((entry, i) => (
                      <Cell key={i} fill={STATUS_COLORS[entry.name] || COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                  <Legend
                    wrapperStyle={{ fontSize: '12px' }}
                    formatter={(value) => <span style={{ color: '#374151' }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Programs by Category */}
          {chartData.programs_by_category?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Programs by Category</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData.programs_by_category} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value) => [value, 'Programs']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.programs_by_category.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Program Scores */}
          {chartData.top_scores?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Top Program Match Scores</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData.top_scores} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value) => [`${value}/100`, 'Score']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {chartData.top_scores.map((entry, i) => (
                      <Cell key={i} fill={entry.score >= 70 ? '#059669' : entry.score >= 50 ? '#d97706' : '#9ca3af'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Scan Status */}
          {chartData.scan_status?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Scanner Status</h2>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={chartData.scan_status}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={({ name, count }) => `${name}: ${count}`}
                    labelLine={true}
                  >
                    {chartData.scan_status.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { to: '/admin/users', label: 'Manage Users', icon: '👥' },
          { to: '/admin/programs', label: 'Manage Programs', icon: '📋' },
          { to: '/admin/applications', label: 'All Applications', icon: '📝' },
          { to: '/admin/scanner', label: 'Scanner', icon: '🔍' },
        ].map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition-shadow no-underline text-center"
          >
            <div className="text-2xl mb-2">{link.icon}</div>
            <div className="text-sm font-medium text-[#1e3a5f]">{link.label}</div>
          </Link>
        ))}
      </div>

      {/* Recent Applications */}
      {recentApps.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[#1e3a5f]">Recent Applications</h2>
            <Link to="/admin/applications" className="text-sm text-[#2d6a9f] hover:underline no-underline">
              View all
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">Program</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {recentApps.map((app) => (
                  <tr key={app.id} className="border-b border-gray-100">
                    <td className="py-2 text-[#1e3a5f]">{app.program_name}</td>
                    <td className="py-2 capitalize">{app.status.replace('_', ' ')}</td>
                    <td className="py-2 text-gray-500">{new Date(app.updated_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
