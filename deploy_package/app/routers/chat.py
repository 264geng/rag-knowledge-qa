"""
对话路由模块
处理聊天问答（SSE 流式 + 同步）、重新生成、对话历史管理、消息反馈、对话标题
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sse_starlette.sse import EventSourceResponse

from ..database import db
from ..models.schemas import (
    ChatRequest, ChatResponse, SourceChunk,
    ConversationResponse, ConversationUpdateRequest,
    MessageResponse, MessageFeedbackRequest,
    ChatRegenerateRequest,
)
from ..services.auth_service import get_current_user
from ..services.rag_engine import answer_question, answer_question_stream
from ..services.logger_service import log_action


def resolve_knowledge_base_ids(request: ChatRequest) -> list:
    """从请求中解析知识库 ID 列表，支持单个和多个"""
    if request.knowledge_base_ids and len(request.knowledge_base_ids) > 0:
        return request.knowledge_base_ids
    elif request.knowledge_base_id:
        return [request.knowledge_base_id]
    else:
        raise HTTPException(status_code=400, detail="请指定知识库")


def validate_kb_access(kb_ids: list, user: dict):
    """验证用户对所有知识库的访问权限"""
    user_id = user["id"]
    is_admin = user.get("is_admin", False)
    print(f"[权限验证] user_id={user_id}, is_admin={is_admin}, kb_ids={kb_ids}")

    for kb_id in kb_ids:
        kb = db.get_knowledge_base_by_id(kb_id)
        if not kb:
            print(f"[权限验证] 知识库 {kb_id} 不存在")
            raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")

        # 管理员可以访问所有知识库
        if is_admin:
            print(f"[权限验证] 知识库 {kb_id}: 管理员权限通过")
            continue

        # 所有者可以访问自己的知识库
        if kb["user_id"] == user_id:
            print(f"[权限验证] 知识库 {kb_id}: 所有者权限通过 (owner={kb['user_id']})")
            continue

        # 公开知识库所有人可访问
        if kb.get("visibility") == "public":
            print(f"[权限验证] 知识库 {kb_id}: 公开知识库权限通过")
            continue

        # 分享的知识库被分享者可访问
        shared = db.get_shared_users(kb_id)
        if any(s["shared_with_user_id"] == user_id for s in shared):
            print(f"[权限验证] 知识库 {kb_id}: 分享权限通过")
            continue

        print(f"[权限验证] 知识库 {kb_id}: 无权访问 (visibility={kb.get('visibility')}, owner={kb['user_id']})")
        raise HTTPException(status_code=403, detail=f"无权访问知识库 {kb_id}")

router = APIRouter(prefix="/api/chat", tags=["对话"])
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    return user


def auto_generate_title(message: str) -> str:
    """根据首条消息自动生成对话标题（截取前 30 字符）"""
    title = message.strip()[:30]
    if len(message.strip()) > 30:
        title += "..."
    return title


@router.post("", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """同步发送消息并获取 RAG 回答"""
    import traceback
    try:
        # 解析并验证知识库
        kb_ids = resolve_knowledge_base_ids(request)
        validate_kb_access(kb_ids, current_user)

        # 获取或创建对话（使用第一个知识库 ID）
        conversation_id = request.conversation_id
        primary_kb_id = kb_ids[0]
        if conversation_id:
            conversation = db.get_conversation_by_id(conversation_id)
            if not conversation or conversation["user_id"] != current_user["id"]:
                raise HTTPException(status_code=404, detail="对话不存在")
            primary_kb_id = conversation["knowledge_base_id"]
        else:
            title = auto_generate_title(request.message)
            conversation_id = db.create_conversation(
                user_id=current_user["id"],
                knowledge_base_id=primary_kb_id,
                title=title,
            )

        # 获取历史消息
        history_messages = db.get_messages_by_conversation(conversation_id)

        # 保存用户消息
        db.create_message(conversation_id, "user", request.message)

        # 调用 RAG 引擎
        result = answer_question(
            question=request.message,
            knowledge_base_id=primary_kb_id,
            knowledge_base_ids=kb_ids if len(kb_ids) > 1 else None,
            chat_history=history_messages,
            top_k=request.top_k,
            temperature=request.temperature,
            system_prompt_id=request.system_prompt_id,
        )

        # 保存助手回答
        sources_json = json.dumps(result["sources"], ensure_ascii=False)
        db.create_message(conversation_id, "assistant", result["answer"], sources=sources_json)

        # 记录日志
        log_action(current_user["id"], "chat", f"conversation_{conversation_id}", request.message[:100])

        sources = [
            SourceChunk(
                content=s["content"],
                document_name=s["document_name"],
                chunk_index=s["chunk_index"],
                distance=s.get("distance"),
            )
            for s in result["sources"]
        ]

        return ChatResponse(
            conversation_id=conversation_id,
            answer=result["answer"],
            sources=sources,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] send_message: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """SSE 流式发送消息并获取 RAG 回答"""
    import traceback
    try:
        print(f"[Chat Stream] user={current_user.get('username')}, user_id={current_user['id']}, "
              f"kb_ids={request.knowledge_base_ids}, kb_id={request.knowledge_base_id}, "
              f"conv_id={request.conversation_id}")
        # 解析并验证知识库
        kb_ids = resolve_knowledge_base_ids(request)
        validate_kb_access(kb_ids, current_user)

        # 获取或创建对话
        conversation_id = request.conversation_id
        primary_kb_id = kb_ids[0]
        if conversation_id:
            conversation = db.get_conversation_by_id(conversation_id)
            if not conversation or conversation["user_id"] != current_user["id"]:
                raise HTTPException(status_code=404, detail="对话不存在")
            primary_kb_id = conversation["knowledge_base_id"]
        else:
            title = auto_generate_title(request.message)
            conversation_id = db.create_conversation(
                user_id=current_user["id"],
                knowledge_base_id=primary_kb_id,
                title=title,
            )

        # 获取历史消息
        history_messages = db.get_messages_by_conversation(conversation_id)

        # 保存用户消息
        user_msg_id = db.create_message(conversation_id, "user", request.message)

        async def event_generator():
            full_answer = ""
            sources_data = []

            async for chunk in answer_question_stream(
                question=request.message,
                knowledge_base_id=primary_kb_id,
                knowledge_base_ids=kb_ids if len(kb_ids) > 1 else None,
                chat_history=history_messages,
                top_k=request.top_k,
                temperature=request.temperature,
                system_prompt_id=request.system_prompt_id,
            ):
                if chunk["type"] == "sources":
                    sources_data = chunk["data"]
                    yield {
                        "event": "sources",
                        "data": json.dumps(chunk["data"], ensure_ascii=False),
                    }
                elif chunk["type"] == "token":
                    full_answer += chunk["data"]
                    yield {
                        "event": "token",
                        "data": chunk["data"],
                    }
                elif chunk["type"] == "done":
                    full_answer = chunk["data"]

            # 保存助手回答
            sources_json = json.dumps(sources_data, ensure_ascii=False)
            msg_id = db.create_message(conversation_id, "assistant", full_answer, sources=sources_json)

            # 发送完成事件（包含 conversation_id、assistant message_id 和 user message_id）
            yield {
                "event": "done",
                "data": json.dumps({
                    "conversation_id": conversation_id,
                    "message_id": msg_id,
                    "user_message_id": user_msg_id,
                }, ensure_ascii=False),
            }

            log_action(current_user["id"], "chat", f"conversation_{conversation_id}", request.message[:100])

        return EventSourceResponse(event_generator())
    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] send_message_stream: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate")
async def regenerate_answer(
    request: ChatRegenerateRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """重新生成回答（SSE 流式）"""
    import traceback
    try:
        # 验证对话归属权
        conversation = db.get_conversation_by_id(request.conversation_id)
        if not conversation or conversation["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 获取原消息
        message = db.get_message_by_id(request.message_id)
        if not message or message["role"] != "user":
            raise HTTPException(status_code=400, detail="只能重新生成对用户消息的回答")

        # 获取历史消息（排除旧的助手回答）
        all_messages = db.get_messages_by_conversation(request.conversation_id)
        # 找到用户消息的位置，捕获旧的助手回答用于更新
        user_msg_idx = None
        old_assistant_msg = None
        for i, msg in enumerate(all_messages):
            if msg["id"] == request.message_id:
                user_msg_idx = i
                if i + 1 < len(all_messages) and all_messages[i + 1]["role"] == "assistant":
                    old_assistant_msg = all_messages[i + 1]
                break
        # 排除用户消息及之后的所有消息（只保留之前的对话历史）
        history_messages = all_messages[:user_msg_idx] if user_msg_idx is not None else all_messages

        async def event_generator():
            full_answer = ""
            sources_data = []

            async for chunk in answer_question_stream(
                question=message["content"],
                knowledge_base_id=conversation["knowledge_base_id"],
                chat_history=history_messages,
                top_k=request.top_k,
                temperature=request.temperature,
                system_prompt_id=request.system_prompt_id,
            ):
                if chunk["type"] == "sources":
                    sources_data = chunk["data"]
                    yield {
                        "event": "sources",
                        "data": json.dumps(chunk["data"], ensure_ascii=False),
                    }
                elif chunk["type"] == "token":
                    full_answer += chunk["data"]
                    yield {
                        "event": "token",
                        "data": chunk["data"],
                    }
                elif chunk["type"] == "done":
                    full_answer = chunk["data"]

            # 更新旧的助手消息
            msg_id = None
            if old_assistant_msg:
                sources_json = json.dumps(sources_data, ensure_ascii=False)
                db.update_message(old_assistant_msg["id"], full_answer, sources=sources_json)
                msg_id = old_assistant_msg["id"]

            yield {
                "event": "done",
                "data": json.dumps({
                    "conversation_id": request.conversation_id,
                    "message_id": msg_id,
                    "user_message_id": request.message_id,
                }, ensure_ascii=False),
            }

        return EventSourceResponse(event_generator())
    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] regenerate_answer: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
def list_conversations(
    keyword: str = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取当前用户的所有对话列表（支持搜索）"""
    conversations = db.get_conversations_by_user(current_user["id"], keyword=keyword)
    return [
        ConversationResponse(
            id=conv["id"],
            knowledge_base_id=conv["knowledge_base_id"],
            knowledge_base_name=conv["knowledge_base_name"],
            title=conv.get("title", "新对话"),
            message_count=conv["message_count"],
            created_at=conv["created_at"],
        )
        for conv in conversations
    ]


