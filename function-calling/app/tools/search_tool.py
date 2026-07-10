"""
Tool 2: search_web — 网页搜索（调真实 API）

与 get_weather 的区别：
- get_weather 是纯模拟，无网络请求
- search_web 调用真实搜索 API（SearXNG / Serper / Tavily）

设计要点：
1. 真实 API 调用用 try-catch 包裹
2. 失败时返回降级结果，不抛异常（Agent 才能继续工作）
3. 超时控制，避免工具阻塞 Agent

前端类比：
    这就像前端调接口，要处理 loading / error / timeout
"""

import os
import httpx
from langchain_core.tools import tool

# 搜索 API 配置（推荐用 SearXNG 自建，免费无限制）
# 也可替换为 Serper.dev / Tavily / Bing Search API
SEARXNG_URL = os.getenv("SEARXNG_URL", "https://searx.be")
SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "10"))


@tool
def search_web(query: str, num_results: int = 5) -> str:
    """搜索互联网获取最新信息。当用户询问实时信息、新闻、最新数据或你不确定的知识时使用此工具。"""
    # 优先尝试真实 API
    try:
        result = _search_searxng(query, num_results)
        if result:
            return result
    except Exception:
        pass

    # 降级：模拟搜索结果
    return _search_fallback(query)


def _search_searxng(query: str, num_results: int) -> str | None:
    """调用 SearXNG 搜索 API"""
    try:
        resp = httpx.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "language": "zh-CN",
            },
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:num_results]

        if not results:
            return None

        output_lines = [f"🔍 搜索 '{query}' 的结果：\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            url = r.get("url", "")
            snippet = r.get("content", "")
            output_lines.append(f"{i}. {title}\n   链接: {url}\n   摘要: {snippet}\n")

        return "\n".join(output_lines)
    except Exception:
        return None


def _search_fallback(query: str) -> str:
    """降级搜索（模拟数据）"""
    mock_results = {
        "Python": [
            {"title": "Python 官方文档", "url": "https://docs.python.org", "snippet": "Python 是一种广泛使用的高级编程语言，最新版本 3.12。"},
            {"title": "Python 教程 - 菜鸟教程", "url": "https://www.runoob.com/python", "snippet": "Python 基础语法、数据类型、面向对象等教程。"},
            {"title": "Real Python", "url": "https://realpython.com", "snippet": "In-depth Python tutorials and guides."},
        ],
        "LangChain": [
            {"title": "LangChain 官方文档", "url": "https://python.langchain.com", "snippet": "LangChain 是 LLM 应用开发框架，支持 Chain、Agent、RAG。"},
            {"title": "LangChain GitHub", "url": "https://github.com/langchain-ai/langchain", "snippet": "LangChain 开源仓库，85k+ stars。"},
        ],
        "LangGraph": [
            {"title": "LangGraph 官方文档", "url": "https://langchain-ai.github.io/langgraph", "snippet": "基于状态图的 Agent 编排框架。"},
            {"title": "LangGraph 入门教程", "url": "https://academy.langchain.com", "snippet": "LangChain Academy 免费课程。"},
        ],
    }

    # 匹配模拟数据
    for key, results in mock_results.items():
        if key.lower() in query.lower():
            lines = [f"🔍 搜索 '{query}' 的结果（模拟数据）：\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}\n   链接: {r['url']}\n   摘要: {r['snippet']}\n")
            return "\n".join(lines)

    # 通用模拟结果
    return (
        f"🔍 搜索 '{query}' 的结果（模拟数据）：\n\n"
        f"1. {query} - 维基百科\n"
        f"   链接: https://zh.wikipedia.org/wiki/{query}\n"
        f"   摘要: 关于{query}的百科全书条目。\n\n"
        f"2. {query} - 最新资讯\n"
        f"   链接: https://www.google.com/search?q={query}\n"
        f"   摘要: {query}相关的最新新闻和信息。\n\n"
        f"💡 提示：配置 SearXNG_URL 环境变量可启用真实搜索。"
    )
