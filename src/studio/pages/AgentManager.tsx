import React from 'react';
import { Bot } from 'lucide-react';

export const AgentManager: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Bot /> Agent Manager</h2>
    <p className="text-slate-400">View and configure multi-agent frameworks.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">9 Specialized Agents Online.</p>
    </div>
  </div>
);
