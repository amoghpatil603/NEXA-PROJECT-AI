import React from 'react';
import { Database } from 'lucide-react';

export const RAGManager: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Database /> RAG Manager</h2>
    <p className="text-slate-400">Configure Retrieval-Augmented Generation pipelines and vector DBs.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">Vector DB Connected.</p>
    </div>
  </div>
);
