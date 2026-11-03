import json
import logging
from collections.abc import Generator
from datetime import date

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.schemas.chat import AgentStep, ChatRequest, ChatResponse
from app.schemas.study_plan import StudyPlanCreateRequest
from app.services import (
    course_doc_service,
    mcp_client_service,
    schedule_service,
    study_plan_service,
)

logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WEEK_TYPE_NAMES = ["每周", "单周", "双周"]

TOOL_LABELS = {
    "get_my_schedule": "查询我的课表",
    "save_study_plan": "保存学习计划",
    "search_course_docs": "检索课程资料",
}

# 系统提示词里明确身份、工具和防编造规则
SYSTEM_PROMPT = f"""你是校园课程智能助手。
今天是 {date.today().isoformat()}，{WEEKDAY_NAMES[date.today().isoweekday()]}。

你可以调用工具查询当前登录学生自己的课表，也可以在用户明确要求时保存学习计划。
规则：
1. 回答与校园课程、课表、学习计划相关的问题。
2. 询问课表时必须调用 get_my_schedule，不能凭空编造。
3. 工具返回为空时，明确说没有查询到课程安排。
4. 用户身份由系统提供，不要询问或猜测 user_id，也不要查询别人的数据。
5. 用简洁、友好的中文回答。
6. 当用户明确说“保存”“记录”“存下来”“帮我保存”时，你必须调用 save_study_plan，不能只回复“已保存”。
7. 如果用户先让你生成计划并要求保存，先生成计划内容，再调用 save_study_plan。
8. 如果用户只是让你规划、列一个计划，没有要求保存，不要调用保存工具，只返回计划文本。
9. 保存时如果缺少日期，默认使用今天到 7 天后，并在回答中说明。
10. 一次对话最多保存一份学习计划，不要重复保存。
11. 课程内容、实验要求、考试范围等资料类问题，优先调用 search_course_docs 检索，不要凭记忆编造。
12. 回答资料类问题时必须基于检索片段，并标注来源，格式为“来源：文件名 第 X 页”。
13. 来源文件名必须使用检索结果中的 source_file，不要自行添加或修改扩展名；source_page 为空时只写文件名，不要编造页码。
14. 检索结果为空时，明确说“知识库中没有找到相关内容”；检索服务异常时，说“当前无法查询资料”，不要编造。
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_schedule",
            "description": (
                "查询当前登录学生已选课程的全部课表，"
                "包括课程名称、老师、教室、星期、节次和周次"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_study_plan",
            "description": (
                "当用户明确要求保存、记录或存下来学习计划时，必须调用此工具。"
                "不要只回复“已保存”而不调用工具。"
                "如果用户要求保存刚才生成的学习计划，请从对话中提取标题、目标和日期后调用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "计划标题，例如：期末复习计划",
                    },
                    "goal": {
                        "type": "string",
                        "description": "学习目标和计划内容",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，格式 YYYY-MM-DD",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式 YYYY-MM-DD",
                    },
                },
                "required": ["title", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_course_docs",
            "description": (
                "检索已上传的课程资料。"
                "回答课程内容、实验要求、考试范围等问题时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要检索的问题或关键词",
                    },
                    "course_id": {
                        "type": "integer",
                        "description": "可选，限定某门课程ID",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def _parse_arguments(arguments: str | None) -> dict:
    """解析模型生成的工具参数 JSON"""
    try:
        return json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return {}


def _execute_tool_local(
    db: Session,
    user_id: int,
    tool_name: str,
    arguments: dict,
):
    """进程内执行工具，MCP 未启用或调用失败时使用"""
    if tool_name == "get_my_schedule":
        schedules = schedule_service.get_my_schedule_list(db, user_id)
        data = []
        for item in schedules:
            row = item.model_dump()
            row["weekday_name"] = WEEKDAY_NAMES[item.weekday]
            row["week_type_name"] = WEEK_TYPE_NAMES[item.week_type]
            data.append(row)

        return data, AgentStep(
            tool="get_my_schedule",
            label="查询我的课表",
            summary=f"查询到 {len(data)} 条课表",
        )

    if tool_name == "save_study_plan":
        try:
            payload = StudyPlanCreateRequest(**arguments)
            plan = study_plan_service.create_plan(db, user_id, payload)
        except ValidationError:
            return {"error": "学习计划参数不合法，请检查标题和日期"}, AgentStep(
                tool="save_study_plan",
                label="保存学习计划",
                summary="保存失败：参数不合法",
            )
        except BusinessException as exc:
            return {"error": exc.message}, AgentStep(
                tool="save_study_plan",
                label="保存学习计划",
                summary=f"保存失败：{exc.message}",
            )

        return (
            {
                "plan_id": plan.id,
                "title": plan.title,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat(),
            },
            AgentStep(
                tool="save_study_plan",
                label="保存学习计划",
                summary=f"已保存：{plan.title}",
            ),
        )

    if tool_name == "search_course_docs":
        query = str(arguments.get("query") or "").strip()
        if not query:
            return {"error": "缺少检索问题"}, AgentStep(
                tool="search_course_docs",
                label="检索课程资料",
                summary="检索失败：缺少问题",
            )

        course_id = arguments.get("course_id")
        if course_id not in (None, ""):
            try:
                course_id = int(course_id)
            except (TypeError, ValueError):
                return {"error": "course_id 不合法"}, AgentStep(
                    tool="search_course_docs",
                    label="检索课程资料",
                    summary="检索失败：课程ID不合法",
                )
        else:
            course_id = None

        results = course_doc_service.search_chunks(db, query, course_id)
        return results, AgentStep(
            tool="search_course_docs",
            label="检索课程资料",
            summary=f"命中 {len(results)} 个片段",
        )

    return {"error": "未知工具"}, AgentStep(
        tool=tool_name,
        label=tool_name,
        summary="未知工具",
    )


def _execute_tool(
    db: Session,
    user_id: int,
    tool_name: str,
    arguments: dict,
    token: str | None = None,
):
    """优先走 MCP；MCP 不可用时回退进程内工具"""
    if settings.MCP_SERVER_URL and token:
        try:
            payload = mcp_client_service.call_tool(
                tool_name, arguments, token
            )
            return payload["data"], AgentStep(
                tool=tool_name,
                label=TOOL_LABELS.get(tool_name, tool_name),
                summary=payload.get("summary", "执行完成"),
            )
        except Exception:
            logger.exception(
                "MCP tool call failed, fallback to local: %s", tool_name
            )

    return _execute_tool_local(db, user_id, tool_name, arguments)


def chat(
    db: Session,
    user: User,
    data: ChatRequest,
    token: str | None = None,
) -> ChatResponse:
    """非流式 DeepSeek + 工具调用循环"""
    if not settings.LLM_API_KEY:
        raise BusinessException(
            message="未配置 DeepSeek API Key，请在 backend/.env 中设置 LLM_API_KEY"
        )

    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend([item.model_dump() for item in data.messages])

    steps: list[AgentStep] = []
    saved_plan = False

    # 最多 5 轮，防止模型无限调用工具
    for _ in range(5):
        try:
            completion = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )
        except Exception:
            logger.exception("DeepSeek chat completion failed")
            raise BusinessException(
                message="AI 服务调用失败，请检查 DeepSeek 配置或网络"
            )

        message = completion.choices[0].message

        # 没有工具调用，说明模型已经可以给出最终回答
        if not message.tool_calls:
            return ChatResponse(
                reply=message.content or "抱歉，我暂时无法回答这个问题。",
                steps=steps,
            )

        # 把模型发起的工具调用加入上下文
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    tool_call.model_dump() for tool_call in message.tool_calls
                ],
            }
        )

        # 执行工具，把结果返回给模型
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = _parse_arguments(tool_call.function.arguments)

            if tool_name == "save_study_plan" and saved_plan:
                tool_result = {
                    "error": "本轮对话已经保存过学习计划，不要重复保存"
                }
                step = AgentStep(
                    tool="save_study_plan",
                    label="保存学习计划",
                    summary="本轮已经保存过，跳过",
                )
            else:
                tool_result, step = _execute_tool(
                    db, user.id, tool_name, arguments, token=token
                )
                if (
                    tool_name == "save_study_plan"
                    and isinstance(tool_result, dict)
                    and tool_result.get("plan_id")
                ):
                    saved_plan = True

            steps.append(step)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result, ensure_ascii=False, default=str
                    ),
                }
            )

    return ChatResponse(
        reply="工具调用次数过多，请换一种问法。",
        steps=steps,
    )


def _sse(event: str, data: dict) -> str:
    """拼成前端能解析的 SSE 事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_chat(
    user_id: int,
    history: list[dict],
    token: str | None = None,
) -> Generator[str, None, None]:
    """SSE 流式 Agent：推状态、工具过程和回答 token"""
    if not settings.LLM_API_KEY:
        yield _sse(
            "error",
            {"message": "未配置 DeepSeek API Key，请在 backend/.env 中设置 LLM_API_KEY"},
        )
        return

    client = OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    # StreamingResponse 期间使用独立数据库会话，避免依赖会话提前关闭
    db = SessionLocal()
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)

        yield _sse("status", {"message": "正在思考..."})

        saved_plan = False

        # 最多 5 轮，防止模型无限调用工具
        for _ in range(5):
            tool_calls_map: dict[int, dict] = {}
            turn_content = ""

            try:
                stream = client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                    stream=True,
                )

                for chunk in stream:
                    if not chunk.choices:
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 普通回答文字，逐字推给前端
                    if delta.content:
                        turn_content += delta.content
                        yield _sse("token", {"text": delta.content})

                    # 流式返回的工具调用是分片的，需要按 index 拼接
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            index = tool_call.index or 0
                            item = tool_calls_map.setdefault(
                                index,
                                {
                                    "id": "",
                                    "type": "function",
                                    "function": {
                                        "name": "",
                                        "arguments": "",
                                    },
                                },
                            )

                            if tool_call.id:
                                item["id"] = tool_call.id

                            if tool_call.function:
                                if tool_call.function.name:
                                    item["function"]["name"] += (
                                        tool_call.function.name
                                    )
                                if tool_call.function.arguments:
                                    item["function"]["arguments"] += (
                                        tool_call.function.arguments
                                    )

            except Exception:
                logger.exception("DeepSeek stream failed")
                yield _sse(
                    "error",
                    {"message": "AI 服务调用失败，请检查 DeepSeek 配置或网络"},
                )
                return

            # 没有工具调用，说明这一轮就是最终回答
            if not tool_calls_map:
                yield _sse(
                    "done",
                    {"reply": turn_content or "抱歉，我暂时无法回答这个问题。"},
                )
                return

            # 有工具调用：把模型的工具请求加入上下文
            tool_calls = [
                tool_calls_map[index] for index in sorted(tool_calls_map)
            ]
            messages.append(
                {
                    "role": "assistant",
                    "content": turn_content,
                    "tool_calls": tool_calls,
                }
            )

            # 执行工具，把结果作为 tool 消息交回模型
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                arguments = _parse_arguments(
                    tool_call["function"]["arguments"]
                )
                label = TOOL_LABELS.get(tool_name, tool_name)

                yield _sse(
                    "tool_start",
                    {"tool": tool_name, "label": label},
                )

                if tool_name == "save_study_plan" and saved_plan:
                    tool_result = {
                        "error": "本轮对话已经保存过学习计划，不要重复保存"
                    }
                    summary = "本轮已经保存过，跳过"
                else:
                    try:
                        tool_result, step = _execute_tool(
                            db,
                            user_id,
                            tool_name,
                            arguments,
                            token=token,
                        )
                        summary = step.summary
                        if (
                            tool_name == "save_study_plan"
                            and isinstance(tool_result, dict)
                            and tool_result.get("plan_id")
                        ):
                            saved_plan = True
                    except Exception:
                        logger.exception("Tool execution failed")
                        tool_result = {"error": "工具执行失败"}
                        summary = "工具执行失败"

                yield _sse(
                    "tool_end",
                    {
                        "tool": tool_name,
                        "label": label,
                        "summary": summary,
                    },
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        yield _sse(
            "error",
            {"message": "工具调用次数过多，请换一种问法。"},
        )
    finally:
        db.close()
