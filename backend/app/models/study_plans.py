from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"
    __table_args__ = {"comment": "学习计划"}

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="学生ID",
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), comment="计划标题", nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, comment="学习目标", nullable=True)
    start_date: Mapped[date] = mapped_column(Date, comment="开始日期", nullable=False)
    end_date: Mapped[date] = mapped_column(Date, comment="结束日期", nullable=False)
    status: Mapped[int] = mapped_column(
        default=0, comment="状态：0-进行中，1-已完成", nullable=False
    )
