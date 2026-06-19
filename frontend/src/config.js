/** URLs relatives — même origine en prod (monolithe) ; proxy Vite en dev. */
export function getWsUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export const MANCHE_LABELS = {
  1: "Classique Q&R",
  2: "Partie Rapidité",
  3: "Le Big Buzzer",
  4: "Face-à-Face Final",
};

export const ROUND3_CLAIMS = [
  { id: "cash", label: "Cash", reward: "+10", penalty: "-2" },
  { id: "carre", label: "Carré", reward: "+6", penalty: "-6" },
  { id: "duo", label: "Duo", reward: "+2", penalty: "-8" },
];
