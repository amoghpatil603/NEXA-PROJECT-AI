export interface Message {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tokens?: number;
  generationTime?: number;
  tokensPerSec?: number;
  isStreaming?: boolean;
  isEdited?: boolean;
}

export interface Chat {
  id: string;
  title: string;
  isPinned: boolean;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

export interface Settings {
  temperature: number;
  top_k: number;
  top_p: number;
  max_new_tokens: number;
  theme: 'dark' | 'light' | 'emerald';
  fontSize: 'small' | 'medium' | 'large';
  systemPrompt: string;
  autosave: boolean;
}

export interface ModelInfo {
  model_name: string;
  checkpoint: string;
  vocab_size: string;
  parameters: string;
  context_length: string;
  device: string;
  memory_usage: string;
  architecture: string;
  status: string;
  inference_time?: number;
  tokens_per_sec?: number;
}

export interface WindowState {
  activeTab: 'chat' | 'model' | 'settings';
  sidebarOpen: boolean;
  activeChatId: string;
  showShortcutsModal: boolean;
  showExportModal: boolean;
  showSettingsModal: boolean;
}
