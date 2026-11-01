from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_student
from app.models.user import User
from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanUpdateRequest,
)
from app.services import study_plan_service

router = APIRouter(prefix="/study-plan", tags=["学习计划"])


@router.get("/list")
def get_study_plan_list(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """查询我的学习计划"""
    res = study_plan_service.get_plan_list(db, current_user.id)
    return Response.success(data=res)


@router.post("")
def create_study_plan(
    data: StudyPlanCreateRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """新建学习计划"""
    res = study_plan_service.create_plan(db, current_user.id, data)
    return Response.success(data=res)


@router.put("/{plan_id}")
def update_study_plan(
    plan_id: int,
    data: StudyPlanUpdateRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """编辑学习计划"""
    res = study_plan_service.update_plan(db, current_user.id, plan_id, data)
    return Response.success(data=res)


@router.delete("/{plan_id}")
def delete_study_plan(
    plan_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """删除学习计划"""
    study_plan_service.delete_plan(db, current_user.id, plan_id)
    return Response.success()
