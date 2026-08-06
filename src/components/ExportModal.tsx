import React, { useRef } from 'react';
import { X, Download, Upload, FileText, Code, FileCode } from 'lucide-react';
import { Chat } from '../types';

interface ExportModalProps {
  chat: Chat;
  onImportChat: (importedChat: Chat) => void;
  onClose: () => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({ chat, onImportChat, onClose }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const exportMarkdown = () => {
    let md = `# ${chat.title}\n*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
    chat.messages.forEach((m) => {
      const sender = m.sender === 'user' ? 'User' : 'NEXA Assistant';
      md += `### ${sender} (${m.timestamp})\n\n${m.content}\n\n---\n\n`;
    });
    downloadFile(md, `${chat.title.replace(/\s+/g, '_')}.md`, 'text/markdown');
  };

  const exportJSON = () => {
    const jsonStr = JSON.stringify(chat, null, 2);
    downloadFile(jsonStr, `${chat.title.replace(/\s+/g, '_')}.json`, 'application/json');
  };

  const exportTXT = () => {
    let txt = `CHAT TITLE: ${chat.title}\nEXPORTED AT: ${new Date().toLocaleString()}\n\n`;
    chat.messages.forEach((m) => {
      txt += `[${m.timestamp}] ${m.sender.toUpperCase()}:\n${m.content}\n\n`;
    });
    downloadFile(txt, `${chat.title.replace(/\s+/g, '_')}.txt`, 'text/plain');
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = JSON.parse(text);
        if (parsed && parsed.title && Array.isArray(parsed.messages)) {
          const newChat: Chat = {
            ...parsed,
            id: `imported-${Date.now()}`,
            updatedAt: new Date().toISOString()
          };
          onImportChat(newChat);
          onClose();
        } else {
          alert('Invalid JSON chat file structure.');
        }
      } catch (err) {
        alert('Failed to parse JSON file.');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-100">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Export & Import Conversation</h3>
              <p className="text-xs text-slate-400">Download active chat session or import previous JSON backup</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4 text-xs">
          <div className="space-y-2">
            <label className="font-semibold text-slate-300 block">Export Formats</label>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={exportMarkdown}
                className="flex flex-col items-center justify-center p-4 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl transition-all group"
              >
                <FileCode className="w-6 h-6 text-indigo-400 mb-2 group-hover:scale-110 transition-transform" />
                <span className="font-semibold text-white">Markdown</span>
                <span className="text-[10px] text-slate-500 mt-0.5">.md</span>
              </button>

              <button
                onClick={exportJSON}
                className="flex flex-col items-center justify-center p-4 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl transition-all group"
              >
                <Code className="w-6 h-6 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
                <span className="font-semibold text-white">JSON Data</span>
                <span className="text-[10px] text-slate-500 mt-0.5">.json</span>
              </button>

              <button
                onClick={exportTXT}
                className="flex flex-col items-center justify-center p-4 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl transition-all group"
              >
                <FileText className="w-6 h-6 text-amber-400 mb-2 group-hover:scale-110 transition-transform" />
                <span className="font-semibold text-white">Plain Text</span>
                <span className="text-[10px] text-slate-500 mt-0.5">.txt</span>
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 space-y-2">
            <label className="font-semibold text-slate-300 block">Import Conversation Backup</label>
            <input
              type="file"
              ref={fileInputRef}
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 py-3 bg-slate-950 hover:bg-slate-800 border border-slate-800/80 rounded-xl font-medium text-slate-200 transition-colors"
            >
              <Upload className="w-4 h-4 text-indigo-400" />
              <span>Import Chat (.json)</span>
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/50">
          <button onClick={onClose} className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-xs font-semibold">
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
