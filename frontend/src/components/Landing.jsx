export default function Landing({ onSelectRole }) {
  return (
    <div className="container centré fade-in">
      <div className="carte landing-carte">
        <h1 className="app-titre app-titre-grand">EnriQuiz Party</h1>
        <p className="sous-titre landing-sous-titre">
          Jeu multijoueur en temps réel — 4 manches, buzzers et scores live.
        </p>
        <div className="landing-actions">
          <button
            className="btn btn-primaire btn-large"
            onClick={() => {
              sessionStorage.removeItem("enriquiz_host_room");
              onSelectRole("host");
            }}
          >
            Maître du Jeu
          </button>
          <button
            className="btn btn-secondaire btn-large"
            onClick={() => {
              sessionStorage.removeItem("enriquiz_team_session");
              onSelectRole("team");
            }}
          >
            Rejoindre une équipe
          </button>
        </div>
      </div>
    </div>
  );
}
