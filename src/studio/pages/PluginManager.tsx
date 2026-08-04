import React from 'react';
import { Blocks } from 'lucide-react';

export const PluginManager: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Blocks /> Plugin Manager</h2>
    <p className="text-slate-400">Manage tool integrations and API plugins.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">5 Core Plugins Loaded.</p>
    </div>
  </div>
);
