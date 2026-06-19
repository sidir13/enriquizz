export default function Scoreboard({ teams, highlightId }) {
  if (!teams?.length) {
    return <p className="sous-titre">Aucune équipe connectée</p>;
  }

  return (
    <ul className="scoreboard">
      {teams.map((team, i) => (
        <li
          key={team.team_id}
          className={`scoreboard-item ${team.team_id === highlightId ? "highlight" : ""}`}
        >
          <span className="scoreboard-rang">{i + 1}</span>
          <span className="scoreboard-nom">{team.name}</span>
          <span className="scoreboard-pts">{team.score} pts</span>
          {team.locked_out && <span className="badge-locked">Locked</span>}
        </li>
      ))}
    </ul>
  );
}
