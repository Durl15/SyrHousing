import { useState, useRef, useEffect } from 'react';
import api from '../lib/api';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hello! I\'m the SyrHousing AI assistant. Ask me about roof repair, heating, structural programs, lead remediation, accessibility, weatherization, or how to apply for grants.\n\nI can also do deep eligibility screening — just ask "Am I eligible for [program name]?"',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    api.get('/ai/status').then((res) => setAiStatus(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setLoading(true);

    try {
      // Build conversation history for context
      const history = messages
        .filter((m) => m.role === 'user' || (m.role === 'assistant' && !m.isSystem))
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.text }));

      const res = await api.post('/ai/chat', {
        question: q,
        conversation_history: history.length > 1 ? history : undefined,
      });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: res.data.answer,
          provider: res.data.provider,
          usedLlm: res.data.used_llm,
        },
      ]);
    } catch {
      // Fallback to offline chatbot
      try {
        const res = await api.post('/chatbot/ask', { question: q });
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: res.data.answer,
            programs: res.data.matched_programs,
            provider: 'offline',
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', text: 'Sorry, something went wrong. Please try again.' },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const quickQuestions = [
    'What grants are available for roof repair?',
    'Am I eligible for heating assistance?',
    'What programs help with lead paint?',
    'How do I apply for the RESTORE program?',
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 flex flex-col" style={{ height: 'calc(100vh - 8rem)' }}>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-[#1e3a5f]">AI Grant Assistant</h1>
        {aiStatus && (
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                aiStatus.llm_available ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
            <span className="text-xs text-gray-500">
              {aiStatus.llm_available
                ? `${aiStatus.provider} (${aiStatus.model})`
                : 'Offline mode'}
            </span>
          </div>
        )}
      </div>

      {/* Quick questions */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {quickQuestions.map((q) => (
            <button
              key={q}
              onClick={() => { setInput(q); }}
              className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 hover:border-[#4a9eda] transition-colors cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-white rounded-xl shadow-md p-4 mb-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-xl px-4 py-3 ${
                m.role === 'user'
                  ? 'bg-[#1e3a5f] text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <pre className="whitespace-pre-wrap text-sm font-sans m-0">{m.text}</pre>
              {m.programs && m.programs.length > 0 && (
                <div className="mt-3 space-y-2">
                  {m.programs.slice(0, 3).map((p) => (
                    <div key={p.program_key} className="bg-white/80 rounded-lg p-2 text-xs text-gray-700">
                      <div className="font-medium">{p.name}</div>
                      <div className="text-gray-500">
                        Score: {p.rank_score}/100 · {p.category}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {m.provider && m.role === 'assistant' && (
                <div className="mt-2 text-xs opacity-50">
                  via {m.provider === 'offline' ? 'offline engine' : m.provider}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-3 text-gray-500 text-sm flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#1e3a5f]"></div>
              {aiStatus?.llm_available ? 'AI is thinking...' : 'Searching programs...'}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about housing programs, eligibility, how to apply..."
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#4a9eda] focus:border-transparent outline-none"
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-[#1e3a5f] text-white font-semibold rounded-xl hover:bg-[#2d6a9f] disabled:opacity-50 transition-colors border-none cursor-pointer"
        >
          Send
        </button>
      </div>
    </div>
  );
}
