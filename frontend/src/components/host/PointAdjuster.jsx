import { useState } from "react";

export default function PointAdjuster({ teams, send }) {
  const [selected, setSelected] = useState("");
  const [delta, setDelta] = useState(5);

  function adjust(amount) {
    if (!selected) return;
    send({ type: "host_action", action: "adjust_points", team_id: selected, delta: amount });
  }

  return (
    <section className="panel">
      <h3 className="panel-titre">Ajustement manuel</h3>
      <div className="adjuster-row">
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Choisir une équipe…</option>
          {teams.map((t) => (
            <option key={t.team_id} value={t.team_id}>
              {t.name} ({t.score} pts)
            </option>
          ))}
        </select>
        <input
          type="number"
          min={1}
          max={100}
          value={delta}
          onChange={(e) => setDelta(Number(e.target.value))}
          className="adjuster-input"
        />
      </div>
      <div className="adjuster-btns">
        <button className="btn btn-vert" onClick={() => adjust(delta)} disabled={!selected}>
          +{delta} pts
        </button>
        <button className="btn btn-rouge" onClick={() => adjust(-delta)} disabled={!selected}>
          −{delta} pts
        </button>
      </div>
    </section>
  );
}
