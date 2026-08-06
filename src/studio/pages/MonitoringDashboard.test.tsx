import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { MonitoringDashboard } from './MonitoringDashboard';
import { useNexaStore } from '../../store';

describe('MonitoringDashboard Studio Page', () => {
  beforeEach(() => {
    useNexaStore.getState().setTelemetry({
      ram_usage_mb: 250,
      cpu_usage_pct: 18,
      active_connections: 3,
      tokens_per_sec: 85.2
    });
    useNexaStore.getState().addLog('Monitoring telemetry initialized', 'INFO');
  });

  it('renders telemetry indicators and system log stream', () => {
    render(<MonitoringDashboard />);
    expect(screen.getByText(/Real-Time Telemetry & Monitoring/i)).toBeInTheDocument();
    expect(screen.getByText('250 MB')).toBeInTheDocument();
    expect(screen.getByText('18%')).toBeInTheDocument();
    expect(screen.getByText('Monitoring telemetry initialized')).toBeInTheDocument();
  });
});
