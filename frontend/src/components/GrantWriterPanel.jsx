import { useState, useEffect } from 'react';
import api from '../lib/api';
import ContentGenerator from './ContentGenerator';
import DraftEditor from './DraftEditor';

export default function GrantWriterPanel({ applicationId, programName, status }) {
  const [drafts, setDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState(null);
  const [showGenerator, setShowGenerator] = useState(false);

  const contentTypes = [
    { value: 'cover_letter', label: 'Cover Letter', icon: '\u2709\uFE0F' },
    { value: 'eligibility_statement', label: 'Eligibility Statement', icon: '\u2713' },
    { value: 'project_description', label: 'Project Description', icon: '\uD83D\uDCDD' },
    { value: 'needs_justification', label: 'Needs Justification', icon: '\uD83D\uDCA1' },
  ];

  useEffect(() => {
    loadDrafts();
  }, [applicationId]);

  const loadDrafts = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/grant-writer/drafts/${applicationId}`);
      setDrafts(res.data.drafts || {});
    } catch (err) {
      console.error('Failed to load drafts', err);
      setDrafts({});
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = (contentType) => {
    setSelectedType(contentType);
    setShowGenerator(true);
  };

  const handleContentGenerated = (contentType, content) => {
    setDrafts(prev => ({
      ...prev,
      [contentType]: content
    }));
    setShowGenerator(false);
    loadDrafts(); // Reload to get the latest from server
  };

  const isEditable = ['draft', 'submitted'].includes(status);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#1e3a5f]"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-[#1e3a5f] mb-4">
        AI Grant Writing Assistant
      </h2>

      {!isEditable && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-yellow-800">
            Application is {status}. Grant writer is read-only.
          </p>
        </div>
      )}

      <p className="text-sm text-gray-600 mb-6">
        Generate professional application content for {programName} using AI or templates.
      </p>

      {/* Content Type Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        {contentTypes.map(type => (
          <button
            key={type.value}
            onClick={() => handleGenerate(type.value)}
            disabled={!isEditable}
            className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-left"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{type.icon}</span>
              <div className="flex-1">
                <div className="font-medium text-sm text-gray-800">{type.label}</div>
                {drafts[type.value] && (
                  <div className="text-xs text-green-600 mt-0.5">
                    \u2713 Generated (v{drafts[type.value].version || 1})
                  </div>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Existing Drafts */}
      {Object.keys(drafts).length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-700">Your Drafts:</h3>
          {contentTypes.map(type => (
            drafts[type.value] && (
              <DraftEditor
                key={type.value}
                title={type.label}
                content={drafts[type.value].content}
                version={drafts[type.value].version}
                usedLLM={drafts[type.value].used_llm}
                generatedAt={drafts[type.value].generated_at}
                editable={isEditable}
              />
            )
          ))}
        </div>
      )}

      {Object.keys(drafts).length === 0 && (
        <div className="text-center py-8 text-gray-400">
          <p>No drafts yet. Click a button above to generate content.</p>
        </div>
      )}

      {/* Content Generator Modal */}
      {showGenerator && (
        <ContentGenerator
          applicationId={applicationId}
          contentType={selectedType}
          onGenerated={handleContentGenerated}
          onClose={() => setShowGenerator(false)}
        />
      )}
    </div>
  );
}
