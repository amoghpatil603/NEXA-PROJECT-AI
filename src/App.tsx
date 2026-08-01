import React, { useState, useEffect, useRef } from 'react';
import { Chat, Message, Settings, WindowState } from './types';
import { 
  loadChats, 
  saveChats, 
  loadSettings, 
  saveSettings, 
  DEFAULT_SETTINGS 
} from './utils/localStorage';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/ChatView';
import { ModelPanel } from './components/ModelPanel';
import { SettingsModal } from './components/SettingsModal';
import { ShortcutsModal } from './components/ShortcutsModal';
import { ExportModal } from './components/ExportModal';

export default function App() {
  const [chats, setChats] = useState<Chat[]>(() => loadChats());
  const [activeChatId, setActiveChatId] = useState<string>(() => chats[0]?.id || 'default-chat-1');
  const [settings, setSettings] = useState<Settings>(() => loadSettings());
  const [activeTab, setActiveTab] = useState<'chat' | 'model' | 'settings'>('chat');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0] || {
    id: 'temp',
    title: 'New Conversation',
    isPinned: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: []
  };

  // Autosave persistence
  useEffect(() => {
    if (settings.autosave) {
      saveChats(chats);
    }
  }, [chats, settings.autosave]);

  useEffect(() => {
    saveSettings(settings);
  }, [settings]);

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl + N: New Chat
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        handleNewChat();
      }
      // Ctrl + L: Clear Active Chat
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
        e.preventDefault();
        handleClearChat();
      }
      // Ctrl + Shift + C: Copy Last Assistant Response
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'c') {
        e.preventDefault();
        copyLastResponse();
      }
      // Esc: Stop generation / close modal
      else if (e.key === 'Escape') {
        if (isGenerating) {
          handleStopGeneration();
        } else {
          setShowShortcutsModal(false);
          setShowExportModal(false);
          setShowSettingsModal(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [chats, activeChatId, isGenerating]);

  const copyLastResponse = () => {
    const assistantMsgs = activeChat.messages.filter((m) => m.sender === 'assistant');
    const lastMsg = assistantMsgs[assistantMsgs.length - 1];
    if (lastMsg) {
      navigator.clipboard.writeText(lastMsg.content);
    }
  };

  const handleNewChat = () => {
    const newId = `chat-${Date.now()}`;
    const newChat: Chat = {
      id: newId,
      title: 'New Conversation',
      isPinned: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: [
        {
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          content: 'New chat session started. What would you like to explore?',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          tokens: 10
        }
      ]
    };

    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newId);
    setActiveTab('chat');
  };

  const handleRenameChat = (id: string, newTitle: string) => {
    setChats((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title: newTitle, updatedAt: new Date().toISOString() } : c))
    );
  };

  const handleDeleteChat = (id: string) => {
    if (chats.length <= 1) {
      handleClearChat();
      return;
    }
    const filtered = chats.filter((c) => c.id !== id);
    setChats(filtered);
    if (activeChatId === id) {
      setActiveChatId(filtered[0].id);
    }
  };

  const handleTogglePinChat = (id: string) => {
    setChats((prev) =>
      prev.map((c) => (c.id === id ? { ...c, isPinned: !c.isPinned } : c))
    );
  };

  const handleClearChat = () => {
    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChatId
          ? {
              ...c,
              updatedAt: new Date().toISOString(),
              messages: [
                {
                  id: `msg-${Date.now()}`,
                  sender: 'assistant',
                  content: 'Conversation reset. How can NEXA assist you now?',
                  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  tokens: 8
                }
              ]
            }
          : c
      )
    );
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
  };

  const handleSendMessage = async (text: string, editMessageId?: string) => {
    if (isGenerating) return;

    let updatedMessages = [...activeChat.messages];

    if (editMessageId) {
      // Find index and truncate from that point
      const idx = updatedMessages.findIndex((m) => m.id === editMessageId);
      if (idx !== -1) {
        updatedMessages = updatedMessages.slice(0, idx);
      }
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      tokens: Math.ceil(text.length / 4)
    };

    updatedMessages.push(userMessage);

    const assistantMsgId = `assistant-${Date.now()}`;
    const assistantPlaceholder: Message = {
      id: assistantMsgId,
      sender: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true
    };

    updatedMessages.push(assistantPlaceholder);

    // Auto-update title if default
    let chatTitle = activeChat.title;
    if (chatTitle === 'New Conversation' || chatTitle === 'Welcome to NEXA Desktop') {
      chatTitle = text.slice(0, 28) + (text.length > 28 ? '...' : '');
    }

    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChatId
          ? {
              ...c,
              title: chatTitle,
              updatedAt: new Date().toISOString(),
              messages: updatedMessages
            }
          : c
      )
    );

    setIsGenerating(true);
    abortControllerRef.current = new AbortController();

    const startTime = performance.now();

    try {
      const historyPayload = updatedMessages
        .filter((m) => m.sender !== 'system' && m.id !== assistantMsgId)
        .map((m) => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.content
        }));

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          message: text,
          system_prompt: settings.systemPrompt,
          history: historyPayload.slice(-6),
          max_tokens: settings.max_new_tokens,
          temperature: settings.temperature,
          top_k: settings.top_k,
          top_p: settings.top_p
        })
      });

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedText = '';
      let tokensCount = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace('data: ', '').trim();
            if (jsonStr === '[DONE]') break;
            try {
              const data = JSON.parse(jsonStr);
              if (data.full) {
                streamedText = data.full;
                tokensCount = data.tokens_count || tokensCount;
              } else if (data.response) {
                streamedText = data.response;
              }

              // Realtime UI state update
              setChats((prev) =>
                prev.map((c) => {
                  if (c.id !== activeChatId) return c;
                  const msgs = c.messages.map((m) =>
                    m.id === assistantMsgId ? { ...m, content: streamedText } : m
                  );
                  return { ...c, messages: msgs };
                })
              );
            } catch (e) {
              // Ignore non-json SSE lines
            }
          }
        }
      }

      const endTime = performance.now();
      const timeSec = Math.max((endTime - startTime) / 1000, 0.1);
      const tps = Math.round((tokensCount || streamedText.split(/\s+/).length) / timeSec);

      // Finalize message state
      setChats((prev) =>
        prev.map((c) => {
          if (c.id !== activeChatId) return c;
          const msgs = c.messages.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: streamedText || 'Response generation complete.',
                  isStreaming: false,
                  generationTime: Math.round(timeSec * 100) / 100,
                  tokensPerSec: tps
                }
              : m
          );
          return { ...c, messages: msgs };
        })
      );
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Generation stopped by user.');
      } else {
        console.error('Streaming error, falling back to standard API', err);
        // Fallback to standard /api/chat if stream fails
        try {
          const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: text,
              system_prompt: settings.systemPrompt,
              history: updatedMessages.slice(-6).map((m) => ({
                role: m.sender === 'user' ? 'user' : 'assistant',
                content: m.content
              })),
              max_tokens: settings.max_new_tokens,
              temperature: settings.temperature
            })
          });
          const fallbackData = await res.json();
          const reply = fallbackData.response || 'No response returned from NEXA ChatEngine.';

          setChats((prev) =>
            prev.map((c) => {
              if (c.id !== activeChatId) return c;
              const msgs = c.messages.map((m) =>
                m.id === assistantMsgId ? { ...m, content: reply, isStreaming: false } : m
              );
              return { ...c, messages: msgs };
            })
          );
        } catch (fbErr) {
          setChats((prev) =>
            prev.map((c) => {
              if (c.id !== activeChatId) return c;
              const msgs = c.messages.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: 'Failed to communicate with NEXA server.', isStreaming: false }
                  : m
              );
              return { ...c, messages: msgs };
            })
          );
        }
      }
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleImportChat = (importedChat: Chat) => {
    setChats((prev) => [importedChat, ...prev]);
    setActiveChatId(importedChat.id);
    setActiveTab('chat');
  };

  const getThemeClass = () => {
    if (settings.theme === 'light') return 'bg-slate-100 text-slate-900';
    if (settings.theme === 'emerald') return 'bg-zinc-950 text-emerald-100';
    return 'bg-slate-900 text-slate-100';
  };

  return (
    <div className={`flex h-screen w-screen overflow-hidden font-sans antialiased ${getThemeClass()}`}>
      {/* Sidebar */}
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        activeTab={activeTab}
        onSelectChat={(id) => setActiveChatId(id)}
        onNewChat={handleNewChat}
        onRenameChat={handleRenameChat}
        onDeleteChat={handleDeleteChat}
        onTogglePinChat={handleTogglePinChat}
        onSelectTab={(tab) => {
          if (tab === 'settings') {
            setShowSettingsModal(true);
          } else {
            setActiveTab(tab);
          }
        }}
        onOpenShortcuts={() => setShowShortcutsModal(true)}
        onOpenExport={() => setShowExportModal(true)}
      />

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full relative">
        {activeTab === 'chat' && (
          <ChatView
            chat={activeChat}
            settings={settings}
            onSendMessage={handleSendMessage}
            onRegenerate={() => {
              const userMsgs = activeChat.messages.filter((m) => m.sender === 'user');
              const lastUser = userMsgs[userMsgs.length - 1];
              if (lastUser) {
                handleSendMessage(lastUser.content);
              }
            }}
            onStopGeneration={handleStopGeneration}
            onClearChat={handleClearChat}
            onTogglePin={() => handleTogglePinChat(activeChat.id)}
            isGenerating={isGenerating}
          />
        )}

        {activeTab === 'model' && <ModelPanel />}
      </main>

      {/* Modals */}
      {showSettingsModal && (
        <SettingsModal
          settings={settings}
          onUpdateSettings={(newSet) => setSettings((prev) => ({ ...prev, ...newSet }))}
          onResetSettings={() => setSettings(DEFAULT_SETTINGS)}
          onClose={() => setShowSettingsModal(false)}
        />
      )}

      {showShortcutsModal && (
        <ShortcutsModal onClose={() => setShowShortcutsModal(false)} />
      )}

      {showExportModal && (
        <ExportModal
          chat={activeChat}
          onImportChat={handleImportChat}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
}
