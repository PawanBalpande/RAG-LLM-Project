# RAG Project (FastAPI + React + Docker)

## Deploy (Render + Vercel)

### Backend on Render (Docker)
1. Push this repo to GitHub.
2. In Render, create **New Web Service** and connect the repo.
3. Render will auto-detect `render.yaml`.
4. Add env var:
   - `GROQ_API_KEY`
   - `DATABASE_URL` (Render PostgreSQL connection string)
5. Deploy and copy backend URL, for example:
   - `https://rag-llm-backend.onrender.com`

### Frontend on Vercel
1. Import the repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Add env var in Vercel project:
   - `VITE_API_BASE=https://your-render-backend-url/api`
4. Deploy.

## Prerequisites
- Docker + Docker Compose
- Groq API key in `.env`
- PostgreSQL database URL (for persistent metadata/chat logs)

`.env`:
```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://username:password@host:5432/dbname
```

## Run With Docker Compose (Recommended)
```bash
cd /Users/pawanbalpande/Desktop/RAG
docker compose up --build
```

Open:
- Frontend: `http://127.0.0.1:5173`
- Backend docs: `http://127.0.0.1:8000/docs`

## Run Backend Container Only
```bash
cd /Users/pawanbalpande/Desktop/RAG
docker build -t rag-backend .
docker run --rm -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" rag-backend
```

## Local Frontend (without Docker)
```bash
cd /Users/pawanbalpande/Desktop/RAG/frontend
cp .env.example .env
npm install
npm run dev
```

If backend is remote, set `VITE_API_BASE` in `frontend/.env`:
```env
VITE_API_BASE=https://your-backend-url/api
```
