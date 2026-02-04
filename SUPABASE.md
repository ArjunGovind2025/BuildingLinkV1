# Link Backend to Supabase

This project can use **Supabase** as the database (PostgreSQL) instead of SQLite.

## 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Click **New project**.
3. Choose organization, name, database password, and region. Click **Create new project**.

## 2. Get the database connection string

1. In the Supabase dashboard, open **Project Settings** (gear icon) → **Database**.
2. Under **Connection string**, choose **URI**.
3. Copy the URI. It looks like:
   ```text
   postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your database password (the one you set when creating the project).

## 3. Configure the backend

**Option A: Local (`.env` in project root)**

Create or edit `.env` in the project root (same folder as `backend/` and `frontend/`):

```env
# Supabase PostgreSQL (use the connection string from step 2)
DATABASE_URL=postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Optional: for future Supabase Auth / client features
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_ANON_KEY=your-anon-key
```

**Option B: Railway**

In your Railway service:

1. **Variables** → Add variable:
   - Name: `DATABASE_URL`
   - Value: the full Supabase connection string from step 2.

2. Redeploy so the new variable is used.

## 4. Run the backend

- **Local:** From `backend/`, run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
- **Railway:** Deployment will use `DATABASE_URL` automatically.

On startup, the app will create the `jobs` table in Supabase if it doesn’t exist.

## 5. Optional: Supabase URL and anon key

If you later add Supabase Auth or the Supabase JS client:

1. In Supabase: **Project Settings** → **API**.
2. Copy **Project URL** and **anon public** key.
3. Add to `.env` or Railway variables:
   - `SUPABASE_URL=https://xxxxx.supabase.co`
   - `SUPABASE_ANON_KEY=your-anon-key`

## Summary

| Environment   | What to set |
|---------------|-------------|
| Local `.env`  | `DATABASE_URL=postgresql://...` (Supabase connection string) |
| Railway       | Variable `DATABASE_URL` = same connection string |

Once `DATABASE_URL` points to your Supabase Postgres URI, the backend is linked to Supabase.