@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取对话详情（包括所有消息）"""
    conversation = db.get_conversation_by_id(conv_id)
    if not conversation or conversation["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = db.get_messages_by_conversation(conv_id)

    return {
        "id": conversation["id"],
        "knowledge_base_id": conversation["knowledge_base_id"],
        "knowledge_base_name": conversation["knowledge_base_name"],
        "title": conversation.get("title", "新对话"),
        "created_at": conversation["created_at"],
        "messages": [
            MessageResponse(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                sources=msg["sources"],
                feedback=msg.get("feedback"),
                created_at=msg["created_at"],
            )
            for msg in messages
        ],
    }


@router.put("/conversations/{conv_id}")
def update_conversation(
    conv_id: int,
    request: ConversationUpdateRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """更新对话标题"""
    conversation = db.get_conversation_by_id(conv_id)
    if not conversation or conversation["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.update_conversation_title(conv_id, request.title)
    return {"message": "更新成功"}


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """删除对话及所有消息"""
    conversation = db.get_conversation_by_id(conv_id)
    if not conversation or conversation["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.delete_conversation(conv_id)
    log_action(current_user["id"], "delete_conversation", f"conversation_{conv_id}")
    return {"message": "对话已删除"}


@router.put("/messages/{msg_id}/feedback")
def update_message_feedback(
    msg_id: int,
    request: MessageFeedbackRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """更新消息反馈（点赞/踩）"""
    message = db.get_message_by_id(msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    if request.feedback not in ("like", "dislike", ""):
        raise HTTPException(status_code=400, detail="反馈值无效")

    db.update_message_feedback(msg_id, request.feedback)
    return {"message": "反馈已更新"}
