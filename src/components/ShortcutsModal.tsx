import React from 'react';
import { X, Keyboard, Command } from 'lucide-react';

interface ShortcutsModalProps {
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ onClose }) => {
  const shortcuts = [
    { key: 'Ctrl + Enter', description: 'Send Message / Execute Prompt' },
    { key: 'Ctrl + L', description: 'Clear Active Conversation' },
    { key: 'Ctrl + N', description: 'Start New Conversation' },
    { key: 'Ctrl + Shift + C', description: 'Copy Last Assistant Response' },
    { key: 'Esc', description: 'Stop Active Generation / Close Modals' }
  ];

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden text-slate-100">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Keyboard className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Keyboard Shortcuts</h3>
              <p className="text-xs text-slate-400">Desktop hotkeys for rapid workflow</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-3 text-xs">
          {shortcuts.map((sc, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800/80">
              <span className="text-slate-300 font-medium">{sc.description}</span>
              <kbd className="bg-slate-800 border border-slate-700/80 text-indigo-300 px-2.5 py-1 rounded-lg font-mono font-semibold shadow-inner text-[11px]">
                {sc.key}
              </kbd>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-950/50">
          <button onClick={onClose} className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-xl text-xs">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
