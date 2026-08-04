import React from 'react';
import { X, Sliders, Sun, Moon, Sparkles, RefreshCw, Check } from 'lucide-react';
import { Settings } from '../types';

interface SettingsModalProps {
  settings: Settings;
  onUpdateSettings: (newSettings: Partial<Settings>) => void;
  onResetSettings: () => void;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  settings,
  onUpdateSettings,
  onResetSettings,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col text-slate-100">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between shrink-0 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Assistant & Model Settings</h3>
              <p className="text-xs text-slate-400">Configure sampling parameters and workspace preferences</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 text-xs flex-1">
          {/* Temperature */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-slate-200">Temperature</label>
              <span className="font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/80 px-2 py-0.5 rounded text-[11px]">
                {settings.temperature}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="2.0"
              step="0.05"
              value={settings.temperature}
              onChange={(e) => onUpdateSettings({ temperature: parseFloat(e.target.value) })}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">Controls output randomness. Lower values are deterministic; higher values are creative.</p>
          </div>

          {/* Top K */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-slate-200">Top-K Sampling</label>
              <span className="font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/80 px-2 py-0.5 rounded text-[11px]">
                {settings.top_k}
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="100"
              step="1"
              value={settings.top_k}
              onChange={(e) => onUpdateSettings({ top_k: parseInt(e.target.value) })}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">Limits token selection pool to top K candidates.</p>
          </div>

          {/* Top P */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-slate-200">Top-P (Nucleus) Sampling</label>
              <span className="font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/80 px-2 py-0.5 rounded text-[11px]">
                {settings.top_p}
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={settings.top_p}
              onChange={(e) => onUpdateSettings({ top_p: parseFloat(e.target.value) })}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">Filters tokens based on cumulative probability mass.</p>
          </div>

          {/* Max New Tokens */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="font-semibold text-slate-200">Max New Tokens</label>
              <span className="font-mono text-indigo-400 bg-indigo-950/60 border border-indigo-800/80 px-2 py-0.5 rounded text-[11px]">
                {settings.max_new_tokens}
              </span>
            </div>
            <input
              type="range"
              min="16"
              max="256"
              step="16"
              value={settings.max_new_tokens}
              onChange={(e) => onUpdateSettings({ max_new_tokens: parseInt(e.target.value) })}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400">Maximum tokens allowed per response generation.</p>
          </div>

          {/* Theme & Font Size */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="font-semibold text-slate-200 block">Appearance Theme</label>
              <select
                value={settings.theme}
                onChange={(e) => onUpdateSettings({ theme: e.target.value as any })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="dark">Dark Slate</option>
                <option value="emerald">Cyberpunk Emerald</option>
                <option value="light">Light Mode</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="font-semibold text-slate-200 block">Font Size</label>
              <select
                value={settings.fontSize}
                onChange={(e) => onUpdateSettings({ fontSize: e.target.value as any })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="small">Small (13px)</option>
                <option value="medium">Medium (14px)</option>
                <option value="large">Large (16px)</option>
              </select>
            </div>
          </div>

          {/* System Prompt */}
          <div className="space-y-2">
            <label className="font-semibold text-slate-200 block">System Prompt</label>
            <textarea
              value={settings.systemPrompt}
              onChange={(e) => onUpdateSettings({ systemPrompt: e.target.value })}
              rows={3}
              placeholder="Enter system prompt instruction..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none font-mono text-[11px]"
            />
          </div>

          {/* Autosave Toggle */}
          <div className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800">
            <div>
              <span className="font-semibold text-slate-200 block">Autosave Conversations</span>
              <p className="text-[11px] text-slate-400">Persist active chats and settings to localStorage</p>
            </div>
            <button
              onClick={() => onUpdateSettings({ autosave: !settings.autosave })}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                settings.autosave ? 'bg-indigo-600 justify-end' : 'bg-slate-800 justify-start'
              }`}
            >
              <span className="w-4 h-4 rounded-full bg-white shadow-md" />
            </button>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 flex justify-between items-center bg-slate-950/50">
          <button
            onClick={onResetSettings}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
          <button
            onClick={onClose}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2 rounded-xl text-xs shadow-md shadow-indigo-600/20 transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
