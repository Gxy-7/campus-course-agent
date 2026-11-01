from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.course import CourseCreateRequest, CourseUpdateRequest
from app.services import course_service

router = APIRouter(prefix="/course", tags=["课程管理"])


@router.get("/list")
def get_course_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keywords: str | None = Query(default=None, max_length=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """课程分页列表：管理员看全部，学生只看正常课程"""
    # 学生端强制过滤 status=1，避免看到已停用课程
    status = None if current_user.role == "admin" else 1
    res = course_service.get_course_page_list(
        db, page, page_size, keywords, status
    )
    return Response.success(data=res)


@router.post("")
def create_course(
    data: CourseCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """新增课程，仅管理员可用"""
    res = course_service.create_course(db, data)
    return Response.success(data=res)


@router.put("/{course_id}")
def update_course(
    course_id: int,
    data: CourseUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """编辑课程，仅管理员可用"""
    res = course_service.update_course(db, course_id, data)
    return Response.success(data=res)


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除课程，仅管理员可用"""
    course_service.delete_course(db, course_id)
    return Response.success()
