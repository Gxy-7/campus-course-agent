import asyncio
import json
import logging

from fastmcp import Client

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_payload(result) -> dict:
    """兼容 FastMCP 的结构化输出和文本输出"""
    data = getattr(result, "data", None)

    if data is not None:
        if isinstance(data, dict):
            payload = data
        elif isinstance(data, str):
            payload = json.loads(data)
        elif hasattr(data, "model_dump"):
            payload = data.model_dump()
        else:
            raise RuntimeError("MCP 返回了无法解析的数据")
    else:
        payload = None
        for block in getattr(result, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                payload = json.loads(text)
                break
        if payload is None:
            raise RuntimeError("MCP 返回结果为空")

    # FastMCP 某些版本会包一层 {"result": ...}
    if (
        isinstance(payload, dict)
        and "result" in payload
        and "summary" not in payload
    ):
        payload = payload["result"]

    return payload


async def _call_tool_async(
    name: str, arguments: dict, token: str
) -> dict:
    async with Client(settings.MCP_SERVER_URL, timeout=30) as client:
        result = await client.call_tool(
            name,
            {**arguments, "token": token},
            timeout=60,
        )
        return _extract_payload(result)


def call_tool(name: str, arguments: dict, token: str) -> dict:
    """同步调用 MCP 工具，供现有同步 Agent 使用"""
    if not settings.MCP_SERVER_URL:
        raise RuntimeError("未配置 MCP_SERVER_URL")

    return asyncio.run(_call_tool_async(name, arguments, token))
