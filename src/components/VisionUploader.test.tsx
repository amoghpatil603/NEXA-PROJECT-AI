import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VisionUploader } from './VisionUploader';

describe('VisionUploader Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.URL.createObjectURL = vi.fn(() => 'blob:http://localhost/test-img');
  });

  it('renders paperclip button to upload vision/document file', () => {
    render(<VisionUploader onExtracted={vi.fn()} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('opens modal and handles file selection', () => {
    render(<VisionUploader onExtracted={vi.fn()} />);
    const file = new File(['test image content'], 'sample.png', { type: 'image/png' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByText('Vision & OCR')).toBeInTheDocument();
    expect(screen.getByText('Selected: sample.png')).toBeInTheDocument();
  });

  it('handles upload process and calls onExtracted callback', async () => {
    const handleExtracted = vi.fn();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ extracted_text: 'Extracted OCR text content from vision model.' })
    } as any);

    render(<VisionUploader onExtracted={handleExtracted} />);
    const file = new File(['test image content'], 'sample.png', { type: 'image/png' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    const processBtn = screen.getByText('Process File');
    fireEvent.click(processBtn);

    await waitFor(() => {
      expect(screen.getByText('Extracted OCR text content from vision model.')).toBeInTheDocument();
    });

    const insertBtn = screen.getByText('Insert Text into Chat');
    fireEvent.click(insertBtn);

    expect(handleExtracted).toHaveBeenCalledWith('Extracted OCR text content from vision model.');
  });
});
