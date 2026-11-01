from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudyPlanBase(BaseModel):
    """学习计划新增/编辑的公共字段"""

    title: str = Field(..., min_length=1, max_length=100)
    goal: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date

    model_config = ConfigDict(str_strip_whitespace=True)

    @model_validator(mode="after")
    def validate_dates(self):
        # 结束日期不能早于开始日期
        if self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class StudyPlanCreateRequest(StudyPlanBase):
    """新建学习计划"""

    status: int = Field(default=0, ge=0, le=1)


class StudyPlanUpdateRequest(StudyPlanBase):
    """编辑学习计划"""

    status: int = Field(default=0, ge=0, le=1)


class StudyPlanResponse(BaseModel):
    id: int
    title: str
    goal: str | None = None
    start_date: date
    end_date: date
    status: int
    create_time: datetime
    update_time: datetime
