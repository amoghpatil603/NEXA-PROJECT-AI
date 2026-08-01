import React, { useState } from 'react';
import { 
  Plus, 
  MessageSquare, 
  Pin, 
  Trash2, 
  Edit3, 
  Check, 
  X, 
  Cpu, 
  Settings as SettingsIcon, 
  Keyboard, 
  Download, 
  Zap, 
  Search,
  CheckCircle2
} from 'lucide-react';
import { Chat } from '../types';

interface SidebarProps {
  chats: Chat[];
  activeChatId: string;
  activeTab: 'chat' | 'model' | 'settings';
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onRenameChat: (id: string, newTitle: string) => void;
  onDeleteChat: (id: string) => void;
  onTogglePinChat: (id: string) => void;
  onSelectTab: (tab: 'chat' | 'model' | 'settings') => void;
  onOpenShortcuts: () => void;
  onOpenExport: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  chats,
  activeChatId,
  activeTab,
  onSelectChat,
  onNewChat,
  onRenameChat,
  onDeleteChat,
  onTogglePinChat,
  onSelectTab,
  onOpenShortcuts,
  onOpenExport,
}) => {
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredChats = chats.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinnedChats = filteredChats.filter((c) => c.isPinned);
  const recentChats = filteredChats
    .filter((c) => !c.isPinned)
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());

  const startRename = (chat: Chat, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
  };

  const saveRename = (id: string, e: React.MouseEvent | React.FormEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameChat(id, editTitle.trim());
    }
    setEditingChatId(null);
  };

  const cancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingChatId(null);
  };

  return (
    <aside className="w-72 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none">
      {/* Top Header & New Chat */}
      <div className="p-4 space-y-4">
        {/* Brand */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30">
              <Zap className="w-4 h-4 fill-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
                NEXA Assistant
              </h1>
              <span className="text-[10px] font-mono text-indigo-400">Desktop v5B</span>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all group"
        >
          <div className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            <span>New Conversation</span>
          </div>
          <span className="text-[10px] bg-indigo-700 px-1.5 py-0.5 rounded font-mono text-indigo-200">
            Ctrl+N
          </span>
        </button>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search chats..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80"
          />
        </div>

        {/* Navigation Tabs */}
        <div className="grid grid-cols-2 gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => onSelectTab('chat')}
            className={`flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'chat'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat</span>
          </button>
          <button
            onClick={() => onSelectTab('model')}
            className={`flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'model'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Model</span>
          </button>
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-3 space-y-4 text-xs">
        {/* Pinned Section */}
        {pinnedChats.length > 0 && (
          <div className="space-y-1">
            <div className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Pin className="w-3 h-3 text-amber-400" />
              <span>Pinned</span>
            </div>
            {pinnedChats.map((chat) => (
              <ChatItem
                key={chat.id}
                chat={chat}
                isActive={activeTab === 'chat' && chat.id === activeChatId}
                isEditing={editingChatId === chat.id}
                editTitle={editTitle}
                setEditTitle={setEditTitle}
                onSelect={() => {
                  onSelectTab('chat');
                  onSelectChat(chat.id);
                }}
                onStartRename={(e) => startRename(chat, e)}
                onSaveRename={(e) => saveRename(chat.id, e)}
                onCancelRename={cancelRename}
                onDelete={(e) => {
                  e.stopPropagation();
                  onDeleteChat(chat.id);
                }}
                onTogglePin={(e) => {
                  e.stopPropagation();
                  onTogglePinChat(chat.id);
                }}
              />
            ))}
          </div>
        )}

        {/* Recent Section */}
        <div className="space-y-1">
          <div className="px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Recent Conversations
          </div>
          {recentChats.length === 0 && (
            <p className="px-2 py-3 text-[11px] text-slate-600 italic">No conversations found.</p>
          )}
          {recentChats.map((chat) => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isActive={activeTab === 'chat' && chat.id === activeChatId}
              isEditing={editingChatId === chat.id}
              editTitle={editTitle}
              setEditTitle={setEditTitle}
              onSelect={() => {
                onSelectTab('chat');
                onSelectChat(chat.id);
              }}
              onStartRename={(e) => startRename(chat, e)}
              onSaveRename={(e) => saveRename(chat.id, e)}
              onCancelRename={cancelRename}
              onDelete={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
              }}
              onTogglePin={(e) => {
                e.stopPropagation();
                onTogglePinChat(chat.id);
              }}
            />
          ))}
        </div>
      </div>

      {/* Footer Utility Actions */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/80 space-y-1">
        <div className="grid grid-cols-3 gap-1">
          <button
            onClick={() => onSelectTab('settings')}
            className={`flex flex-col items-center justify-center p-2 rounded-lg text-[11px] transition-colors ${
              activeTab === 'settings'
                ? 'bg-slate-800 text-indigo-300 font-medium'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
            title="Settings"
          >
            <SettingsIcon className="w-4 h-4 mb-0.5" />
            <span>Settings</span>
          </button>

          <button
            onClick={onOpenShortcuts}
            className="flex flex-col items-center justify-center p-2 rounded-lg text-[11px] text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors"
            title="Shortcuts"
          >
            <Keyboard className="w-4 h-4 mb-0.5" />
            <span>Shortcuts</span>
          </button>

          <button
            onClick={onOpenExport}
            className="flex flex-col items-center justify-center p-2 rounded-lg text-[11px] text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors"
            title="Export"
          >
            <Download className="w-4 h-4 mb-0.5" />
            <span>Export</span>
          </button>
        </div>

        <div className="pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono px-1">
          <span>Engine Status</span>
          <span className="text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Ready
          </span>
        </div>
      </div>
    </aside>
  );
};

interface ChatItemProps {
  chat: Chat;
  isActive: boolean;
  isEditing: boolean;
  editTitle: string;
  setEditTitle: (val: string) => void;
  onSelect: () => void;
  onStartRename: (e: React.MouseEvent) => void;
  onSaveRename: (e: React.MouseEvent) => void;
  onCancelRename: (e: React.MouseEvent) => void;
  onDelete: (e: React.MouseEvent) => void;
  onTogglePin: (e: React.MouseEvent) => void;
}

const ChatItem: React.FC<ChatItemProps> = ({
  chat,
  isActive,
  isEditing,
  editTitle,
  setEditTitle,
  onSelect,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onDelete,
  onTogglePin,
}) => {
  return (
    <div
      onClick={onSelect}
      className={`group relative flex items-center justify-between px-2.5 py-2 rounded-lg cursor-pointer transition-all ${
        isActive
          ? 'bg-slate-800 text-white font-medium shadow-sm border border-slate-700/60'
          : 'text-slate-300 hover:bg-slate-900/80 hover:text-slate-100'
      }`}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1 pr-2">
        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
        
        {isEditing ? (
          <div className="flex items-center gap-1 w-full" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full bg-slate-950 border border-indigo-500 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSaveRename(e as any);
                if (e.key === 'Escape') onCancelRename(e as any);
              }}
            />
            <button onClick={onSaveRename} className="text-emerald-400 hover:text-emerald-300 p-0.5">
              <Check className="w-3.5 h-3.5" />
            </button>
            <button onClick={onCancelRename} className="text-slate-400 hover:text-slate-300 p-0.5">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <span className="truncate text-xs">{chat.title}</span>
        )}
      </div>

      {!isEditing && (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onTogglePin}
            className={`p-1 hover:text-amber-400 ${chat.isPinned ? 'text-amber-400 opacity-100' : 'text-slate-400'}`}
            title={chat.isPinned ? 'Unpin chat' : 'Pin chat'}
          >
            <Pin className="w-3 h-3" />
          </button>

          <button
            onClick={onStartRename}
            className="p-1 text-slate-400 hover:text-indigo-300"
            title="Rename"
          >
            <Edit3 className="w-3 h-3" />
          </button>

          <button
            onClick={onDelete}
            className="p-1 text-slate-400 hover:text-rose-400"
            title="Delete"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
};
