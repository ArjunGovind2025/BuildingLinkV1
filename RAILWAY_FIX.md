# Railway Build Fix - CRITICAL STEP

## ⚠️ You MUST Do This in Railway Dashboard:

The build is failing because Railway is scanning the root directory. You need to tell it to use the `backend` folder.

### Step-by-Step Fix:

1. **Go to Railway Dashboard**: https://railway.app
2. **Click on your service** (BuildingLinkV1)
3. **Go to "Settings" tab**
4. **Scroll down to "Root Directory"**
5. **Set it to**: `backend`
6. **Click "Save"**

Railway will automatically trigger a new deployment.

### Why This Fixes It:

- Railway scans the root directory by default
- Your Python app is in the `backend/` folder
- Setting Root Directory = `backend` tells Railway where to look
- Now it will find `requirements.txt`, `nixpacks.toml`, and your Python files

### After Setting Root Directory:

✅ Railway will detect Python from `runtime.txt`  
✅ Install dependencies from `requirements.txt`  
✅ Use the `nixpacks.toml` config  
✅ Start your FastAPI app  

**The deployment should succeed within 2-3 minutes!**

---

## Alternative: If Root Directory Setting Doesn't Work

If you still have issues after setting Root Directory, try:

1. Delete the service in Railway
2. Create a new service
3. **Immediately** set Root Directory to `backend` BEFORE the first deployment
4. Add environment variables
5. Generate domain

This ensures Railway knows where to look from the start.
