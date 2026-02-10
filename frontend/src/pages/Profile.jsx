import { useState, useEffect } from 'react';
import api from '../lib/api';

const ALL_TAGS = [
  'roof', 'heating', 'structural', 'electrical', 'plumbing',
  'windows', 'doors', 'lead', 'mold', 'accessibility',
  'stairs', 'ramps', 'grab bars', 'bathroom', 'insulation',
  'energy', 'exterior', 'facade', 'siding', 'paint',
];

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.get('/profiles/default')
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  const toggleNeed = (tag) => {
    if (!profile) return;
    const needs = profile.repair_needs || [];
    const severity = profile.repair_severity || {};
    if (needs.includes(tag)) {
      setProfile({
        ...profile,
        repair_needs: needs.filter((t) => t !== tag),
        repair_severity: { ...severity, [tag]: undefined },
      });
    } else {
      setProfile({
        ...profile,
        repair_needs: [...needs, tag],
        repair_severity: { ...severity, [tag]: severity[tag] || 3 },
      });
    }
  };

  const setSeverity = (tag, val) => {
    if (!profile) return;
    setProfile({
      ...profile,
      repair_severity: { ...profile.repair_severity, [tag]: val },
    });
  };

  const save = async () => {
    if (!profile) return;
    setSaving(true);
    setMessage('');
    try {
      const severity = {};
      for (const tag of (profile.repair_needs || [])) {
        severity[tag] = profile.repair_severity?.[tag] || 3;
      }
      await api.patch(`/profiles/${profile.id}`, {
        city: profile.city,
        county: profile.county,
        is_senior: profile.is_senior,
        is_fixed_income: profile.is_fixed_income,
        repair_needs: profile.repair_needs,
        repair_severity: severity,
      });
      setMessage('Profile saved successfully.');
    } catch {
      setMessage('Failed to save profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center text-gray-500">
        No default profile found. Please seed the database first.
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f] mb-6">My Home Profile</h1>

      <div className="bg-white rounded-xl shadow-md p-6 space-y-6">
        {message && (
          <div className={`px-4 py-3 rounded-lg text-sm ${message.includes('success') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
            {message}
          </div>
        )}

        {/* Location */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
            <input
              type="text"
              value={profile.city}
              onChange={(e) => setProfile({ ...profile, city: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">County</label>
            <input
              type="text"
              value={profile.county}
              onChange={(e) => setProfile({ ...profile, county: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="flex gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={profile.is_senior}
              onChange={(e) => setProfile({ ...profile, is_senior: e.target.checked })}
              className="w-4 h-4 text-[#1e3a5f] rounded"
            />
            <span className="text-sm">Senior (60+/62+)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={profile.is_fixed_income}
              onChange={(e) => setProfile({ ...profile, is_fixed_income: e.target.checked })}
              className="w-4 h-4 text-[#1e3a5f] rounded"
            />
            <span className="text-sm">Fixed Income</span>
          </label>
        </div>

        {/* Repair Needs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Repair Needs (click to toggle, drag slider for severity)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ALL_TAGS.map((tag) => {
              const active = (profile.repair_needs || []).includes(tag);
              const sev = profile.repair_severity?.[tag] || 3;
              return (
                <div
                  key={tag}
                  className={`p-3 rounded-lg border-2 transition-colors ${
                    active ? 'border-[#4a9eda] bg-blue-50' : 'border-gray-200 bg-white'
                  }`}
                >
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleNeed(tag)}
                      className="w-4 h-4 rounded"
                    />
                    <span className="text-sm font-medium capitalize">{tag}</span>
                  </label>
                  {active && (
                    <div className="mt-2 flex items-center gap-2">
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={sev}
                        onChange={(e) => setSeverity(tag, parseInt(e.target.value))}
                        className="flex-1 h-1.5 accent-[#1e3a5f]"
                      />
                      <span className="text-xs text-gray-500 w-8 text-right">{sev}/10</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <button
          onClick={save}
          disabled={saving}
          className="w-full py-2.5 bg-[#1e3a5f] text-white font-semibold rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer"
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
}
