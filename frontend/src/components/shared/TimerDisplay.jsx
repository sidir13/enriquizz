export default function TimerDisplay({ remaining, total, label, variant = "default" }) {
  const pct = total > 0 ? (remaining / total) * 100 : 0;

  return (
    <div className={`timer-block timer-${variant}`}>
      {label && <span className="timer-label">{label}</span>}
      <div className="timer-chiffre">{Math.ceil(remaining)}s</div>
      <div className="barre-progression timer-barre">
        <div
          className={`barre-remplissage ${variant === "final" ? "barre-final" : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
