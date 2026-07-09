"""
Chain 1: Prompt → LLM → StrOutputParser（基础链）

LCEL (LangChain Expression Language) 核心语法：
    chain = prompt | llm | parser
等价于 JS 的：
    result = await prompt(input).then(llm).then(parser)

这是 LangChain 最基础的链式组合，类似 Promise 链。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek

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


def create_basic_chain(provider: str | None = None, model: str | None = None):
    """
    创建基础链: Prompt → LLM → StrOutputParser

    前端类比：
        const chain = (question) => prompt(question).then(llm).then(toString);

    LCEL 语法：
        chain = prompt | llm | parser
        | 操作符 = 管道，把上一步输出作为下一步输入
    """
    # 1. 定义 Prompt 模板
    # 类似 Vue 的 template，用 {variable} 占位
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个知识渊博的AI助手，回答要简洁准确。"),
        ("human", "{question}"),
    ])

    # 2. 获取 LLM
    llm = _get_llm(provider, model)

    # 3. 输出解析器：将 AIMessage 转为纯字符串
    # 类似 JS 的 .then(msg => msg.content)
    parser = StrOutputParser()

    # 4. 用 | 组合成链（LCEL 核心语法）
    chain = prompt | llm | parser

    return chain


async def run_basic_chain(question: str, provider: str | None = None, model: str | None = None) -> str:
    """
    执行基础链

    前端类比：
        const answer = await chain({ question: "什么是LangChain？" });
    """
    chain = create_basic_chain(provider, model)
    # invoke = 同步执行，ainvoke = 异步执行
    result = await chain.ainvoke({"question": question})
    return result

async def stream_basic_chain(question: str, provider: str | None = None, model: str | None = None):
    """
    流式执行基础链

    前端类比：
        for await (const token of chain.stream({ question })) {
            console.log(token);
        }
    """
    chain = create_basic_chain(provider, model)
    # astream = 异步流式输出，逐 token 返回
    async for token in chain.astream({"question": question}):
        yield token


async def main():
    print(">>> 非流式输出: ", end="", flush=True)
    result = await run_basic_chain('什么是LangChain')
    print(result)
    print(">>> 流式输出: ", end="", flush=True)
    async for token in stream_basic_chain('什么是LangChain'):
        print(token, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(main())
