from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.courses import Course
from app.models.enrollments import CourseEnrollment
from app.models.schedules import CourseSchedule
from app.services.course_service import get_course_or_404

WEEKDAY_NAMES = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def get_enrolled_course_ids(db: Session, student_id: int) -> list[int]:
    """查询学生已选课程 ID"""
    rows = (
        db.query(CourseEnrollment.course_id)
        .filter(CourseEnrollment.student_id == student_id)
        .order_by(CourseEnrollment.id.desc())
        .all()
    )
    return [row[0] for row in rows]


def _week_type_matches(week_type: int, start_week: int, end_week: int) -> bool:
    """判断周次区间内是否包含指定周类型"""
    if week_type == 0:
        return True
    # 区间长度 >= 2 时，一定同时包含奇数和偶数周
    if start_week < end_week:
        return True
    # 单周区间：判断这一周是奇数还是偶数
    return start_week % 2 == (1 if week_type == 1 else 0)


def _weeks_overlap(a: CourseSchedule, b: CourseSchedule) -> bool:
    """判断两个课表周次是否重叠"""
    start = max(a.start_week, b.start_week)
    end = min(a.end_week, b.end_week)
    if start > end:
        return False

    if a.week_type == 0:
        return _week_type_matches(b.week_type, start, end)
    if b.week_type == 0:
        return _week_type_matches(a.week_type, start, end)
    # 单周和双周不会重叠
    if a.week_type != b.week_type:
        return False
    return _week_type_matches(a.week_type, start, end)


def _sections_overlap(a: CourseSchedule, b: CourseSchedule) -> bool:
    """判断两个课表节次是否重叠"""
    return max(a.start_section, b.start_section) <= min(a.end_section, b.end_section)


def _check_conflict(db: Session, student_id: int, course: Course) -> None:
    """检查新课程和已选课程是否有时间冲突"""
    new_schedules = (
        db.query(CourseSchedule)
        .filter(CourseSchedule.course_id == course.id)
        .all()
    )
    if not new_schedules:
        return

    enrolled_schedules = (
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
        .all()
    )

    for new_item in new_schedules:
        for old_item, old_course in enrolled_schedules:
            if new_item.weekday != old_item.weekday:
                continue
            if not _sections_overlap(new_item, old_item):
                continue
            if not _weeks_overlap(new_item, old_item):
                continue

            raise BusinessException(
                message=(
                    f"与已选课程《{old_course.name}》时间冲突："
                    f"{WEEKDAY_NAMES[old_item.weekday]} "
                    f"第 {old_item.start_section}-{old_item.end_section} 节"
                )
            )


def enroll_course(db: Session, student_id: int, course_id: int) -> None:
    """学生选课"""
    course = get_course_or_404(db, course_id)
    if course.status != 1:
        raise BusinessException(message="课程已停用，不能选课")

    exist = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.course_id == course_id,
        )
        .first()
    )
    if exist:
        raise BusinessException(message="已经选过这门课了")

    # 选课前先检查时间冲突
    _check_conflict(db, student_id, course)

    db.add(CourseEnrollment(student_id=student_id, course_id=course_id))
    db.commit()


def unenroll_course(db: Session, student_id: int, course_id: int) -> None:
    """学生退课"""
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.course_id == course_id,
        )
        .first()
    )
    if not enrollment:
        raise BusinessException(message="还没有选这门课")

    db.delete(enrollment)
    db.commit()
