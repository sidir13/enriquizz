# EnriQuiz Party

Jeu de quiz multijoueur en temps réel (4 manches) — **FastAPI + React**, déployé comme **un seul Web Service** sur Render.

## Architecture monolithique

```
enriquizz/
├── frontend/          # React (Vite) — build → backend/static/
├── backend/
│   ├── main.py        # API REST + WebSocket + fichiers statiques
│   ├── questions/     # Un CSV par manche (manche1.csv … manche4.csv)
│   └── static/        # Frontend compilé (généré par npm run build)
└── render.yaml        # Blueprint Render (optionnel)
```

En production, **uvicorn** sert tout sur le même domaine :
- `/api/*` — REST
- `/ws` — WebSocket
- `/assets/*` — JS/CSS Vite
- `/*` — `index.html` (SPA React)

---

## Développement local

### Option A — Deux terminaux (recommandé en dev)

```bash
# Terminal 1 — Backend
cd backend
python -m venv env
# Windows : env\Scripts\activate
# macOS/Linux : source env/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (proxy /api et /ws → :8000)
cd frontend
npm install
npm run dev
```

Ouvrir **http://localhost:5173** — les appels API et WebSocket passent en relatif via le proxy Vite.

### Option B — Un seul processus (comme en prod)

```bash
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Ouvrir **http://localhost:8000**

---

## Déploiement Render (Single Web Service)

### Paramètres du dashboard

| Champ | Valeur |
|-------|--------|
| **Root Directory** | *(vide — racine du repo)* |
| **Runtime** | Python 3 |
| **Build Command** | `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt` |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |

Aucune variable `VITE_API_URL` ni Static Site séparé : le frontend est compilé dans `backend/static/` pendant le build.

### Blueprint (optionnel)

Importer `render.yaml` depuis le dashboard Render, ou créer le service manuellement avec les commandes ci-dessus.

### Persistance du CSV

Sur Render, le disque est éphémère. Les questions ajoutées via l’interface MJ sont perdues au redémarrage sauf si vous attachez un **Persistent Disk** (1 Go recommandé) monté sur le dossier `backend/`.

---

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/health` | Santé du service |
| `GET /api/questions` | Liste des questions |
| `POST /api/questions` | Ajouter une question (append CSV) |
| `WS /ws` | WebSocket multijoueur (salles, manches, buzzer) |

---

## Déroulement d’une partie

1. **MJ** → Maître du Jeu → code salle affiché
2. **Équipes** → nom + code salle (mobile)
3. MJ configure le timer, lance la partie, pilote les 4 manches

Voir aussi [DEPLOYMENT.md](./DEPLOYMENT.md) pour le dépannage détaillé.
