import { useCallback, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import HostDashboard from "./host/HostDashboard";

const HOST_STORAGE_KEY = "enriquiz_host_room";

export default function HostView({ onBack }) {
  const [roomCode, setRoomCode] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState(null);

  const handleMessage = useCallback((msg) => {
    if (msg.type === "room_created") {
      setRoomCode(msg.room_code);
      sessionStorage.setItem(HOST_STORAGE_KEY, msg.room_code);
    } else if (msg.type === "state") {
      setGameState(msg.payload);
    } else if (msg.type === "error") {
      setError(msg.message);
    }
  }, []);

  const handleOpen = useCallback((sendFn) => {
    const saved = sessionStorage.getItem(HOST_STORAGE_KEY);
    if (saved) {
      sendFn({ type: "host_rejoin", room_code: saved });
    } else {
      sendFn({ type: "host_create" });
    }
  }, []);

  const { connected, reconnecting, send } = useWebSocket({
    enabled: true,
    onMessage: handleMessage,
    onOpen: handleOpen,
  });

  return (
    <>
      <button
        className="btn btn-ghost btn-back"
        onClick={() => {
          sessionStorage.removeItem(HOST_STORAGE_KEY);
          onBack();
        }}
      >
        ← Retour
      </button>
      {error && <p className="erreur banner-erreur">{error}</p>}
      <HostDashboard
        state={gameState}
        send={send}
        roomCode={roomCode}
        connected={connected}
        reconnecting={reconnecting}
      />
    </>
  );
}
