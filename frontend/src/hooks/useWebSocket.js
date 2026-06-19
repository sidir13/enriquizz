import { useCallback, useEffect, useRef, useState } from "react";
import { getWsUrl } from "../config";

export function useWebSocket({ enabled = true, onMessage, onOpen, onClose }) {
  const wsRef = useRef(null);
  const mounted = useRef(true);
  const handlersRef = useRef({ onMessage, onOpen, onClose });
  const connectedConfirmed = useRef(false);
  const connectRef = useRef(null);
  const disconnectRef = useRef(null);

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

  const connect = useCallback(() => {
    if (!enabled || !mounted.current) return;

    if (wsRef.current) {
      const old = wsRef.current;
      wsRef.current = null;
      old.onclose = null;
      old.onerror = null;
      if (old.readyState === WebSocket.OPEN || old.readyState === WebSocket.CONNECTING) {
        old.close(1000, "Reconnecting");
      }
    }

    connectedConfirmed.current = false;

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mounted.current) return;
      console.log("[WS] onopen");
      setReconnecting(false);
      // Do NOT set connected=true here; wait for server ack
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("[WS] onmessage:", data);

        // First message should be "connected" from server
        if (data.type === "connected" && !connectedConfirmed.current) {
          connectedConfirmed.current = true;
          setConnected(true);
          const sendFn = (payload) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify(payload));
              return true;
            }
            return false;
          };
          handlersRef.current.onOpen?.(sendFn);
          return;
        }

        handlersRef.current.onMessage?.(data);
      } catch {
        /* ignore malformed payloads */
      }
    };

    ws.onclose = () => {
      if (!mounted.current) return;
      console.log("[WS] onclose");
      setConnected(false);
      connectedConfirmed.current = false;
      wsRef.current = null;
      handlersRef.current.onClose?.();
    };

    ws.onerror = (event) => {
      console.error("[WS] onerror:", event);
      ws.close();
    };
  }, [enabled]);

  const disconnect = useCallback(() => {
    connectedConfirmed.current = false;
    const ws = wsRef.current;
    if (!ws) {
      setConnected(false);
      setReconnecting(false);
      return;
    }
    wsRef.current = null;
    ws.onclose = null;
    ws.onerror = null;
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close(1000, "Client disconnect");
    }
    setConnected(false);
    setReconnecting(false);
  }, []);

  connectRef.current = connect;
  disconnectRef.current = disconnect;

  useEffect(() => {
    mounted.current = true;
    if (enabled) connectRef.current?.();
    return () => {
      mounted.current = false;
      disconnectRef.current?.();
    };
  }, [enabled]);

  useEffect(() => {
    if (!enabled || !connected) return;
    const interval = setInterval(() => send({ type: "ping" }), 25000);
    return () => clearInterval(interval);
  }, [enabled, connected, send]);

  return { connected, reconnecting, send, disconnect, reconnect: connect };
}
