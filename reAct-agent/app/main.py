import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from app.models.schemas import ChatRequest, StreamEvent
from app.react_agent import run_react_agent_stream
from app.tools import ALL_TOOLS

load_dotenv()

app = FastAPI(title="ReAct Agent Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式 ReAct Agent 对话"""
    async def event_generator():
        async for event in run_react_agent_stream(
            req.message, req.provider, req.model, req.max_iterations
        ):
            yield {"data": json.dumps(event, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/api/tools")
async def list_tools():
    """可用工具列表"""
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "args_schema": t.args_schema.model_json_schema() if t.args_schema else {},
            }
            for t in ALL_TOOLS
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
