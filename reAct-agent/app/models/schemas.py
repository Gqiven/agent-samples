from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ReActStep(BaseModel):
    """ReAct 单步记录"""
    step: int
    phase: str  # "thought" | "action" | "observation"
    thought: str = ""
    action_name: str = ""
    action_args: dict = {}
    observation: str = ""


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None
    max_iterations: int = Field(default=6, ge=1, le=15)


class StreamEvent(BaseModel):
    type: str  # "thought" | "action" | "observation" | "answer" | "iteration" | "done"
    content: str
    step: int = 0
    iteration: int = 0
    action_name: Optional[str] = None
    action_args: Optional[dict] = None
    max_iterations: int = 6
