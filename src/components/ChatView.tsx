import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Square, 
  RotateCcw, 
  Trash2, 
  Copy, 
  Check, 
  Edit3, 
  User, 
  Bot, 
  Sparkles, 
  Pin, 
  Zap, 
  Clock, 
  Gauge, 
  Cpu, 
  ArrowDown
} from 'lucide-react';
import { Chat, Message, Settings } from '../types';
import { MarkdownMessage } from './MarkdownMessage';
import { VisionUploader } from './VisionUploader';

interface ChatViewProps {
  chat: Chat;
  settings: Settings;
  onSendMessage: (text: string, editMessageId?: string) => void;
  onRegenerate: () => void;
  onStopGeneration: () => void;
  onClearChat: () => void;
  onTogglePin: () => void;
  isGenerating: boolean;
}

export const ChatView: React.FC<ChatViewProps> = ({
  chat,
  settings,
  onSendMessage,
  onRegenerate,
  onStopGeneration,
  onClearChat,
  onTogglePin,
  isGenerating,
}) => {
  const [input, setInput] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editInput, setEditInput] = useState('');
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
  };

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [chat.messages, isGenerating, autoScroll]);

  const handleScroll = () => {
    if (!feedRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = feedRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 80;
    setAutoScroll(isAtBottom);
  };

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isGenerating) return;
    onSendMessage(input.trim());
    setInput('');
    setAutoScroll(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    } else if (e.key === 'Escape' && isGenerating) {
      e.preventDefault();
      onStopGeneration();
    }
  };

  const handleCopyMessage = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const startEditMessage = (msg: Message) => {
    setEditingMessageId(msg.id);
    setEditInput(msg.content);
  };

  const saveEditMessage = (msgId: string) => {
    if (editInput.trim()) {
      onSendMessage(editInput.trim(), msgId);
    }
    setEditingMessageId(null);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900 min-w-0 font-sans">
      {/* Active Chat Header Bar */}
      <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-950/60 backdrop-blur shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse" />
          <h2 className="font-semibold text-slate-100 text-sm truncate">
            {chat.title}
          </h2>
          <button
            onClick={onTogglePin}
            className={`p-1 rounded hover:bg-slate-800 transition-colors ${
              chat.isPinned ? 'text-amber-400' : 'text-slate-500 hover:text-slate-300'
            }`}
            title={chat.isPinned ? 'Unpin' : 'Pin'}
          >
            <Pin className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Top Actions */}
        <div className="flex items-center gap-2">
          {chat.messages.length > 1 && (
            <button
              onClick={onRegenerate}
              disabled={isGenerating}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 disabled:opacity-50 px-3 py-1.5 rounded-lg border border-slate-700/60 transition-colors"
              title="Regenerate Last Response"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Regenerate</span>
            </button>
          )}

          <button
            onClick={onClearChat}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-rose-300 bg-slate-800/60 hover:bg-rose-900/30 px-3 py-1.5 rounded-lg border border-slate-700/60 transition-colors"
            title="Clear Conversation (Ctrl+L)"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </header>

      {/* Messages Feed */}
      <div
        ref={feedRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 relative"
      >
        {chat.messages.map((msg, index) => {
          const isUser = msg.sender === 'user';
          const isAssistant = msg.sender === 'assistant';
          const isSystem = msg.sender === 'system';

          if (isSystem) {
            return (
              <div key={msg.id} className="flex justify-center my-2">
                <span className="bg-slate-800/60 border border-slate-700/50 text-slate-400 text-xs px-3 py-1 rounded-full font-mono">
                  {msg.content}
                </span>
              </div>
            );
          }

          return (
            <div
              key={msg.id}
              className={`flex gap-3 sm:gap-4 max-w-4xl ${
                isUser ? 'ml-auto flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs shrink-0 shadow-md ${
                  isUser
                    ? 'bg-indigo-600 text-white shadow-indigo-600/20'
                    : 'bg-slate-800 text-indigo-400 border border-slate-700/80 shadow-slate-900/50'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Content & Info */}
              <div className={`space-y-1.5 min-w-0 max-w-[85%] ${isUser ? 'items-end' : ''}`}>
                <div className={`flex items-center gap-2 text-[11px] text-slate-400 ${isUser ? 'justify-end' : ''}`}>
                  <span className="font-semibold text-slate-300">
                    {isUser ? 'You' : 'NEXA Assistant'}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.tokensPerSec && (
                    <span className="text-emerald-400 font-mono ml-1">
                      ({msg.tokensPerSec} t/s)
                    </span>
                  )}
                </div>

                {/* Bubble Container */}
                <div
                  className={`group relative p-4 rounded-2xl text-sm leading-relaxed transition-all ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/10'
                      : 'bg-slate-800/90 text-slate-100 border border-slate-700/70 rounded-tl-none shadow-md shadow-slate-950/40'
                  }`}
                >
                  {editingMessageId === msg.id ? (
                    <div className="space-y-2">
                      <textarea
                        value={editInput}
                        onChange={(e) => setEditInput(e.target.value)}
                        className="w-full bg-slate-950 text-white border border-indigo-400 rounded-xl p-2.5 text-sm focus:outline-none"
                        rows={3}
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => setEditingMessageId(null)}
                          className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-200"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => saveEditMessage(msg.id)}
                          className="px-2.5 py-1 bg-indigo-500 hover:bg-indigo-400 rounded text-xs text-white font-medium"
                        >
                          Save & Submit
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <MarkdownMessage content={msg.content} />
                      {msg.isStreaming && (
                        <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse" />
                      )}
                    </div>
                  )}

                  {/* Message Action Bar */}
                  {!editingMessageId && (
                    <div
                      className={`absolute bottom-2 ${
                        isUser ? '-left-16' : '-right-16'
                      } flex items-center gap-1 bg-slate-950/90 border border-slate-800 rounded-lg p-1 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg backdrop-blur`}
                    >
                      <button
                        onClick={() => handleCopyMessage(msg.id, msg.content)}
                        className="p-1 text-slate-400 hover:text-white"
                        title="Copy message"
                      >
                        {copiedMsgId === msg.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {isUser && (
                        <button
                          onClick={() => startEditMessage(msg)}
                          className="p-1 text-slate-400 hover:text-indigo-300"
                          title="Edit prompt"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Typing / Generating Indicator */}
        {isGenerating && (
          <div className="flex gap-4 max-w-4xl">
            <div className="w-8 h-8 rounded-xl bg-slate-800 text-indigo-400 border border-slate-700 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-800/90 border border-slate-700/60 p-4 rounded-2xl rounded-tl-none text-slate-300 text-sm flex items-center gap-3">
              <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
              <span className="font-mono text-xs">NEXA is thinking & streaming...</span>
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />

        {/* Scroll To Bottom Button */}
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true);
              scrollToBottom();
            }}
            className="fixed bottom-24 right-8 bg-indigo-600 hover:bg-indigo-500 text-white p-2.5 rounded-full shadow-xl border border-indigo-400/40 transition-all z-20 flex items-center gap-1 text-xs"
          >
            <ArrowDown className="w-4 h-4" />
            <span className="pr-1 font-medium">Scroll to bottom</span>
          </button>
        )}
      </div>

      {/* Quick Suggestion Pills */}
      <div className="px-6 py-2 bg-slate-950/40 border-t border-slate-800/50 flex gap-2 overflow-x-auto shrink-0">
        {[
          'Write a Python quicksort algorithm',
          'Explain NexaTransformer BPE architecture',
          'Create a React state custom hook'
        ].map((pill, idx) => (
          <button
            key={idx}
            onClick={() => {
              setInput(pill);
              textareaRef.current?.focus();
            }}
            className="text-[11px] bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 px-3 py-1 rounded-full whitespace-nowrap transition-colors"
          >
            {pill}
          </button>
        ))}
      </div>

      {/* Prompt Input Form Bar */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/80 shrink-0">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto flex items-end gap-3">
          <div className="flex-1 bg-slate-900 border border-slate-700/80 focus-within:border-indigo-500 rounded-2xl p-2.5 shadow-inner transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <VisionUploader onExtracted={(text) => setInput((prev) => prev ? prev + "\n\n" + text : text)} />
            </div>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask NEXA Assistant... (Ctrl+Enter to send)"
              rows={2}
              className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2"
            />
            <div className="flex justify-between items-center px-2 pt-1 border-t border-slate-800/60 text-[10px] text-slate-500 font-mono">
              <span>Temp: {settings.temperature} • Max Tokens: {settings.max_new_tokens}</span>
              <span>Press <kbd className="bg-slate-800 text-slate-300 px-1 rounded">Ctrl+Enter</kbd></span>
            </div>
          </div>

          {isGenerating ? (
            <button
              type="button"
              onClick={onStopGeneration}
              className="bg-rose-600 hover:bg-rose-500 text-white px-5 py-3.5 rounded-2xl flex items-center gap-2 text-xs font-semibold shadow-lg shadow-rose-600/20 transition-all shrink-0"
              title="Stop Generation (Esc)"
            >
              <Square className="w-4 h-4 fill-white" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-3.5 rounded-2xl flex items-center gap-2 text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all shrink-0"
            >
              <span>Send</span>
              <Send className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
};
