export default function RoundBuzzer({ lockedOut, buzzerTeam, myTeamId, onBuzz, phase }) {
  const someoneElseBuzzed =
    phase === "buzzer_locked" && buzzerTeam && buzzerTeam.team_id !== myTeamId;
  const iBuzzed = phase === "buzzer_locked" && buzzerTeam?.team_id === myTeamId;

  return (
    <div className="round-buzzer">
      {lockedOut && (
        <p className="locked-msg">Vous êtes verrouillé(e) pour cette question</p>
      )}

      {someoneElseBuzzed && (
        <p className="buzz-wait">{buzzerTeam.name} a buzzé en premier…</p>
      )}

      {iBuzzed && (
        <p className="buzz-success">Vous avez buzzé ! Répondez à l&apos;oral.</p>
      )}

      {!lockedOut && phase === "active" && (
        <div className="buzzer-zone">
          <button className="buzzer-btn" onClick={() => onBuzz(null)}>
            BUZZER
          </button>
        </div>
      )}
    </div>
  );
}
