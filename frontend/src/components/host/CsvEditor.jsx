import { useState } from "react";

export default function CsvEditor({ onAdded, send }) {
  const [form, setForm] = useState({
    question: "",
    option_a: "",
    option_b: "",
    option_c: "",
    option_d: "",
    reponse_correcte: "",
    manche: 1,
  });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      const res = await fetch("/api/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      setForm({
        question: "",
        option_a: "",
        option_b: "",
        option_c: "",
        option_d: "",
        reponse_correcte: "",
        manche: form.manche,
      });
      setStatus({ type: "ok", text: "Question ajoutée au CSV ✓" });
      send?.({ type: "host_action", action: "reload_questions" });
      onAdded?.();
    } catch {
      setStatus({ type: "err", text: "Impossible d'ajouter la question" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h3 className="panel-titre">➕ Ajouter une question</h3>
      <form className="form-grid" onSubmit={handleSubmit}>
        <label className="form-label full">
          Question
          <textarea
            value={form.question}
            onChange={(e) => update("question", e.target.value)}
            required
            rows={2}
          />
        </label>
        {["option_a", "option_b", "option_c", "option_d"].map((key, i) => (
          <label key={key} className="form-label">
            Option {String.fromCharCode(65 + i)}
            <input
              value={form[key]}
              onChange={(e) => update(key, e.target.value)}
            />
          </label>
        ))}
        <label className="form-label">
          Bonne réponse
          <input
            value={form.reponse_correcte}
            onChange={(e) => update("reponse_correcte", e.target.value)}
          />
        </label>
        <label className="form-label">
          Manche
          <select
            value={form.manche}
            onChange={(e) => update("manche", Number(e.target.value))}
          >
            <option value={1}>1 — Classique</option>
            <option value={2}>2 — Rapidité</option>
            <option value={3}>3 — Buzzer</option>
            <option value={4}>4 — Final</option>
          </select>
        </label>
        <div className="form-actions full">
          <button type="submit" className="btn btn-primaire" disabled={loading}>
            {loading ? "Enregistrement…" : "Enregistrer dans le CSV"}
          </button>
        </div>
        {status && (
          <p className={`form-status ${status.type}`}>{status.text}</p>
        )}
      </form>
    </section>
  );
}
