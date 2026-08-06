import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AgentManager } from './AgentManager';

describe('AgentManager Studio Page', () => {
  it('renders Agent Mesh Fleet status and active agents', () => {
    render(<AgentManager />);
    expect(screen.getByText(/Multi-Agent Framework Manager/i)).toBeInTheDocument();
    expect(screen.getByText('Goal Planner Agent')).toBeInTheDocument();
    expect(screen.getByText('Memory Engine Agent')).toBeInTheDocument();
    expect(screen.getByText('RAG Engine Agent')).toBeInTheDocument();
  });
});
