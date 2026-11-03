import logging

import chromadb
from openai import OpenAI
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import CHROMA_DIR, settings
from app.models.course_docs import CourseDocChunk, CourseDocument
from app.models.courses import Course

logger = logging.getLogger(__name__)

COLLECTION_NAME = "course_docs"
EMBED_BATCH_SIZE = 10


def is_configured() -> bool:
    """是否配置了 Embedding Key"""
    return bool(settings.EMBEDDING_API_KEY)


def _get_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _get_collection(client=None):
    client = client or _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 Embedding API，分批向量化"""
    if not settings.EMBEDDING_API_KEY:
        raise BusinessException(
            message="未配置 Embedding API Key，请在 backend/.env 中设置 EMBEDDING_API_KEY"
        )

    client = OpenAI(
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
    )

    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=batch,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors.extend([item.embedding for item in ordered])
    return vectors


def _vectorize_with_collection(
    collection,
    db: Session,
    document: CourseDocument,
    course: Course,
) -> int:
    chunks = (
        db.query(CourseDocChunk)
        .filter(CourseDocChunk.document_id == document.id)
        .order_by(CourseDocChunk.chunk_index)
        .all()
    )
    if not chunks:
        return 0

    texts = [chunk.content for chunk in chunks]
    embeddings = _embed_texts(texts)

    ids = [
        f"doc_{document.id}_chunk_{chunk.chunk_index}" for chunk in chunks
    ]
    metadatas = [
        {
            "document_id": document.id,
            "course_id": document.course_id,
            "chunk_index": chunk.chunk_index,
            "document_title": document.title,
            "source_file": document.original_name,
            "file_type": document.file_type,
            "course_name": course.name if course else "",
            "source_page": chunk.source_page or 0,
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(chunks)


def vectorize_document(db: Session, document_id: int) -> int:
    """向量化单份资料，上传资料后调用"""
    if not is_configured():
        return 0

    document = (
        db.query(CourseDocument)
        .filter(CourseDocument.id == document_id)
        .first()
    )
    if not document:
        return 0

    course = (
        db.query(Course).filter(Course.id == document.course_id).first()
    )
    collection = _get_collection()
    return _vectorize_with_collection(collection, db, document, course)


def delete_document_vectors(document_id: int) -> None:
    """删除某份资料的全部向量"""
    if not is_configured():
        return

    collection = _get_collection()
    collection.delete(where={"document_id": document_id})


def reindex_all(db: Session) -> dict:
    """清空并重建全部资料向量，用于已有资料升级或模型切换"""
    if not is_configured():
        raise BusinessException(
            message="未配置 Embedding API Key，请在 backend/.env 中设置 EMBEDDING_API_KEY"
        )

    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        # 首次运行时 collection 还不存在
        pass

    collection = _get_collection(client)
    documents = db.query(CourseDocument).order_by(CourseDocument.id).all()
    total_chunks = 0

    for document in documents:
        course = (
            db.query(Course).filter(Course.id == document.course_id).first()
        )
        total_chunks += _vectorize_with_collection(
            collection, db, document, course
        )

    return {
        "documents": len(documents),
        "chunks": total_chunks,
        "collection": COLLECTION_NAME,
    }


def search_vectors(
    query: str, course_id: int | None = None, top_k: int = 3
) -> list[dict]:
    """向量检索，返回片段和真实来源文件"""
    if not is_configured():
        return []

    query_vector = _embed_texts([query])[0]
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_kwargs = {
        "query_embeddings": [query_vector],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if course_id is not None:
        query_kwargs["where"] = {"course_id": course_id}

    result = collection.query(**query_kwargs)
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    results = []
    for content, metadata, distance in zip(
        documents, metadatas, distances
    ):
        metadata = metadata or {}
        source_page = metadata.get("source_page") or None
        results.append(
            {
                "course_name": metadata.get("course_name", ""),
                "document_title": metadata.get("document_title", ""),
                "source_file": metadata.get("source_file", ""),
                "file_type": metadata.get("file_type", ""),
                "source_page": source_page,
                "content": content,
                "score": round(1 - float(distance), 4),
            }
        )
    return results
