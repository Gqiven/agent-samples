"""
Tool 4: translate — 文本翻译

额外工具，展示多工具组合的场景。
当用户问"北京天气如何？再把结果翻译成英文"时，
Agent 会先调 get_weather，再调 translate。
"""

from langchain_core.tools import tool


@tool
def translate(text: str, target_lang: str = "英文") -> str:
    """将文本翻译为指定语言。当用户需要翻译文本时使用此工具。

    参数:
        text: 要翻译的文本
        target_lang: 目标语言，如"英文"、"中文"、"日文"、"法文"等
    """
    # 模拟翻译（生产环境替换为翻译 API）
    mock_translations = {
        ("你好", "英文"): "Hello",
        ("你好", "日文"): "こんにちは",
        ("谢谢", "英文"): "Thank you",
        ("Hello", "中文"): "你好",
        ("Thank you", "中文"): "谢谢",
        ("Good morning", "中文"): "早上好",
        ("AI Agent", "中文"): "AI 智能体",
    }

    key = (text, target_lang)
    if key in mock_translations:
        return f"🌐 翻译结果 ({text} → {target_lang}): {mock_translations[key]}"

    # 通用模拟返回
    return (
        f"🌐 翻译结果 ({text} → {target_lang}):\n"
        f"原文: {text}\n"
        f"译文: [模拟] 这是将'{text}'翻译为{target_lang}的结果。\n"
        f"💡 提示：接入翻译 API 可获得真实翻译结果。"
    )
