import React, { useEffect, useRef } from 'react';
import { Chat, Message } from './types';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/ChatView';
import { ModelPanel } from './components/ModelPanel';
import { SettingsModal } from './components/SettingsModal';
import { ShortcutsModal } from './components/ShortcutsModal';
import { ExportModal } from './components/ExportModal';
import { StudioMain } from './studio/StudioMain';
import { wsClient } from './utils/websocketClient';
import { useNexaStore } from './store';

export default function App() {
  const {
    chats,
    activeChatId,
    settings,
    activeTab,
    isGenerating,
    showShortcutsModal,
    showExportModal,
    showSettingsModal,
    setChats,
    setActiveChatId,
    setIsGenerating,
    setActiveTab,
    setShowShortcutsModal,
    setShowExportModal,
    setShowSettingsModal,
    newChat: handleNewChat,
    renameChat: handleRenameChat,
    deleteChat: handleDeleteChat,
    togglePinChat: handleTogglePinChat,
    clearChat: handleClearChat,
    importChat: handleImportChat,
    updateSettings,
    resetSettings
  } = useNexaStore();

  const abortControllerRef = useRef<AbortController | null>(null);

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0] || {
    id: 'temp',
    title: 'New Conversation',
    isPinned: false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: []
  };

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

    const historyPayload = updatedMessages
      .filter((m) => m.sender !== 'system' && m.id !== assistantMsgId)
      .map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.content
      }));

    // WebSocket Real-Time Chat Streaming
    if (wsClient.getStatus() === 'connected') {
      const requestId = `ws-req-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
      wsClient.streamChat(
        {
          request_id: requestId,
          message: text,
          system_prompt: settings.systemPrompt,
          history: historyPayload.slice(-6),
          max_tokens: settings.max_new_tokens,
          temperature: settings.temperature
        },
        (chunkData) => {
          const streamedText = chunkData.full || chunkData.chunk;
          setChats((prev) =>
            prev.map((c) => {
              if (c.id !== activeChatId) return c;
              const msgs = c.messages.map((m) =>
                m.id === assistantMsgId ? { ...m, content: streamedText } : m
              );
              return { ...c, messages: msgs };
            })
          );
        },
        (doneData) => {
          const finalFull = doneData.full || 'Response generation complete.';
          setChats((prev) =>
            prev.map((c) => {
              if (c.id !== activeChatId) return c;
              const msgs = c.messages.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: finalFull,
                      isStreaming: false,
                      generationTime: doneData.time_taken,
                      tokensPerSec: doneData.tokens_per_sec
                    }
                  : m
              );
              return { ...c, messages: msgs };
            })
          );
          setIsGenerating(false);
        },
        (err) => {
          console.warn('[NEXA WS] Stream error, falling back to HTTP SSE', err);
          thisFallbackSSE();
        }
      );
      return;
    }

    // Fallback SSE Stream over HTTP
    async function thisFallbackSSE() {
      try {
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: abortControllerRef.current?.signal,
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
    }

    thisFallbackSSE();
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
        {activeTab === 'studio' && <StudioMain />}
      </main>

      {/* Modals */}
      {showSettingsModal && (
        <SettingsModal
          settings={settings}
          onUpdateSettings={(newSet) => updateSettings(newSet)}
          onResetSettings={resetSettings}
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
