from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_student
from app.models.user import User
from app.services import enrollment_service

router = APIRouter(prefix="/enrollment", tags=["选课管理"])


@router.get("/my")
def get_my_enrollment_ids(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """查询当前学生已选课程 ID"""
    res = enrollment_service.get_enrolled_course_ids(db, current_user.id)
    return Response.success(data=res)


@router.post("/{course_id}")
def enroll_course(
    course_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """选课，仅学生可用"""
    enrollment_service.enroll_course(db, current_user.id, course_id)
    return Response.success(message="选课成功")


@router.delete("/{course_id}")
def unenroll_course(
    course_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """退课，仅学生可用"""
    enrollment_service.unenroll_course(db, current_user.id, course_id)
    return Response.success(message="退课成功")
