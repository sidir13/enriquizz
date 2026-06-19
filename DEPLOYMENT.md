# Déploiement EnriQuiz Party sur Render

> **Architecture actuelle : monolithe** — un seul Web Service sert l’API, les WebSockets et le frontend React.  
> Voir [README.md](./README.md) pour la configuration complète.

## Render — Single Web Service

| Champ | Valeur |
|-------|--------|
| **Build Command** | `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt` |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |

Le build Vite écrit dans `backend/static/`. FastAPI monte `/assets` et renvoie `index.html` pour toutes les routes hors `/api` et `/ws`.

## Variables d'environnement

Aucune variable obligatoire pour l’URL de l’API (URLs relatives).

Optionnel : disque persistant pour `backend/questions.csv`.

## Checklist post-déploiement

- [ ] `https://VOTRE-APP.onrender.com/api/health` → `{"status":"ok"}`
- [ ] La page d’accueil React s’affiche sur `/`
- [ ] WebSocket se connecte sur `wss://VOTRE-APP.onrender.com/ws`
- [ ] (Optionnel) Persistent Disk pour conserver les questions ajoutées en jeu

## Dépannage

| Problème | Solution |
|----------|----------|
| Page blanche / 404 Frontend not built | Vérifier que le build command inclut `npm run build` |
| WebSocket échoue | Render supporte WS sur Web Services ; cold start ~30s en free tier |
| Questions perdues après redeploy | Attacher un Persistent Disk sur `backend/` |
| Dev local CORS | Utiliser `npm run dev` (proxy Vite) ou build + uvicorn seul |

## Développement local

```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend (autre terminal)
cd frontend && npm run dev
# → http://localhost:5173
```

Ou mode prod local :

```bash
cd frontend && npm run build
cd ../backend && uvicorn main:app --port 8000
# → http://localhost:8000
```
