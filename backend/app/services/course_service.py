from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.courses import Course
from app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
    CourseUpdateRequest,
)


def get_course_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    status: int | None = None,
) -> PageResponse:
    """分页查询课程，支持按名称、代码、老师模糊搜索"""
    query = db.query(Course)

    if keywords:
        # 课程名称、课程代码、授课老师任意一个匹配即可
        query = query.filter(
            or_(
                Course.name.ilike(f"%{keywords}%"),
                Course.code.ilike(f"%{keywords}%"),
                Course.teacher.ilike(f"%{keywords}%"),
            )
        )

    # status 为 None 时查全部；学生端会固定传 1，只查正常课程
    if status is not None:
        query = query.filter(Course.status == status)

    total = query.count()
    items = (
        query.order_by(Course.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[CourseResponse.model_validate(item) for item in items],
        total=total,
    )


def get_course_or_404(db: Session, course_id: int) -> Course:
    """根据 ID 查询课程，不存在时抛出业务异常"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise BusinessException(message="课程不存在")
    return course


def create_course(db: Session, data: CourseCreateRequest) -> CourseResponse:
    """新增课程，课程代码必须唯一"""
    exist = db.query(Course).filter(Course.code == data.code).first()
    if exist:
        raise BusinessException(message="课程代码已存在")

    course = Course(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseResponse.model_validate(course)


def update_course(
    db: Session, course_id: int, data: CourseUpdateRequest
) -> CourseResponse:
    """编辑课程；修改代码时仍要保证全局唯一"""
    course = get_course_or_404(db, course_id)
    payload = data.model_dump(exclude_none=True)

    new_code = payload.get("code")
    if new_code and new_code != course.code:
        exist = (
            db.query(Course)
            .filter(Course.code == new_code, Course.id != course_id)
            .first()
        )
        if exist:
            raise BusinessException(message="课程代码已存在")

    for field, value in payload.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return CourseResponse.model_validate(course)


def delete_course(db: Session, course_id: int) -> None:
    """删除课程；当前为物理删除"""
    course = get_course_or_404(db, course_id)
    db.delete(course)
    db.commit()
