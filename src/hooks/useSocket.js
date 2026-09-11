import { useEffect, useCallback, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../context/AuthContext';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const MAX_RECONNECT_ATTEMPTS = 10;

let sharedSocket = null;

function getSocket(token) {
  if (sharedSocket && sharedSocket.connected) return sharedSocket;
  if (sharedSocket) sharedSocket.disconnect();

  sharedSocket = io(SOCKET_URL, {
    autoConnect: false,
    auth: { token },
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 30000,
    reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
    transports: ['websocket', 'polling'],
  });

  return sharedSocket;
}

/**
 * useSocket — real-time Socket.io hook with JWT auth and auto-reconnect.
 *
 * @param {string} roomId - Room to join (e.g., user ID, org ID, or order ID)
 * @param {Object} eventHandlers - Map of event name → callback
 * @returns {{ connected: boolean, emit: Function }}
 *
 * @example
 * const { connected, emit } = useSocket(`user:${userId}`, {
 *   'notification': (data) => toast(data.message),
 *   'order:updated': (data) => refetchOrder(data.orderId),
 * });
 */
export function useSocket(roomId, eventHandlers = {}) {
  const { token } = useAuth();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!token || !roomId) return;

    const s = getSocket(token);
    s.connect();

    const onConnect = () => {
      setConnected(true);
      s.emit('join-room', roomId);
    };
    const onDisconnect = () => setConnected(false);

    s.on('connect', onConnect);
    s.on('disconnect', onDisconnect);

    Object.entries(eventHandlers).forEach(([event, handler]) => {
      s.on(event, handler);
    });

    if (s.connected) {
      setConnected(true);
      s.emit('join-room', roomId);
    }

    return () => {
      s.emit('leave-room', roomId);
      Object.keys(eventHandlers).forEach((event) => {
        s.off(event, eventHandlers[event]);
      });
      s.off('connect', onConnect);
      s.off('disconnect', onDisconnect);
    };
  }, [token, roomId]);

  const emit = useCallback((event, data) => {
    if (sharedSocket?.connected) {
      sharedSocket.emit(event, data);
    }
  }, []);

  return { connected, emit };
}

export default useSocket;
