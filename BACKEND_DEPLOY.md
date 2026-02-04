# Deploy Backend (Railway via GitHub)

**Use [RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md) for the full flow.** Summary:

1. **Test locally first**: `./scripts/test-backend-local.sh`
2. **Railway** → New Project → Deploy from GitHub repo → **Root Directory** = `backend`
3. Add **Variables**: `OPENAI_API_KEY`, optionally `OPENAI_PROJECT_ID`, `DATABASE_URL`
4. **Generate Domain** in Settings, then verify: `curl https://YOUR-URL.up.railway.app/api/health`
5. Set frontend env `NEXT_PUBLIC_BACKEND_URL` to that URL (Vercel or `./fix-backend-url.sh <url>`)

---

## 🔄 Alternative: Render (Also Easy)

1. Go to **https://render.com** and sign up/login
2. Click **"New"** → **"Web Service"**
3. Connect GitHub and select **ArjunGovind2025/BuildingLinkV1**
4. Configure:
   - **Name**: buildinglink-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend` (if available)
5. Add environment variables (same as Railway above)
6. Click **"Create Web Service"**
7. Copy the URL when it's ready

---

## ⚡ Quick Script

Run this for guided deployment:
```bash
./deploy-backend-easy.sh
```
