from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_access_token, get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services import agent_service

router = APIRouter(prefix="/chat", tags=["课程助手"])


@router.post("/stream")
def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_access_token),
):
    """SSE 流式对话"""
    history = [item.model_dump() for item in data.messages]
    return StreamingResponse(
        agent_service.stream_chat(
            current_user.id, history, token=token
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("")
def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_access_token),
    db: Session = Depends(get_db),
):
    """课程助手对话，当前用户身份由 JWT 提供"""
    res = agent_service.chat(db, current_user, data, token=token)
    return Response.success(data=res)
