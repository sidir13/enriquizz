import { ROUND3_CLAIMS } from "../../config";

export default function RoundBuzzer({
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
    <div className="round-buzzer">
      <h2 className="texte-question">{question.question}</h2>
      <p className="buzzer-hint">Répondez à l'oral après avoir buzzé !</p>

      {lockedOut && (
        <p className="locked-msg">🔒 Vous êtes verrouillé(e) pour cette question</p>
      )}

      {someoneElseBuzzed && (
        <p className="buzz-wait">
          {buzzerTeam.name} a buzzé en premier…
        </p>
      )}

      {iBuzzed && (
        <p className="buzz-success">Vous avez buzzé ! Répondez à l'oral.</p>
      )}

      {!lockedOut && phase === "active" && (
        <div className="buzzer-zone">
          <button className="buzzer-btn" onClick={() => onBuzz(null)}>
            BUZZER
          </button>
          <div className="claim-hints">
            {ROUND3_CLAIMS.map((c) => (
              <button
                key={c.id}
                className="btn btn-secondaire btn-sm claim-btn"
                onClick={() => onBuzz(c.id)}
              >
                {c.label}
              </button>
            ))}
          </div>
          <p className="claim-note">Optionnel : buzzer avec Cash / Carré / Duo</p>
        </div>
      )}
    </div>
  );
}
