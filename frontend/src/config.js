/** En dev : connexion directe au backend (évite les erreurs ECONNABORTED du proxy Vite). */
export function getWsUrl() {
  if (import.meta.env.DEV) {
    return "ws://127.0.0.1:8000/ws";
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export const MANCHE_LABELS = {
  1: "Rapide et vif",
  2: "Duo / Carré / Cash",
  3: "Buzzer oral",
  4: "Question pour un champion",
};

export const ROUND2_CLAIMS = [
  { id: "duo", label: "Duo", reward: "+2", penalty: "-8" },
  { id: "carre", label: "Carré", reward: "+4", penalty: "-6" },
  { id: "cash", label: "Cash", reward: "+8", penalty: "-2" },
];

/** @deprecated use ROUND2_CLAIMS */
export const ROUND3_CLAIMS = ROUND2_CLAIMS;
