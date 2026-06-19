export default function BuzzValidationModal({ buzzerTeam, manche, frozenPoints, onValidate }) {
  if (!buzzerTeam || manche !== 4) return null;

  return (
    <div className="modal-overlay">
      <div className="modal carte" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-titre">Validation — {buzzerTeam.name}</h2>
        <p className="modal-info">
          Points en jeu : <strong>{frozenPoints ?? "—"}</strong>
        </p>
        <div className="modal-actions">
          <button className="btn btn-vert btn-large" onClick={() => onValidate(true)}>
            Bonne réponse (+{frozenPoints ?? "?"} pts)
          </button>
          <button className="btn btn-rouge btn-large" onClick={() => onValidate(false)}>
            Mauvaise réponse (verrouillage)
          </button>
        </div>
      </div>
    </div>
  );
}
