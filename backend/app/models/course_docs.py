from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CourseDocument(Base):
    __tablename__ = "course_documents"
    __table_args__ = {"comment": "课程资料"}

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        comment="课程ID",
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), comment="资料标题", nullable=False)
    original_name: Mapped[str] = mapped_column(
        String(255), comment="原始文件名", nullable=False
    )
    disk_name: Mapped[str] = mapped_column(
        String(255), comment="磁盘文件名", nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(20), comment="文件类型", nullable=False
    )
    char_count: Mapped[int] = mapped_column(
        default=0, comment="字符数", nullable=False
    )
    chunk_count: Mapped[int] = mapped_column(
        default=0, comment="文本块数量", nullable=False
    )
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="上传人ID",
        nullable=True,
    )


class CourseDocChunk(Base):
    __tablename__ = "course_doc_chunks"
    __table_args__ = {"comment": "课程资料文本块"}

    document_id: Mapped[int] = mapped_column(
        ForeignKey("course_documents.id", ondelete="CASCADE"),
        comment="资料ID",
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(comment="块序号", nullable=False)
    content: Mapped[str] = mapped_column(Text, comment="文本内容", nullable=False)
    source_page: Mapped[int | None] = mapped_column(
        comment="PDF页码，从1开始", nullable=True
    )
