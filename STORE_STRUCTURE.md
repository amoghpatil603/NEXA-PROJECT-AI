# NEXA Store Structure & Slice Specification

## Store File Location

- `src/store/useNexaStore.ts` — Core Zustand store definition
- `src/store/index.ts` — Unified export entry point

---

## Slice Breakdown

### 1. Chat Slice (`ChatSlice`)
- **State**:
  - `chats`: `Chat[]`
  - `activeChatId`: `string`
  - `isGenerating`: `boolean`
- **Actions**:
  - `setChats(chats)`
  - `setActiveChatId(id)`
  - `setIsGenerating(boolean)`
  - `newChat()`
  - `renameChat(id, title)`
  - `deleteChat(id)`
  - `togglePinChat(id)`
  - `clearChat()`
  - `importChat(chat)`

### 2. Session Slice (`SessionSlice`)
- **State**:
  - `user`: `UserSession`
  - `activeTab`: `'chat' | 'model' | 'settings' | 'studio'`
  - `showShortcutsModal`: `boolean`
  - `showExportModal`: `boolean`
  - `showSettingsModal`: `boolean`
  - `sidebarOpen`: `boolean`
- **Actions**:
  - `setUser(user)`
  - `setActiveTab(tab)`
  - `setShowShortcutsModal(bool)`
  - `setShowExportModal(bool)`
  - `setShowSettingsModal(bool)`
  - `toggleSidebar()`

### 3. WebSocket Slice (`WSSlice`)
- **State**:
  - `wsStatus`: `WSStatus` (`'connecting' | 'connected' | 'reconnecting' | 'disconnected'`)
  - `wsClientId`: `string | null`
  - `latencyMs`: `number`
- **Actions**:
  - `setWsStatus(status)`
  - `setWsClientId(clientId)`
  - `setLatencyMs(ms)`

### 4. Studio Slice (`StudioSlice`)
- **State**:
  - `activeStudioPage`: `string`
  - `agents`: `StudioAgent[]`
- **Actions**:
  - `setActiveStudioPage(page)`
  - `setAgents(agents)`

### 5. Monitoring Slice (`MonitoringSlice`)
- **State**:
  - `telemetry`: `TelemetryData`
  - `logs`: `LogEntry[]`
- **Actions**:
  - `setTelemetry(data)`
  - `addLog(msg, type)`
  - `clearLogs()`

### 6. Voice Slice (`VoiceSlice`)
- **State**:
  - `isRecording`: `boolean`
  - `interimTranscript`: `string`
  - `lastVoiceResponse`: `string | null`
- **Actions**:
  - `setIsRecording(bool)`
  - `setInterimTranscript(text)`
  - `setLastVoiceResponse(response)`

### 7. Vision Slice (`VisionSlice`)
- **State**:
  - `uploadedImages`: `UploadedImage[]`
  - `visionAnalysis`: `string | null`
  - `isAnalyzing`: `boolean`
- **Actions**:
  - `addUploadedImage(img)`
  - `removeUploadedImage(id)`
  - `setVisionAnalysis(text)`
  - `setIsAnalyzing(bool)`

### 8. Notifications Slice (`NotificationsSlice`)
- **State**:
  - `notifications`: `NotificationItem[]`
- **Actions**:
  - `addNotification(msg, type)`
  - `removeNotification(id)`
  - `clearNotifications()`

### 9. Settings Slice (`SettingsSlice`)
- **State**:
  - `settings`: `Settings`
- **Actions**:
  - `updateSettings(newSet)`
  - `resetSettings()`
