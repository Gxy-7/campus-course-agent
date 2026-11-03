import logging
import os
import re
import shutil
import time
import uuid
from pathlib import Path

import jieba
from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader
from rank_bm25 import BM25Plus
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import (
    COURSE_DOC_DIR,
    COURSE_DOC_EXTENSIONS,
    MAX_COURSE_DOC_SIZE,
)
from app.models.course_docs import CourseDocChunk, CourseDocument
from app.models.courses import Course
from app.schemas.course_doc import CourseDocumentResponse
from app.services import vector_service
from app.services.course_service import get_course_or_404

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """中文分词，过滤空白和纯标点 token"""
    return [
        token.strip()
        for token in jieba.lcut_for_search(text)
        if token.strip() and re.search(r"[\w\u4e00-\u9fff]", token)
    ]


def _split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按固定长度切块，并保留少量重叠，避免语义被切断"""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def _extract_pages(path: Path, file_type: str) -> list[tuple[str, int | None]]:
    """抽取文本，返回 (文本, 页码) 列表"""
    if file_type in {".txt", ".md"}:
        raw = path.read_bytes()
        for encoding in ("utf-8", "gbk"):
            try:
                return [(raw.decode(encoding), None)]
            except UnicodeDecodeError:
                continue
        return [(raw.decode("utf-8", errors="ignore"), None)]

    if file_type == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((text, index + 1))
        return pages

    if file_type == ".docx":
        document = Document(str(path))
        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )
        return [(text, None)] if text.strip() else []

    raise BusinessException(message=f"暂不支持的文件类型：{file_type}")


def _to_response(
    document: CourseDocument, course: Course
) -> CourseDocumentResponse:
    return CourseDocumentResponse(
        id=document.id,
        course_id=document.course_id,
        course_name=course.name,
        title=document.title,
        original_name=document.original_name,
        file_type=document.file_type,
        char_count=document.char_count,
        chunk_count=document.chunk_count,
        create_time=document.create_time,
    )


def create_document(
    db: Session,
    course_id: int,
    title: str | None,
    upload: UploadFile,
    uploaded_by: int,
) -> CourseDocumentResponse:
    """保存文件、抽取文本、切块并入库"""
    course = get_course_or_404(db, course_id)

    original_name = os.path.basename(upload.filename or "")
    if not original_name:
        raise BusinessException(message="文件名不能为空")

    file_type = Path(original_name).suffix.lower()
    if file_type not in COURSE_DOC_EXTENSIONS:
        raise BusinessException(
            message="只支持 .txt / .md / .pdf / .docx 文件"
        )

    if upload.size and upload.size > MAX_COURSE_DOC_SIZE:
        raise BusinessException(message="资料不能超过 20MB")

    disk_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{file_type}"
    file_path = COURSE_DOC_DIR / disk_name

    # 先保存文件，后续抽取失败要清理
    with open(file_path, "wb") as file_obj:
        shutil.copyfileobj(upload.file, file_obj)

    try:
        pages = _extract_pages(file_path, file_type)
        chunks: list[tuple[str, int | None]] = []
        for text, page_number in pages:
            for piece in _split_text(text):
                chunks.append((piece, page_number))

        if not chunks:
            raise BusinessException(
                message="没有从文件中抽取到文本，可能是扫描版 PDF"
            )

        char_count = sum(len(piece) for piece, _ in chunks)
        document = CourseDocument(
            course_id=course_id,
            title=(title or Path(original_name).stem)[:150],
            original_name=original_name[:255],
            disk_name=disk_name,
            file_type=file_type,
            char_count=char_count,
            chunk_count=len(chunks),
            uploaded_by=uploaded_by,
        )
        db.add(document)
        db.flush()

        for index, (content, source_page) in enumerate(chunks):
            db.add(
                CourseDocChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                    source_page=source_page,
                )
            )

        db.commit()
        db.refresh(document)

        # 向量化失败不阻断上传，之后可以通过“重新入库”补
        if vector_service.is_configured():
            try:
                vector_service.vectorize_document(db, document.id)
            except Exception:
                logger.exception(
                    "Vectorize document failed: %s", document.id
                )

        return _to_response(document, course)
    except Exception:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise


def get_documents(
    db: Session, course_id: int | None = None
) -> list[CourseDocumentResponse]:
    query = (
        db.query(CourseDocument, Course)
        .join(Course, Course.id == CourseDocument.course_id)
    )
    if course_id is not None:
        query = query.filter(CourseDocument.course_id == course_id)

    rows = query.order_by(CourseDocument.id.desc()).all()
    return [_to_response(document, course) for document, course in rows]


def delete_document(db: Session, document_id: int) -> None:
    document = (
        db.query(CourseDocument)
        .filter(CourseDocument.id == document_id)
        .first()
    )
    if not document:
        raise BusinessException(message="课程资料不存在")

    if vector_service.is_configured():
        try:
            vector_service.delete_document_vectors(document_id)
        except Exception:
            logger.exception(
                "Delete document vectors failed: %s", document_id
            )

    disk_name = document.disk_name
    db.delete(document)
    db.commit()

    file_path = COURSE_DOC_DIR / disk_name
    if file_path.exists():
        file_path.unlink()


def search_chunks(
    db: Session,
    query: str,
    course_id: int | None = None,
    top_k: int = 3,
) -> list[dict]:
    """关键词 + BM25 检索课程资料片段"""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    # 优先向量检索；没有命中或调用失败时回退 BM25
    if vector_service.is_configured():
        try:
            vector_results = vector_service.search_vectors(
                query, course_id, top_k
            )
            if vector_results:
                return vector_results
        except Exception:
            logger.exception("Vector search failed, fallback to BM25")

    db_query = (
        db.query(CourseDocChunk, CourseDocument, Course)
        .join(CourseDocument, CourseDocument.id == CourseDocChunk.document_id)
        .join(Course, Course.id == CourseDocument.course_id)
    )
    if course_id is not None:
        db_query = db_query.filter(CourseDocument.course_id == course_id)

    rows = db_query.all()
    if not rows:
        return []

    items = []
    corpus = []
    for chunk, document, course in rows:
        tokens = _tokenize(chunk.content)
        if not tokens:
            continue
        items.append((chunk, document, course))
        corpus.append(tokens)

    if not corpus:
        return []

    # BM25Plus 对单文档/小语料更稳定，不会因为 IDF 为负导致全部被过滤
    bm25 = BM25Plus(corpus)
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        enumerate(scores), key=lambda item: item[1], reverse=True
    )[:top_k]

    results = []
    for index, score in ranked:
        if score <= 0:
            continue
        chunk, document, course = items[index]
        results.append(
            {
                "course_name": course.name,
                "document_title": document.title,
                "source_file": document.original_name,
                "file_type": document.file_type,
                "source_page": chunk.source_page,
                "content": chunk.content,
                "score": round(float(score), 4),
            }
        )
    return results
