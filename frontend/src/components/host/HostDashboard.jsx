import { useState } from "react";
import Scoreboard from "../shared/Scoreboard";
import TimerDisplay from "../shared/TimerDisplay";
import PointAdjuster from "./PointAdjuster";
import CsvEditor from "./CsvEditor";
import BuzzValidationModal from "./BuzzValidationModal";
import Round3HostValidation from "./Round3HostValidation";
import RoundOralHostValidation from "./RoundOralHostValidation";
import ProgressiveQuestion from "../shared/ProgressiveQuestion";
import { MANCHE_LABELS } from "../../config";

export default function HostDashboard({ state, send, roomCode, connected, reconnecting }) {
  const [timerConfig, setTimerConfig] = useState(state?.timer_seconds ?? 10);

  if (!state) {
    return (
      <div className="container centré">
        <div className="spinner" />
        <p className="sous-titre">
          {!connected
            ? "Connexion au serveur…"
            : roomCode
              ? `Salle ${roomCode} — synchronisation…`
              : "Création de la salle…"}
        </p>
      </div>
    );
  }

  const {
    phase,
    current_manche,
    question_index,
    question_total,
    timer_seconds,
    timer_remaining,
    frozen_points,
    current_question,
    teams,
    buzzer_team,
    answers,
    countdown_seconds,
    show_correction,
    part_reveal_interval,
  } = state;

  const showBuzzModal = phase === "buzzer_locked" && buzzer_team && current_manche === 4;
  const canShowCorrection =
    current_question &&
    (current_manche <= 3 || current_manche === 4) &&
    phase !== "lobby";

  function hostAction(action, extra = {}) {
    send({ type: "host_action", action, ...extra });
  }

  function applyConfig() {
    hostAction("set_config", { timer_seconds: timerConfig });
  }

  function validateBuzz(correct, claim) {
    hostAction("validate_buzz", { correct, claim });
  }

  return (
    <div className="container host-container fade-in">
      <header className="header host-header">
        <div>
          <h1 className="app-titre">Dashboard MJ</h1>
          <p className="host-code">
            Code salle : <strong>{roomCode}</strong>
            {!connected && <span className="badge-warn"> Déconnecté</span>}
            {reconnecting && <span className="badge-warn"> Reconnexion…</span>}
          </p>
        </div>
        <span className="compteur">
          Manche {current_manche} — {MANCHE_LABELS[current_manche]}
        </span>
      </header>

      <div className="host-grid">
        <main className="host-main">
          {phase === "lobby" && (
            <section className="panel">
              <h3 className="panel-titre">Configuration</h3>
              <div className="config-row">
                <label>
                  Timer questions (s)
                  <input
                    type="number"
                    min={5}
                    max={90}
                    value={timerConfig}
                    onChange={(e) => setTimerConfig(Number(e.target.value))}
                  />
                </label>
                <button className="btn btn-secondaire" onClick={applyConfig}>
                  Appliquer
                </button>
              </div>
              {current_manche === 4 && (
                <p className="sous-titre host-mj-hint">
                  Timer 20 s — une nouvelle partie apparaît toutes les 5 s (découpée aux points).
                  Plus la réponse est rapide, plus les points sont élevés (10 → 1).
                </p>
              )}
              <p className="sous-titre">
                {teams.length} équipe{teams.length !== 1 ? "s" : ""} connectée
                {teams.length !== 1 ? "s" : ""}
              </p>
              {current_manche === 1 && question_index === 0 && phase === "lobby" && (
                <button className="btn btn-primaire btn-large" onClick={() => hostAction("start_game")}>
                  Lancer la partie
                </button>
              )}
              {phase === "lobby" && current_manche > 1 && (
                <button className="btn btn-primaire btn-large" onClick={() => hostAction("start_countdown")}>
                  Démarrer la manche {current_manche}
                </button>
              )}
            </section>
          )}

          {phase === "countdown" && (
            <section className="panel panel-centré">
              <h2 className="phase-titre">Départ dans…</h2>
              <TimerDisplay
                remaining={timer_remaining}
                total={countdown_seconds}
                variant="countdown"
              />
            </section>
          )}

          {(phase === "active" || phase === "buzzer_locked" || phase === "reveal") && current_question && (
            <section className="panel">
              <div className="question-header">
                <span className="numéro-question">
                  Q{question_index + 1}/{question_total} — Manche {current_manche}
                </span>
                {(current_manche === 1 || current_manche === 4) && phase === "active" && (
                  <TimerDisplay
                    remaining={timer_remaining}
                    total={timer_seconds}
                    variant={current_manche === 4 ? "final" : "speed"}
                  />
                )}
                {current_manche === 4 && phase === "active" && (
                  <div className="points-counter">
                    Points en jeu : <strong>{frozen_points ?? 10}</strong>
                  </div>
                )}
              </div>

              {current_manche === 4 && current_question?.parts?.length > 0 ? (
                <ProgressiveQuestion
                  parts={current_question.parts}
                  totalParts={current_question.total_parts}
                  revealedCount={current_question.revealed_parts_count}
                  partRevealInterval={part_reveal_interval ?? 5}
                  timerRemaining={timer_remaining}
                  timerTotal={timer_seconds}
                />
              ) : (
                <h2 className="texte-question">{current_question.question}</h2>
              )}

              {current_manche === 2 && (
                <p className="sous-titre host-mj-hint">
                  Lisez la proposition à l&apos;oral. Les options Duo / Carré / Cash apparaissent après un buzz.
                </p>
              )}

              {current_manche === 3 && (
                <p className="sous-titre host-mj-hint">
                  Les équipes voient la question et peuvent buzzer. Validez la réponse orale (+10 pts, pas de pénalité).
                </p>
              )}

              {current_manche === 2 && phase === "buzzer_locked" && buzzer_team && (
                <Round3HostValidation
                  buzzerTeam={buzzer_team}
                  question={current_question}
                  onValidate={validateBuzz}
                />
              )}

              {current_manche === 3 && phase === "buzzer_locked" && buzzer_team && (
                <RoundOralHostValidation
                  buzzerTeam={buzzer_team}
                  onValidate={validateBuzz}
                />
              )}

              {current_manche !== 4 &&
                current_question.options?.length > 0 &&
                current_manche !== 2 && (
                  <ul className="liste-options host-options">
                    {current_question.options.map((opt) => (
                      <li key={opt}>{opt}</li>
                    ))}
                  </ul>
                )}

              {canShowCorrection && (
                <div className="correction-block">
                  {!show_correction ? (
                    <button
                      className="btn btn-secondaire"
                      onClick={() => hostAction("show_correction")}
                    >
                      Correction
                    </button>
                  ) : (
                    <div className="correction-reveal">
                      <span className="correction-label">Bonne réponse :</span>
                      <strong>{current_question.reponse_correcte}</strong>
                    </div>
                  )}
                </div>
              )}

              {buzzer_team && current_manche !== 2 && current_manche !== 3 && (
                <div className="buzz-alert">
                  <strong>{buzzer_team.name}</strong> a buzzé !
                </div>
              )}

              {Object.keys(answers || {}).length > 0 && (
                <div className="answers-log">
                  <h4>Réponses reçues</h4>
                  {Object.values(answers).map((a) => (
                    <p key={a.team_id} className={a.correct ? "answer-ok" : "answer-ko"}>
                      {a.name}: {a.answer} → {a.points} pts
                    </p>
                  ))}
                </div>
              )}
            </section>
          )}

          {phase === "manche_end" && (
            <section className="panel panel-centré">
              <h2 className="phase-titre">Fin de la manche {current_manche}</h2>
              <button className="btn btn-primaire btn-large" onClick={() => hostAction("next_manche")}>
                Manche suivante →
              </button>
            </section>
          )}

          {phase === "game_end" && (
            <section className="panel panel-centré">
              <h2 className="titre-résultat">Partie terminée !</h2>
              <Scoreboard teams={teams} />
            </section>
          )}

          <section className="panel host-controls">
            <h3 className="panel-titre">Contrôles</h3>
            <div className="controls-grid">
              {phase === "reveal" && (
                <button className="btn btn-primaire" onClick={() => hostAction("next_question")}>
                  Question suivante →
                </button>
              )}
              {(phase === "active" || phase === "buzzer_locked") && (
                <button className="btn btn-secondaire" onClick={() => hostAction("skip_question")}>
                  Passer la question
                </button>
              )}
            </div>
          </section>
        </main>

        <aside className="host-sidebar">
          <section className="panel">
            <h3 className="panel-titre">Classement</h3>
            <Scoreboard teams={teams} highlightId={buzzer_team?.team_id} />
          </section>
          <PointAdjuster teams={teams} send={send} />
          <CsvEditor send={send} currentManche={current_manche} />
        </aside>
      </div>

      {showBuzzModal && (
        <BuzzValidationModal
          buzzerTeam={buzzer_team}
          manche={current_manche}
          frozenPoints={frozen_points}
          onValidate={validateBuzz}
        />
      )}
    </div>
  );
}
