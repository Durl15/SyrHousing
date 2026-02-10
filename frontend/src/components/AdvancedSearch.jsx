import { useState, useEffect } from 'react';

/**
 * AdvancedSearch component
 * Provides comprehensive search and filtering UI for grants
 */
export default function AdvancedSearch({ onSearch, onClear }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [programType, setProgramType] = useState('');
  const [minBenefit, setMinBenefit] = useState('');
  const [maxBenefit, setMaxBenefit] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [sortBy, setSortBy] = useState('priority');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const categories = [
    'URGENT SAFETY',
    'HEALTH HAZARDS',
    'AGING IN PLACE',
    'ENERGY & BILLS',
    'HISTORIC RESTORATION',
    'BUYING HELP',
    'GENERAL',
  ];

  const programTypes = [
    { value: '', label: 'All Types' },
    { value: 'grant', label: 'Grants' },
    { value: 'loan', label: 'Loans' },
    { value: 'deferred', label: 'Deferred/Forgivable' },
  ];

  const sortOptions = [
    { value: 'priority', label: 'Best Match' },
    { value: 'name', label: 'Alphabetical' },
    { value: 'benefit', label: 'Benefit Amount' },
    { value: 'recent', label: 'Recently Added' },
    { value: 'deadline', label: 'Deadline' },
  ];

  const jurisdictions = [
    { value: '', label: 'All Areas' },
    { value: 'Syracuse', label: 'Syracuse' },
    { value: 'Onondaga', label: 'Onondaga County' },
    { value: 'New York', label: 'New York State' },
  ];

  // Load saved preferences
  useEffect(() => {
    const saved = localStorage.getItem('searchPreferences');
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        setSelectedCategories(prefs.selectedCategories || []);
        setProgramType(prefs.programType || '');
        setJurisdiction(prefs.jurisdiction || '');
        setSortBy(prefs.sortBy || 'priority');
        setSortOrder(prefs.sortOrder || 'desc');
      } catch (e) {
        console.error('Failed to load preferences:', e);
      }
    }
  }, []);

  // Save preferences
  const savePreferences = () => {
    const prefs = {
      selectedCategories,
      programType,
      jurisdiction,
      sortBy,
      sortOrder,
    };
    localStorage.setItem('searchPreferences', JSON.stringify(prefs));
  };

  const toggleCategory = (category) => {
    setSelectedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const handleSearch = () => {
    const params = {
      search: searchTerm || undefined,
      categories: selectedCategories.length > 0 ? selectedCategories.join(',') : undefined,
      program_type: programType || undefined,
      min_benefit: minBenefit ? parseInt(minBenefit) : undefined,
      max_benefit: maxBenefit ? parseInt(maxBenefit) : undefined,
      jurisdiction: jurisdiction || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    };

    // Remove undefined values
    Object.keys(params).forEach(key =>
      params[key] === undefined && delete params[key]
    );

    savePreferences();
    onSearch(params);
  };

  const handleClear = () => {
    setSearchTerm('');
    setSelectedCategories([]);
    setProgramType('');
    setMinBenefit('');
    setMaxBenefit('');
    setJurisdiction('');
    setSortBy('priority');
    setSortOrder('desc');
    localStorage.removeItem('searchPreferences');
    onClear();
  };

  const activeFilterCount =
    selectedCategories.length +
    (programType ? 1 : 0) +
    (minBenefit ? 1 : 0) +
    (maxBenefit ? 1 : 0) +
    (jurisdiction ? 1 : 0);

  return (
    <div className="bg-white rounded-xl shadow-md p-4 mb-6">
      {/* Main Search Bar */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search grants by name, agency, requirements..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-6 py-2 bg-[#1e3a5f] text-white rounded-lg hover:bg-[#2d4a7f] transition-colors font-medium"
        >
          Search
        </button>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="border-t border-gray-200 pt-4 space-y-4">
          {/* Category Multi-Select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Categories
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => toggleCategory(category)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedCategories.includes(category)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Filters Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Program Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Program Type
              </label>
              <select
                value={programType}
                onChange={(e) => setProgramType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {programTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Jurisdiction */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Area
              </label>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {jurisdictions.map(j => (
                  <option key={j.value} value={j.value}>
                    {j.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Min Benefit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Benefit ($)
              </label>
              <input
                type="number"
                value={minBenefit}
                onChange={(e) => setMinBenefit(e.target.value)}
                placeholder="e.g. 5000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Max Benefit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Benefit ($)
              </label>
              <input
                type="number"
                value={maxBenefit}
                onChange={(e) => setMaxBenefit(e.target.value)}
                placeholder="e.g. 20000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Sort Options */}
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sortOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">High to Low</option>
                <option value="asc">Low to High</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-[#1e3a5f] text-white rounded-lg hover:bg-[#2d4a7f] transition-colors font-medium"
            >
              Apply Filters
            </button>
            <button
              onClick={handleClear}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              Clear All
            </button>
          </div>

          {/* Active Filters Display */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
              <span className="text-sm font-medium text-gray-600">Active Filters:</span>
              {selectedCategories.map(cat => (
                <span
                  key={cat}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full flex items-center gap-1"
                >
                  {cat}
                  <button
                    onClick={() => toggleCategory(cat)}
                    className="hover:text-blue-900"
                  >
                    ×
                  </button>
                </span>
              ))}
              {programType && (
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  Type: {programType}
                </span>
              )}
              {jurisdiction && (
                <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                  Area: {jurisdiction}
                </span>
              )}
              {minBenefit && (
                <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                  Min: ${minBenefit}
                </span>
              )}
              {maxBenefit && (
                <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                  Max: ${maxBenefit}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
