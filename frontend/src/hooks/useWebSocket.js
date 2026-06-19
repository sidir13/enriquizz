import { useCallback, useEffect, useRef, useState } from "react";
import { getWsUrl } from "../config";

const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_DELAY_MS = 15000;

export function useWebSocket({ enabled = true, onMessage, onOpen, onClose }) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const reconnectAttempt = useRef(0);
  const mounted = useRef(true);
  const handlersRef = useRef({ onMessage, onOpen, onClose });

  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  handlersRef.current = { onMessage, onOpen, onClose };

  const send = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }, []);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!enabled || !mounted.current) return;

    clearReconnectTimer();

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mounted.current) return;
      reconnectAttempt.current = 0;
      setConnected(true);
      setReconnecting(false);
      const sendFn = (payload) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(payload));
          return true;
        }
        return false;
      };
      handlersRef.current.onOpen?.(sendFn);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handlersRef.current.onMessage?.(data);
      } catch {
        /* ignore malformed payloads */
      }
    };

    ws.onclose = () => {
      if (!mounted.current) return;
      setConnected(false);
      wsRef.current = null;
      handlersRef.current.onClose?.();

      if (enabled) {
        setReconnecting(true);
        const delay = Math.min(
          RECONNECT_DELAY_MS * 2 ** reconnectAttempt.current,
          MAX_RECONNECT_DELAY_MS
        );
        reconnectAttempt.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [enabled, clearReconnectTimer]);

  const disconnect = useCallback(() => {
    clearReconnectTimer();
    reconnectAttempt.current = 0;
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setReconnecting(false);
  }, [clearReconnectTimer]);

  useEffect(() => {
    mounted.current = true;
    if (enabled) connect();
    return () => {
      mounted.current = false;
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  useEffect(() => {
    if (!enabled || !connected) return;
    const interval = setInterval(() => send({ type: "ping" }), 25000);
    return () => clearInterval(interval);
  }, [enabled, connected, send]);

  return { connected, reconnecting, send, disconnect, reconnect: connect };
}
