# Local development and testing

Run backend and frontend locally and test the upload flow before deploying.

## 1. Backend (port 8000)

From project root:

```bash
cd backend
pip install -r requirements.txt   # if not already
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave this running. You should see `Uvicorn running on http://127.0.0.1:8000`.

Optional: create a `.env` in project root with `OPENAI_API_KEY` (and optionally `OPENAI_PROJECT_ID`, `DATABASE_URL`) so the full pipeline (transcription, spec, acceptance criteria) runs. Without it, upload and job creation still work; the pipeline may fail at the AI step.

## 2. Frontend (port 3000 or 3001)

In another terminal:

```bash
cd frontend
# Ensure .env.local exists with:
#   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000 (or 3001 if 3000 is in use). The app will call the local backend for `/api/*`.

## 3. Test upload

- **Browser**: Open the app, choose a video (MP4 or WebM, max 32MB), click "Upload and process". You should be redirected to `/jobs/<id>` and see status (pending → processing → completed or failed).
- **Script**: From project root, with the backend running:
  ```bash
  ./scripts/test-upload-local.sh
  ```
  This checks health, creates a minimal test video if needed, POSTs it to `/api/jobs`, and GETs the job. It does not start the backend or frontend.

## 4. Verify output

- **Job page**: After upload, the job page polls `GET /api/jobs/:id` every 2s and shows status, spec, acceptance criteria, and evidence when ready.
- **Backend logs**: In the terminal where uvicorn is running, you should see lines like:
  - `request start method=POST path=/api/jobs content_length=...`
  - `create_job start filename=...`
  - `create_job body read size=... bytes`
  - `create_job success job_id=...`

If upload works locally but fails in production (e.g. Railway), check request size limits and timeouts in your host's logs.
