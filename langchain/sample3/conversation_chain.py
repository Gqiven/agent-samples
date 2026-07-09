"""
Chain 3: 多轮对话链（带历史消息管理）

核心：维护对话上下文，让 LLM 能理解之前的对话内容
前端类比：Pinia/Redux Store 管理对话历史

两种实现方式：
1. RunnableWithMessageHistory — LangChain 内置历史管理（推荐）
2. 手动管理 messages 列表 — 更灵活，适合自定义存储

本 Demo 展示方式 2（手动管理），更直观易懂，便于前端开发者理解。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import uuid
from collections import defaultdict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek

from app.models.schemas import ConversationMessage

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


# 内存存储（生产环境替换为 Redis/DB）
# 类似前端的 Map<conversationId, Message[]>
_conversations: dict[str, list[ConversationMessage]] = defaultdict(list)


def _to_langchain_messages(history: list[ConversationMessage]) -> list:
    """
    将自定义 Message 列表转为 LangChain Message 对象

    前端类比：
        // 前端消息格式 → API 请求格式
        messages.map(m => ({ role: m.role, content: m.content }))
    """
    result = []
    for m in history:
        if m.role == "user":
            result.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            result.append(AIMessage(content=m.content))
    return result


def create_conversation_chain(provider: str | None = None, model: str | None = None):
    """
    创建多轮对话链

    关键：MessagesPlaceholder 占位符
    类似 Vue 的 <slot>，在运行时动态插入历史消息

    Prompt 结构：
        SystemMessage  — 系统提示词
        MessagesPlaceholder("history")  — 历史消息（动态插入）
        HumanMessage   — 当前用户消息
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的AI助手，擅长多轮对话。请记住之前的对话内容，保持上下文连贯。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    llm = _get_llm(provider, model)
    parser = StrOutputParser()

    chain = prompt | llm | parser

    return chain


async def run_conversation_chain(
    message: str,
    conversation_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str, str, list[ConversationMessage]]:
    """
    执行多轮对话链

    前端类比：
        // 类似 React 的状态更新
        const history = conversations[id] || [];
        history.push({ role: 'user', content: message });
        const answer = await chain({ history, input: message });
        history.push({ role: 'assistant', content: answer });
        conversations[id] = history;
    """
    conversation_id = conversation_id or str(uuid.uuid4())
    history = _conversations[conversation_id]

    # 将历史消息转为 LangChain 格式
    lc_history = _to_langchain_messages(history)

    chain = create_conversation_chain(provider, model)

    # 执行链：传入 history + 当前 input
    result = await chain.ainvoke({
        "history": lc_history,
        "input": message,
    })

    # 更新历史
    history.append(ConversationMessage(role="user", content=message))
    history.append(ConversationMessage(role="assistant", content=result))

    return conversation_id, result, list(history)


async def stream_conversation_chain(
    message: str,
    conversation_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
):
    """
    流式执行多轮对话链

    前端类比：
        const stream = chain.stream({ history, input: message });
        for await (const token of stream) {
            updateUI(token);
        }
    """
    conversation_id = conversation_id or str(uuid.uuid4())
    history = _conversations[conversation_id]
    lc_history = _to_langchain_messages(history)

    chain = create_conversation_chain(provider, model)

    full_text = ""
    async for token in chain.astream({
        "history": lc_history,
        "input": message,
    }):
        full_text += token
        yield token, conversation_id

    # 流式结束后更新历史
    history.append(ConversationMessage(role="user", content=message))
    history.append(ConversationMessage(role="assistant", content=full_text))


def get_conversation_history(conversation_id: str) -> list[ConversationMessage]:
    """获取对话历史"""
    return list(_conversations.get(conversation_id, []))


def clear_conversation(conversation_id: str) -> None:
    """清空对话历史"""
    if conversation_id in _conversations:
        del _conversations[conversation_id]


async def main():
    """演示多轮对话链的调用方式"""
    # ===== 非流式：等待完整结果 =====
    print("=" * 50)
    print("非流式调用演示")
    print("=" * 50)
    cid, answer, _ = await run_conversation_chain("你好，我叫小明")
    print(f"[会话: {cid[:8]}...]")
    print(f"用户: 你好，我叫小明")
    print(f"助手: {answer}\n")

    _, answer2, _ = await run_conversation_chain("我叫什么名字？", conversation_id=cid)
    print(f"用户: 我叫什么名字？")
    print(f"助手: {answer2}\n")

    # ===== 流式：逐字输出，适合前端 SSE/WebSocket =====
    print("=" * 50)
    print("流式调用演示")
    print("=" * 50)
    new_cid = None
    user_msg = "给我推荐一部好看的电影"
    print(f"用户: {user_msg}")
    print(f"助手: ", end="", flush=True)
    async for token, new_cid in stream_conversation_chain(user_msg):
        print(token, end="", flush=True)  # 逐字打印，前端这里就是 updateUI(token)
    print(f"\n[会话: {new_cid[:8]}...]\n")

    # 查看完整历史（非流式对话）
    history = get_conversation_history(cid)
    print(f"--- 非流式对话历史（共 {len(history)} 条）---")
    for m in history:
        role = "用户" if m.role == "user" else "助手"
        print(f"[{role}] {m.content}")

    # 查看完整历史（流式对话）
    stream_history = get_conversation_history(new_cid)
    print(f"\n--- 流式对话历史（共 {len(stream_history)} 条）---")
    for m in stream_history:
        role = "用户" if m.role == "user" else "助手"
        print(f"[{role}] {m.content}")

    # 清空对话
    clear_conversation(cid)
    clear_conversation(new_cid)
    print(f"\n对话已清空，剩余历史: {len(get_conversation_history(cid)) + len(get_conversation_history(new_cid))}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

