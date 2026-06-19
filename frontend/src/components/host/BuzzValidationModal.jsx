import { ROUND3_CLAIMS } from "../../config";

export default function BuzzValidationModal({ buzzerTeam, manche, frozenPoints, onValidate }) {
  if (!buzzerTeam) return null;

  return (
    <div className="modal-overlay">
      <div className="modal carte" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-titre">Validation — {buzzerTeam.name}</h2>
        {manche === 4 && (
          <p className="modal-info">
            Points en jeu : <strong>{frozenPoints ?? "—"}</strong>
          </p>
        )}
        {manche === 3 && (
          <p className="modal-info">Choisissez la prétention orale de l'équipe :</p>
        )}

        {manche === 3 ? (
          <div className="claim-grid">
            {ROUND3_CLAIMS.map((c) => (
              <div key={c.id} className="claim-btns">
                <span className="claim-label">{c.label}</span>
                <button
                  className="btn btn-vert btn-sm"
                  onClick={() => onValidate(true, c.id)}
                >
                  ✓ {c.reward}
                </button>
                <button
                  className="btn btn-rouge btn-sm"
                  onClick={() => onValidate(false, c.id)}
                >
                  ✗ {c.penalty}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="modal-actions">
            <button className="btn btn-vert btn-large" onClick={() => onValidate(true)}>
              ✓ Correct (+{frozenPoints ?? "?"} pts)
            </button>
            <button className="btn btn-rouge btn-large" onClick={() => onValidate(false)}>
              ✗ Incorrect (verrouillage)
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
