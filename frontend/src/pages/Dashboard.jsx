import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#1e3a5f', '#2d6a9f', '#4a9eda', '#c9a84c', '#059669', '#d97706'];

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [topPrograms, setTopPrograms] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [programsRes, rankingRes, scanRes, chartRes] = await Promise.all([
          api.get('/programs?limit=200'),
          api.get('/ranking/ranked-programs'),
          api.get('/scanner/state'),
          api.get('/ranking/chart-data').catch(() => ({ data: null })),
        ]);
        setStats({
          totalPrograms: programsRes.data.length,
          scanStates: scanRes.data.length,
          openPrograms: scanRes.data.filter((s) => s.status === 'open/unknown').length,
        });
        setTopPrograms(rankingRes.data.slice(0, 5));
        setChartData(chartRes.data);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const resendVerification = async () => {
    setResending(true);
    try {
      await api.post('/auth/resend-verification');
      alert('Verification email sent! Check your inbox.');
    } catch {
      alert('Could not send verification email.');
    }
    setResending(false);
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Email Verification Banner */}
      {user && !user.is_verified && (
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-amber-600 text-lg">&#9888;</span>
            <div>
              <p className="text-sm font-medium text-amber-800">Verify your email address</p>
              <p className="text-xs text-amber-600">Check your inbox for a verification link, or request a new one.</p>
            </div>
          </div>
          <button
            onClick={resendVerification}
            disabled={resending}
            className="px-4 py-1.5 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors border-none cursor-pointer whitespace-nowrap"
          >
            {resending ? 'Sending...' : 'Resend Email'}
          </button>
        </div>
      )}

      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f]">
          Welcome, {user?.full_name}
        </h1>
        <p className="text-gray-500 mt-1">
          Your Syracuse housing grant dashboard
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        {[
          { label: 'Available Programs', value: stats?.totalPrograms || 0, color: 'bg-[#1e3a5f]' },
          { label: 'Monitored Sites', value: stats?.scanStates || 0, color: 'bg-[#2d6a9f]' },
          { label: 'Open / Active', value: stats?.openPrograms || 0, color: 'bg-emerald-600' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className={`${s.color} h-1.5`} />
            <div className="p-6">
              <div className="text-3xl font-bold text-[#1e3a5f]">{s.value}</div>
              <div className="text-sm text-gray-500 mt-1">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      {chartData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Program Scores */}
          {chartData.top_programs?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Top Program Match Scores</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData.top_programs} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value) => [`${value}/100`, 'Score']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {chartData.top_programs.map((_, i) => (
                      <Cell key={i} fill={chartData.top_programs[i].score >= 70 ? '#059669' : chartData.top_programs[i].score >= 50 ? '#d97706' : '#9ca3af'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Programs by Category */}
          {chartData.programs_by_category?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Programs by Category</h2>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={chartData.programs_by_category}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={({ name, count }) => `${count}`}
                    labelLine={false}
                  >
                    {chartData.programs_by_category.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
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

          {/* Score Distribution */}
          {chartData.score_distribution?.length > 0 && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Score Distribution</h2>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData.score_distribution} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value) => [value, 'Programs']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="count" fill="#4a9eda" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Top Ranked Programs */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#1e3a5f]">Top Ranked Programs for You</h2>
          <Link
            to="/programs"
            className="text-sm text-[#2d6a9f] hover:underline no-underline"
          >
            View all
          </Link>
        </div>
        <div className="space-y-3">
          {topPrograms.map((p) => (
            <div
              key={p.program_key}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium text-[#1e3a5f] truncate">{p.name}</div>
                <div className="text-sm text-gray-500">
                  {p.menu_category} · {p.agency || 'N/A'}
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <div className="text-right">
                  <div className="text-lg font-bold text-[#1e3a5f]">{p.computed_score}</div>
                  <div className="text-xs text-gray-400">score</div>
                </div>
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-white text-sm font-bold"
                  style={{
                    background: p.computed_score >= 70 ? '#059669' : p.computed_score >= 50 ? '#d97706' : '#9ca3af',
                  }}
                >
                  {p.computed_score}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Link
          to="/programs"
          className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-center no-underline"
        >
          <div className="text-2xl mb-2">🔍</div>
          <div className="font-semibold text-[#1e3a5f]">Browse Programs</div>
          <div className="text-sm text-gray-500 mt-1">Search and filter all grants</div>
        </Link>
        <Link
          to="/chat"
          className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-center no-underline"
        >
          <div className="text-2xl mb-2">🤖</div>
          <div className="font-semibold text-[#1e3a5f]">Ask AI Assistant</div>
          <div className="text-sm text-gray-500 mt-1">Get help finding programs</div>
        </Link>
        <Link
          to="/applications"
          className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-center no-underline"
        >
          <div className="text-2xl mb-2">📋</div>
          <div className="font-semibold text-[#1e3a5f]">My Applications</div>
          <div className="text-sm text-gray-500 mt-1">Track your applications</div>
        </Link>
        <Link
          to="/profile"
          className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow text-center no-underline"
        >
          <div className="text-2xl mb-2">🏠</div>
          <div className="font-semibold text-[#1e3a5f]">My Home Profile</div>
          <div className="text-sm text-gray-500 mt-1">Update repair needs</div>
        </Link>
      </div>
    </div>
  );
}
