"""
Tool 3: calculate — 数学计算

设计要点：
1. 用 eval 但限制命名空间（安全！不用 __builtins__）
2. 只暴露数学相关函数
3. 错误返回友好提示，不抛异常

前端类比：
    这就像一个沙箱化的 eval()，只允许数学运算
    类似前端用 new Function() 替代 eval()
"""

import math
from langchain_core.tools import tool


# 安全的数学命名空间
_SAFE_MATH_NAMESPACE = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": math.pow,
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
    "gcd": math.gcd,
}


@tool
def calculate(expression: str) -> str:
    """计算数学表达式。支持加减乘除、幂运算、三角函数、对数、常量等。当用户需要进行数学计算时使用此工具。

    支持的运算符: + - * / ** %
    支持的函数: sin cos tan sqrt log log2 log10 abs round ceil floor factorial
    支持的常量: pi, e

    示例:
        "2 + 3 * 4" → 14
        "sqrt(144)" → 12
        "sin(pi/2)" → 1.0
        "2**10 + 100" → 1124
    """
    # 清理输入
    expr = expression.strip()
    # 替换中文符号
    expr = expr.replace("×", "*").replace("÷", "/").replace("（", "(").replace("）", ")")

    try:
        # 安全 eval：限制命名空间，禁用内置函数
        result = eval(expr, {"__builtins__": {}}, _SAFE_MATH_NAMESPACE)

        # 格式化结果
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 10)

        return f"🧮 {expression} = {result}"

    except ZeroDivisionError:
        return f"🧮 计算错误: 除数不能为零 ({expression})"
    except SyntaxError:
        return f"🧮 计算错误: 表达式语法无效 ({expression})，请检查格式"
    except Exception as e:
        return f"🧮 计算错误: {e} ({expression})"
