import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import AdvancedSearch from '../components/AdvancedSearch';
import GrantCard from '../components/GrantCard';

export default function Programs() {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [screening, setScreening] = useState(null);
  const [screeningLoading, setScreeningLoading] = useState(false);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({});
  const { user } = useAuth();
  const navigate = useNavigate();

  const loadPrograms = (params = {}) => {
    setLoading(true);
    const urlParams = new URLSearchParams();

    // Add all search parameters
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        urlParams.set(key, params[key]);
      }
    });

    urlParams.set('limit', '200');

    // Try ranked programs first (if profile exists), fallback to regular programs
    api.get(`/ranking/ranked-programs?${urlParams.toString()}`)
      .then((res) => setPrograms(res.data))
      .catch(() => {
        api.get(`/programs?${urlParams.toString()}`)
          .then((res) => setPrograms(res.data));
      })
      .finally(() => setLoading(false));
  };

  // Initial load
  useEffect(() => {
    loadPrograms();
  }, []);

  const handleSearch = (params) => {
    setSearchParams(params);
    loadPrograms(params);
  };

  const handleClearSearch = () => {
    setSearchParams({});
    loadPrograms();
  };

  const runScreening = async (programKey) => {
    setScreeningLoading(true);
    setScreening(null);
    try {
      const res = await api.post('/ai/screen', { program_key: programKey });
      setScreening(res.data);
    } catch {
      setScreening({ screening: 'Unable to run eligibility screening. Please try again later.', used_llm: false });
    } finally {
      setScreeningLoading(false);
    }
  };

  const trackApplication = async (programKey) => {
    if (!user) {
      navigate('/login');
      return;
    }
    setTrackingLoading(true);
    try {
      await api.post('/applications', { program_key: programKey });
      navigate('/applications');
    } catch (err) {
      if (err.response?.status === 409) {
        navigate('/applications');
      } else {
        alert(err.response?.data?.detail || 'Failed to create application');
      }
    }
    setTrackingLoading(false);
  };

  const categoryColors = {
    'URGENT SAFETY': 'bg-red-100 text-red-800',
    'HEALTH HAZARDS': 'bg-orange-100 text-orange-800',
    'AGING IN PLACE': 'bg-purple-100 text-purple-800',
    'ENERGY & BILLS': 'bg-green-100 text-green-800',
    'HISTORIC RESTORATION': 'bg-amber-100 text-amber-800',
    'BUYING HELP': 'bg-blue-100 text-blue-800',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f] mb-6">
        Syracuse Housing Grants
        <span className="text-base font-normal text-gray-600 ml-3">
          {programs.length} grant{programs.length !== 1 ? 's' : ''} available
        </span>
      </h1>

      {/* Advanced Search Component */}
      <AdvancedSearch onSearch={handleSearch} onClear={handleClearSearch} />

      {/* Old Filters - Removed, replaced by AdvancedSearch */}
      {/* <div className="bg-white rounded-xl shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search programs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none bg-white"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none bg-white"
          >
            <option value="">All Repair Tags</option>
            {tags.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div> */}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Program List */}
          <div className="lg:col-span-2 space-y-3">
            {programs.length === 0 && (
              <div className="bg-white rounded-xl p-8 text-center text-gray-500">
                No programs found matching your filters.
              </div>
            )}
            {programs.map((p) => (
              <div
                key={p.program_key}
                onClick={() => { setSelected(p); setScreening(null); }}
                className={`bg-white rounded-xl shadow-sm p-5 cursor-pointer transition-all hover:shadow-md border-2 ${
                  selected?.program_key === p.program_key
                    ? 'border-[#4a9eda]'
                    : 'border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-[#1e3a5f] truncate">{p.name}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryColors[p.menu_category] || 'bg-gray-100 text-gray-700'}`}>
                        {p.menu_category}
                      </span>
                      {p.max_benefit && (
                        <span className="text-xs text-gray-500">
                          {p.max_benefit}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {p.agency || 'N/A'} · {p.phone || ''}
                    </div>
                  </div>
                  {p.computed_score !== undefined && (
                    <div
                      className="w-11 h-11 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                      style={{
                        background: p.computed_score >= 70 ? '#059669' : p.computed_score >= 50 ? '#d97706' : '#9ca3af',
                      }}
                    >
                      {p.computed_score}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-6 sticky top-24">
              {selected ? (
                <div>
                  <h2 className="text-lg font-bold text-[#1e3a5f] mb-4">{selected.name}</h2>

                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Category:</span>
                      <span className="ml-2">{selected.menu_category}</span>
                    </div>
                    {selected.program_type && (
                      <div>
                        <span className="font-medium text-gray-700">Type:</span>
                        <span className="ml-2">{selected.program_type}</span>
                      </div>
                    )}
                    {selected.max_benefit && (
                      <div>
                        <span className="font-medium text-gray-700">Benefit:</span>
                        <span className="ml-2">{selected.max_benefit}</span>
                      </div>
                    )}
                    {selected.status_or_deadline && (
                      <div>
                        <span className="font-medium text-gray-700">Status:</span>
                        <span className="ml-2">{selected.status_or_deadline}</span>
                      </div>
                    )}
                    {selected.agency && (
                      <div>
                        <span className="font-medium text-gray-700">Agency:</span>
                        <span className="ml-2">{selected.agency}</span>
                      </div>
                    )}
                    {selected.phone && (
                      <div>
                        <span className="font-medium text-gray-700">Phone:</span>
                        <a href={`tel:${selected.phone}`} className="ml-2 text-[#2d6a9f]">{selected.phone}</a>
                      </div>
                    )}
                    {selected.website && (
                      <div>
                        <span className="font-medium text-gray-700">Website:</span>
                        <a href={selected.website} target="_blank" rel="noopener noreferrer" className="ml-2 text-[#2d6a9f] hover:underline break-all">
                          Visit
                        </a>
                      </div>
                    )}
                    {selected.repair_tags && (
                      <div>
                        <span className="font-medium text-gray-700 block mb-1">Repair Tags:</span>
                        <div className="flex flex-wrap gap-1">
                          {selected.repair_tags.split(';').map((t) => (
                            <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                              {t.trim()}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {selected.computed_score !== undefined && (
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <div className="font-medium text-[#1e3a5f] mb-2">
                        AI Score: {selected.computed_score}/100
                      </div>
                      {selected.rank_explanation && (
                        <ul className="text-xs text-gray-600 space-y-1">
                          {selected.rank_explanation.map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Eligibility Screening */}
                  <div className="mt-4">
                    {!screening && (
                      <button
                        onClick={() => runScreening(selected.program_key)}
                        disabled={screeningLoading}
                        className="w-full px-4 py-2.5 bg-[#1e3a5f] text-white font-medium rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer text-sm"
                      >
                        {screeningLoading ? (
                          <span className="flex items-center justify-center gap-2">
                            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                            Screening...
                          </span>
                        ) : (
                          'Screen My Eligibility'
                        )}
                      </button>
                    )}
                    {screening && (
                      <div className="mt-2 p-4 bg-blue-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-[#1e3a5f] text-sm">Eligibility Screening</span>
                          <span className="text-xs text-gray-500">
                            {screening.used_llm ? 'AI-powered' : 'Offline'}
                          </span>
                        </div>
                        <pre className="whitespace-pre-wrap text-xs text-gray-700 font-sans m-0">
                          {screening.screening}
                        </pre>
                        <button
                          onClick={() => setScreening(null)}
                          className="mt-3 text-xs text-[#2d6a9f] hover:underline bg-transparent border-none cursor-pointer p-0"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Track Application */}
                  <button
                    onClick={() => trackApplication(selected.program_key)}
                    disabled={trackingLoading}
                    className="mt-3 w-full px-4 py-2.5 bg-[#c9a84c] text-[#1e3a5f] font-medium rounded-lg hover:bg-[#d4b85d] disabled:opacity-50 transition-colors border-none cursor-pointer text-sm"
                  >
                    {trackingLoading ? 'Creating...' : 'Track Application'}
                  </button>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8">
                  <div className="text-3xl mb-3">👈</div>
                  <p>Select a program to see details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
