import TimerDisplay from "../shared/TimerDisplay";
import ProgressiveQuestion from "../shared/ProgressiveQuestion";

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
  partRevealInterval,
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
          <span className="points-value">{frozenPoints ?? 10}</span>
        </div>
      </div>

      {question?.parts?.length > 0 && (
        <ProgressiveQuestion
          parts={question.parts}
          totalParts={question.total_parts}
          revealedCount={question.revealed_parts_count}
          partRevealInterval={partRevealInterval ?? 5}
          timerRemaining={timerRemaining}
          timerTotal={timerTotal}
        />
      )}

      {lockedOut && (
        <p className="locked-msg">Verrouillé pour cette question</p>
      )}

      {someoneElseBuzzed && (
        <p className="buzz-wait">{buzzerTeam.name} a buzzé !</p>
      )}

      {iBuzzed && (
        <p className="buzz-success">Vous avez buzzé — répondez à l&apos;oral !</p>
      )}

      {!lockedOut && phase === "active" && (
        <button className="buzzer-btn buzzer-btn-final" onClick={() => onBuzz()}>
          ✡️
        </button>
      )}
    </div>
  );
}
