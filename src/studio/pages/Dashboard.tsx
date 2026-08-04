import React, { useEffect, useState } from 'react';
import { Activity, Cpu, Server, Brain, Zap, Database, Boxes, CheckCircle2 } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [sysStatus, setSysStatus] = useState<any>(null);
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/system/status').then(r => r.json()).catch(() => null),
      fetch('/api/model/info').then(r => r.json()).catch(() => null),
      fetch('/api/health').then(r => r.json()).catch(() => null)
    ]).then(([sys, model, hlt]) => {
      if (sys) setSysStatus(sys);
      if (model) setModelInfo(model);
      if (hlt) setHealth(hlt);
    });
  }, []);

  return (
    <div className="h-full w-full bg-slate-950 p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">NEXA Command Center</h1>
          <p className="text-sm text-slate-400">Live platform status and system telemetry.</p>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-indigo-600/20 text-indigo-400">
              <Activity size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">System Health</p>
              <h3 className="text-lg font-bold text-emerald-400 flex items-center gap-2">
                {health?.status === 'ok' ? 'OPTIMAL' : 'OFFLINE'}
                <CheckCircle2 size={16} />
              </h3>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-600/20 text-blue-400">
              <Cpu size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">CPU Usage</p>
              <h3 className="text-lg font-bold text-white">{sysStatus?.cpu_usage_pct || 0}%</h3>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-amber-600/20 text-amber-400">
              <Server size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">RAM Allocation</p>
              <h3 className="text-lg font-bold text-white">{sysStatus?.ram_usage_mb || 0} MB</h3>
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-purple-600/20 text-purple-400">
              <Zap size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Inference Speed</p>
              <h3 className="text-lg font-bold text-white">{sysStatus?.tokens_per_sec || 0} t/s</h3>
            </div>
          </div>
        </div>

        {/* detailed grids */}
        <div className="grid grid-cols-2 gap-6">
          {/* AI Model Status */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
              <Brain className="text-indigo-400" size={18} /> Model Configuration
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">Active Model</span>
                <span className="text-sm font-mono text-white">{modelInfo?.model_name || 'Loading...'}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">Parameters</span>
                <span className="text-sm font-mono text-white">{modelInfo?.parameters || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">Context Window</span>
                <span className="text-sm font-mono text-white">{modelInfo?.context_length || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Phase</span>
                <span className="text-sm font-mono text-emerald-400">{health?.phase || 'UNKNOWN'}</span>
              </div>
            </div>
          </div>

          {/* Module Status */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
              <Boxes className="text-emerald-400" size={18} /> Platform Subsystems
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { name: 'Multi-Agent Framework', status: 'Online' },
                { name: 'RAG Pipeline', status: 'Online' },
                { name: 'Long-Term Memory', status: 'Online' },
                { name: 'Vision Engine', status: 'Online' },
                { name: 'Voice Synthesis', status: 'Online' },
                { name: 'Plugin Ecosystem', status: 'Online' },
              ].map((sub, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-xs font-medium text-slate-300">{sub.name}</span>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
