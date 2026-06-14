"""
Pydantic 数据模型
定义请求/响应的数据结构
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ==================== 用户相关 ====================

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    password: str


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    is_admin: bool = False
    created_at: str


class TokenResponse(BaseModel):
    """登录 Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class UserStatsResponse(BaseModel):
    """用户统计信息"""
    knowledge_base_count: int = 0
    document_count: int = 0
    conversation_count: int = 0
    message_count: int = 0


# ==================== 知识库相关 ====================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    description: Optional[str] = ""


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: str
    document_count: int = 0
    chunk_count: int = 0
    created_at: str
    visibility: str = "private"
    ownership: str = "owner"
    owner_name: str = ""
    shared_by_username: str = ""


# ==================== 文档相关 ====================

class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    filename: str
    chunk_count: int
    status: str
    file_size: int = 0
    file_type: str = ""
    created_at: str


class DocumentChunkResponse(BaseModel):
    """文档分块响应"""
    chunk_index: int
    content: str


class DocumentPreviewResponse(BaseModel):
    """文档预览响应"""
    id: int
    filename: str
    file_type: str
    content_preview: str
    chunks: List[DocumentChunkResponse]
    total_chunks: int


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    knowledge_base_id: Optional[int] = None
    knowledge_base_ids: Optional[List[int]] = None
    conversation_id: Optional[int] = None
    # 可调 RAG 参数
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt_id: Optional[int] = None


class ChatRegenerateRequest(BaseModel):
    """重新生成回答请求"""
    message_id: int
    conversation_id: int
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt_id: Optional[int] = None


class SourceChunk(BaseModel):
    """来源文档块"""
    content: str
    document_name: str
    chunk_index: int
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: int
    answer: str
    sources: List[SourceChunk]


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    sources: Optional[str] = None
    feedback: Optional[str] = None
    created_at: str


class MessageFeedbackRequest(BaseModel):
    """消息反馈请求"""
    feedback: str  # like / dislike


class ConversationResponse(BaseModel):
    """对话响应"""
    id: int
    knowledge_base_id: int
    knowledge_base_name: str
    title: str
    message_count: int
    created_at: str


class ConversationUpdateRequest(BaseModel):
    """更新对话标题"""
    title: str


# ==================== Prompt 模板相关 ====================

class PromptTemplateCreate(BaseModel):
    """创建 Prompt 模板"""
    name: str
    description: Optional[str] = ""
    system_prompt: str
    default_top_k: Optional[int] = 4
    default_temperature: Optional[float] = 0.3


class PromptTemplateResponse(BaseModel):
    """Prompt 模板响应"""
    id: int
    name: str
    description: str
    system_prompt: str
    default_top_k: int = 4
    default_temperature: float = 0.3
    is_default: bool = False
    created_at: str


# ==================== 管理后台相关 ====================

class AdminUserResponse(BaseModel):
    """管理员查看的用户信息"""
    id: int
    username: str
    is_admin: bool
    knowledge_base_count: int = 0
    document_count: int = 0
    conversation_count: int = 0
    created_at: str


class SystemStatsResponse(BaseModel):
    """系统统计信息"""
    total_users: int = 0
    total_knowledge_bases: int = 0
    total_documents: int = 0
    total_conversations: int = 0
    total_messages: int = 0


class LogResponse(BaseModel):
    """操作日志响应"""
    id: int
    user_id: int
    username: str
    action: str
    target: str
    detail: str
    created_at: str
