# Deploy Backend via Railway + GitHub

Deployment is **Railway (backend) + GitHub**. Firebase deploy has been removed.

## 1. Test backend locally (recommended)

From repo root:

```bash
./scripts/test-backend-local.sh
```

You should see `{"status":"ok"}` from `/api/health`. Then deploy.

## 2. Deploy backend to Railway from GitHub

1. **Railway**: Go to [railway.app](https://railway.app) → sign in (e.g. with GitHub).
2. **New project** → **Deploy from GitHub repo** → connect and select this repository.
3. **Settings** for the new service:
   - **Root Directory**: set to `backend` (required).
   - **Generate Domain** (Settings → Generate Domain) and copy the URL (e.g. `https://xxx.up.railway.app`).
4. **Variables** tab: add at least:
   - `OPENAI_API_KEY` (required for AI)
   - `OPENAI_PROJECT_ID` (if you use project-scoped keys)
   - `DATABASE_URL` (optional; if not set, SQLite is used)

Railway will build with the **Dockerfile** in `backend/` (avoids the Nixpacks `libstdc++.so.6` issue with numpy/OpenCV). If you see that error, ensure Root Directory is `backend` and redeploy. Every push to the connected branch will redeploy.

## 3. Verify deployed backend

```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/api/health
# Expect: {"status":"ok"}
```

## 4. Frontend (Vercel or static)

- **Vercel**: New project from same GitHub repo → Root Directory `frontend` → add env `NEXT_PUBLIC_BACKEND_URL` = your Railway URL.
- **Local build**: `./fix-backend-url.sh https://YOUR-RAILWAY-URL.up.railway.app` then deploy the `frontend/out` (or use Vercel).

## Troubleshooting

- **Build fails**: Ensure **Root Directory** is set to `backend` in Railway (see [RAILWAY_FIX.md](./RAILWAY_FIX.md)).
- **502 / timeout**: Check Railway logs; ensure `PORT` is used (the app uses `$PORT`).
- **libstdc++.so.6 / numpy ImportError**: The repo uses a Dockerfile for the backend so this should not occur. If you still see it, in Railway → Service → Settings set builder to **Dockerfile** (or ensure Root Directory is `backend` so `backend/Dockerfile` is used).
- **Health check**: Use `/api/health`; avoid relying on `/api/jobs` for “up” checks (method/route may differ).
