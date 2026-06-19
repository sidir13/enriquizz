import TimerDisplay from "../shared/TimerDisplay";

export default function RoundFinal({
  question,
  lockedOut,
  buzzerTeam,
  myTeamId,
  onBuzz,
  phase,
  timerRemaining,
  timerTotal,
  frozenPoints,
}) {
  const someoneElseBuzzed =
    phase === "buzzer_locked" && buzzerTeam && buzzerTeam.team_id !== myTeamId;
  const iBuzzed = phase === "buzzer_locked" && buzzerTeam?.team_id === myTeamId;

  return (
    <div className="round-final">
      <div className="final-gauge">
        <TimerDisplay
          remaining={timerRemaining}
          total={timerTotal}
          variant="final"
        />
        <div className="points-counter points-counter-large">
          <span className="points-label">Points en jeu</span>
          <span className="points-value">{frozenPoints ?? 1}</span>
        </div>
      </div>

      <h2 className="texte-question">{question.question}</h2>
      <p className="buzzer-hint">Écoutez le MJ et buzzez quand vous connaissez la réponse !</p>

      {lockedOut && (
        <p className="locked-msg">🔒 Verrouillé pour cette question</p>
      )}

      {someoneElseBuzzed && (
        <p className="buzz-wait">{buzzerTeam.name} a buzzé !</p>
      )}

      {iBuzzed && (
        <p className="buzz-success">Vous avez buzzé — répondez à l'oral !</p>
      )}

      {!lockedOut && phase === "active" && (
        <button className="buzzer-btn buzzer-btn-final" onClick={() => onBuzz()}>
          BUZZER
        </button>
      )}
    </div>
  );
}
