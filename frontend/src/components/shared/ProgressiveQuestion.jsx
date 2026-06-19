export default function ProgressiveQuestion({
  parts,
  totalParts,
  revealedCount,
  partRevealInterval,
  timerRemaining,
  timerTotal,
}) {
  if (!parts?.length) return null;

  const total = totalParts ?? parts.length;
  const revealed = revealedCount ?? parts.length;
  const nextPartIn =
    revealed < total && timerRemaining != null && timerTotal != null
      ? Math.max(
          0,
          Math.ceil(revealed * partRevealInterval - (timerTotal - timerRemaining))
        )
      : null;

  return (
    <div className="progressive-question">
      <div className="progressive-meta">
        <span className="progressive-counter">
          Partie {revealed} / {total}
        </span>
        {nextPartIn != null && nextPartIn > 0 && revealed < total && (
          <span className="progressive-next">Prochaine partie dans {nextPartIn}s</span>
        )}
      </div>
      <div className="question-parts">
        {parts.map((part, i) => (
          <div key={i} className="question-part fade-in">
            <span className="part-label">Partie {i + 1}</span>
            <p className="part-text">{part}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
