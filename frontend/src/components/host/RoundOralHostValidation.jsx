export default function RoundOralHostValidation({ buzzerTeam, onValidate, points = 10 }) {
  if (!buzzerTeam) return null;

  return (
    <div className="round-oral-validation">
      <div className="buzz-alert">
        <strong>{buzzerTeam.name}</strong> a buzzé — validez la réponse orale :
      </div>
      <div className="validation-actions">
        <button
          className="btn btn-vert btn-large"
          onClick={() => onValidate(true)}
        >
          Bonne réponse (+{points} pts)
        </button>
        <button
          className="btn btn-rouge btn-large"
          onClick={() => onValidate(false)}
        >
          Mauvaise réponse (verrouillage)
        </button>
      </div>
    </div>
  );
}
