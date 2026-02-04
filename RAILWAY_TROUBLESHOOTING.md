# Railway Troubleshooting

## "Failed to get private network endpoint" - Not a Problem!

This message is **not an error** - it's just Railway trying to set up private networking, which is only needed if you have multiple services that need to talk to each other privately.

**Your backend will still work perfectly fine** with its public URL. You can ignore this message.

## Check if Your Backend is Working

1. **Get your backend URL:**
   - Go to Railway dashboard → Your service → Settings
   - Look for "Generate Domain" or check the "Networking" tab
   - Copy the public URL (e.g., `https://your-app.up.railway.app`)

2. **Test the backend:**
   ```bash
   curl https://your-app.up.railway.app/api/jobs
   ```
   
   You should see: `{"detail":"Method Not Allowed"}` - this means it's working! (GET isn't allowed, but POST is)

3. **Update your frontend:**
   ```bash
   ./fix-backend-url.sh https://your-app.up.railway.app
   ```

## Common Issues

### Build Failed
- Make sure **Root Directory** is set to `backend` in Railway settings
- Check that environment variables are set (OPENAI_API_KEY, OPENAI_PROJECT_ID)

### Service Not Starting
- Check the logs in Railway dashboard
- Verify the start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### CORS Errors
- Your backend already has CORS configured to allow all origins
- If you see CORS errors, check that your frontend URL matches what's allowed

## Private Networking (Optional)

Private networking is only needed if:
- You have multiple Railway services
- You want them to communicate privately (not over public internet)
- You're using Railway's internal DNS

For a single backend service, **you don't need this feature**.
