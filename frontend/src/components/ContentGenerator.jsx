import { useState } from 'react';
import api from '../lib/api';

export default function ContentGenerator({ applicationId, contentType, onGenerated, onClose }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const labels = {
    cover_letter: 'Cover Letter',
    eligibility_statement: 'Eligibility Statement',
    project_description: 'Project Description',
    needs_justification: 'Needs Justification',
  };

  const descriptions = {
    cover_letter: 'A professional introduction expressing your interest and need for assistance.',
    eligibility_statement: 'A point-by-point statement showing how you meet the program requirements.',
    project_description: 'A detailed narrative describing your repair needs and their urgency.',
    needs_justification: 'An explanation of why you need assistance and how it will help you.',
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.post('/grant-writer/generate', {
        application_id: applicationId,
        content_type: contentType
      });
      onGenerated(contentType, res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate content. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-bold text-[#1e3a5f] mb-4">
          Generate {labels[contentType]}
        </h3>

        <p className="text-sm text-gray-600 mb-6">
          {descriptions[contentType]}
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-xs text-blue-800">
            <strong>\uD83E\uDD16 AI-Powered:</strong> Content will be generated based on your profile and the program requirements. Review and personalize before using.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-4 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex-1 px-4 py-2 bg-[#1e3a5f] text-white rounded-lg hover:bg-[#2d4a7f] disabled:opacity-50 transition-colors"
          >
            {generating ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                Generating...
              </span>
            ) : (
              'Generate'
            )}
          </button>
          <button
            onClick={onClose}
            disabled={generating}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
