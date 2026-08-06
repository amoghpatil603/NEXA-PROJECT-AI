import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Dashboard } from './Dashboard';

describe('Dashboard Studio Page', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/health')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'ok' })
        });
      }
      if (url.includes('/api/system/status')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ cpu_usage_pct: 12, ram_usage_mb: 180 })
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ model: 'nexa-v1.1.2-7b' })
      });
    }) as any;
  });

  it('renders NEXA Command Center header and KPI metrics', async () => {
    render(<Dashboard />);
    expect(screen.getByText('NEXA Command Center')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('OPTIMAL')).toBeInTheDocument();
    });
  });
});
