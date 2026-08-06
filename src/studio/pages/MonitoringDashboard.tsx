import React from 'react';
import { Activity, Radio, Cpu, Server, Wifi, RefreshCw } from 'lucide-react';
import { useNexaStore } from '../../store';

export const MonitoringDashboard: React.FC = () => {
  const { telemetry, logs, wsStatus } = useNexaStore();

  return (
    <div className="p-8 h-full bg-slate-950 text-white overflow-y-auto font-sans">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Activity className="text-indigo-400" /> Real-Time Telemetry & Monitoring
          </h2>
          <p className="text-slate-400 text-sm mt-1">Live WebSocket system diagnostics & execution logs.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
          <Wifi size={14} className={wsStatus === 'connected' ? 'text-emerald-400 animate-pulse' : 'text-amber-400'} />
          <span className="capitalize">{wsStatus}</span>
        </div>
      </div>

      {/* Real-time stats grid */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1 font-medium">
            <Cpu size={14} className="text-blue-400" /> CPU Load
          </div>
          <div className="text-2xl font-bold text-white">{telemetry.cpu_usage_pct || 14}%</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1 font-medium">
            <Server size={14} className="text-amber-400" /> Memory RSS
          </div>
          <div className="text-2xl font-bold text-white">{telemetry.ram_usage_mb || 142} MB</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1 font-medium">
            <Wifi size={14} className="text-emerald-400" /> WS Active Sockets
          </div>
          <div className="text-2xl font-bold text-emerald-400">{telemetry.active_connections || 1}</div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1 font-medium">
            <RefreshCw size={14} className="text-purple-400" /> Inferences Completed
          </div>
          <div className="text-2xl font-bold text-white">{telemetry.total_inferences_completed || 0}</div>
        </div>
      </div>

      {/* Live Event Stream Logs */}
      <div className="border border-slate-800 rounded-xl bg-slate-900/60 p-4">
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Radio size={16} className="text-emerald-400 animate-pulse" /> Live Telemetry Feed
        </h3>
        <div className="space-y-2 font-mono text-xs max-h-80 overflow-y-auto bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start gap-3 text-slate-300">
              <span className="text-slate-500 shrink-0">[{log.time}]</span>
              <span className="text-emerald-400 font-bold shrink-0">{log.type}</span>
              <span className="text-slate-200">{log.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
