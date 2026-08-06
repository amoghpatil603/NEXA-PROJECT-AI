import { describe, it, expect, beforeEach } from 'vitest';
import { useNexaStore } from './useNexaStore';

describe('useNexaStore (Centralized Zustand Store)', () => {
  beforeEach(() => {
    useNexaStore.getState().resetSettings();
  });

  it('initializes with default session and chat values', () => {
    const state = useNexaStore.getState();
    expect(state.activeTab).toBe('chat');
    expect(state.chats.length).toBeGreaterThan(0);
    expect(state.user.isAuthenticated).toBe(true);
    expect(state.isGenerating).toBe(false);
  });

  it('creates a new chat session via newChat()', () => {
    const initialCount = useNexaStore.getState().chats.length;
    useNexaStore.getState().newChat();
    const updatedChats = useNexaStore.getState().chats;
    expect(updatedChats.length).toBe(initialCount + 1);
    expect(updatedChats[0].title).toBe('New Conversation');
    expect(useNexaStore.getState().activeTab).toBe('chat');
  });

  it('renames an existing chat session via renameChat()', () => {
    const activeId = useNexaStore.getState().activeChatId;
    useNexaStore.getState().renameChat(activeId, 'Updated Title Test');
    const updated = useNexaStore.getState().chats.find((c) => c.id === activeId);
    expect(updated?.title).toBe('Updated Title Test');
  });

  it('deletes a chat session or resets if single chat remaining', () => {
    useNexaStore.getState().newChat();
    const activeId = useNexaStore.getState().activeChatId;
    const prevCount = useNexaStore.getState().chats.length;

    useNexaStore.getState().deleteChat(activeId);
    expect(useNexaStore.getState().chats.length).toBe(prevCount - 1);
  });

  it('updates settings and resets settings correctly', () => {
    useNexaStore.getState().updateSettings({ theme: 'emerald', temperature: 0.9 });
    expect(useNexaStore.getState().settings.theme).toBe('emerald');
    expect(useNexaStore.getState().settings.temperature).toBe(0.9);

    useNexaStore.getState().resetSettings();
    expect(useNexaStore.getState().settings.theme).toBe('dark');
  });

  it('handles telemetry updates and log entries in MonitoringSlice', () => {
    useNexaStore.getState().setTelemetry({ cpu_usage_pct: 42, ram_usage_mb: 256 });
    expect(useNexaStore.getState().telemetry.cpu_usage_pct).toBe(42);
    expect(useNexaStore.getState().telemetry.ram_usage_mb).toBe(256);

    useNexaStore.getState().addLog('Test log entry', 'INFO');
    const logs = useNexaStore.getState().logs;
    expect(logs[0].msg).toBe('Test log entry');
  });

  it('handles voice and vision state slice modifications', () => {
    useNexaStore.getState().setIsRecording(true);
    expect(useNexaStore.getState().isRecording).toBe(true);

    useNexaStore.getState().setVisionAnalysis('Extracted text sample');
    expect(useNexaStore.getState().visionAnalysis).toBe('Extracted text sample');
  });
});
