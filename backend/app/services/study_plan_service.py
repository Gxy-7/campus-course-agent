from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.study_plans import StudyPlan
from app.schemas.study_plan import (
    StudyPlanCreateRequest,
    StudyPlanResponse,
    StudyPlanUpdateRequest,
)


def _get_plan_or_404(db: Session, student_id: int, plan_id: int) -> StudyPlan:
    """查询计划时带上 student_id，避免访问别人的计划"""
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.id == plan_id, StudyPlan.student_id == student_id)
        .first()
    )
    if not plan:
        raise BusinessException(message="学习计划不存在")
    return plan


def _to_response(plan: StudyPlan) -> StudyPlanResponse:
    return StudyPlanResponse(
        id=plan.id,
        title=plan.title,
        goal=plan.goal,
        start_date=plan.start_date,
        end_date=plan.end_date,
        status=plan.status,
        create_time=plan.create_time,
        update_time=plan.update_time,
    )


def get_plan_list(db: Session, student_id: int) -> list[StudyPlanResponse]:
    """查询当前学生的全部学习计划"""
    plans = (
        db.query(StudyPlan)
        .filter(StudyPlan.student_id == student_id)
        .order_by(StudyPlan.status.asc(), StudyPlan.id.desc())
        .all()
    )
    return [_to_response(plan) for plan in plans]


def create_plan(
    db: Session, student_id: int, data: StudyPlanCreateRequest
) -> StudyPlanResponse:
    """新建学习计划"""
    plan = StudyPlan(student_id=student_id, **data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _to_response(plan)


def update_plan(
    db: Session, student_id: int, plan_id: int, data: StudyPlanUpdateRequest
) -> StudyPlanResponse:
    """编辑学习计划"""
    plan = _get_plan_or_404(db, student_id, plan_id)
    for field, value in data.model_dump().items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return _to_response(plan)


def delete_plan(db: Session, student_id: int, plan_id: int) -> None:
    """删除学习计划"""
    plan = _get_plan_or_404(db, student_id, plan_id)
    db.delete(plan)
    db.commit()
