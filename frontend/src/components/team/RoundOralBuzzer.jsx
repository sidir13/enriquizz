export default function RoundOralBuzzer({
  question,
  lockedOut,
  buzzerTeam,
  myTeamId,
  onBuzz,
  phase,
}) {
  const someoneElseBuzzed =
    phase === "buzzer_locked" && buzzerTeam && buzzerTeam.team_id !== myTeamId;
  const iBuzzed = phase === "buzzer_locked" && buzzerTeam?.team_id === myTeamId;

  return (
    <div className="round-oral-buzzer">
      <h2 className="texte-question">{question?.question}</h2>

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
        <div className="buzzer-zone buzzer-zone-centered">
          <button className="buzzer-btn" onClick={() => onBuzz(null)}>
          🔥
          </button>
        </div>
      )}
    </div>
  );
}
