import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VoiceRecorder } from './VoiceRecorder';
import { useNexaStore } from '../store';

describe('VoiceRecorder Component', () => {
  beforeEach(() => {
    useNexaStore.getState().setIsRecording(false);
    delete (window as any).webkitSpeechRecognition;
    delete (window as any).SpeechRecognition;
  });

  it('renders Voice Not Supported when SpeechRecognition is not available', () => {
    render(<VoiceRecorder onTranscript={vi.fn()} />);
    const button = screen.getByTitle('Voice Not Supported');
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it('renders interactive mic button when SpeechRecognition is mocked', async () => {
    const mockStart = vi.fn();
    const mockStop = vi.fn();
    function MockSpeechRecognition() {
      (this as any).start = mockStart;
      (this as any).stop = mockStop;
      (this as any).continuous = true;
      (this as any).interimResults = true;
    }
    (window as any).webkitSpeechRecognition = MockSpeechRecognition;
    (window as any).SpeechRecognition = MockSpeechRecognition;

    render(<VoiceRecorder onTranscript={vi.fn()} />);
    const button = await screen.findByTitle('Start Voice Dictation');
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(useNexaStore.getState().isRecording).toBe(true);
    expect(mockStart).toHaveBeenCalled();
  });
});
