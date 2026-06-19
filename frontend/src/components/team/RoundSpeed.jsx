import { useState } from "react";
import TimerDisplay from "../shared/TimerDisplay";

export default function RoundSpeed({
  question,
  answered,
  onAnswer,
  lastPoints,
  timerRemaining,
  timerTotal,
}) {
  const [selected, setSelected] = useState(null);

  function handle(option) {
    if (answered || selected) return;
    setSelected(option);
    onAnswer(option);
  }

  return (
    <div className="round-speed">
      <TimerDisplay
        remaining={timerRemaining}
        total={timerTotal}
        label="Temps restant"
        variant="speed"
      />
      <h2 className="texte-question">{question.question}</h2>
      <ul className="liste-options">
        {question.options.map((option) => (
          <li key={option}>
            <button
              className={`option ${selected === option ? "selected" : ""}`}
              onClick={() => handle(option)}
              disabled={answered || selected !== null}
            >
              {option}
            </button>
          </li>
        ))}
      </ul>
      {answered && lastPoints !== undefined && (
        <p className="feedback-pts">
          {lastPoints > 0 ? `+${lastPoints} pts !` : "0 pt"}
        </p>
      )}
    </div>
  );
}
