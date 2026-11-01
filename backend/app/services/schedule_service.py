from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.courses import Course
from app.models.enrollments import CourseEnrollment
from app.models.schedules import CourseSchedule
from app.schemas.schedule import (
    CourseScheduleCreateRequest,
    CourseScheduleResponse,
    CourseScheduleUpdateRequest,
)
from app.services.course_service import get_course_or_404


def _to_response(
    schedule: CourseSchedule, course: Course
) -> CourseScheduleResponse:
    """把课表对象和课程对象拼成前端需要的数据"""
    return CourseScheduleResponse(
        id=schedule.id,
        course_id=course.id,
        course_code=course.code,
        course_name=course.name,
        teacher=course.teacher,
        weekday=schedule.weekday,
        start_section=schedule.start_section,
        end_section=schedule.end_section,
        start_week=schedule.start_week,
        end_week=schedule.end_week,
        week_type=schedule.week_type,
        classroom=schedule.classroom,
    )


def _check_duplicate(
    db: Session,
    data: CourseScheduleCreateRequest | CourseScheduleUpdateRequest,
    exclude_id: int | None = None,
) -> None:
    """同一门课的同一天、同一开始节次、同一开始周、同一周类型不能重复"""
    query = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == data.course_id,
        CourseSchedule.weekday == data.weekday,
        CourseSchedule.start_section == data.start_section,
        CourseSchedule.start_week == data.start_week,
        CourseSchedule.week_type == data.week_type,
    )
    if exclude_id:
        query = query.filter(CourseSchedule.id != exclude_id)
    if query.first():
        raise BusinessException(message="该课程在这个时间已经有课表安排了")


def get_course_schedule_list(
    db: Session, course_id: int, only_active: bool = False
) -> list[CourseScheduleResponse]:
    """查询某门课的全部课表"""
    course = get_course_or_404(db, course_id)

    # 学生端不能查看已停用课程的课表
    if only_active and course.status != 1:
        return []

    schedules = (
        db.query(CourseSchedule)
        .filter(CourseSchedule.course_id == course_id)
        .order_by(CourseSchedule.weekday, CourseSchedule.start_section)
        .all()
    )
    return [_to_response(item, course) for item in schedules]


def get_schedule_list(
    db: Session, only_active: bool = True
) -> list[CourseScheduleResponse]:
    """查询所有课程课表，学生默认只看正常课程"""
    query = (
        db.query(CourseSchedule, Course)
        .join(Course, Course.id == CourseSchedule.course_id)
    )
    if only_active:
        query = query.filter(Course.status == 1)

    rows = query.order_by(
        CourseSchedule.weekday, CourseSchedule.start_section
    ).all()
    return [_to_response(schedule, course) for schedule, course in rows]


def get_my_schedule_list(
    db: Session, student_id: int
) -> list[CourseScheduleResponse]:
    """查询当前学生已选课程的全部课表"""
    rows = (
        db.query(CourseSchedule, Course)
        .join(
            CourseEnrollment,
            CourseEnrollment.course_id == CourseSchedule.course_id,
        )
        .join(Course, Course.id == CourseSchedule.course_id)
        .filter(
            CourseEnrollment.student_id == student_id,
            Course.status == 1,
        )
        .order_by(CourseSchedule.weekday, CourseSchedule.start_section)
        .all()
    )
    return [_to_response(schedule, course) for schedule, course in rows]


def create_schedule(
    db: Session, data: CourseScheduleCreateRequest
) -> CourseScheduleResponse:
    """新增课表时间段"""
    course = get_course_or_404(db, data.course_id)
    _check_duplicate(db, data)

    schedule = CourseSchedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return _to_response(schedule, course)


def update_schedule(
    db: Session, schedule_id: int, data: CourseScheduleUpdateRequest
) -> CourseScheduleResponse:
    """编辑课表时间段"""
    schedule = (
        db.query(CourseSchedule)
        .filter(CourseSchedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise BusinessException(message="课表记录不存在")

    course = get_course_or_404(db, data.course_id)
    _check_duplicate(db, data, exclude_id=schedule_id)

    for field, value in data.model_dump().items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return _to_response(schedule, course)


def delete_schedule(db: Session, schedule_id: int) -> None:
    """删除课表时间段"""
    schedule = (
        db.query(CourseSchedule)
        .filter(CourseSchedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise BusinessException(message="课表记录不存在")

    db.delete(schedule)
    db.commit()
