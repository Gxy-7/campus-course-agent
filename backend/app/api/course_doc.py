from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from app.services import course_doc_service, vector_service

router = APIRouter(prefix="/course-doc", tags=["课程资料"])


@router.post("/upload")
def upload_course_document(
    course_id: int = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """上传并解析课程资料，仅管理员可用"""
    res = course_doc_service.create_document(
        db, course_id, title, file, current_user.id
    )
    return Response.success(data=res)


@router.post("/reindex")
def reindex_course_documents(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """重新向量化全部课程资料，仅管理员可用"""
    res = vector_service.reindex_all(db)
    return Response.success(
        message=f"重新入库完成：{res['documents']} 份资料，{res['chunks']} 个文本块",
        data=res,
    )


@router.get("/list")
def get_course_document_list(
    course_id: int | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """课程资料列表，仅管理员可用"""
    res = course_doc_service.get_documents(db, course_id)
    return Response.success(data=res)


@router.delete("/{document_id}")
def delete_course_document(
    document_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除课程资料和文本块，仅管理员可用"""
    course_doc_service.delete_document(db, document_id)
    return Response.success()
