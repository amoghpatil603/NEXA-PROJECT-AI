import { Chat, Settings, WindowState } from '../types';

const STORAGE_KEYS = {
  CHATS: 'nexa_phase5b_chats',
  SETTINGS: 'nexa_phase5b_settings',
  WINDOW_STATE: 'nexa_phase5b_window_state',
};

export const DEFAULT_SETTINGS: Settings = {
  temperature: 0.7,
  top_k: 50,
  top_p: 0.9,
  max_new_tokens: 128,
  theme: 'dark',
  fontSize: 'medium',
  systemPrompt: 'You are NEXA, an advanced AI desktop assistant powered by an 8K BPE Transformer model.',
  autosave: true,
};

export const DEFAULT_CHAT: Chat = {
  id: 'default-chat-1',
  title: 'Welcome to NEXA Desktop',
  isPinned: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  messages: [
    {
      id: 'msg-init-1',
      sender: 'assistant',
      content: 'Hello! I am **NEXA Desktop AI Assistant**, powered by the optimized 8K BPE NexaTransformer model.\n\nHere is what I can do:\n- **Streaming responses** with character animation\n- **Markdown & Code block rendering** with copy functionality\n- **Multiple Chat Sessions** with pin, rename, & export\n- **Model Telemetry Panel** for live parameter tracking\n- **Keyboard Shortcuts** (`Ctrl+Enter`, `Ctrl+L`, `Ctrl+N`, `Esc`)\n\nHow can I assist you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      tokens: 48
    }
  ]
};

export function loadChats(): Chat[] {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.CHATS);
    if (data) {
      const parsed = JSON.parse(data);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.error('Failed to load chats from local storage', e);
  }
  return [DEFAULT_CHAT];
}

export function saveChats(chats: Chat[]): void {
  try {
    localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(chats));
  } catch (e) {
    console.error('Failed to save chats to local storage', e);
  }
}

export function loadSettings(): Settings {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
    if (data) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(data) };
    }
  } catch (e) {
    console.error('Failed to load settings from local storage', e);
  }
  return DEFAULT_SETTINGS;
}

export function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
  } catch (e) {
    console.error('Failed to save settings to local storage', e);
  }
}

export function loadWindowState(): Partial<WindowState> {
  try {
    const data = localStorage.getItem(STORAGE_KEYS.WINDOW_STATE);
    if (data) return JSON.parse(data);
  } catch (e) {
    console.error('Failed to load window state', e);
  }
  return {};
}

export function saveWindowState(state: Partial<WindowState>): void {
  try {
    localStorage.setItem(STORAGE_KEYS.WINDOW_STATE, JSON.stringify(state));
  } catch (e) {
    console.error('Failed to save window state', e);
  }
}
