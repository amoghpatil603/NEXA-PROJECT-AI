import React from 'react';
import { Bot, Radio, CheckCircle2 } from 'lucide-react';
import { useNexaStore } from '../../store';

export const AgentManager: React.FC = () => {
  const { agents } = useNexaStore();

  return (
    <div className="p-8 h-full bg-slate-950 text-white overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Bot className="text-indigo-400" /> Multi-Agent Framework Manager
          </h2>
          <p className="text-slate-400 text-sm mt-1">Real-time status tracking for specialized NEXA autonomous agents.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-emerald-400 font-mono">
          <Radio size={14} className="animate-pulse" /> Live WebSocket Agent Stream
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div key={agent.id} className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                <Bot size={16} className="text-indigo-400" />
                {agent.name}
              </h3>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${agent.status === 'ONLINE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400'}`}>
                {agent.status}
              </span>
            </div>

            <div className="text-xs space-y-1 text-slate-400 font-mono">
              {agent.tasks_completed !== undefined && <div>Tasks Completed: <span className="text-white font-bold">{agent.tasks_completed}</span></div>}
              {agent.database && <div>Vector Engine: <span className="text-indigo-300 font-bold">{agent.database}</span></div>}
              {agent.mode && <div>Mode: <span className="text-emerald-300 font-bold">{agent.mode}</span></div>}
              {agent.active_sockets !== undefined && <div>Live Sockets: <span className="text-emerald-300 font-bold">{agent.active_sockets}</span></div>}
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1"><CheckCircle2 size={12} className="text-emerald-400" /> System Ready</span>
              <span>ID: {agent.id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
