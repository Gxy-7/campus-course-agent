from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """前端传上来的历史消息，只允许 user / assistant"""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    # 最多带最近 20 条，避免上下文无限增长
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=20)


class AgentStep(BaseModel):
    """一次工具调用的过程信息"""

    tool: str
    label: str
    summary: str


class ChatResponse(BaseModel):
    reply: str
    steps: list[AgentStep] = []
