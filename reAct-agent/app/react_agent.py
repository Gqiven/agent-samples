"""
LangGraph ReAct Agent — 完整循环实现

ReAct (Reasoning + Acting) 核心思想：
    思考(Thought) → 行动(Action) → 观察(Observation) → 思考 → ...

LangGraph 实现的三个核心组件：
    1. agent_node  — LLM 思考 + 决策（选工具 or 直接回答）
    2. tool_node   — 执行工具调用
    3. should_continue — 条件边：有 tool_calls → 继续循环；没有 → 结束

状态图结构：
    ┌───────────┐   should_continue="tools"   ┌───────────┐
    │   agent   │ ────────────────────────→ │   tools    │
    │  (思考)   │                             │  (执行)    │
    └───────────┘ ←──────────────────────── └───────────┘
         │              should_continue="end"
         └───────────────→ END (输出最终回答)

前端类比：
    StateGraph ≈ Vue Router 路由图
    agent_node ≈ 路由页面 "思考页"
    tool_node ≈ 路由页面 "执行页"
    should_continue ≈ 路由守卫 router.beforeEach
    State(TypedDict) ≈ Pinia Store 的 state 定义
    Conditional Edge ≈ if/else 条件渲染

关键区别：LangGraph 支持【循环】
    普通 Router: A → B → C → END（线性）
    LangGraph:   A → B → A → B → A → END（循环，直到条件满足）
"""

import os
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, RemoveMessage
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.tools import ALL_TOOLS


# ============================================================
# State 定义 — Agent 的"Pinia Store"
# ============================================================

class ReActState(TypedDict):
    """
    ReAct Agent 共享状态

    前端类比：这就像 Pinia 的 state 定义
    - messages: 对话消息（add_messages = 自动合并，类似 array.push）
    - iteration: 当前循环次数（防止无限循环）
    - max_iterations: 最大循环次数限制
    """
    messages: Annotated[list, add_messages]
    iteration: int
    max_iterations: int


# ============================================================
# System Prompt — Agent 的"人格设定"
# ============================================================

REACT_SYSTEM_PROMPT = """你是一个使用 ReAct（推理+行动）模式的 AI Agent。

## 工作模式
每次收到用户问题，你按以下循环工作：
1. **Thought（思考）**：分析问题，决定下一步做什么
2. **Action（行动）**：选择合适的工具并调用
3. **Observation（观察）**：分析工具返回的结果
4. 如果还需要更多信息，继续循环；否则给出最终回答

## 可用工具
- get_weather: 查城市天气
- search_web: 搜索互联网
- calculate: 数学计算
- get_time: 查当前时间
- count_words: 统计文本字数

## 规则
- 不确定的事实信息，用 search_web 查证
- 数学计算，用 calculate 工具，不要自己算
- 可以连续调用多个工具解决复杂问题
- 当你有了足够信息，直接回答，不要继续调用工具
- 回答要简洁、准确、中文为主"""


# ============================================================
# LLM 初始化
# ============================================================

def _get_llm(provider: str | None = None, model: str | None = None):
    provider = provider or os.getenv("LLM_PROVIDER", "deepseek")
    return ChatDeepSeek(
        model=model or os.getenv("LLM_MODEL", "deepseek-v4-flash"),
        temperature=0.7,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )


# ============================================================
# Node 1: agent_node — LLM 思考 + 决策
# ============================================================

def agent_node(state: ReActState) -> dict:
    """
    Agent 节点：LLM 接收当前消息历史，思考并决定下一步

    输入：ReActState（包含所有历史消息 + 工具结果）
    处理：LLM 分析上下文，决定：
        - 调用工具 → 返回 AIMessage(tool_calls=[...])
        - 直接回答 → 返回 AIMessage(content="最终回答")
    输出：{"messages": [AIMessage], "iteration": n+1}

    前端类比：
        这就像一个 Vue 组件接收 props(messages)，
        调用 API(LLM)，返回 emit("update:messages", newMsg)
    """
    llm = _get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # 组装消息：系统提示 + 对话历史
    messages = [SystemMessage(content=REACT_SYSTEM_PROMPT)] + state["messages"]

    # 调用 LLM
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
        "iteration": state["iteration"] + 1,
    }


# ============================================================
# Node 2: tool_node — 执行工具调用（LangGraph 内置）
# ============================================================

# ToolNode 是 LangGraph 内置的工具执行节点
# 它自动处理 AIMessage.tool_calls → 执行对应工具 → 返回 ToolMessage
# 类似前端的 API middleware：接收请求 → 调用后端 → 返回响应

tool_node = ToolNode(ALL_TOOLS)


# ============================================================
# Conditional Edge: should_continue — 路由守卫
# ============================================================

