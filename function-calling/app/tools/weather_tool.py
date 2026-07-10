"""
Tool 1: get_weather — 天气查询（模拟数据）

LangChain @tool 装饰器：
- 自动从函数签名提取 name、description、parameters
- description 来自 docstring（LLM 靠它决定何时调用）
- 参数类型从 type hint 推断（类似 TypeScript）

前端类比：
    @tool ≈ 注册一个 API endpoint
    函数签名 ≈ API 的 request body schema
    docstring ≈ API 的 description（Swagger 文档）
"""

from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气信息，包括温度、湿度、天气状况等。当用户询问某个城市的天气时使用此工具。"""
    # 模拟天气数据（生产环境替换为真实 API，如和风天气/OpenWeatherMap）
    weather_db = {
        "北京": {"temp": "22°C", "condition": "晴天", "humidity": "45%", "wind": "北风3级", "aqi": "良好"},
        "上海": {"temp": "25°C", "condition": "多云", "humidity": "75%", "wind": "东风2级", "aqi": "良好"},
        "深圳": {"temp": "30°C", "condition": "阵雨", "humidity": "85%", "wind": "南风2级", "aqi": "中等"},
        "广州": {"temp": "32°C", "condition": "雷阵雨", "humidity": "90%", "wind": "东南风3级", "aqi": "中等"},
        "杭州": {"temp": "20°C", "condition": "阴天", "humidity": "65%", "wind": "微风", "aqi": "良好"},
        "成都": {"temp": "18°C", "condition": "小雨", "humidity": "80%", "wind": "微风", "aqi": "良好"},
        "武汉": {"temp": "28°C", "condition": "晴转多云", "humidity": "60%", "wind": "南风2级", "aqi": "良好"},
        "西安": {"temp": "24°C", "condition": "晴天", "humidity": "35%", "wind": "西北风3级", "aqi": "良好"},
        "重庆": {"temp": "26°C", "condition": "多云", "humidity": "70%", "wind": "微风", "aqi": "中等"},
        "南京": {"temp": "23°C", "condition": "晴间多云", "humidity": "55%", "wind": "东风2级", "aqi": "良好"},
        "New York": {"temp": "72°F", "condition": "Sunny", "humidity": "45%", "wind": "NW 10mph", "aqi": "Good"},
        "London": {"temp": "55°F", "condition": "Rainy", "humidity": "80%", "wind": "SW 15mph", "aqi": "Good"},
        "Tokyo": {"temp": "68°F", "condition": "Cloudy", "humidity": "60%", "wind": "E 8mph", "aqi": "Good"},
    }

    # 模糊匹配
    for key, data in weather_db.items():
        if city in key or key in city:
            return (
                f"📍 {key} 当前天气：\n"
                f"  天气：{data['condition']}\n"
                f"  温度：{data['temp']}\n"
                f"  湿度：{data['humidity']}\n"
                f"  风力：{data['wind']}\n"
                f"  空气质量：{data['aqi']}"
            )

    # 找不到时返回通用信息（避免工具报错，让 LLM 能优雅降级）
    return f"暂无 {city} 的天气数据。目前支持的城市：北京、上海、深圳、广州、杭州、成都、武汉、西安、重庆、南京、New York、London、Tokyo"
