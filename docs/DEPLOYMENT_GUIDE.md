# IDMAP Production Deployment Guide

This guide details how to decouple code from large datasets (e.g. `images.h5`, `data.zip`) and deploy the full **IDMAP (Intelligent Disaster Mitigation and Prediction)** platform to production.

---

## 1. Architecture Overview

```
                      ┌───────────────────────────────────────┐
                      │          GitHub (Source Code)         │
                      │  (FastAPI, React Vite, Prisma Schemas)│
                      └──────────────────┬────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼ (CI / CD)                                     ▼ (CI / CD)
     ┌───────────────────────┐                       ┌───────────────────────┐
     │  Frontend Deployment  │                       │   Backend Deployment  │
     │  (Vercel / Netlify)   │                       │ (Render / Cloud Run)  │
     │                       │                       │                       │
     │  VITE_API_URL ───────┼──────────────────────►│  FastAPI (Port 8000)  │
     └───────────────────────┘                       └───────────┬───────────┘
                                                                 │
                                          ┌──────────────────────┼──────────────────────┐
                                          │                      │                      │
                                          ▼                      ▼                      ▼
                               ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
                               │  Managed Database  │ │ Cloud Object Store │ │ External APIs      │
                               │  (Neon PostgreSQL) │ │  (Cloudflare R2/S3)│ │ (Open-Meteo, NASA) │
                               └────────────────────┘ └────────────────────┘ └────────────────────┘
```

---

## 2. Managing Large Datasets & Model Weights

Because datasets like `images.h5` (~5.2 GB) and census sheets exceed GitHub's 100 MB file limit:

1. **Source Code vs Big Data Separation**:
   - Source code, API routes, React UI, Prisma schemas, and lightweight regression weights are committed to GitHub.
   - Raw multi-gigabyte training sets (`data/`, `data.zip`, `*.h5`) are kept in [`.gitignore`](file:///c:/Professional/Projects/IDMAP/.gitignore).

2. **Storage for Large Datasets & Checkpoints**:
   - **Cloudflare R2 / AWS S3**: Store large training datasets (`data.zip`, `images.h5`) for automated downloading during model retraining jobs.
   - **Hugging Face Hub**: Free hosting for open-source model checkpoints (`*.pt`, `*.onnx`).
   - Run `python scripts/download_assets.py --verify` on servers to verify or fetch missing models.

---

## 3. Recommended Deployment Routes

### Route A: Serverless PaaS (Fastest & Free-Tier Friendly)

#### 1. Database (Neon PostgreSQL)
- Create a free serverless PostgreSQL database at [Neon.tech](https://neon.tech).
- Grab the connection string: `postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require`.

#### 2. Backend (Render / Railway / Google Cloud Run)
- Connect your GitHub repository to **Render** or **Railway**.
- Set the build type to **Docker** (using the root [`Dockerfile`](file:///c:/Professional/Projects/IDMAP/Dockerfile)) or Python runtime.
- Set Environment Variables:
  ```env
  DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require
  GEMINI_API_KEY=your_gemini_api_key_here
  CORS_ORIGINS=https://idmap.vercel.app
  PORT=8000
  ```

#### 3. Frontend (Vercel / Netlify)
- Import the `frontend` folder into [Vercel](https://vercel.com).
- Build command: `npm run build`
- Output directory: `dist`
- Environment Variables:
  ```env
  VITE_API_URL=https://your-backend-service.onrender.com
  ```

---

### Route B: Containerized VM Deployment (Docker Compose)

Deploy everything on a single Ubuntu VM (AWS EC2 / DigitalOcean Droplet / Hetzner Cloud):

1. **Clone the repository onto the server**:
   ```bash
   git clone https://github.com/your-username/IDMAP.git
   cd IDMAP
   ```

2. **Configure `.env`**:
   ```bash
   cp .env.example .env
   nano .env
   # Add your DATABASE_URL and GEMINI_API_KEY
   ```

3. **Start the containers**:
   ```bash
   docker compose up -d --build
   ```
   - Frontend is served on port `3000` (or `80` with Nginx reverse proxy).
   - Backend API is accessible on port `8000`.

---

## 4. Verification & Health Checks

Once deployed, verify your service endpoints:
- **API Health**: `GET /api/status` -> returns system health, database connectivity status, and loaded models.
- **Frontend**: Check that all tabs (Overview, Advisory, Live Weather, Spatial Forecast, Resource Allocation) load data from the API seamlessly.
