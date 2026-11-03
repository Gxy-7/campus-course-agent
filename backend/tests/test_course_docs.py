from sqlalchemy import func

from app.models.course_docs import CourseDocChunk
from app.services import course_doc_service, vector_service


def test_upload_search_and_delete_course_doc(
    client,
    db,
    admin_headers,
    student_headers,
    course_factory,
    monkeypatch,
    tmp_path,
):
    # 测试不调用 Embedding，强制走 BM25
    monkeypatch.setattr(vector_service, "is_configured", lambda: False)
    monkeypatch.setattr(course_doc_service, "COURSE_DOC_DIR", tmp_path)

    course = course_factory()

    upload = client.post(
        "/api/course-doc/upload",
        headers=admin_headers,
        data={"course_id": str(course["id"]), "title": "实验指导"},
        files={
            "file": (
                "实验指导.md",
                "# 实验要求\n实验前需要预习，并提交预习报告。".encode(
                    "utf-8"
                ),
                "text/markdown",
            )
        },
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["code"] == 200, body
    assert body["data"]["chunk_count"] >= 1
    document_id = body["data"]["id"]

    listed = client.get(
        "/api/course-doc/list", headers=admin_headers
    )
    assert listed.json()["data"][0]["id"] == document_id

    forbidden = client.post(
        "/api/course-doc/upload",
        headers=student_headers,
        data={"course_id": str(course["id"]), "title": "越权资料"},
        files={
            "file": (
                "越权.md",
                "越权".encode("utf-8"),
                "text/markdown",
            )
        },
    )
    assert forbidden.json()["code"] == 403

    results = course_doc_service.search_chunks(
        db, "预习", course["id"]
    )
    assert results
    assert results[0]["source_file"] == "实验指导.md"

    deleted = client.delete(
        f"/api/course-doc/{document_id}", headers=admin_headers
    )
    assert deleted.json()["code"] == 200

    remaining = (
        db.query(func.count(CourseDocChunk.id))
        .filter(CourseDocChunk.document_id == document_id)
        .scalar()
    )
    assert remaining == 0
    assert list(tmp_path.iterdir()) == []
