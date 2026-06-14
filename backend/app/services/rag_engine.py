"""
RAG 问答引擎模块
实现检索增强生成的完整流程：Query 改写 → 检索 → Rerank → 构建 Prompt → 流式/同步生成回答
"""

import json
from typing import List, Dict, Optional, AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from ..config import settings
from ..database import db
from .vector_store import search_similar, rerank_results, search_multiple_knowledge_bases


# 默认 RAG 系统提示词模板
DEFAULT_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据以下参考资料来回答用户的问题。

要求：
1. 仅基于提供的参考资料回答问题，不要编造信息
2. 如果参考资料中没有相关信息，请明确告知用户
3. 回答要准确、简洁、有条理
4. 在回答末尾注明信息来源

参考资料：
{context}
"""

# Query 改写提示词
QUERY_REWRITE_PROMPT = """你是一个搜索查询优化助手。请将以下用户问题改写为更适合检索的形式。
要求：
1. 保留原始问题的核心意图
2. 扩展相关关键词，增加召回率
3. 只输出改写后的查询，不要添加任何解释

用户问题：{question}
改写后的查询："""


def build_context(search_results: List[Dict]) -> str:
    """将检索到的文档块构建为上下文字符串"""
    if not search_results:
        return "（未找到相关参考资料）"

    context_parts = []
    for i, result in enumerate(search_results, 1):
        source = f"来源: {result['document_name']} (段落 {result['chunk_index'] + 1})"
        # 转义花括号，防止被 LangChain 解析为变量
        content = result['content'].replace('{', '{{').replace('}', '}}')
        context_parts.append(f"[参考{i}] {source}\n{content}")

    return "\n\n".join(context_parts)


def build_history_context(messages: List[Dict], max_turns: int = 5) -> str:
    """构建对话历史上下文（最近 max_turns 轮对话）"""
    if not messages:
        return ""

    recent = messages[-(max_turns * 2):]
    history_parts = []
    for msg in recent:
        role = "用户" if msg["role"] == "user" else "助手"
        history_parts.append(f"{role}: {msg['content']}")

    return "\n".join(history_parts)


def get_llm(temperature: float = 0.3, max_tokens: int = 1024) -> ChatOpenAI:
    """获取 LangChain ChatOpenAI 实例"""
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def rewrite_query(question: str) -> str:
    """使用 LLM 对用户问题进行 Query 改写，提升检索召回率"""
    try:
        llm = get_llm(temperature=0.3, max_tokens=200)
        prompt = ChatPromptTemplate.from_messages([
            ("human", QUERY_REWRITE_PROMPT.format(question=question))
        ])
        chain = prompt | llm
        response = chain.invoke({})
        rewritten = response.content.strip()
        return rewritten if rewritten else question
    except Exception:
        return question


def retrieve_and_rerank(
    question: str,
    knowledge_base_id: int = None,
    kb_ids: List[int] = None,
    top_k: int = None,
) -> List[Dict]:
    """
    检索流程：检索 → Rerank
    支持单知识库或多知识库检索
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    # 检索（多取一些给 Rerank 用）
    retrieve_count = top_k * 3 if settings.RERANK_ENABLED else top_k

    if kb_ids and len(kb_ids) > 1:
        results = search_multiple_knowledge_bases(kb_ids, question, top_k=retrieve_count)
    elif knowledge_base_id:
        results = search_similar(knowledge_base_id, question, top_k=retrieve_count)
    else:
        return []

    # Rerank
    if settings.RERANK_ENABLED:
        results = rerank_results(question, results, top_k=top_k)
    else:
        results = results[:top_k]

    return results


def get_system_prompt(system_prompt_id: int = None) -> str:
    """获取系统提示词（支持自定义模板）"""
    if system_prompt_id:
        template = db.get_prompt_template_by_id(system_prompt_id)
        if template:
            return template["system_prompt"]
    return DEFAULT_SYSTEM_PROMPT


def answer_question(
    question: str,
    knowledge_base_id: int,
    knowledge_base_ids: Optional[List[int]] = None,
    chat_history: Optional[List[Dict]] = None,
    top_k: int = None,
    temperature: float = None,
    system_prompt_id: int = None,
    rewrite: bool = False,
) -> Dict:
    """
    RAG 问答的完整流程（同步版本）
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    if temperature is None:
        temperature = 0.3

    # Step 1: Query 改写
    search_query = rewrite_query(question) if rewrite else question

    # Step 2: 检索 + Rerank
    search_results = retrieve_and_rerank(
        search_query,
        knowledge_base_id=knowledge_base_id,
        kb_ids=knowledge_base_ids,
        top_k=top_k,
    )

    # Step 3: 构建上下文
    context = build_context(search_results)

    # Step 4: 构建对话历史
    history_text = ""
    if chat_history:
        history_text = build_history_context(chat_history)

    # Step 5: 构建 Prompt 并调用 LLM
    llm = get_llm(temperature=temperature)
    system_template = get_system_prompt(system_prompt_id)
    system_message = system_template.format(context=context)

    messages = [("system", system_message)]
    if history_text:
        messages.append(("system", f"对话历史：\n{history_text}"))
    messages.append(("human", question))

    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm
    response = chain.invoke({})

    # Step 6: 整理来源信息
    sources = []
    for result in search_results:
        sources.append({
            "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
            "document_name": result["document_name"],
            "chunk_index": result["chunk_index"],
            "distance": result.get("distance", 0),
        })

    return {
        "answer": response.content,
        "sources": sources,
    }


async def answer_question_stream(
    question: str,
    knowledge_base_id: int,
    knowledge_base_ids: Optional[List[int]] = None,
    chat_history: Optional[List[Dict]] = None,
    top_k: int = None,
    temperature: float = None,
    system_prompt_id: int = None,
    rewrite: bool = False,
) -> AsyncGenerator[Dict, None]:
    """
    RAG 问答的完整流程（SSE 流式版本）
    先返回 sources，再流式返回 answer token
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    if temperature is None:
        temperature = 0.3

    # Step 1: Query 改写
    search_query = rewrite_query(question) if rewrite else question

    # Step 2: 检索 + Rerank
    search_results = retrieve_and_rerank(
        search_query,
        knowledge_base_id=knowledge_base_id,
        kb_ids=knowledge_base_ids,
        top_k=top_k,
    )

    # Step 3: 构建上下文
    context = build_context(search_results)

    # Step 4: 构建对话历史
    history_text = ""
    if chat_history:
        history_text = build_history_context(chat_history)

    # Step 5: 构建 Prompt
    system_template = get_system_prompt(system_prompt_id)
    system_message = system_template.format(context=context)

    messages = [("system", system_message)]
    if history_text:
        messages.append(("system", f"对话历史：\n{history_text}"))
    messages.append(("human", question))

    # 整理来源信息
    sources = []
    for result in search_results:
        sources.append({
            "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
            "document_name": result["document_name"],
            "chunk_index": result["chunk_index"],
            "distance": result.get("distance", 0),
        })

    # 先 yield sources
    yield {"type": "sources", "data": sources}

    # Step 6: 流式调用 LLM
    llm = get_llm(temperature=temperature)
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm

    full_answer = ""
    async for chunk in chain.astream({}):
        token = chunk.content
        if token:
            full_answer += token
            yield {"type": "token", "data": token}

    # 结束标记
    yield {"type": "done", "data": full_answer}
