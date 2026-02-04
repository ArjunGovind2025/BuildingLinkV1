# Quick Deploy Instructions

Your code is now on GitHub: https://github.com/ArjunGovind2025/BuildingLinkV1

## Automated Deployment (After Authentication)

Once you're logged into both Railway and Vercel, run:

```bash
./deploy-now.sh
```

But first, you need to authenticate:

### Step 1: Login to Railway
```bash
railway login
```
This will open a browser - complete the authentication there.

### Step 2: Login to Vercel  
```bash
vercel login
```
This will open a browser - complete the authentication there.

### Step 3: Run Deployment Script
```bash
./deploy-now.sh
```

---

## OR: Web-Based Deployment (Easier - No CLI needed)

### Backend on Railway (5 minutes)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select repository: **ArjunGovind2025/BuildingLinkV1**
4. After it starts deploying, click on the service
5. Go to "Variables" tab
6. Add: `OPENAI_API_KEY` = your OpenAI API key
7. Go to "Settings" → "Root Directory" → Set to: `backend`
8. Go to "Settings" → "Generate Domain" → Copy the URL (e.g., `https://xxx.up.railway.app`)

### Frontend on Vercel (3 minutes)

1. Go to https://vercel.com
2. Click "Add New Project"
3. Import from GitHub: **ArjunGovind2025/BuildingLinkV1**
4. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend` (click "Edit" and set this)
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)
5. Click "Environment Variables"
6. Add: `NEXT_PUBLIC_BACKEND_URL` = your Railway backend URL from above
7. Click "Deploy"

### Done! 🎉

Your frontend URL will be shown in Vercel dashboard (e.g., `https://building-link-v1.vercel.app`)
