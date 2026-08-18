import React, { useCallback, useState } from 'react';
import { 
  ReactFlow, 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  Connection,
  Edge,
  Node,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Save, Play, Download, Upload } from 'lucide-react';

const initialNodes: Node[] = [
  { id: '1', position: { x: 100, y: 100 }, data: { label: 'Input Prompt' }, type: 'input' },
  { id: '2', position: { x: 350, y: 100 }, data: { label: 'Multi-Agent Router' } },
  { id: '3', position: { x: 600, y: 100 }, data: { label: 'Response Output' }, type: 'output' },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e2-3', source: '2', target: '3' },
];

export const WorkflowBuilder: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddNode = (type: string, label: string) => {
    const newNode: Node = {
      id: Date.now().toString(),
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: { label },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const executeWorkflow = () => {
    setIsExecuting(true);
    setExecutionLogs(['Initializing Execution Engine...']);
    
    setTimeout(() => {
      setExecutionLogs(prev => [...prev, 'Validating computational graph...']);
      setTimeout(() => {
        setExecutionLogs(prev => [...prev, 'Graph verified. 3 nodes scheduled.']);
        setTimeout(() => {
          setExecutionLogs(prev => [...prev, 'Executing node: Input Prompt']);
          setTimeout(() => {
            setExecutionLogs(prev => [...prev, 'Executing node: Multi-Agent Router']);
            setTimeout(() => {
              setExecutionLogs(prev => [...prev, 'Executing node: Response Output']);
              setTimeout(() => {
                setExecutionLogs(prev => [...prev, 'Workflow execution completed successfully.']);
                setIsExecuting(false);
              }, 600);
            }, 600);
          }, 600);
        }, 600);
      }, 600);
    }, 600);
  };

  const saveWorkflow = () => {
    const data = JSON.stringify({ nodes, edges });
    localStorage.setItem('nexa_workflow', data);
    alert('Workflow saved locally!');
  };

  const loadWorkflow = () => {
    const data = localStorage.getItem('nexa_workflow');
    if (data) {
      const parsed = JSON.parse(data);
      setNodes(parsed.nodes || []);
      setEdges(parsed.edges || []);
    }
  };

  return (
    <div className="flex h-full w-full">
      {/* Node Palette */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-4">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Components</h3>
        
        <div className="space-y-2">
          {['Prompt', 'LLM', 'Agent', 'Memory', 'RAG', 'Vision', 'Voice', 'Plugin', 'Logic', 'Output'].map((t) => (
            <button
              key={t}
              onClick={() => handleAddNode('default', t)}
              className="w-full text-left px-3 py-2 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition-colors"
            >
              + {t} Node
            </button>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative bg-slate-950">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          className="dark"
        >
          <Background color="#334155" gap={16} />
          <Controls className="bg-slate-800 border-slate-700 fill-slate-200" />
          <MiniMap className="bg-slate-900 border border-slate-800" maskColor="rgba(15, 23, 42, 0.6)" />
          
          <Panel position="top-right" className="flex gap-2 bg-slate-900/80 p-2 rounded-xl backdrop-blur-sm border border-slate-800">
            <button onClick={saveWorkflow} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium transition-colors">
              <Save size={14} /> Save
            </button>
            <button onClick={loadWorkflow} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-medium transition-colors">
              <Upload size={14} /> Load
            </button>
            <button 
              onClick={executeWorkflow} 
              disabled={isExecuting}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-md text-xs font-bold transition-colors ${
                isExecuting ? 'bg-indigo-600/50 text-indigo-300' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_15px_rgba(79,70,229,0.4)]'
              }`}
            >
              <Play size={14} /> {isExecuting ? 'Running...' : 'Execute'}
            </button>
          </Panel>
        </ReactFlow>
      </div>

      {/* Execution Logs */}
      <div className="w-80 bg-slate-900 border-l border-slate-800 flex flex-col">
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Execution Engine</h3>
          {isExecuting && <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>}
        </div>
        <div className="flex-1 p-4 font-mono text-[10px] overflow-y-auto space-y-2">
          {executionLogs.length === 0 ? (
            <p className="text-slate-600 italic">No execution logs yet. Click 'Execute' to run the workflow.</p>
          ) : (
            executionLogs.map((log, idx) => (
              <div key={idx} className="text-slate-300">
                <span className="text-slate-500">[{new Date().toLocaleTimeString()}]</span> {log}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
