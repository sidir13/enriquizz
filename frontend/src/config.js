/** URLs relatives — même origine en prod (monolithe) ; proxy Vite en dev. */
export function getWsUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export const MANCHE_LABELS = {
  1: "Classique Q&R",
  2: "Rapide et vif, comme le enrizizi",
  3: "CASH DANS LE CUL",
  4: "Touche ma question et devine la réponse",
};

export const ROUND3_CLAIMS = [
  { id: "duo", label: "Duo", reward: "+2", penalty: "-8" },
  { id: "carre", label: "Carré", reward: "+6", penalty: "-6" },
  { id: "cash", label: "Cash", reward: "+10", penalty: "-2" },
];
