# Docker instructions

Prerequisites: Docker Desktop or Docker Engine + docker-compose.

Quick start (PowerShell):

```powershell
# from repo root
docker-compose build
docker-compose up
```

Services:
- Backend: http://localhost:8000 (FastAPI)
- Frontend: http://localhost:3000 (built site served by nginx)

Notes:
- For security, do NOT commit secrets into the repo. Instead set the `HUGGINGFACE_API_KEY` as an environment variable on your host.

Local setup (PowerShell):

```powershell
# copy example and set key locally (do NOT commit this file)
copy .\HandwrittenNotes\backend\.env.example .\HandwrittenNotes\backend\.env
notepad .\HandwrittenNotes\backend\.env
# add your key as: HUGGINGFACE_API_KEY=sk_your_real_key_here

# Or set the environment variable directly for the current session before running compose:
$env:HUGGINGFACE_API_KEY = 'sk_your_real_key_here'
docker-compose up --build
```

- The SQLite DB is persisted in `HandwrittenNotes/backend/database.db` (host path) and uploads/results are persisted in `HandwrittenNotes/backend/uploads` and `.../results`.
- For live frontend development we run Vite dev server on port 5000 (see `docker-compose.override.yml`).
