from contextlib import contextmanager

from fastmcp import FastMCP
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.study_plan import StudyPlanCreateRequest
from app.services import (
    course_doc_service,
    schedule_service,
    study_plan_service,
)
from app.utils.jwt import decode_access_token

mcp = FastMCP("campus-course-tools")

WEEKDAY_NAMES = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WEEK_TYPE_NAMES = ["每周", "单周", "双周"]


@contextmanager
def _auth(token: str):
    """解析 JWT，拿到当前用户和数据库会话"""
    db: Session = SessionLocal()
    try:
        try:
            payload = decode_access_token(token)
        except Exception:
            raise ValueError("登录已失效")

        user_id = payload.get("user_id")
        user = (
            db.query(User)
            .filter(User.id == user_id, User.status == 1)
            .first()
        )
        if not user:
            raise ValueError("用户不存在或已被禁用")

        yield db, user
    finally:
        db.close()


@mcp.tool
def get_my_schedule(token: str) -> dict:
    """查询当前登录学生已选课程的全部课表"""
    with _auth(token) as (db, user):
        schedules = schedule_service.get_my_schedule_list(db, user.id)
        data = []
        for item in schedules:
            row = item.model_dump()
            row["weekday_name"] = WEEKDAY_NAMES[item.weekday]
            row["week_type_name"] = WEEK_TYPE_NAMES[item.week_type]
            data.append(row)

        return {
            "summary": f"查询到 {len(data)} 条课表",
            "data": data,
        }


@mcp.tool
def search_course_docs(
    token: str, query: str, course_id: int | None = None
) -> dict:
    """检索已上传的课程资料"""
    if not query.strip():
        raise ValueError("检索问题不能为空")

    with _auth(token) as (db, user):
        results = course_doc_service.search_chunks(db, query, course_id)
        return {
            "summary": f"命中 {len(results)} 个片段",
            "data": results,
        }


@mcp.tool
def save_study_plan(
    token: str,
    title: str,
    start_date: str,
    end_date: str,
    goal: str | None = None,
) -> dict:
    """保存当前用户的学习计划"""
    with _auth(token) as (db, user):
        payload = StudyPlanCreateRequest(
            title=title,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            status=0,
        )
        plan = study_plan_service.create_plan(db, user.id, payload)
        return {
            "summary": f"已保存：{plan.title}",
            "data": {
                "plan_id": plan.id,
                "title": plan.title,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat(),
            },
        }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        path="/mcp",
        # FastMCP 默认会向 uvicorn 请求 websockets-sansio，
        # 当前锁定的 uvicorn 0.34.0 不认这个值；MCP 走 HTTP 不需要 WebSocket
        uvicorn_config={"ws": "none"},
    )
