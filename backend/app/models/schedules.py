from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CourseSchedule(Base):
    __tablename__ = "course_schedules"
    __table_args__ = (
        # 同一门课在同一天、同一开始节次、同一开始周、同一周类型下只允许一条记录
        UniqueConstraint(
            "course_id",
            "weekday",
            "start_section",
            "start_week",
            "week_type",
            name="uk_course_schedule",
        ),
        {"comment": "课程课表"},
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        comment="课程ID",
        nullable=False,
        index=True,
    )
    weekday: Mapped[int] = mapped_column(comment="星期：1-7", nullable=False)
    start_section: Mapped[int] = mapped_column(comment="开始节次", nullable=False)
    end_section: Mapped[int] = mapped_column(comment="结束节次", nullable=False)
    start_week: Mapped[int] = mapped_column(comment="开始周", nullable=False)
    end_week: Mapped[int] = mapped_column(comment="结束周", nullable=False)
    week_type: Mapped[int] = mapped_column(
        default=0, comment="周类型：0-每周，1-单周，2-双周", nullable=False
    )
    classroom: Mapped[str] = mapped_column(
        String(100), comment="上课地点", nullable=False
    )
