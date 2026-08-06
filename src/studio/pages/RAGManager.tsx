import React, { useState } from 'react';
import { Database, FileText } from 'lucide-react';
import { VisionUploader } from '../../components/VisionUploader';

export const RAGManager: React.FC = () => {
  const [lastExtracted, setLastExtracted] = useState<string>('');

  return (
    <div className="p-8 h-full bg-slate-950 text-white">
      <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Database /> RAG Manager</h2>
      <p className="text-slate-400">Configure Retrieval-Augmented Generation pipelines and vector DBs.</p>
      
      <div className="mt-6 p-4 border border-slate-800 rounded-lg bg-slate-900">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <FileText size={18} />
          Document Upload & OCR
        </h3>
        <p className="text-sm text-slate-400 mb-4">Upload PDFs, Images, or Text to parse and embed into the RAG vector store automatically.</p>
        
        <VisionUploader onExtracted={(text) => setLastExtracted(text)} />
        
        {lastExtracted && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-emerald-400 mb-2">Last Extracted Text:</h4>
            <div className="p-3 bg-slate-950 border border-slate-800 rounded text-xs font-mono text-slate-300 whitespace-pre-wrap overflow-y-auto max-h-64">
              {lastExtracted}
            </div>
            <button 
              onClick={() => {
                localStorage.setItem('workflow_initial_prompt', lastExtracted);
                alert("Extracted text saved to workflow clipboard. Please navigate to Workflow Builder.");
              }}
              className="mt-3 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 rounded text-xs font-medium"
            >
              Send to Workflow Builder
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
