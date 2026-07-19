import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';


const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';


function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [error, setError] = useState('');
  const chatEndRef = useRef(null);

  const sessionId = useMemo(() => 'demo-session', []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loadingAnswer]);

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    setUploading(true);
    setError('');

    try {
      const uploadResults = await Promise.all(
        files.map((file) => {
          const formData = new FormData();
          formData.append('file', file);
          return axios.post(`${API_BASE}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
        })
      );

      const uploadedNames = uploadResults.map((response) => response.data.filename);
      setDocuments((prev) => [...prev, ...uploadedNames.filter((name) => !prev.includes(name))]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoadingAnswer(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        question: userMessage.content,
        session_id: sessionId,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        citations: response.data.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to get answer.');
    } finally {
      setLoadingAnswer(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <div className="mx-auto flex h-screen max-w-7xl flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-200 bg-white p-4 lg:w-80 lg:border-b-0 lg:border-r">
          <div className="mb-6">
            <h2 className="text-xl font-semibold">OpsPilot</h2>
            <p className="text-sm text-slate-500">AI document assistant</p>
          </div>

          <label className="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm font-medium text-slate-600 transition hover:bg-slate-100">
            <span>{uploading ? 'Uploading...' : 'Upload PDFs'}</span>
            <input type="file" multiple accept="application/pdf" className="hidden" onChange={handleUpload} />
          </label>

          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Uploaded Documents</h3>
            <ul className="space-y-2">
              {documents.length ? (
                documents.map((doc) => (
                  <li key={doc} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{doc}</li>
                ))
              ) : (
                <li className="text-sm text-slate-400">No documents yet.</li>
              )}
            </ul>
          </div>
        </aside>

        <main className="flex flex-1 flex-col bg-white">
          <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
            {messages.length === 0 && !loadingAnswer && (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-slate-500">
                Ask a question about your uploaded documents.
              </div>
            )}

            <div className="space-y-4">
              {messages.map((message, index) => {
                const isUserMessage = message.role === 'user';
                return (
                  <div key={`${message.role}-${index}`} className={`flex ${isUserMessage ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${isUserMessage ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-800'}`}>
                      <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                      {message.role === 'assistant' && message.citations?.length > 0 && (
                        <div className="mt-3 border-t border-slate-200 pt-2 text-xs text-slate-600">
                          <p className="mb-1 font-semibold">Citations</p>
                          <ul className="space-y-1">
                            {message.citations.map((citation, citationIndex) => (
                              <li key={`${citation.document}-${citationIndex}`}>
                                <span className="font-medium">{citation.document || '—'}</span>
                                {' • Page '} {citation.page_number ?? '—'}
                                {' • Score '} {citation.similarity_score?.toFixed(3) ?? '—'}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {loadingAnswer && (
                <div className="flex justify-start">
                  <div className="rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-600">Thinking...</div>
                </div>
              )}

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
              )}

              <div ref={chatEndRef} />
            </div>
          </div>

          <div className="border-t border-slate-200 p-4 sm:p-6">
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-slate-500"
                placeholder="Ask about your documents..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button
                className="rounded-xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
                onClick={handleSend}
              >
                Send
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
