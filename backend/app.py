from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from typing import Any
from db import engine, get_session
from models import Base, ChatLog, UploadedDocument


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)


class ReindexRequest(BaseModel):
    chunk_size: int = Field(default=1000, ge=200, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)


app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service: Any = None


@app.on_event("startup")
def startup_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_rag_service():
    global rag_service
    if rag_service is None:
        from rag_service import RagService
        rag_service = RagService()
    return rag_service


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    service = get_rag_service()
    try:
        response = service.ask(query=payload.query, top_k=payload.top_k)
        with get_session() as session:
            session.add(
                ChatLog(
                    query=payload.query,
                    answer=response.get("answer", ""),
                    top_k=payload.top_k,
                    contexts_count=response.get("total_contexts", 0),
                )
            )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reindex")
def reindex(payload: ReindexRequest) -> dict:
    service = get_rag_service()
    try:
        return service.reindex_pdfs(
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reset")
def reset_vectorstore() -> dict:
    service = get_rag_service()
    try:
        return service.reset_collection()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, str]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    service = get_rag_service()
    result = service.index_uploaded_pdf(
        filename=file.filename, content=content)
    with get_session() as session:
        session.add(
            UploadedDocument(
                filename=file.filename,
                pages_loaded=result["pages_loaded"],
                chunks_indexed=result["chunks_indexed"],
                collection_count=result["collection_count"],
            )
        )
    return {
        "status": "indexed_in_memory",
        "filename": file.filename,
        "pages_loaded": str(result["pages_loaded"]),
        "chunks_indexed": str(result["chunks_indexed"]),
        "collection_count": str(result["collection_count"]),
    }


@app.get("/api/history")
def chat_history(limit: int = 20) -> dict[str, list[dict]]:
    with get_session() as session:
        rows = (
            session.query(ChatLog)
            .order_by(ChatLog.created_at.desc())
            .limit(limit)
            .all()
        )
    return {
        "history": [
            {
                "id": row.id,
                "query": row.query,
                "answer": row.answer,
                "top_k": row.top_k,
                "contexts_count": row.contexts_count,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }
