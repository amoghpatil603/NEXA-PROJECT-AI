import React, { useState, useEffect } from 'react';
import { Terminal, Cpu, Database, BookOpen, Settings, Send, RefreshCw, CheckCircle2 } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge' | 'tools' | 'settings'>('chat');
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [chatMessages, setChatMessages] = useState<Array<{role: string, content: string}>>([
    { role: 'assistant', content: 'NEXA Intelligence Engine active. Ready for queries and knowledge retrieval.' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/system/status')
      .then(res => res.json())
      .then(data => setSystemStatus(data))
      .catch(() => {});
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMsg = inputMessage;
    setInputMessage('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response || data.text || JSON.stringify(data) }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error communicating with inference engine.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          <Cpu className="w-8 h-8 text-cyan-400 animate-pulse" />
          <div>
            <h1 className="text-xl font-bold tracking-wider text-cyan-400">NEXA INTELLIGENCE</h1>
            <p className="text-xs text-slate-400">Phase 5B5 Stability Certified • 14.2M Parameter Model</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          {systemStatus && (
            <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-700">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-300 font-mono">RAM: {systemStatus.ram_usage_mb}MB</span>
              <span className="text-slate-500">|</span>
              <span className="text-cyan-300 font-mono">Model: {systemStatus.current_model}</span>
            </div>
          )}
        </div>
      </header>

      <div className="bg-slate-800/60 border-b border-slate-700 px-6 flex space-x-2">
        <button
          onClick={() => setActiveTab('chat')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors flex items-center space-x-2 ${activeTab === 'chat' ? 'border-cyan-400 text-cyan-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
          <Terminal className="w-4 h-4" />
          <span>Chat / Inference</span>
        </button>
        <button
          onClick={() => setActiveTab('knowledge')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors flex items-center space-x-2 ${activeTab === 'knowledge' ? 'border-cyan-400 text-cyan-400 bg-slate-800' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Knowledge & RAG</span>
        </button>
      </div>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'chat' && (
          <div className="flex flex-col h-[75vh] bg-slate-800/40 rounded-xl border border-slate-700 shadow-xl overflow-hidden">
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xl rounded-lg p-4 text-sm leading-relaxed ${msg.role === 'user' ? 'bg-cyan-600 text-white' : 'bg-slate-800 border border-slate-700 text-slate-200'}`}>
                    <p className="font-semibold text-xs text-slate-400 mb-1 uppercase tracking-wider">{msg.role === 'user' ? 'User' : 'NEXA Engine'}</p>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm text-slate-400 animate-pulse flex items-center space-x-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                    <span>Processing inference query...</span>
                  </div>
                </div>
              )}
            </div>
            <form onSubmit={handleSendMessage} className="p-4 bg-slate-800 border-t border-slate-700 flex space-x-3">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                placeholder="Enter prompt or query for NEXA..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </form>
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className="bg-slate-800/40 p-6 rounded-xl border border-slate-700 shadow-xl space-y-6">
            <h2 className="text-xl font-bold text-cyan-400">Knowledge Engine & Document RAG</h2>
            <p className="text-slate-300 text-sm">Upload and index documents (.pdf, .docx, .txt, .md) for retrieval-augmented generation.</p>
            <div className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center bg-slate-800/60 hover:border-cyan-500 transition-colors cursor-pointer">
              <BookOpen className="w-12 h-12 text-cyan-400 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-200">Drag and drop knowledge files here, or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">Supports PDF, Word, Markdown, and Text files</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
