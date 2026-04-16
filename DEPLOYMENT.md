# Ayush-Guard Deployment Guide

This guide describes how to deploy the Ayush-Guard project. The project is split into two halves:
- **Frontend**: React (Vite) application suited for rapid static hosting.
- **Backend**: Python FastAPI service embedded with Machine Learning dependencies (SpaCy, Scikit-learn).

---

## 1. Frontend Deployment (Vercel)

Vercel provides extremely fast, out-of-the-box infrastructure for Vite/React applications.

### Steps:
1. Push your repository to GitHub.
2. Log into [Vercel](https://vercel.com) and click **"Add New Project"**.
3. Import the GitHub repository holding your Ayush-Guard code.
4. Expand the **"Build and Output Settings"**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend` (Important: do not leave it at the project root)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Map **Environment Variables**:
   - Add `VITE_API_BASE_URL` = `<URL_OF_YOUR_DEPLOYED_BACKEND>` (e.g., `https://ayush-guard-api.onrender.com`)
6. Click **Deploy**.

---

## 2. Backend Deployment (Render)

Render is an excellent Platform-as-a-Service capable of hosting the heavyweight Python/FastAPI environment required by the ML model.

### Can we just use Supabase for everything?
> [!NOTE]
> **No.** Supabase is solely a database Platform-as-a-Service (PostgreSQL + built-in Auth rules). Supabase does not run Docker containers or custom Python applications. You **must** host the FastAPI application elsewhere to provide the computational execution (NLP and ML analysis). However, your backend will continue to seamlessly point to your existing Supabase database via standard credentials.

### Render Specifications Required
- **CPU/RAM**: The NLP models (like `en_core_web_sm`) and Scikit-learn models consume roughly 500MB+ of RAM upon startup initialization. The standard Render Free Tier (512MB RAM) *might* encounter transient Out-Of-Memory (OOM) errors during startup. It is highly recommended to use the **Starter Tier ($7/mo - 512MB RAM but unthrottled)** or ideally **1GB RAM instances** for high availability.

### Steps to Deploy on Render:
1. Log into [Render](https://render.com) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
     > *Crucial Step: The SpaCy model isn't listed directly as a pip dependency artifact, so it must be downloaded via this inline build script.*
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set **Environment Variables** (matching your `.env` locally):
   - `SUPABASE_URL`: Your Supabase Project URL.
   - `SUPABASE_KEY`: Your Supabase Anon Key.
   - `SUPABASE_SERVICE_KEY`: Your Supabase Service Role Key (used for inserting data as an admin).
5. Click **Create Web Service**. Render will install the dependencies, execute the build step, and bind the Uvicorn ASGI server to the dynamic `$PORT`.

Once deployed, copy the Render URL and update your Vercel frontend's `VITE_API_BASE_URL` environment variable to link the two halves of the system.
