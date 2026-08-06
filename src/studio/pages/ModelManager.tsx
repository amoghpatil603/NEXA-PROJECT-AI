import React from 'react';
import { Box } from 'lucide-react';

export const ModelManager: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Box /> Model Manager</h2>
    <p className="text-slate-400">Manage loaded models and weights.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">Loaded Models: nexa_base_v1, nexa_sft_v1</p>
    </div>
  </div>
);
