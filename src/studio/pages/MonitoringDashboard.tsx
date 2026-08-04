import React from 'react';
import { Activity } from 'lucide-react';

export const MonitoringDashboard: React.FC = () => (
  <div className="p-8 h-full bg-slate-950 text-white">
    <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Activity /> Monitoring Dashboard</h2>
    <p className="text-slate-400">View real-time telemetry and logs.</p>
    <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
      <p className="text-sm">All systems nominal.</p>
    </div>
  </div>
);
