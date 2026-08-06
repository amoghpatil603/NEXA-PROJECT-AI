import { create } from 'zustand';
import { Chat, Message, Settings, WindowState } from '../types';
import { 
  loadChats, 
  saveChats, 
  loadSettings, 
  saveSettings, 
  DEFAULT_SETTINGS, 
  DEFAULT_CHAT 
} from '../utils/localStorage';
import { wsClient, WSStatus } from '../utils/websocketClient';

export interface UserSession {
  id: string;
  name: string;
  email: string;
  role: string;
  isAuthenticated: boolean;
}

export interface StudioAgent {
  id: string;
  name: string;
  status: string;
  tasks_completed?: number;
  database?: string;
  mode?: string;
  active_sockets?: number;
}

export interface TelemetryData {
  ram_usage_mb: number;
  cpu_usage_pct: number;
  active_connections: number;
  queue_length: number;
  total_inferences_completed: number;
  tokens_per_sec: number;
  inference_time_sec?: number;
  timestamp?: string;
}

export interface LogEntry {
  id: string;
  msg: string;
  time: string;
  type: string;
}

export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
}

export interface UploadedImage {
  id: string;
  url: string;
  name: string;
  timestamp: string;
}

export interface ChatSlice {
  chats: Chat[];
  activeChatId: string;
  isGenerating: boolean;
  setChats: (chats: Chat[] | ((prev: Chat[]) => Chat[])) => void;
  setActiveChatId: (id: string) => void;
  setIsGenerating: (isGenerating: boolean) => void;
  newChat: () => void;
  renameChat: (id: string, newTitle: string) => void;
  deleteChat: (id: string) => void;
  togglePinChat: (id: string) => void;
  clearChat: () => void;
  importChat: (chat: Chat) => void;
}

export interface SessionSlice {
  user: UserSession;
  activeTab: 'chat' | 'model' | 'settings' | 'studio';
  showShortcutsModal: boolean;
  showExportModal: boolean;
  showSettingsModal: boolean;
  sidebarOpen: boolean;
  setUser: (user: UserSession) => void;
  setActiveTab: (tab: 'chat' | 'model' | 'settings' | 'studio') => void;
  setShowShortcutsModal: (show: boolean) => void;
  setShowExportModal: (show: boolean) => void;
  setShowSettingsModal: (show: boolean) => void;
  toggleSidebar: () => void;
}

export interface WSSlice {
  wsStatus: WSStatus;
  wsClientId: string | null;
  latencyMs: number;
  setWsStatus: (status: WSStatus) => void;
  setWsClientId: (clientId: string) => void;
  setLatencyMs: (ms: number) => void;
}

export interface StudioSlice {
  activeStudioPage: string;
  agents: StudioAgent[];
  setActiveStudioPage: (page: string) => void;
  setAgents: (agents: StudioAgent[]) => void;
}

export interface MonitoringSlice {
  telemetry: TelemetryData;
  logs: LogEntry[];
  setTelemetry: (data: Partial<TelemetryData>) => void;
  addLog: (msg: string, type?: string) => void;
  clearLogs: () => void;
}

export interface VoiceSlice {
  isRecording: boolean;
  interimTranscript: string;
  lastVoiceResponse: string | null;
  setIsRecording: (recording: boolean) => void;
  setInterimTranscript: (text: string) => void;
  setLastVoiceResponse: (response: string | null) => void;
}

export interface VisionSlice {
  uploadedImages: UploadedImage[];
  visionAnalysis: string | null;
  isAnalyzing: boolean;
  addUploadedImage: (img: UploadedImage) => void;
  removeUploadedImage: (id: string) => void;
  setVisionAnalysis: (analysis: string | null) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
}

