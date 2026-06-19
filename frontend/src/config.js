export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const base = API_URL.replace(/\/$/, "");
  return base.replace(/^http/, "ws") + "/ws";
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
