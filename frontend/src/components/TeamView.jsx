import { useCallback, useRef, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { MANCHE_LABELS } from "../config";
import TimerDisplay from "./shared/TimerDisplay";
import RoundClassic from "./team/RoundClassic";
import RoundSpeed from "./team/RoundSpeed";
import RoundBuzzer from "./team/RoundBuzzer";
import RoundFinal from "./team/RoundFinal";

const TEAM_STORAGE_KEY = "enriquiz_team_session";

function readTeamSession() {
  try {
    const raw = sessionStorage.getItem(TEAM_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function TeamView({ onBack }) {
  const savedSession = readTeamSession();
  const [screen, setScreen] = useState(savedSession ? "play" : "join");
  const [roomCode, setRoomCode] = useState(savedSession?.room_code ?? "");
  const [teamName, setTeamName] = useState(savedSession?.team_name ?? "");
  const [teamId, setTeamId] = useState(savedSession?.team_id ?? null);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState(null);
  const pendingJoin = useRef(null);
  const hasJoined = useRef(!!savedSession);

  const handleMessage = useCallback((msg) => {
    if (msg.type === "joined") {
      setTeamId(msg.team_id);
      setScreen("play");
      hasJoined.current = true;
      if (pendingJoin.current) {
        sessionStorage.setItem(
          TEAM_STORAGE_KEY,
          JSON.stringify({
            room_code: pendingJoin.current.room_code,
            team_id: msg.team_id,
            team_name: pendingJoin.current.team_name,
          })
        );
        pendingJoin.current = null;
      }
    } else if (msg.type === "state") {
      setGameState(msg.payload);
    } else if (msg.type === "error") {
      setError(msg.message);
    }
  }, []);

  const handleOpen = useCallback((sendFn) => {
    if (pendingJoin.current) {
      sendFn({
        type: "team_join",
        room_code: pendingJoin.current.room_code,
        team_name: pendingJoin.current.team_name,
      });
      return;
    }
    if (hasJoined.current) {
      const saved = sessionStorage.getItem(TEAM_STORAGE_KEY);
      if (saved) {
        try {
          const session = JSON.parse(saved);
          sendFn({
            type: "team_rejoin",
            room_code: session.room_code,
            team_id: session.team_id,
          });
        } catch {
          /* ignore */
        }
      }
    }
  }, []);

  const { connected, reconnecting, send } = useWebSocket({
    enabled: screen !== "join",
    onMessage: handleMessage,
    onOpen: handleOpen,
  });

  function submitJoin(e) {
    e.preventDefault();
    setError(null);
    pendingJoin.current = {
      room_code: roomCode.toUpperCase().trim(),
      team_name: teamName.trim(),
    };
    setScreen("connecting");
  }

  function handleAnswer(answer) {
    send({ type: "team_answer", answer });
  }

  function handleBuzz(claim) {
    send({ type: "team_buzz", claim });
  }

  if (screen === "join") {
    return (
      <div className="container centré fade-in">
        <button
          className="btn btn-ghost btn-back"
          onClick={() => {
            sessionStorage.removeItem(TEAM_STORAGE_KEY);
            onBack();
          }}
        >
          Retour
        </button>
        <div className="carte landing-carte">
          <h1 className="app-titre">Rejoindre la partie</h1>
          <form className="join-form" onSubmit={submitJoin}>
            <label className="form-label full">
              Nom du groupe
              <input
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="les valises"
                required
              />
            </label>
            <label className="form-label full">
              Code de la salle
              <input
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                placeholder="ABC12"
                required
                maxLength={6}
                className="code-input"
              />
            </label>
            {error && <p className="erreur">{error}</p>}
            <button type="submit" className="btn btn-primaire btn-large">
              Entrer dans la salle
            </button>
          </form>
        </div>
      </div>
    );
  }

  const myTeam = gameState?.my_team;
  const phase = gameState?.phase;
  const manche = gameState?.current_manche;
  const question = gameState?.current_question;
  const questionKey = question ? `${question.id}-${gameState?.question_index}` : "none";

  return (
    <div className="container team-container fade-in">
      <header className="team-header">
        <button className="btn btn-ghost btn-back-sm" onClick={onBack}>
          ←
        </button>
        <div className="team-info">
          <h1 className="team-name">{myTeam?.name || teamName}</h1>
          <span className="team-score">{myTeam?.score ?? 0} pts</span>
        </div>
        <div className="team-status">
          {!connected && <span className="badge-warn">●</span>}
          {reconnecting && <span className="badge-warn">↻</span>}
        </div>
      </header>

      {gameState && (
        <div className="manche-badge">
          Manche {manche} — {MANCHE_LABELS[manche]}
        </div>
      )}

      {screen === "connecting" && !gameState && (
        <div className="centré team-wait">
          <div className="spinner" />
          <p className="sous-titre">Connexion à la salle…</p>
        </div>
      )}

      {phase === "lobby" && (
        <div className="carte panel-centré">
          <p className="phase-titre">En attente du MJ…</p>
          <p className="sous-titre">Salle {gameState?.room_code}</p>
        </div>
      )}

      {phase === "countdown" && (
        <div className="carte panel-centré">
          <p className="phase-titre">Préparez-vous !</p>
          <TimerDisplay
            remaining={gameState.timer_remaining}
            total={gameState.countdown_seconds}
            variant="countdown"
          />
        </div>
      )}

      {phase === "manche_end" && (
        <div className="carte panel-centré">
          <p className="phase-titre">Fin de la manche {manche}</p>
          <p className="sous-titre">Le MJ prépare la suite…</p>
        </div>
      )}

      {phase === "game_end" && (
        <div className="carte panel-centré">
          <h2 className="titre-résultat">Partie terminée !</h2>
          <p className="score-final">{myTeam?.score ?? 0} pts</p>
        </div>
      )}

      {(phase === "active" || phase === "buzzer_locked" || phase === "reveal") && question && (
        <main className="carte team-round" key={questionKey}>
          {manche === 1 && (
            <RoundClassic
              question={question}
              answered={myTeam?.answered}
              onAnswer={handleAnswer}
              lastPoints={myTeam?.last_points_awarded}
            />
          )}
          {manche === 2 && (
            <RoundSpeed
              question={question}
              answered={myTeam?.answered}
              onAnswer={handleAnswer}
              lastPoints={myTeam?.last_points_awarded}
              timerRemaining={gameState.timer_remaining}
              timerTotal={gameState.timer_seconds}
            />
          )}
          {manche === 3 && (
            <RoundBuzzer
              lockedOut={myTeam?.locked_out}
              buzzerTeam={gameState.buzzer_team}
              myTeamId={teamId}
              onBuzz={handleBuzz}
              phase={phase}
            />
          )}
          {manche === 4 && (
            <RoundFinal
              question={question}
              lockedOut={myTeam?.locked_out}
              buzzerTeam={gameState.buzzer_team}
              myTeamId={teamId}
              onBuzz={handleBuzz}
              phase={phase}
              timerRemaining={gameState.timer_remaining}
              timerTotal={gameState.timer_seconds}
              frozenPoints={gameState.frozen_points}
              partRevealInterval={gameState.part_reveal_interval}
            />
          )}
          {phase === "reveal" && myTeam?.last_points_awarded > 0 && (
            <p className="feedback-pts reveal-pts">+{myTeam.last_points_awarded} pts</p>
          )}
        </main>
      )}

      {error && <p className="erreur banner-erreur">{error}</p>}
    </div>
  );
}
