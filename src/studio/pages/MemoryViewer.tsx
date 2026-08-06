import React from 'react';
import { Brain } from 'lucide-react';

export const MemoryViewer: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Brain /> Memory Viewer</h2>
    <p className="text-slate-400">Inspect short-term and long-term memory states.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">Memory Store Active.</p>
    </div>
  </div>
);
