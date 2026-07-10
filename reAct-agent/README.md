# ReAct Agent Demo

> LangGraph 实现完整 ReAct 循环：Thought → Action → Observation → Thought → ... → Answer

## 项目结构

```
react-agent-demo/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── react_agent.py             # ⭐ ReAct Agent 核心（状态图 + 三大组件）
│   ├── models/
│   │   └── schemas.py             # Pydantic 模型
│   └── tools/
│       └── __init__.py            # 5 个工具：天气/搜索/计算/时间/统计
├── frontend/                      # Vue3 前端（ReAct 循环可视化）
├── requirements.txt
└── .env.example
```

## 快速启动

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API Key
python -m app.main    # 端口 8003

cd frontend && npm install && npm run dev  # 端口 3003
```

## ReAct Agent 三大核心组件

### 1. agent_node — LLM 思考 + 决策

```python
def agent_node(state: ReActState) -> dict:
    """
    接收消息历史 → LLM 思考 → 返回决策
    - 有 tool_calls → 需要调用工具
    - 无 tool_calls → 直接回答

    前端类比：Vue 组件接收 props → 调 API → emit 结果
    """
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    messages = [SystemMessage(content=REACT_SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "iteration": state["iteration"] + 1}
```

### 2. tool_node — 执行工具调用

```python
# LangGraph 内置 ToolNode，自动处理：
# AIMessage(tool_calls=[...]) → 执行对应工具 → 返回 ToolMessage
tool_node = ToolNode(ALL_TOOLS)

# 前端类比：API middleware
# request → route to handler → response
```

### 3. should_continue — 条件边（路由守卫）

```python
def should_continue(state: ReActState) -> Literal["tools", "end"]:
    """
    决定循环是否继续：
    - 有 tool_calls 且未超迭代 → "tools"（继续）
    - 无 tool_calls 或超迭代 → "end"（结束）

    前端类比：
        router.beforeEach((to, from, next) => {
            if (hasToolCalls && iteration < max) next('/tools');
            else next('/end');
        })
    """
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"
```

## LangGraph 状态图构建

```python
graph = StateGraph(ReActState)

# 添加节点
graph.add_node("agent", agent_node)    # 思考页
graph.add_node("tools", tool_node)     # 执行页

# 入口
graph.set_entry_point("agent")

# 条件边（核心！实现 ReAct 循环）
graph.add_conditional_edges(
    "agent",                    # 源节点
    should_continue,            # 条件函数
    {"tools": "tools", "end": END},  # 映射
)

# 工具执行后回到 agent（循环！）
graph.add_edge("tools", "agent)

# 编译
agent = graph.compile()
```

## ReAct 循环示例

```
用户: "北京和上海哪个更热？"

迭代 #1:
  Thought → 用户要比较两个城市温度，需要分别查天气
  Action  → get_weather(city="北京")
  Observation → ☀️ 晴天 | 温度: 22°C | ...

迭代 #2:
  Thought → 拿到北京22°C，还需要上海数据
  Action  → get_weather(city="上海")
  Observation → ⛅ 多云 | 温度: 25°C | ...

迭代 #3:
  Thought → 北京22°C，上海25°C，上海更热
  Answer  → 上海(25°C)比北京(22°C)更热，温差3°C
```

## 前端类比对照表

| LangGraph | Vue/React 类比 | 说明 |
|-----------|---------------|------|
| `StateGraph` | Vue Router | 路由图 |
| `add_node` | 添加路由页面 | 注册处理节点 |
| `add_edge` | `router.push()` | 无条件跳转 |
| `add_conditional_edges` | `router.beforeEach()` | 条件分支 |
| `ReActState(TypedDict)` | Pinia Store `state` | 共享数据 |
| `add_messages` | `array.push()` | 消息自动合并 |
| `set_entry_point` | 默认路由 `/` | 起始节点 |
| `compile()` | `app.mount()` | 编译挂载 |
| `stream()` | `for await...of` | 流式输出 |
| **循环 edge** | **while 循环** | **LangGraph 核心能力：支持循环！** |

## 5 个工具

| 工具 | 说明 | 场景 |
|------|------|------|
| `get_weather` | 查城市天气 | 单步/对比 |
| `search_web` | 搜索互联网 | 知识查询 |
| `calculate` | 数学计算 | 运算需求 |
| `get_time` | 查当前时间 | 时间相关 |
| `count_words` | 统计文本字数 | 文本分析 |
