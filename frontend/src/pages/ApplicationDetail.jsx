import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../lib/api';
import StatusBadge from '../components/StatusBadge';
import GrantWriterPanel from '../components/GrantWriterPanel';

const statusActions = {
  draft: [{ status: 'submitted', label: 'Submit Application', color: 'bg-[#1e3a5f]' }],
  submitted: [{ status: 'withdrawn', label: 'Withdraw', color: 'bg-gray-500' }],
  under_review: [{ status: 'withdrawn', label: 'Withdraw', color: 'bg-gray-500' }],
  approved: [],
  denied: [],
  withdrawn: [{ status: 'draft', label: 'Reopen as Draft', color: 'bg-[#2d6a9f]' }],
};

export default function ApplicationDetail() {
  const { id } = useParams();
  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);

  const fetchApp = () => {
    setLoading(true);
    api.get(`/applications/${id}`)
      .then((res) => {
        setApp(res.data);
        setNotes(res.data.notes || '');
      })
      .catch(() => setApp(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchApp(); }, [id]);

  const saveNotes = async () => {
    setSaving(true);
    try {
      const res = await api.patch(`/applications/${id}`, { notes });
      setApp((prev) => ({ ...prev, ...res.data }));
    } catch { /* ignore */ }
    setSaving(false);
  };

  const changeStatus = async (newStatus) => {
    setStatusLoading(true);
    try {
      await api.post(`/applications/${id}/status`, { status: newStatus });
      fetchApp();
    } catch { /* ignore */ }
    setStatusLoading(false);
  };

  const toggleDoc = async (docName) => {
    const checklist = { ...(app.documents_checklist || {}) };
    checklist[docName] = !checklist[docName];
    try {
      const res = await api.patch(`/applications/${id}`, { documents_checklist: checklist });
      setApp((prev) => ({ ...prev, ...res.data }));
    } catch { /* ignore */ }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e3a5f]"></div>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p className="text-gray-500">Application not found.</p>
        <Link to="/applications" className="text-[#2d6a9f] hover:underline mt-2 inline-block">
          Back to My Applications
        </Link>
      </div>
    );
  }

  const actions = statusActions[app.status] || [];
  const docs = app.documents_checklist || {};

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <Link to="/applications" className="text-[#2d6a9f] hover:underline text-sm mb-4 inline-block">
        &larr; Back to My Applications
      </Link>

      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-xl font-bold text-[#1e3a5f]">{app.program_name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              Program: {app.program_key}
            </p>
          </div>
          <StatusBadge status={app.status} />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-6">
          <div>
            <span className="text-gray-500 block">Created</span>
            <span className="font-medium">{new Date(app.created_at).toLocaleDateString()}</span>
          </div>
          {app.applied_at && (
            <div>
              <span className="text-gray-500 block">Applied</span>
              <span className="font-medium">{new Date(app.applied_at).toLocaleDateString()}</span>
            </div>
          )}
          {app.decided_at && (
            <div>
              <span className="text-gray-500 block">Decision</span>
              <span className="font-medium">{new Date(app.decided_at).toLocaleDateString()}</span>
            </div>
          )}
          <div>
            <span className="text-gray-500 block">Last Updated</span>
            <span className="font-medium">{new Date(app.updated_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Status Actions */}
        {actions.length > 0 && (
          <div className="flex gap-3 mb-6">
            {actions.map((a) => (
              <button
                key={a.status}
                onClick={() => changeStatus(a.status)}
                disabled={statusLoading}
                className={`px-4 py-2 text-white text-sm font-medium rounded-lg ${a.color} hover:opacity-90 disabled:opacity-50 transition-colors border-none cursor-pointer`}
              >
                {a.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notes */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-[#1e3a5f] mb-3">Notes</h2>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none resize-y"
            placeholder="Add your notes about this application..."
          />
          <button
            onClick={saveNotes}
            disabled={saving || notes === (app.notes || '')}
            className="mt-3 px-4 py-2 bg-[#1e3a5f] text-white text-sm font-medium rounded-lg hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save Notes'}
          </button>
        </div>

        {/* Document Checklist */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-[#1e3a5f] mb-3">Document Checklist</h2>
          {Object.keys(docs).length === 0 ? (
            <div>
              <p className="text-sm text-gray-500 mb-3">No documents tracked yet. Common documents:</p>
              <div className="space-y-2">
                {['Proof of ownership', 'Income verification', 'Photo ID', 'Tax returns', 'Utility bills'].map((doc) => (
                  <button
                    key={doc}
                    onClick={() => toggleDoc(doc)}
                    className="block w-full text-left px-3 py-2 text-sm bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border-none cursor-pointer text-gray-700"
                  >
                    + {doc}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(docs).map(([doc, checked]) => (
                <label key={doc} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleDoc(doc)}
                    className="w-4 h-4 rounded border-gray-300 text-[#1e3a5f] focus:ring-[#4a9eda]"
                  />
                  <span className={`text-sm ${checked ? 'line-through text-gray-400' : 'text-gray-700'}`}>
                    {doc}
                  </span>
                </label>
              ))}
              <button
                onClick={() => {
                  const name = prompt('Document name:');
                  if (name) toggleDoc(name);
                }}
                className="text-sm text-[#2d6a9f] hover:underline bg-transparent border-none cursor-pointer p-0 mt-2"
              >
                + Add document
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Grant Writing Assistant */}
      <div className="mt-6">
        <GrantWriterPanel
          applicationId={id}
          programName={app.program_name || 'this program'}
          status={app.status}
        />
      </div>

      {/* Status History Timeline */}
      {app.status_history && app.status_history.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6 mt-6">
          <h2 className="text-lg font-semibold text-[#1e3a5f] mb-4">Status History</h2>
          <div className="space-y-4">
            {app.status_history.map((h, i) => (
              <div key={h.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full bg-[#1e3a5f] flex-shrink-0 mt-1"></div>
                  {i < app.status_history.length - 1 && (
                    <div className="w-0.5 flex-1 bg-gray-200 mt-1"></div>
                  )}
                </div>
                <div className="pb-4">
                  <div className="flex items-center gap-2">
                    {h.from_status && (
                      <>
                        <StatusBadge status={h.from_status} />
                        <span className="text-gray-400 text-xs">&rarr;</span>
                      </>
                    )}
                    <StatusBadge status={h.to_status} />
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {new Date(h.created_at).toLocaleString()}
                    {h.changed_by && ' (by admin)'}
                  </div>
                  {h.notes && <p className="text-sm text-gray-600 mt-1">{h.notes}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
