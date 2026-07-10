"""
工具注册中心

所有工具在此汇总，Agent 运行时引用 ALL_TOOLS。

前端类比：
    这就像 Vue 的插件注册
    app.use(router)
    app.use(store)
    → Agent 绑定 tools = ALL_TOOLS
"""

from langchain_core.tools import tool as lc_tool
from app.tools.weather_tool import get_weather
from app.tools.search_tool import search_web
from app.tools.calculate_tool import calculate
from app.tools.translate_tool import translate

# 汇总所有工具
ALL_TOOLS: list[lc_tool] = [get_weather, search_web, calculate, translate]

# 工具元信息（供前端展示）
TOOLS_META = [
    {
        "name": get_weather.name,
        "description": get_weather.description,
        "args_schema": get_weather.args_schema.model_json_schema() if get_weather.args_schema else {},
        "icon": "🌤️",
        "color": "#53d769",
    },
    {
        "name": search_web.name,
        "description": search_web.description,
        "args_schema": search_web.args_schema.model_json_schema() if search_web.args_schema else {},
        "icon": "🔍",
        "color": "#0099ff",
    },
    {
        "name": calculate.name,
        "description": calculate.description,
        "args_schema": calculate.args_schema.model_json_schema() if calculate.args_schema else {},
        "icon": "🧮",
        "color": "#f5a623",
    },
    {
        "name": translate.name,
        "description": translate.description,
        "args_schema": translate.args_schema.model_json_schema() if translate.args_schema else {},
        "icon": "🌐",
        "color": "#e94560",
    },
]
