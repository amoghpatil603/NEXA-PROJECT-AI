import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ChatWindow } from '../../ChatWindow';

describe('ChatWindow Desktop Component', () => {
  it('renders chat-container wrapper element', () => {
    const { container } = render(<ChatWindow />);
    const div = container.querySelector('.chat-container');
    expect(div).toBeInTheDocument();
  });
});
