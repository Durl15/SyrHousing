import { useState, useEffect } from 'react';
import api from '../../lib/api';

export default function ScannerManagement() {
  const [states, setStates] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      api.get('/scanner/state'),
      api.get('/scanner/history?limit=20'),
    ])
      .then(([stateRes, histRes]) => {
        setStates(stateRes.data);
        setHistory(histRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const triggerScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.post('/scanner/run');
      setScanResult(res.data);
      fetchData();
    } catch (err) {
      setScanResult({ error: err.response?.data?.detail || 'Scan failed' });
    }
    setScanning(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f]">Scanner Management</h1>
        <button
          onClick={triggerScan}
          disabled={scanning}
          className="px-4 py-2 bg-[#1e3a5f] text-white text-sm font-medium rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer flex items-center gap-2"
        >
          {scanning && <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>}
          {scanning ? 'Scanning...' : 'Run Scan Now'}
        </button>
      </div>

      {scanResult && (
        <div className={`mb-6 p-4 rounded-xl ${scanResult.error ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>
          {scanResult.error || `Scan complete. Checked ${scanResult.total_checked || 0} sites, ${scanResult.changes_detected || 0} changes detected.`}
        </div>
      )}

      {/* Current States */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Current Scan States</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 font-medium">Program</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Last Checked</th>
                <th className="pb-2 font-medium">URL</th>
              </tr>
            </thead>
            <tbody>
              {states.map((s) => (
                <tr key={s.program_key} className="border-b border-gray-100">
                  <td className="py-2 font-medium text-[#1e3a5f]">{s.name}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      s.status === 'open/unknown' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="py-2 text-gray-500 text-xs">
                    {s.last_checked ? new Date(s.last_checked).toLocaleString() : 'Never'}
                  </td>
                  <td className="py-2">
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-xs text-[#2d6a9f] hover:underline">
                      Visit
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {states.length === 0 && (
          <p className="text-center text-gray-500 py-4">No scan states found.</p>
        )}
      </div>

      {/* Scan History */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Recent Scan History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 font-medium">Timestamp</th>
                <th className="pb-2 font-medium">Program</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Changed</th>
                <th className="pb-2 font-medium">Notes</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id} className="border-b border-gray-100">
                  <td className="py-2 text-xs text-gray-500">
                    {new Date(h.timestamp).toLocaleString()}
                  </td>
                  <td className="py-2 text-[#1e3a5f]">{h.name}</td>
                  <td className="py-2">{h.status}</td>
                  <td className="py-2">
                    {h.changed && <span className="text-amber-600 font-medium">Yes</span>}
                  </td>
                  <td className="py-2 text-xs text-gray-500 max-w-[200px] truncate">{h.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {history.length === 0 && (
          <p className="text-center text-gray-500 py-4">No scan history found.</p>
        )}
      </div>
    </div>
  );
}
