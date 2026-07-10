"""
LangGraph ReAct Agent — 工具调用的核心编排

执行流程（ReAct 循环）：
    用户问题 → Agent 思考 → 选择工具 → 执行工具 → 观察结果 → 继续思考/回答

LangGraph 状态图：
    ┌─────────┐     有工具调用     ┌─────────┐
    │  agent  │ ──────────────→ │  tools   │
    │ (思考)  │                  │ (执行)   │
    └─────────┘ ←────────────── └─────────┘
         │           无工具调用
         └──────→ END（输出最终回答）

前端类比：
    StateGraph ≈ Vue Router 路由图
    Node ≈ 路由页面
    Conditional Edge ≈ 路由守卫（if/else 分支）
    State ≈ Pinia Store（共享数据）
"""

import os
import time
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools import ALL_TOOLS


class AgentState(TypedDict):
    """Agent 状态 — 所有节点共享的数据对象

    前端类比：Pinia Store 的 state
    - messages: 对话消息列表（自动合并，类似数组的 push）
    - tool_calls_trace: 工具调用追踪记录
    """
    messages: Annotated[list, add_messages]
    tool_calls_trace: list[dict]


SYSTEM_PROMPT = """你是一个功能强大的AI助手，可以使用以下工具来帮助用户：

🛠️ 可用工具：
1. **get_weather** - 查询城市天气（温度、湿度、风力、空气质量）
2. **search_web** - 搜索互联网获取最新信息
3. **calculate** - 计算数学表达式（支持三角函数、对数等）
4. **translate** - 翻译文本到指定语言

📋 使用规则：
- 根据用户问题选择合适的工具，不需要时直接回答
- 可以连续调用多个工具（如先查天气再翻译）
- 数学计算优先使用 calculate 工具，不要自己算
- 搜索实时信息时使用 search_web
- 回答要简洁准确，中文为主
"""

# 创建llm实例
def _get_llm(provider: str | None = None, model: str | None = None):
    provider = provider or os.getenv("LLM_PROVIDER", "deepseek")
    return ChatDeepSeek(
        model=model or os.getenv("LLM_MODEL", "deepseek-v4-flash"),
        temperature=0.7,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    # if provider == "deepseek":
    #     return ChatDeepSeek(
    #         model=model or os.getenv("LLM_MODEL", "deepseek-v4-flash"),
    #         temperature=0.7,
    #         base_url=os.getenv("DEEPSEEK_BASE_URL"),
    #         api_key=os.getenv("DEEPSEEK_API_KEY")
    #     )
    # elif provider == "anthropic":
    #     return ChatAnthropic(
    #         model=model or os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
    #         temperature=0.7,
    #     )
    # return ChatOpenAI(
    #     model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
    #     temperature=0.7,
    #     base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    # )


def create_agent_graph(provider: str | None = None, model: str | None = None):
    """
    创建 LangGraph ReAct Agent

    核心概念对照：
    ┌──────────────────┬────────────────────┐
    │ LangGraph        │ 前端类比           │
    ├──────────────────┼────────────────────┤
    │ StateGraph       │ Vue Router 路由图  │
    │ add_node         │ 添加路由页面       │
    │ add_edge         │ 页面跳转           │
    │ add_conditional  │ 路由守卫 if/else   │
    │ State (TypedDict)│ Pinia Store        │
    │ compile()        │ app.mount()        │
    └──────────────────┴────────────────────┘
    """
    # 1. 初始化 LLM + 绑定工具
    llm = _get_llm(provider, model)
    # bind_tools：告诉 LLM 有哪些工具可用
    # 类似前端注册 API endpoints，让 UI 知道可以调哪些接口
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # 2. 定义 Agent 节点（思考 + 决策）
    def agent_node(state: AgentState) -> dict:
        """
        Agent 节点：LLM 思考并决定下一步

        输入：当前消息历史
        输出：AIMessage（可能包含 tool_calls）
        """
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # 3. 定义条件边（路由守卫）
    def should_continue(state: AgentState) -> str:
        """
        条件边：决定下一步走哪条路

        - 如果 LLM 返回了 tool_calls → 走 "tools" 节点
        - 如果没有 tool_calls → 走 "end" 结束

        前端类比：
            if (response.toolCalls.length > 0) {
                router.push('/tools');
            } else {
                router.push('/end');
            }
        """
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "end"

    # 4. 工具执行节点（LangGraph 内置）
    tool_node = ToolNode(ALL_TOOLS)

    # 5. 构建状态图
    graph = StateGraph(AgentState)

    # 添加节点（类似 Vue Router 的 routes）
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # 设置入口点
    graph.set_entry_point("agent")

    # 添加条件边（类似路由守卫）
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )

    # 工具执行后回到 Agent 继续思考
    graph.add_edge("tools", "agent")

    # 6. 编译图（类似 app.mount()）
    return graph.compile()


async def run_agent_stream(message: str, provider: str | None = None, model: str | None = None):
    """
    流式执行 Agent，yield 每个步骤的事件

    事件类型：
    - thought: Agent 思考（AIMessage 内容）
    - tool_call: Agent 决定调用工具
    - tool_result: 工具执行结果
    - answer: 最终回答
    - done: 执行完成
    """
    graph = create_agent_graph(provider, model)
    input_msg = {"messages": [HumanMessage(content=message)]}

    for event in graph.stream(input_msg, stream_mode="updates"):
        for node_name, node_output in event.items():
            if "messages" not in node_output:
                continue

            for msg in node_output["messages"]:
                if isinstance(msg, AIMessage):
                    # Agent 思考 + 可能的工具调用
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield {
                                "type": "tool_call",
                                "content": f"调用工具: {tc['name']}",
                                "tool_name": tc["name"],
                                "tool_args": tc["args"],
                            }
                    elif msg.content:
                        yield {
                            "type": "answer",
                            "content": msg.content,
                        }

                elif isinstance(msg, ToolMessage):
                    # 工具执行结果
                    yield {
                        "type": "tool_result",
                        "content": msg.content[:1000],
                        "tool_name": msg.name or "",
                    }

    yield {"type": "done", "content": ""}
