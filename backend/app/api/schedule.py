from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import (
    get_current_admin,
    get_current_student,
    get_current_user,
)
from app.models.user import User
from app.schemas.schedule import (
    CourseScheduleCreateRequest,
    CourseScheduleUpdateRequest,
)
from app.services import schedule_service

router = APIRouter(prefix="/schedule", tags=["课表管理"])


@router.get("/list")
def get_schedule_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询所有课程课表：管理员看全部，学生只看正常课程"""
    res = schedule_service.get_schedule_list(
        db, only_active=current_user.role != "admin"
    )
    return Response.success(data=res)


@router.get("/my")
def get_my_schedule_list(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """查询当前学生已选课程的全部课表"""
    res = schedule_service.get_my_schedule_list(db, current_user.id)
    return Response.success(data=res)


@router.get("/course/{course_id}")
def get_course_schedule_list(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询某门课程的课表"""
    res = schedule_service.get_course_schedule_list(
        db, course_id, only_active=current_user.role != "admin"
    )
    return Response.success(data=res)


@router.post("")
def create_schedule(
    data: CourseScheduleCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """新增课表，仅管理员可用"""
    res = schedule_service.create_schedule(db, data)
    return Response.success(data=res)


@router.put("/{schedule_id}")
def update_schedule(
    schedule_id: int,
    data: CourseScheduleUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """编辑课表，仅管理员可用"""
    res = schedule_service.update_schedule(db, schedule_id, data)
    return Response.success(data=res)


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除课表，仅管理员可用"""
    schedule_service.delete_schedule(db, schedule_id)
    return Response.success()
