# Function Calling Agent Demo

> 4 个工具 + LangGraph ReAct Agent，Agent 自主决定调用哪个工具

## 项目结构

```
function-calling-demo/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── agent.py                   # LangGraph ReAct Agent 编排
│   ├── models/
│   │   └── schemas.py             # Pydantic 模型
│   └── tools/
│       ├── __init__.py            # 工具注册中心
│       ├── weather_tool.py        # 🌤️ get_weather — 天气查询（模拟）
│       ├── search_tool.py         # 🔍 search_web — 网页搜索（真实API+降级）
│       ├── calculate_tool.py      # 🧮 calculate — 数学计算（安全 eval）
│       └── translate_tool.py      # 🌐 translate — 文本翻译
├── frontend/                      # Vue3 前端
├── requirements.txt
└── .env.example
```

## 快速启动

```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API Key
python -m app.main    # 端口 8002

cd frontend && npm install && npm run dev  # 端口 3002
```

## 4 个工具详解

### Tool 1: get_weather（模拟数据）

```python
@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气信息"""
    # 模拟数据，支持13个城市
    # 前端类比：mock API，开发阶段用模拟数据
```

### Tool 2: search_web（真实 API + 降级）

```python
@tool
def search_web(query: str, num_results: int = 5) -> str:
    """搜索互联网获取最新信息"""
    # 优先调 SearXNG 真实 API
    # 失败自动降级到模拟数据
    # 前端类比：try { fetch(api) } catch { fallback() }
```

### Tool 3: calculate（安全数学计算）

```python
@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    # 安全 eval：限制命名空间，禁用 __builtins__
    # 支持：+ - * / ** sqrt sin cos log pi e ...
    # 前端类比：沙箱化的 new Function()
```

### Tool 4: translate（文本翻译）

```python
@tool
def translate(text: str, target_lang: str = "英文") -> str:
    """将文本翻译为指定语言"""
    # 模拟翻译，可替换为真实 API
```

## Agent 如何决定调用哪个工具？

```
用户: "北京天气如何？再把结果翻译成英文"

ReAct 循环：
  Think → 用户要查北京天气 + 翻译，需要两个工具
  Act   → get_weather(city="北京")          ← 第1次工具调用
  Observe → 📍 北京 晴天 22°C ...
  Think → 拿到天气数据，现在需要翻译
  Act   → translate(text="北京：晴天22°C...", target_lang="英文")  ← 第2次工具调用
  Observe → 🌐 Beijing: Sunny, 22°C ...
  Answer → 整合结果输出最终回答
```

## Function Calling 核心概念

| 步骤 | 说明 | 前端类比 |
|------|------|---------|
| 定义 Tool | `@tool` + docstring + type hint | 定义 API endpoint + Swagger 文档 |
| 绑定 Tool | `llm.bind_tools(ALL_TOOLS)` | 注册可用 API 列表给 UI |
| LLM 决策 | 分析用户意图 → 选择工具 + 提取参数 | 类似前端表单自动校验+提交 |
| 执行 Tool | `ToolNode` 自动执行 | 调用 API 获取数据 |
| 错误处理 | 工具失败 → 降级/重试 | try-catch + fallback |

## @tool 装饰器 vs Pydantic 定义

```python
# 方式1: @tool 装饰器（推荐，简洁）
@tool
def get_weather(city: str) -> str:
    """docstring 就是 LLM 看到的工具描述"""
    ...

# 方式2: Pydantic 定义（更灵活，适合复杂参数）
class WeatherInput(BaseModel):
    city: str = Field(description="城市名称")
    unit: Literal["celsius", "fahrenheit"] = "celsius"

@tool(args_schema=WeatherInput)
def get_weather(city: str, unit: str = "celsius") -> str:
    ...
```
