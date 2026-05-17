import os
import uuid
from pathlib import Path
from typing import Any

import chromadb
import fitz
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer


class RagService:
    def __init__(
        self,
        persist_directory: str = "data/vectorstore",
        collection_name: str = "pdf_documents",
        embedding_model: str = "all-MiniLM-L6-v2",
        llm_model: str = "llama-3.1-8b-instant",
    ):
        load_dotenv()

        root = Path(__file__).resolve().parents[1]
        self.persist_directory = str((root / persist_directory).resolve())
        self.collection_name = collection_name

        self.embedder = SentenceTransformer(embedding_model)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model=llm_model,
            temperature=0.1,
            max_tokens=1024,
        )

    def ask(self, query: str, top_k: int = 4) -> dict[str, Any]:
        query_vec = self.embedder.encode([query])[0].tolist()

        result = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        contexts = []
        for doc, meta, distance in zip(docs, metas, distances):
            contexts.append(
                {
                    "content": doc,
                    "metadata": meta,
                    "distance": distance,
                }
            )

        context_text = "\n\n".join([c["content"] for c in contexts]) if contexts else "No relevant context found."

        prompt = f"""You are a helpful RAG assistant.
Answer only from the provided context.
If answer is not in context, say you don't have enough information.

Context:
{context_text}

Question:
{query}

Answer:
"""

        response = self.llm.invoke(prompt)

        return {
            "query": query,
            "answer": response.content,
            "contexts": contexts,
            "total_contexts": len(contexts),
        }

    def index_uploaded_pdf(
        self,
        filename: str,
        content: bytes,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> dict[str, int]:
        pdf = fitz.open(stream=content, filetype="pdf")
        documents: list[Document] = []
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if text and text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": filename, "page": page_number},
                    )
                )

        if not documents:
            raise ValueError("Uploaded PDF has no extractable text.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        texts = [doc.page_content for doc in chunks]
        metadatas = [dict(doc.metadata) for doc in chunks]
        ids = [f"upload_{uuid.uuid4().hex}" for _ in chunks]
        embeddings = self.embedder.encode(texts).tolist()

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return {
            "pages_loaded": len(documents),
            "chunks_indexed": len(chunks),
            "collection_count": self.collection.count(),
        }

    def reindex_pdfs(
        self,
        pdf_directory: str = "data/pdf",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> dict[str, int]:
        root = Path(__file__).resolve().parents[1]
        target_dir = (root / pdf_directory).resolve()
        if not target_dir.exists():
            raise ValueError(f"PDF directory does not exist: {target_dir}")

        loader = DirectoryLoader(
            str(target_dir),
            glob="**/*.pdf",
            loader_cls=PyMuPDFLoader,
            show_progress=True,
        )
        documents = loader.load()
        if not documents:
            raise ValueError("No PDF documents found to index.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(documents)

        ids = [f"chunk_{i}" for i in range(len(chunks))]
        texts = [doc.page_content for doc in chunks]
        metadatas = [dict(doc.metadata) for doc in chunks]
        embeddings = self.embedder.encode(texts).tolist()

        # Reset collection so count reflects latest documents.
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return {
            "documents_loaded": len(documents),
            "chunks_indexed": len(chunks),
            "collection_count": self.collection.count(),
        }

    def reset_collection(self) -> dict[str, int | str]:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        return {
            "status": "reset",
            "collection_name": self.collection_name,
            "collection_count": self.collection.count(),
        }
