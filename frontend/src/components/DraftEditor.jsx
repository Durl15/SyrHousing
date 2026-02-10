import { useState } from 'react';

export default function DraftEditor({ title, content, version, usedLLM, generatedAt, editable }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadAsText = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_v${version}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div
        className="bg-gray-50 px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-800 truncate">{title}</h4>
          <p className="text-xs text-gray-500">
            v{version} \u2022 {usedLLM ? '\uD83E\uDD16 AI-generated' : '\uD83D\uDCDD Template'} \u2022 {formatDate(generatedAt)}
          </p>
        </div>
        <button className="text-gray-500 hover:text-gray-700 ml-2">
          {expanded ? '\u25BC' : '\u25B6'}
        </button>
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-4 bg-white">
          <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-4 mb-3 max-h-96 overflow-y-auto">
            {content}
          </pre>

          {/* Actions */}
          <div className="flex flex-wrap gap-2 mb-3">
            <button
              onClick={copyToClipboard}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1.5"
            >
              {copied ? (
                <>
                  <span>\u2713</span>
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <span>\uD83D\uDCCB</span>
                  <span>Copy</span>
                </>
              )}
            </button>
            <button
              onClick={downloadAsText}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1.5"
            >
              <span>\u2B07\uFE0F</span>
              <span>Download</span>
            </button>
          </div>

          {/* Tip */}
          <div className="p-3 bg-blue-50 rounded-lg text-xs text-blue-800">
            <strong>\uD83D\uDCA1 Tip:</strong> Review and personalize this content before using it in your application. Add specific details about your situation to make it more compelling.
          </div>
        </div>
      )}
    </div>
  );
}
