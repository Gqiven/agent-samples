"""
Chain 2: Prompt → LLM → PydanticOutputParser（结构化输出）

核心：让 LLM 输出符合 Pydantic 模型的 JSON，而非自由文本
前端类比：TypeScript interface + Zod schema validation

关键步骤：
1. 用 Pydantic BaseModel 定义输出结构（类似 TS interface）
2. PydanticOutputParser 自动生成格式说明注入 Prompt
3. LLM 按 JSON Schema 输出
4. Parser 解析 + 校验，失败自动重试
"""

import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek

from app.models.schemas import MovieReview

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

def create_structured_chain(provider: str | None = None, model: str | None = None):
    """
    创建结构化输出链: Prompt → LLM → PydanticOutputParser

    前端类比：
        // TypeScript
        interface MovieReview {
            movie_name: string;
            rating: number;  // 1-10
            genre: string[];
            summary: string;
            recommend: boolean;
        }
        const result: MovieReview = await chain(input);
    """
    # 1. 创建 PydanticOutputParser
    # 它会自动做两件事：
    #   a. 生成 JSON Schema 格式说明（注入到 Prompt）
    #   b. 解析 LLM 输出并校验（类似 Zod.parse）
    parser = PydanticOutputParser(pydantic_object=MovieReview)

    # 2. 定义 Prompt（包含格式说明）
    # {format_instructions} 是 parser 自动生成的 JSON Schema 描述
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的电影评论家。请严格按照指定格式输出。\n{format_instructions}"),
        ("human", "请评价电影: {movie_name}"),
    ])

    # 3. 获取 LLM
    llm = _get_llm(provider, model)

    # 4. 组合链
    # 注意：partial_variables 把 format_instructions 预填到 prompt 中
    # 类似 React 的 props 预填充
    chain = prompt.partial(format_instructions=parser.get_format_instructions()) | llm | parser

    return chain, parser


async def run_structured_chain(
    movie_name: str,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[MovieReview, str]:
    """
    执行结构化输出链

    返回: (解析后的 Pydantic 对象, LLM 原始输出)

    前端类比：
        const [data, raw] = await chain({ movie_name: "星际穿越" });
        // data = { movie_name: "星际穿越", rating: 9, ... }
        // raw = '{"movie_name":"星际穿越","rating":9,...}'
    """
    chain, parser = create_structured_chain(provider, model)

    try:
        # ainvoke：解析成功，直接返回 Pydantic 对象
        result = await chain.ainvoke({"movie_name": movie_name})
        return result, result.model_dump_json()
    except Exception as e:
        # 解析失败（LLM 输出不符合格式），尝试手动修复
        # 这种情况在实际开发中很常见
        llm = _get_llm(provider, model)
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "你是电影评论家。请用JSON格式输出，字段：movie_name, rating(1-10), genre(数组), summary, recommend(布尔值)"),
            ("human", "评价电影: {movie_name}"),
        ])
        # 降级方案：用 with_structured_output 让 LLM 强制输出结构
        llm_structured = llm.with_structured_output(MovieReview)
        simple_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是电影评论家。"),
            ("human", "评价电影: {movie_name}，输出JSON格式"),
        ])
        chain_fallback = simple_prompt | llm_structured
        result = await chain_fallback.ainvoke({"movie_name": movie_name})
        return result, result.model_dump_json()

async def main():
    result = await run_structured_chain('海街日记')
    print(result)

if __name__ == "__main__":
    asyncio.run(main())