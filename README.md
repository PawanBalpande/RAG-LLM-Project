# RAG Project (Backend + React UI)

This project now has:
- FastAPI backend for RAG query (`/api/chat`)
- React frontend UI to ask questions from your PDF vectorstore

## Project Structure

- `backend/app.py`: FastAPI app
- `backend/rag_service.py`: retrieval + LLM answer flow
- `frontend/`: React + Vite UI
- `data/vectorstore/`: existing ChromaDB persistence

## 1) Setup Python Environment

```bash
cd /Users/pawanbalpande/Desktop/RAG
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install fastapi uvicorn
```

## 2) Add API Key

In `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

## 3) Run Backend

```bash
cd /Users/pawanbalpande/Desktop/RAG
source .venv/bin/activate
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Health check:
- `http://127.0.0.1:8000/health`

## 4) Run Frontend

In another terminal:

```bash
cd /Users/pawanbalpande/Desktop/RAG/frontend
npm install
npm run dev
```

Open:
- `http://127.0.0.1:5173`

## Notes

- The UI posts to `http://127.0.0.1:8000/api/chat`.
- If retrieval seems stale, rebuild/reinsert embeddings into the same Chroma collection (`pdf_documents`).
