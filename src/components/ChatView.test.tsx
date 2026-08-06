import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatView } from './ChatView';
import { Chat, Settings } from '../types';

const mockSettings: Settings = {
  theme: 'dark',
  model: 'nexa-v1.1.2-7b-instruct',
  temperature: 0.7,
  maxTokens: 2048,
  systemPrompt: 'You are NEXA AI Assistant.',
  streamResponse: true,
  autosave: true,
  apiEndpoint: 'http://localhost:3000/api',
  fastapiEndpoint: 'http://localhost:8000',
  customApiKey: '',
  memoryEnabled: true,
  ragEnabled: true,
  topP: 0.9,
  frequencyPenalty: 0,
  presencePenalty: 0
};

const mockChat: Chat = {
  id: 'chat-test-1',
  title: 'Test Chat Room',
  isPinned: false,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  messages: [
    {
      id: 'msg-1',
      sender: 'assistant',
      content: 'Hello! How can I assist you today?',
      timestamp: '10:00 AM',
      tokens: 8
    }
  ]
};

describe('ChatView Component', () => {
  it('renders chat title and initial assistant message', () => {
    render(
      <ChatView
        chat={mockChat}
        settings={mockSettings}
        onSendMessage={vi.fn()}
        onRegenerate={vi.fn()}
        onStopGeneration={vi.fn()}
        onClearChat={vi.fn()}
        onTogglePin={vi.fn()}
        isGenerating={false}
      />
    );

    expect(screen.getByText('Test Chat Room')).toBeInTheDocument();
    expect(screen.getByText('Hello! How can I assist you today?')).toBeInTheDocument();
  });

  it('triggers onSendMessage when user types and submits message', () => {
    const handleSendMessage = vi.fn();
    render(
      <ChatView
        chat={mockChat}
        settings={mockSettings}
        onSendMessage={handleSendMessage}
        onRegenerate={vi.fn()}
        onStopGeneration={vi.fn()}
        onClearChat={vi.fn()}
        onTogglePin={vi.fn()}
        isGenerating={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask NEXA Assistant/i);
    fireEvent.change(textarea, { target: { value: 'Explain quantum computing' } });

    const submitBtn = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(submitBtn);

    expect(handleSendMessage).toHaveBeenCalledWith('Explain quantum computing');
  });

  it('shows stop generation button when isGenerating is true', () => {
    const handleStop = vi.fn();
    render(
      <ChatView
        chat={mockChat}
        settings={mockSettings}
        onSendMessage={vi.fn()}
        onRegenerate={vi.fn()}
        onStopGeneration={handleStop}
        onClearChat={vi.fn()}
        onTogglePin={vi.fn()}
        isGenerating={true}
      />
    );

    const stopButton = screen.getByText('Stop');
    expect(stopButton).toBeInTheDocument();
    fireEvent.click(stopButton);
    expect(handleStop).toHaveBeenCalled();
  });
});
