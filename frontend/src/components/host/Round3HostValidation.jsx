import { useEffect, useState } from "react";
import { ROUND3_CLAIMS } from "../../config";

function propositionsForClaim(claim, options) {
  if (!options?.length || !claim) return [];
  if (claim === "duo") return options.slice(0, 2);
  if (claim === "carre") return options.slice(0, 4);
  return [];
}

export default function Round3HostValidation({ buzzerTeam, question, onValidate }) {
  const [selectedClaim, setSelectedClaim] = useState(null);

  useEffect(() => {
    setSelectedClaim(null);
  }, [buzzerTeam?.team_id]);

  if (!buzzerTeam) return null;

  const claimInfo = ROUND3_CLAIMS.find((c) => c.id === selectedClaim);
  const shown = propositionsForClaim(selectedClaim, question?.options);

  return (
    <div className="round3-validation">
      <div className="buzz-alert">
        <strong>{buzzerTeam.name}</strong> a buzzé — choisissez sa prétention :
      </div>

      <div className="claim-select-row claim-select-large">
        {ROUND3_CLAIMS.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`btn ${selectedClaim === c.id ? "btn-primaire" : "btn-secondaire"}`}
            onClick={() => setSelectedClaim(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {selectedClaim && (
        <div className="claim-display">
          {selectedClaim === "cash" ? (
            <p className="claim-count-label">0 proposition affichée — réponse orale (Cash)</p>
          ) : (
            <>
              <p className="claim-count-label">
                {shown.length} proposition{shown.length > 1 ? "s" : ""} affichée{shown.length > 1 ? "s" : ""}
              </p>
              <ul className="host-options claim-options">
                {shown.map((opt, i) => (
                  <li key={opt}>
                    {String.fromCharCode(65 + i)}. {opt}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {selectedClaim && claimInfo && (
        <div className="validation-actions">
          <button
            className="btn btn-vert btn-large"
            onClick={() => onValidate(true, selectedClaim)}
          >
            Bonne réponse ({claimInfo.reward} pts)
          </button>
          <button
            className="btn btn-rouge btn-large"
            onClick={() => onValidate(false, selectedClaim)}
          >
            Mauvaise réponse ({claimInfo.penalty} pts)
          </button>
        </div>
      )}
    </div>
  );
}
