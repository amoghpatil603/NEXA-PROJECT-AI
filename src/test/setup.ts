import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

Element.prototype.scrollIntoView = vi.fn();

class MockWebSocket {
  readyState = 1;
  onopen: any = null;
  onclose: any = null;
  onerror: any = null;
  onmessage: any = null;
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn();
  send = vi.fn();
  close = vi.fn();
}

global.WebSocket = MockWebSocket as any;
if (typeof window !== 'undefined') {
  (window as any).WebSocket = MockWebSocket;
}

afterEach(() => {
  cleanup();
});
