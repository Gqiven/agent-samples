"""
ReAct Agent 工具集

工具设计原则：
1. docstring 详细 → LLM 靠它决定何时调用
2. 返回结构化文本 → Agent 能准确解析结果
3. 错误友好 → 不抛异常，返回错误信息让 Agent 降级
"""

import math
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气信息，包括温度、湿度、天气状况。当用户询问某个城市的天气时使用。"""
    weather_db = {
        "北京": "☀️ 晴天 | 温度: 22°C | 湿度: 45% | 风力: 北风3级 | 空气质量: 良好",
        "上海": "⛅ 多云 | 温度: 25°C | 湿度: 75% | 风力: 东风2级 | 空气质量: 良好",
        "深圳": "🌧️ 阵雨 | 温度: 30°C | 湿度: 85% | 风力: 南风2级 | 空气质量: 中等",
        "广州": "⛈️ 雷阵雨 | 温度: 32°C | 湿度: 90% | 风力: 东南风3级 | 空气质量: 中等",
        "杭州": "☁️ 阴天 | 温度: 20°C | 湿度: 65% | 风力: 微风 | 空气质量: 良好",
        "成都": "🌧️ 小雨 | 温度: 18°C | 湿度: 80% | 风力: 微风 | 空气质量: 良好",
        "武汉": "🌤️ 晴转多云 | 温度: 28°C | 湿度: 60% | 风力: 南风2级 | 空气质量: 良好",
        "西安": "☀️ 晴天 | 温度: 24°C | 湿度: 35% | 风力: 西北风3级 | 空气质量: 良好",
        "New York": "☀️ Sunny | 72°F | Humidity: 45% | Wind: NW 10mph",
        "London": "🌧️ Rainy | 55°F | Humidity: 80% | Wind: SW 15mph",
        "Tokyo": "☁️ Cloudy | 68°F | Humidity: 60% | Wind: E 8mph",
    }
    for key, val in weather_db.items():
        if city in key or key in city:
            return f"【{key}天气】{val}"
    return f"暂无 {city} 的天气数据。支持：北京/上海/深圳/广州/杭州/成都/武汉/西安/New York/London/Tokyo"


@tool
def search_web(query: str) -> str:
    """搜索互联网获取信息。当需要查找实时信息、新闻、最新数据时使用。"""
    kb = {
        "Python": "Python 是高级编程语言，最新版 3.12。支持异步编程(asyncio)、类型提示(Type Hints)、模式匹配(match-case)等现代特性。",
        "LangChain": "LangChain 是 LLM 应用开发框架(2022年发布)。核心模块：Chain(链式调用)、Agent(智能体)、RAG(检索增强)。2024年推出 LangGraph 作为 Agent 编排首选。",
        "LangGraph": "LangGraph 是基于状态图的 Agent 编排框架。核心概念：StateGraph、Node、Edge、Conditional Edge、Checkpoint。支持 ReAct/Plan-and-Execute 等模式。",
        "AI Agent": "AI Agent = LLM + 工具 + 记忆 + 规划。核心模式：ReAct(推理+行动循环)、Plan-and-Execute(先规划后执行)、Multi-Agent(多智能体协作)。",
        "RAG": "RAG(Retrieval-Augmented Generation)通过外部知识检索减少幻觉。关键链路：Embedding → Chunking → Vector DB → Retrieval → Rerank → Generation。",
    }
    for key, val in kb.items():
        if key.lower() in query.lower() or any(w in val for w in query.split()[:3]):
            return f"🔍 搜索结果: {val}"
    return f"🔍 搜索'{query}'：暂无精确结果。建议提供更具体的搜索关键词。"


@tool
def calculate(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算、三角函数、对数、常量pi/e等。需要数学计算时使用。"""
    safe_ns = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sqrt": math.sqrt, "pow": math.pow, "log": math.log,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
    }
    expr = expression.strip().replace("×", "*").replace("÷", "/")
    try:
        result = eval(expr, {"__builtins__": {}}, safe_ns)
        if isinstance(result, float) and result == int(result):
            result = int(result)
        return f"🧮 {expression} = {result}"
    except ZeroDivisionError:
        return f"🧮 错误: 除数不能为零"
    except Exception as e:
        return f"🧮 计算错误: {e}"


@tool
def get_time(timezone: str = "Asia/Shanghai") -> str:
    """获取当前时间。当用户询问当前时间、日期时使用。"""
    from datetime import datetime
    try:
        import pytz
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return f"🕐 当前时间({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S %A')}"
    except Exception:
        now = datetime.now()
        return f"🕐 当前时间(本地): {now.strftime('%Y-%m-%d %H:%M:%S %A')}"


@tool
def count_words(text: str) -> str:
    """统计文本的字数、词数、句数。当用户需要文本分析时使用。"""
    chars = len(text)
    words = len(text.split())
    sentences = text.count("。") + text.count("！") + text.count("？") + text.count(".") + text.count("!") + text.count("?")
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return (
        f"📊 文本统计:\n"
        f"  总字符数: {chars}\n"
        f"  中文字数: {chinese_chars}\n"
        f"  英文词数: {words - chinese_chars}\n"
        f"  句子数: {max(sentences, 1)}"
    )


ALL_TOOLS = [get_weather, search_web, calculate, get_time, count_words]
