from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ToolCallDisplay(BaseModel):
    """前端展示工具调用过程"""
    tool_name: str
    tool_args: dict
    tool_result: str
    execution_time_ms: float = 0


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None


class StreamEvent(BaseModel):
    type: str  # "thought" | "tool_call" | "tool_result" | "answer" | "done"
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    execution_time_ms: Optional[float] = None
