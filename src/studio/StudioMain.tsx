import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Workflow, 
  Bot, 
  Blocks, 
  Brain, 
  Database, 
  Box,
  Cloud,
  Activity
} from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { WorkflowBuilder } from './pages/WorkflowBuilder';
import { AgentManager } from './pages/AgentManager';
import { PluginManager } from './pages/PluginManager';
import { MemoryViewer } from './pages/MemoryViewer';
import { RAGManager } from './pages/RAGManager';
import { ModelManager } from './pages/ModelManager';
import { DeploymentManager } from './pages/DeploymentManager';
import { MonitoringDashboard } from './pages/MonitoringDashboard';

type StudioPage = 
  | 'dashboard' 
  | 'workflow' 
  | 'agents' 
  | 'plugins' 
  | 'memory' 
  | 'rag' 
  | 'models'
  | 'deployment'
  | 'monitoring';

export const StudioMain: React.FC = () => {
  const [activePage, setActivePage] = useState<StudioPage>('dashboard');

  const navItems: { id: StudioPage; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
    { id: 'workflow', label: 'Workflow Builder', icon: <Workflow size={16} /> },
    { id: 'agents', label: 'Agent Manager', icon: <Bot size={16} /> },
    { id: 'plugins', label: 'Plugin Manager', icon: <Blocks size={16} /> },
    { id: 'memory', label: 'Memory Viewer', icon: <Brain size={16} /> },
    { id: 'rag', label: 'RAG Manager', icon: <Database size={16} /> },
    { id: 'models', label: 'Model Manager', icon: <Box size={16} /> },
    { id: 'deployment', label: 'Deployment', icon: <Cloud size={16} /> },
    { id: 'monitoring', label: 'Monitoring', icon: <Activity size={16} /> },
  ];

  return (
    <div className="flex h-full w-full bg-slate-950 text-slate-200">
      <div className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <LayoutDashboard size={20} className="text-indigo-400" />
            NEXA Studio
          </h2>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activePage === item.id 
                  ? 'bg-indigo-600/20 text-indigo-400' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
      </div>
      
      <div className="flex-1 overflow-hidden relative">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage === 'workflow' && <WorkflowBuilder />}
        {activePage === 'agents' && <AgentManager />}
        {activePage === 'plugins' && <PluginManager />}
        {activePage === 'memory' && <MemoryViewer />}
        {activePage === 'rag' && <RAGManager />}
        {activePage === 'models' && <ModelManager />}
        {activePage === 'deployment' && <DeploymentManager />}
        {activePage === 'monitoring' && <MonitoringDashboard />}
      </div>
    </div>
  );
};
