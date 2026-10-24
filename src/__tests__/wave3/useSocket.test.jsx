import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const auth = vi.hoisted(() => ({ token: 'jwt-1' }));
const ioMock = vi.hoisted(() => vi.fn());

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ token: auth.token }),
}));

vi.mock('socket.io-client', () => ({
  io: (...args) => ioMock(...args),
}));

import { HEARTBEAT_INTERVAL_MS, useSocket } from '../../hooks/useSocket';

function createFakeSocket() {
  const listeners = new Map();
  const emitted = [];

  return {
    connected: false,
    emitted,
    connect: vi.fn(),
    disconnect: vi.fn(function disconnect() {
      this.connected = false;
    }),
    on: vi.fn((event, listener) => {
      listeners.set(event, [...(listeners.get(event) || []), listener]);
    }),
    off: vi.fn((event, listener) => {
      listeners.set(event, (listeners.get(event) || []).filter((fn) => fn !== listener));
    }),
    removeAllListeners: vi.fn(() => listeners.clear()),
    emit: vi.fn(function emit(event, data) {
      emitted.push([event, data]);
    }),
    trigger(event, data) {
      if (event === 'connect') this.connected = true;
      if (event === 'disconnect') this.connected = false;
      (listeners.get(event) || []).forEach((listener) => listener(data));
    },
    listenerCount: (event) => (listeners.get(event) || []).length,
  };
}

const mounted = [];

function mount(roomId, handlers) {
  const view = renderHook(() => useSocket(roomId, handlers));
  mounted.push(view);
  return view;
}

beforeEach(() => {
  auth.token = 'jwt-1';
  ioMock.mockReset();
});

afterEach(() => {
  mounted.forEach(({ unmount }) => unmount());
  mounted.length = 0;
  vi.useRealTimers();
});

describe('useSocket', () => {
  it('never creates a socket without a token and room', () => {
    auth.token = null;
    const { result } = mount('user:1', {});

    expect(ioMock).not.toHaveBeenCalled();
    expect(result.current.connected).toBe(false);
    expect(result.current.emit('order:created', { id: 1 })).toBe(false);
  });

  it('connects with JWT auth, joins the room, and heartbeats every 25s', () => {
    vi.useFakeTimers();
    const socket = createFakeSocket();
    ioMock.mockReturnValue(socket);

    const { result } = mount('user:42', {});
    expect(ioMock).toHaveBeenCalledWith(
      'http://localhost:5000',
      expect.objectContaining({
        autoConnect: false,
        auth: { token: 'jwt-1' },
        reconnectionDelay: 1000,
        reconnectionDelayMax: 30000,
      })
    );
    expect(socket.connect).toHaveBeenCalledTimes(1);
    expect(result.current.connected).toBe(false);

    act(() => socket.trigger('connect'));

    expect(result.current.connected).toBe(true);
    expect(socket.emitted).toContainEqual(['join-room', 'user:42']);
    expect(result.current.emit('order:created', { id: 7 })).toBe(true);
    expect(socket.emitted).toContainEqual(['order:created', { id: 7 }]);

    act(() => vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS));
    const heartbeats = socket.emitted.filter(([event]) => event === 'system:heartbeat');
    expect(heartbeats).toHaveLength(1);
    expect(heartbeats[0][1]).toEqual({ at: expect.any(Number) });
  });

  it('clears the connection and heartbeat on disconnect, then re-joins on reconnect', () => {
    vi.useFakeTimers();
    const socket = createFakeSocket();
    ioMock.mockReturnValue(socket);
    const { result } = mount('org:7', {});

    act(() => socket.trigger('connect'));
    act(() => socket.trigger('disconnect'));

    expect(result.current.connected).toBe(false);
    act(() => vi.advanceTimersByTime(HEARTBEAT_INTERVAL_MS * 2));
    expect(socket.emitted.filter(([event]) => event === 'system:heartbeat')).toHaveLength(0);

    act(() => socket.trigger('connect'));
    expect(result.current.connected).toBe(true);
    expect(socket.emitted.filter(([event]) => event === 'join-room')).toHaveLength(2);
  });

  it('leaves the room and tears the socket down on unmount', () => {
    const socket = createFakeSocket();
    ioMock.mockReturnValue(socket);
    const { unmount } = mount('order:1234', {});

    act(() => socket.trigger('connect'));
    unmount();

    expect(socket.emitted).toContainEqual(['leave-room', 'order:1234']);
    expect(socket.removeAllListeners).toHaveBeenCalled();
    expect(socket.disconnect).toHaveBeenCalled();
  });

  it('shares one socket between consumers and disconnects only after the last one leaves', () => {
    const socket = createFakeSocket();
    ioMock.mockReturnValue(socket);

    const first = mount('user:1', {});
    const second = mount('user:1', {});
    expect(ioMock).toHaveBeenCalledTimes(1);

    act(() => socket.trigger('connect'));
    first.unmount();
    expect(socket.disconnect).not.toHaveBeenCalled();

    second.unmount();
    expect(socket.disconnect).toHaveBeenCalledTimes(1);
  });

  it('routes events to the latest handlers without re-subscribing', () => {
    const socket = createFakeSocket();
    ioMock.mockReturnValue(socket);
    const firstHandler = vi.fn();
    const secondHandler = vi.fn();

    const { rerender, unmount } = renderHook(
      ({ handlers }) => useSocket('user:1', handlers),
      { initialProps: { handlers: { 'order:created': firstHandler } } }
    );
    mounted.push({ unmount });

    act(() => socket.trigger('order:created', { id: 1 }));
    expect(firstHandler).toHaveBeenCalledWith({ id: 1 });

    rerender({ handlers: { 'order:created': secondHandler } });
    act(() => socket.trigger('order:created', { id: 2 }));

    expect(secondHandler).toHaveBeenCalledWith({ id: 2 });
    expect(firstHandler).toHaveBeenCalledTimes(1);
    expect(socket.listenerCount('order:created')).toBe(1);
  });
});
