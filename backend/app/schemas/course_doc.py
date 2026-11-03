from datetime import datetime

from pydantic import BaseModel


class CourseDocumentResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    title: str
    original_name: str
    file_type: str
    char_count: int
    chunk_count: int
    create_time: datetime
