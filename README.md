# Video to Acceptance Criteria

Convert a narrated screen recording into acceptance criteria with evidence: feature summary, user stories, GIVEN/WHEN/THEN criteria, and open questions. Every requirement is traceable to a timestamp, transcript excerpt, and screenshot (captured only when the screen meaningfully changes via pixel diff).

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLite (SQLAlchemy), ffmpeg, OpenCV. Background pipeline runs in a thread (no Redis required for MVP).
- **APIs:** OpenAI Whisper (transcription), GPT-4o (vision + spec + acceptance criteria).
- **Frontend:** Next.js 15 (App Router), TypeScript.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` in the **project root** (e.g. `BuildingLinkV1/.env`) with:

- `OPENAI_API_KEY` – required for transcription, vision, and LLM.

If you use a **project API key** (starts with `sk-proj-`) and get 401 invalid_api_key, add your project ID from https://platform.openai.com/settings (select your project, copy the project ID):

- `OPENAI_PROJECT_ID` – optional; required for project-scoped keys (`sk-proj-*`).
- `OPENAI_ORG_ID` – optional; use if you have multiple organizations.

Optional:

- `STORAGE_ROOT` – directory for jobs (default: project root `storage/`).
- `DATABASE_URL` – default `sqlite:///./storage/video2ac.db` (relative to CWD when running from `backend/`).

Ensure **ffmpeg** is installed and on `PATH`. Ensure **storage** exists (created on first request if using defaults).

Run the API:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The Next app rewrites `/api/*` to http://localhost:8000, so the backend must be running on port 8000.

## Usage

1. **Upload:** On the home page, choose a video (MP4 or WebM, max 500MB) and click “Upload and process.”
2. **Status:** You are redirected to the job page; status is polled until `completed` or `failed`.
3. **Results:** When complete, you see feature summary, user stories, spec (editable JSON), acceptance criteria with evidence (timestamp + transcript + screenshot thumbnail), and open questions.
4. **Edit:** Edit the spec JSON and click “Save”; then “Regenerate from spec” to regenerate acceptance criteria.
5. **Export:** Download Markdown or JSON (Jira/Linear-friendly).

## Pipeline

1. **Ingest:** Video saved under `storage/jobs/{jobId}/`, job row created, pipeline started in background.
2. **Media:** ffmpeg extracts audio to WAV; OpenCV decodes frames, computes pixel diff (downscaled grayscale), captures PNG screenshots when diff exceeds threshold and min interval (2s).
3. **Transcription:** OpenAI Whisper produces timestamped segments → `transcript.json`.
4. **Vision:** For each screenshot, GPT-4o describes UI (page, elements, errors, empty states, navigation) → cached under `cache/vision/`.
5. **Grounding:** Transcript segments aligned to screenshots by timestamp → `grounded_chunks.json`.
6. **Spec:** LLM turns grounded chunks into structured spec (feature_summary, user_stories, workflows, business_rules, permissions, open_questions) with evidence_refs; invalid JSON is repaired.
7. **Acceptance criteria:** LLM converts spec to GIVEN/WHEN/THEN with evidence_refs; saved and persisted to DB.

## Success criteria

- PM can generate acceptance criteria from a single narrated screen recording.
- Each requirement can be traced to a precise moment (timestamp + transcript + screenshot).
- Minimal manual edits needed for correctness; spec and AC are editable and regeneratable.
