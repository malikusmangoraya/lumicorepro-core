import { useEffect, useCallback, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../context/AuthContext';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/** Documented heartbeat (AGENTS.md §12) — one app-level pulse every 25 seconds. */
export const HEARTBEAT_INTERVAL_MS = 25000;
/** Reconnect backoff window: first retry after 1s, capped at 30s (AGENTS.md §12). */
export const RECONNECT_DELAY_MS = 1000;
export const RECONNECT_DELAY_MAX_MS = 30000;

/**
 * Wire events used by the hook itself. Domain events follow the same
 * `domain:action` convention (e.g. `order:created`, `order:updated`).
 * `join-room` / `leave-room` keep their existing names because
 * `backend/server.js` implements exactly those.
 */
export const SOCKET_EVENTS = {
  HEARTBEAT: 'system:heartbeat',
  JOIN_ROOM: 'join-room',
  LEAVE_ROOM: 'leave-room',
};

let sharedSocket = null;
let sharedSocketToken = null;
let consumers = 0;
let heartbeatId = null;

function stopHeartbeat() {
  if (heartbeatId !== null) {
    clearInterval(heartbeatId);
    heartbeatId = null;
  }
}

function startHeartbeat(socket) {
  stopHeartbeat();
  heartbeatId = setInterval(() => {
    if (socket.connected) socket.emit(SOCKET_EVENTS.HEARTBEAT, { at: Date.now() });
  }, HEARTBEAT_INTERVAL_MS);
}

/** One socket per token, shared by every mounted consumer. */
function acquireSocket(token) {
  if (sharedSocket && sharedSocketToken === token) {
    consumers += 1;
    return sharedSocket;
  }

  if (sharedSocket) {
    stopHeartbeat();
    sharedSocket.disconnect();
  }

  sharedSocket = io(SOCKET_URL, {
    autoConnect: false,
    // JWT travels in the handshake `auth` payload — the server verifies it before
    // the socket may join any room.
    auth: { token },
    reconnection: true,
    reconnectionDelay: RECONNECT_DELAY_MS,
    reconnectionDelayMax: RECONNECT_DELAY_MAX_MS,
    reconnectionAttempts: Infinity,
    // Transport liveness matching the documented 25s cadence; socket.io reconnects
    // automatically when the peer stops answering.
    pingInterval: HEARTBEAT_INTERVAL_MS,
    pingTimeout: 20000,
    transports: ['websocket', 'polling'],
  });
  sharedSocketToken = token;
  consumers = 1;

  // Heartbeat belongs to the socket, not to a component: one timer per connection,
  // started on connect and cleared on disconnect/teardown.
  sharedSocket.on('connect', () => startHeartbeat(sharedSocket));
  sharedSocket.on('disconnect', stopHeartbeat);

  return sharedSocket;
}

/** Drop the shared socket once the last consumer unmounts. */
function releaseSocket(socket) {
  consumers = Math.max(0, consumers - 1);
  if (consumers > 0 || !socket) return;

  stopHeartbeat();
  socket.removeAllListeners();
  socket.disconnect();
  if (sharedSocket === socket) {
    sharedSocket = null;
    sharedSocketToken = null;
  }
}

/**
 * useSocket — real-time Socket.io hook with JWT auth, heartbeat and backoff.
 *
 * Behaviour:
 *   - connects only when both a JWT and a room are available
 *   - joins `roomId` on connect and re-joins after every reconnect
 *   - emits `system:heartbeat` every 25s, cleared on disconnect and on teardown
 *   - reconnect backoff delegated to socket.io (1s → 30s, exponential)
 *   - the last unmounting consumer tears the socket down
 *
 * Event handlers are read through a ref, so callers can pass an inline object
 * without exposing a stale closure or re-subscribing on every render.
 *
 * @param {string} roomId — room to join (e.g. `user:42`, `org:7`, `order:1234`)
 * @param {Record<string, Function>} eventHandlers — namespaced event name → callback
 * @returns {{ connected: boolean, emit: (event: string, data?: unknown) => boolean }}
 *
 * @example
 * const { connected, emit } = useSocket(`user:${userId}`, {
 *   'order:created': (data) => toast(data.message),
 *   'order:updated': (data) => refetchOrder(data.orderId),
 * });
 */
export function useSocket(roomId, eventHandlers = {}) {
  const { token } = useAuth();
  const [connected, setConnected] = useState(false);

  const handlersRef = useRef(eventHandlers);
  handlersRef.current = eventHandlers;

  useEffect(() => {
    if (!token || !roomId) {
      setConnected(false);
      return undefined;
    }

    const socket = acquireSocket(token);
    let disposed = false;

    const handleConnect = () => {
      if (disposed) return;
      setConnected(true);
      socket.emit(SOCKET_EVENTS.JOIN_ROOM, roomId);
    };

    const handleDisconnect = () => {
      if (!disposed) setConnected(false);
    };

    // Stable listeners that resolve the current handler from the ref.
    const boundHandlers = Object.keys(handlersRef.current).map((event) => {
      const listener = (...args) => handlersRef.current[event]?.(...args);
      socket.on(event, listener);
      return [event, listener];
    });

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);

    if (!socket.connected) socket.connect();
    if (socket.connected) handleConnect();

    return () => {
      disposed = true;
      if (socket.connected) socket.emit(SOCKET_EVENTS.LEAVE_ROOM, roomId);
      boundHandlers.forEach(([event, listener]) => socket.off(event, listener));
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      releaseSocket(socket);
      setConnected(false);
    };
  }, [token, roomId]);

  const emit = useCallback((event, data) => {
    if (sharedSocket?.connected) {
      sharedSocket.emit(event, data);
      return true;
    }
    return false;
  }, []);

  return { connected, emit };
}

export default useSocket;
