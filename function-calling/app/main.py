import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from app.models.schemas import ChatRequest, StreamEvent
from app.agent import run_agent_stream
from app.tools import TOOLS_META

load_dotenv()

app = FastAPI(title="Function Calling Agent Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式 Agent 对话"""
    async def event_generator():
        async for event in run_agent_stream(req.message, req.provider, req.model):
            yield {"data": json.dumps(event, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/api/tools")
async def list_tools():
    """可用工具列表（含 JSON Schema）"""
    return {"tools": TOOLS_META}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
