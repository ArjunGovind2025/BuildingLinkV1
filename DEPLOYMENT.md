# Deployment Guide

This guide will help you deploy your Video to Acceptance Criteria application to public URLs.

**Backend:** Deploy via **Railway + GitHub** (Firebase deploy removed). See **[RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md)** for the full flow and local test step.

## Architecture

- **Frontend**: Next.js app deployed on Vercel (or static export)
- **Backend**: FastAPI app deployed on Railway via GitHub (or Render)

## Prerequisites

1. GitHub account (for connecting repositories)
2. Vercel account (free tier available)
3. Railway account (free tier available) or Render account

## Step 1: Deploy Backend to Railway

### Option A: Railway (Recommended)

1. **Install Railway CLI** (optional, but helpful):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy via Railway Dashboard**:
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account and select this repository
   - Railway will detect it's a Python project

3. **Configure Backend**:
   - Set the **Root Directory** to `backend`
   - Add environment variables:
     - `OPENAI_API_KEY` - Your OpenAI API key (required)
     - `OPENAI_PROJECT_ID` - If using project-scoped keys (optional)
     - `OPENAI_ORG_ID` - If using multiple organizations (optional)
     - `STORAGE_ROOT` - Set to `/app/storage` (optional, defaults work)
     - `DATABASE_URL` - Leave default or set custom SQLite path (optional)

4. **Get Backend URL**:
   - After deployment, Railway will provide a public URL like `https://your-app.up.railway.app`
   - Copy this URL - you'll need it for the frontend

### Option B: Render

1. Go to https://render.com
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
   - Set environment variables (same as Railway above)
5. Get the public URL from Render dashboard

## Step 2: Deploy Frontend to Vercel

1. **Install Vercel CLI** (optional):
   ```bash
   npm install -g vercel
   vercel login
   ```

2. **Deploy via Vercel Dashboard**:
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Next.js
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build` (auto-detected)
     - **Output Directory**: `.next` (auto-detected)

3. **Add Environment Variable**:
   - In Vercel project settings, go to "Environment Variables"
   - Add: `NEXT_PUBLIC_BACKEND_URL` = your backend URL from Railway/Render
     - Example: `https://your-app.up.railway.app`

4. **Redeploy**:
   - After adding the environment variable, trigger a new deployment
   - Vercel will provide a public URL like `https://your-app.vercel.app`

## Step 3: Update CORS (if needed)

The backend already has CORS configured to allow all origins (`allow_origins=["*"]`), so it should work with your Vercel frontend URL automatically.

If you want to restrict CORS to only your Vercel domain, update `backend/app/main.py`:

```python
allow_origins=["https://your-app.vercel.app", "http://localhost:3000"]
```

## Step 4: Test Your Deployment

1. Visit your Vercel frontend URL
2. Try uploading a video
3. Check that the API calls are working (check browser console for errors)

## Troubleshooting

### Backend Issues

- **Port**: Railway/Render sets `$PORT` automatically - make sure your start command uses it
- **Storage**: Files are stored in the container's filesystem. For persistence, consider using Railway volumes or external storage (S3, etc.)
- **Database**: SQLite file is stored in the container. For production, consider PostgreSQL (Railway offers free PostgreSQL)

### Frontend Issues

- **API Errors**: Check that `NEXT_PUBLIC_BACKEND_URL` is set correctly in Vercel
- **CORS Errors**: Ensure backend CORS allows your Vercel domain
- **Build Errors**: Check Vercel build logs for dependency issues

### Quick Local Test

To test with production backend locally:

```bash
cd frontend
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.up.railway.app npm run dev
```

## Alternative: Quick Testing with ngrok

For quick local testing with a public URL:

1. **Start backend locally**:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start frontend locally**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Expose with ngrok**:
   ```bash
   # Install ngrok: https://ngrok.com/download
   ngrok http 3000  # For frontend
   # In another terminal:
   ngrok http 8000  # For backend
   ```

4. Update `NEXT_PUBLIC_BACKEND_URL` to your ngrok backend URL

## Production Considerations

- **Database**: Consider migrating from SQLite to PostgreSQL for production
- **Storage**: Use cloud storage (S3, Cloudflare R2) for video files
- **Redis**: Optional but recommended for background jobs at scale
- **Monitoring**: Add error tracking (Sentry) and logging
- **Rate Limiting**: Add rate limiting to prevent abuse
