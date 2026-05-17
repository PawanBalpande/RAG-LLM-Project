from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_service import RagService


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

rag_service: RagService | None = None


def get_rag_service() -> RagService:
    global rag_service
    if rag_service is None:
        rag_service = RagService()
    return rag_service


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    service = get_rag_service()
    try:
        return service.ask(query=payload.query, top_k=payload.top_k)
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
    return {
        "status": "indexed_in_memory",
        "filename": file.filename,
        "pages_loaded": str(result["pages_loaded"]),
        "chunks_indexed": str(result["chunks_indexed"]),
        "collection_count": str(result["collection_count"]),
    }