export interface NotificationsSlice {
  notifications: NotificationItem[];
  addNotification: (message: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export interface SettingsSlice {
  settings: Settings;
  updateSettings: (newSet: Partial<Settings>) => void;
  resetSettings: () => void;
}

export type NexaStore = ChatSlice &
  SessionSlice &
  WSSlice &
  StudioSlice &
  MonitoringSlice &
  VoiceSlice &
  VisionSlice &
  NotificationsSlice &
  SettingsSlice;

const initialChats = loadChats();
const initialSettings = loadSettings();

export const useNexaStore = create<NexaStore>((set, get) => ({
  // --- Chat Slice ---
  chats: initialChats,
  activeChatId: initialChats[0]?.id || 'default-chat-1',
  isGenerating: false,

  setChats: (chatsOrFn) => {
    set((state) => {
      const newChats = typeof chatsOrFn === 'function' ? chatsOrFn(state.chats) : chatsOrFn;
      if (state.settings.autosave) {
        saveChats(newChats);
      }
      return { chats: newChats };
    });
  },

  setActiveChatId: (id) => set({ activeChatId: id }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),

  newChat: () => {
    const newId = `chat-${Date.now()}`;
    const newChatObj: Chat = {
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

    set((state) => {
      const updated = [newChatObj, ...state.chats];
      if (state.settings.autosave) saveChats(updated);
      return {
        chats: updated,
        activeChatId: newId,
        activeTab: 'chat'
      };
    });
  },

  renameChat: (id, newTitle) => {
    set((state) => {
      const updated = state.chats.map((c) =>
        c.id === id ? { ...c, title: newTitle, updatedAt: new Date().toISOString() } : c
      );
      if (state.settings.autosave) saveChats(updated);
      return { chats: updated };
    });
  },

  deleteChat: (id) => {
    set((state) => {
      if (state.chats.length <= 1) {
        // Reset single remaining chat
        const resetChat: Chat = {
          ...state.chats[0],
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
        };
        const updated = [resetChat];
        if (state.settings.autosave) saveChats(updated);
        return { chats: updated };
      }

      const filtered = state.chats.filter((c) => c.id !== id);
      const nextActiveId = state.activeChatId === id ? filtered[0].id : state.activeChatId;
      if (state.settings.autosave) saveChats(filtered);
      return { chats: filtered, activeChatId: nextActiveId };
    });
  },

  togglePinChat: (id) => {
    set((state) => {
      const updated = state.chats.map((c) =>
        c.id === id ? { ...c, isPinned: !c.isPinned } : c
      );
      if (state.settings.autosave) saveChats(updated);
      return { chats: updated };
    });
  },

  clearChat: () => {
    set((state) => {
      const updated = state.chats.map((c) =>
        c.id === state.activeChatId
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
      );
      if (state.settings.autosave) saveChats(updated);
      return { chats: updated };
    });
  },

  importChat: (importedChat) => {
    set((state) => {
      const updated = [importedChat, ...state.chats];
      if (state.settings.autosave) saveChats(updated);
      return {
        chats: updated,
        activeChatId: importedChat.id,
        activeTab: 'chat'
      };
    });
  },

  // --- Session Slice ---
  user: {
    id: 'usr-admin-1',
    name: 'NEXA Architect',
    email: 'architect@nexa.ai',
    role: 'Lead AI Engineer',
    isAuthenticated: true
  },
  activeTab: 'chat',
  showShortcutsModal: false,
  showExportModal: false,
  showSettingsModal: false,
  sidebarOpen: true,

  setUser: (user) => set({ user }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setShowShortcutsModal: (showShortcutsModal) => set({ showShortcutsModal }),
  setShowExportModal: (showExportModal) => set({ showExportModal }),
  setShowSettingsModal: (showSettingsModal) => set({ showSettingsModal }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // --- WebSocket Slice ---
  wsStatus: wsClient.getStatus(),
  wsClientId: null,
  latencyMs: 12,
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setWsClientId: (wsClientId) => set({ wsClientId }),
  setLatencyMs: (latencyMs) => set({ latencyMs }),

  // --- Studio Slice ---
  activeStudioPage: 'dashboard',
  agents: [
    { id: 'agent-planner', name: 'Goal Planner Agent', status: 'ONLINE', tasks_completed: 42 },
    { id: 'agent-memory', name: 'Memory Engine Agent', status: 'ONLINE', database: 'PostgreSQL pgvector' },
    { id: 'agent-rag', name: 'RAG Engine Agent', status: 'ONLINE', mode: 'Vector Search Active' },
    { id: 'agent-exec', name: 'Execution Engine Agent', status: 'IDLE' },
    { id: 'agent-ws', name: 'WebSocket Stream Manager', status: 'ONLINE', active_sockets: 1 }
  ],
  setActiveStudioPage: (activeStudioPage) => set({ activeStudioPage }),
  setAgents: (agents) => set({ agents }),

  // --- Monitoring Slice ---
  telemetry: {
    ram_usage_mb: 142,
    cpu_usage_pct: 15,
    active_connections: 1,
    queue_length: 0,
    total_inferences_completed: 0,
    tokens_per_sec: 78.5
  },
  logs: [
    {
      id: 'init-1',
      msg: 'WebSocket Production Server Listening on ws://0.0.0.0:3000/ws',
      time: new Date().toLocaleTimeString(),
      type: 'INFO'
    }
  ],
  setTelemetry: (data) =>
    set((state) => ({
      telemetry: { ...state.telemetry, ...data }
    })),
  addLog: (msg, type = 'EVENT') =>
    set((state) => ({
      logs: [
        {
          id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
          msg,
          time: new Date().toLocaleTimeString(),
          type
        },
        ...state.logs.slice(0, 49)
      ]
    })),
  clearLogs: () => set({ logs: [] }),

  // --- Voice Slice ---
  isRecording: false,
  interimTranscript: '',
  lastVoiceResponse: null,
  setIsRecording: (isRecording) => set({ isRecording }),
  setInterimTranscript: (interimTranscript) => set({ interimTranscript }),
  setLastVoiceResponse: (lastVoiceResponse) => set({ lastVoiceResponse }),

  // --- Vision Slice ---
  uploadedImages: [],
  visionAnalysis: null,
  isAnalyzing: false,
  addUploadedImage: (img) => set((state) => ({ uploadedImages: [img, ...state.uploadedImages] })),
  removeUploadedImage: (id) =>
    set((state) => ({ uploadedImages: state.uploadedImages.filter((i) => i.id !== id) })),
  setVisionAnalysis: (visionAnalysis) => set({ visionAnalysis }),
  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  // --- Notifications Slice ---
  notifications: [],
  addNotification: (message, type = 'info') =>
    set((state) => ({
      notifications: [
        {
          id: `notif-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
          type,
          message,
          timestamp: new Date().toLocaleTimeString()
        },
        ...state.notifications
      ]
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id)
    })),
  clearNotifications: () => set({ notifications: [] }),

  // --- Settings Slice ---
  settings: initialSettings,
  updateSettings: (newSet) =>
    set((state) => {
      const updated = { ...state.settings, ...newSet };
      saveSettings(updated);
      return { settings: updated };
    }),
  resetSettings: () => {
    saveSettings(DEFAULT_SETTINGS);
    set({ settings: DEFAULT_SETTINGS });
  }
}));

// Automatic WebSocket Sync Hook Listener
if (typeof window !== 'undefined') {
  wsClient.onStatusChange((status) => {
    useNexaStore.getState().setWsStatus(status);
  });

  wsClient.subscribe('studio_event', (event) => {
    if (event.event_type === 'telemetry') {
      useNexaStore.getState().setTelemetry(event.data);
    } else if (event.event_type === 'agent_progress' && event.data?.agents) {
      useNexaStore.getState().setAgents(event.data.agents);
    } else if (event.event_type === 'notification' && event.data?.message) {
      useNexaStore.getState().addLog(event.data.message, 'EVENT');
      useNexaStore.getState().addNotification(event.data.message, 'info');
    }
  });
}
