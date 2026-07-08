from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# ========== Chain 1: 基础链 ==========

class BasicChainRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None


class BasicChainResponse(BaseModel):
    question: str
    answer: str


# ========== Chain 2: 结构化输出 ==========

class MovieReview(BaseModel):
    """Pydantic 模型：LLM 输出将被解析为这个结构"""
    movie_name: str = Field(description="电影名称")
    rating: int = Field(ge=1, le=10, description="评分 1-10")
    genre: list[str] = Field(description="类型标签，如['科幻','动作']")
    summary: str = Field(description="一句话评价")
    recommend: bool = Field(description="是否推荐")


class StructuredChainRequest(BaseModel):
    movie_name: str = Field(..., description="电影名称")
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None


class StructuredChainResponse(BaseModel):
    input_movie: str
    parsed: MovieReview
    raw_output: str


# ========== Chain 3: 多轮对话 ==========

class ConversationMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ConversationChainRequest(BaseModel):
    message: str = Field(..., description="当前用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID，为空则新建")
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None


class ConversationChainResponse(BaseModel):
    conversation_id: str
    answer: str
    history: list[ConversationMessage]


# ========== 通用 ==========

class StreamEvent(BaseModel):
    type: str  # "token" | "done" | "error"
    content: str
    data: Optional[dict] = None
