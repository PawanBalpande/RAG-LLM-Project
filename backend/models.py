from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    pages_loaded: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_indexed: Mapped[int] = mapped_column(Integer, nullable=False)
    collection_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    contexts_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

