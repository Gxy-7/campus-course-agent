from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        # 一个学生同一门课只能选一次
        UniqueConstraint("course_id", "student_id", name="uk_course_enrollment"),
        {"comment": "学生选课关系"},
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        comment="课程ID",
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="学生ID",
        nullable=False,
        index=True,
    )
