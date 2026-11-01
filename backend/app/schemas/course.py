from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseResponse(BaseModel):
    """课程列表/详情返回的数据结构"""

    id: int
    name: str
    code: str
    teacher: str | None = None
    description: str | None = None
    status: int
    create_time: datetime
    update_time: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseCreateRequest(BaseModel):
    """新增课程的请求参数"""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    teacher: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    # 0-停用，1-正常
    status: int = Field(default=1, ge=0, le=1)

    # 自动去掉字符串首尾空格，避免名称或代码前后带空格
    model_config = ConfigDict(str_strip_whitespace=True)


class CourseUpdateRequest(BaseModel):
    """编辑课程的请求参数，字段都可以不传"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    teacher: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    status: int | None = Field(default=None, ge=0, le=1)

    model_config = ConfigDict(str_strip_whitespace=True)
