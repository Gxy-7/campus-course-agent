from pydantic import BaseModel, ConfigDict, Field, model_validator


class CourseScheduleBase(BaseModel):
    """课表新增/编辑的公共字段"""

    course_id: int
    weekday: int = Field(..., ge=1, le=7, description="1=周一，7=周日")
    start_section: int = Field(..., ge=1, le=12)
    end_section: int = Field(..., ge=1, le=12)
    start_week: int = Field(..., ge=1, le=20)
    end_week: int = Field(..., ge=1, le=20)
    week_type: int = Field(default=0, ge=0, le=2)
    classroom: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)

    @model_validator(mode="after")
    def validate_ranges(self):
        # 结束节次不能早于开始节次
        if self.end_section < self.start_section:
            raise ValueError("结束节次不能小于开始节次")
        # 结束周不能早于开始周
        if self.end_week < self.start_week:
            raise ValueError("结束周不能小于开始周")
        return self


class CourseScheduleCreateRequest(CourseScheduleBase):
    """新增课表请求"""


class CourseScheduleUpdateRequest(CourseScheduleBase):
    """编辑课表请求，编辑时整条记录替换"""


class CourseScheduleResponse(BaseModel):
    """课表返回数据，包含课程名称、代码和老师"""

    id: int
    course_id: int
    course_code: str
    course_name: str
    teacher: str | None = None
    weekday: int
    start_section: int
    end_section: int
    start_week: int
    end_week: int
    week_type: int
    classroom: str
