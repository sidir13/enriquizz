# Déploiement EnriQuiz Party sur Render

Ce guide décrit le déploiement du backend (Web Service FastAPI) et du frontend (Static Site Vite/React) sur [Render](https://render.com).

## Architecture

| Service | Type Render | Rôle |
|---------|-------------|------|
| `enriquiz-api` | **Web Service** (Python) | API REST + WebSockets (`/ws`) |
| `enriquiz-web` | **Static Site** | Interface React (MJ + Équipes) |

## 1. Backend — Web Service

### Paramètres Render

- **Root Directory** : `backend`
- **Runtime** : Python 3.13 (ou 3.11+)
- **Build Command** :
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command** :
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### Variables d'environnement

| Variable | Exemple | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `https://enriquiz-web.onrender.com,http://localhost:5173` | Origines autorisées (séparées par des virgules). **Retirez `*` en production.** |

### Fichiers persistants

Les questions ajoutées via l'interface MJ sont écrites dans `questions.csv`. Sur Render, le disque du conteneur est **éphémère** : les ajouts sont perdus au redémarrage sauf si vous attachez un **Persistent Disk** monté sur `/opt/render/project/src/backend` (ou le chemin de `questions.csv`).

> **Recommandation prod** : ajoutez un disque persistant de 1 Go pointant vers le dossier `backend/`.

### URL WebSocket

L'API expose le WebSocket sur :
```
wss://VOTRE-BACKEND.onrender.com/ws
```

Render supporte les WebSockets sur les Web Services sans configuration supplémentaire.

---

## 2. Frontend — Static Site

### Paramètres Render

- **Root Directory** : `frontend`
- **Build Command** :
  ```bash
  npm install && npm run build
  ```
- **Publish Directory** : `dist`

### Variables d'environnement (build time)

| Variable | Exemple | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `https://enriquiz-api.onrender.com` | URL du backend (REST) |
| `VITE_WS_URL` | `wss://enriquiz-api.onrender.com/ws` | URL WebSocket (optionnel — dérivée de `VITE_API_URL` si absent) |

> Les variables `VITE_*` sont injectées **au moment du build**. Après modification, relancez un déploiement.

---

## 3. Développement local

### Backend

```bash
cd backend
python -m venv env
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Créez `frontend/.env.local` (optionnel) :

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 4. Déroulement d'une partie

1. Le **MJ** ouvre l'app → **Maître du Jeu** → un code salle s'affiche (ex. `K7X2M`).
2. Chaque **équipe** ouvre l'app sur mobile → **Rejoindre une équipe** → nom + code.
3. Le MJ configure le timer global, ajoute des questions si besoin, puis **Lancer la partie**.
4. Le MJ pilote les 4 manches : countdown, validation buzzer (manches 3 & 4), ajustement manuel des points.

---

## 5. Checklist post-déploiement

- [ ] Backend `/api/health` répond `{"status":"ok"}`
- [ ] Frontend charge sans erreur CORS
- [ ] WebSocket se connecte (`wss://.../ws`) depuis le navigateur
- [ ] `CORS_ORIGINS` contient l'URL exacte du Static Site
- [ ] (Optionnel) Disque persistant pour `questions.csv`

---

## 6. Dépannage

| Problème | Solution |
|----------|----------|
| CORS bloqué | Vérifier `CORS_ORIGINS` côté backend |
| WebSocket déconnecté | Render free tier : cold start ~30s ; le client reconnecte automatiquement |
| Questions perdues après redeploy | Attacher un Persistent Disk ou externaliser le CSV |
| `VITE_API_URL` ignorée | Rebuild le Static Site après changement de variable |