def should_continue(state: ReActState) -> Literal["tools", "end"]:
    """
    条件边：决定 Agent 循环是否继续

    逻辑：
    1. 检查最后一条消息是否有 tool_calls → 有 → 继续循环("tools")
    2. 没有 tool_calls → LLM 已经给出最终回答 → 结束("end")
    3. 安全检查：超过最大迭代次数 → 强制结束

    前端类比：
        router.beforeEach((to, from, next) => {
            if (hasToolCalls && iteration < max) {
                next('/tools');  // 继续循环
            } else {
                next('/end');    // 结束
            }
        })

    LangGraph 提供了 ToolsCondition 作为默认实现，
    但我们手动实现以便加入迭代次数限制。
    """
    last_msg = state["messages"][-1]

    # 安全限制：防止无限循环
    if state["iteration"] >= state["max_iterations"]:
        return "end"

    # 检查是否有工具调用
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"

    # 没有工具调用 → LLM 已给出最终回答
    return "end"


# ============================================================
# 构建状态图 — 组装 Agent
# ============================================================

def create_react_agent(provider: str | None = None, model: str | None = None, max_iterations: int = 6):
    """
    构建 ReAct Agent 的 LangGraph 状态图

    步骤（类似 Vue Router 配置）：
    1. 创建 StateGraph(ReActState)     → 创建路由实例
    2. add_node("agent", agent_node)    → 添加"思考页"路由
    3. add_node("tools", tool_node)     → 添加"执行页"路由
    4. set_entry_point("agent")         → 设置默认路由
    5. add_conditional_edges(...)       → 添加路由守卫（条件分支）
    6. add_edge("tools", "agent")       → 执行完后回到思考页
    7. compile()                        → app.mount() 编译挂载
    """
    # 保存 provider/model 到闭包，agent_node 闭包内会用 _get_llm()
    # 注意：agent_node 用的是模块级 _get_llm()，这里仅定义图结构

    graph = StateGraph(ReActState)

    # 1. 添加节点
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # 2. 设置入口：每次新对话从 agent 节点开始
    graph.set_entry_point("agent")

    # 3. 条件边：agent → tools 或 agent → END
    graph.add_conditional_edges(
        "agent",               # 源节点
        should_continue,       # 条件函数（路由守卫）
        {                      # 映射表：函数返回值 → 目标节点
            "tools": "tools",  # should_continue="tools" → 跳到 tools 节点
            "end": END,        # should_continue="end" → 结束
        },
    )

    # 4. 工具执行后回到 agent，继续 ReAct 循环
    graph.add_edge("tools", "agent")

    # 5. 编译
    return graph.compile()


# ============================================================
# 流式执行 — yield 每个步骤的事件
# ============================================================

async def run_react_agent_stream(
    message: str,
    provider: str | None = None,
    model: str | None = None,
    max_iterations: int = 6,
):
    """
    流式执行 ReAct Agent

    每个事件对应 ReAct 循环中的一个阶段：
    - thought:  Agent 思考（AIMessage 的文字部分）
    - action:   Agent 选择工具（AIMessage 的 tool_calls）
    - observation: 工具返回结果（ToolMessage）
    - answer:   最终回答（无 tool_calls 的 AIMessage）
    """
    graph = create_react_agent(provider, model, max_iterations)
    input_state = {
        "messages": [HumanMessage(content=message)],
        "iteration": 0,
        "max_iterations": max_iterations,
    }

    iteration = 0

    # stream(mode="updates") 返回每个节点的输出
    for event in graph.stream(input_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            if "messages" not in node_output:
                continue

            # 获取当前迭代次数
            iteration = node_output.get("iteration", iteration)

            for msg in node_output["messages"]:
                if isinstance(msg, AIMessage):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        # ===== Action 阶段 =====
                        # Agent 决定调用工具
                        for tc in msg.tool_calls:
                            yield {
                                "type": "action",
                                "content": f"选择工具: {tc['name']}",
                                "step": iteration,
                                "iteration": iteration,
                                "action_name": tc["name"],
                                "action_args": tc["args"],
                                "max_iterations": max_iterations,
                            }
                    elif msg.content:
                        # ===== Answer 阶段 =====
                        # Agent 给出最终回答
                        yield {
                            "type": "answer",
                            "content": msg.content,
                            "step": iteration,
                            "iteration": iteration,
                            "max_iterations": max_iterations,
                        }

                elif isinstance(msg, ToolMessage):
                    # ===== Observation 阶段 =====
                    # 工具返回结果
                    yield {
                        "type": "observation",
                        "content": msg.content[:800],
                        "step": iteration,
                        "iteration": iteration,
                        "action_name": msg.name or "",
                        "max_iterations": max_iterations,
                    }

    yield {
        "type": "done",
        "content": "",
        "step": iteration,
        "iteration": iteration,
        "max_iterations": max_iterations,
    }