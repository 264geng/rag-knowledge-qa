"""
知识库与文档管理路由模块
处理知识库的增删改查、文档上传（批量）、预览、重新处理、搜索
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import settings
from ..database import db
from ..models.schemas import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    DocumentResponse, DocumentPreviewResponse, DocumentChunkResponse,
)
from ..services.auth_service import get_current_user
from ..services.document_parser import process_document, get_content_preview
from ..services.vector_store import (
    add_documents, delete_document_vectors,
    delete_knowledge_base_vectors, get_document_chunks,
)
from ..services.logger_service import log_action

router = APIRouter(prefix="/api", tags=["知识库"])
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    return user


def ensure_kb_ownership(kb_id: int, user_id: int) -> dict:
    """验证知识库归属权（仅创建者和管理员可写）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 管理员可以操作所有
    user = db.get_user_by_id(user_id)
    if user and user.get("is_admin"):
        return kb
    if kb["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权操作该知识库")
    return kb


def ensure_kb_readable(kb_id: int, user_id: int) -> dict:
    """验证知识库可读权限（创建者/管理员/公开/分享均可读）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 创建者可读
    if kb["user_id"] == user_id:
        return kb
    # 管理员可读
    user = db.get_user_by_id(user_id)
    if user and user.get("is_admin"):
        return kb
    # 公开可读
    if kb.get("visibility") == "public":
        return kb
    # 分享可读
    shared = db.get_shared_users(kb_id)
    if any(s["shared_with_user_id"] == user_id for s in shared):
        return kb
    raise HTTPException(status_code=403, detail="无权访问该知识库")


# ==================== 知识库接口 ====================

@router.post("/knowledge-base", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    current_user: dict = Depends(get_current_user_from_token),
):
    """创建新知识库"""
    kb_id = db.create_knowledge_base(
        name=request.name,
        description=request.description or "",
        user_id=current_user["id"],
    )
    kb = db.get_knowledge_base_by_id(kb_id)
    log_action(current_user["id"], "create_knowledge_base", f"kb_{kb_id}", request.name)
    return KnowledgeBaseResponse(
        id=kb["id"],
        name=kb["name"],
        description=kb["description"],
        document_count=0,
        chunk_count=0,
        created_at=kb["created_at"],
    )


@router.get("/knowledge-base")
def list_knowledge_bases(
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取知识库列表：自己的 + 分享给我的 + 公开的"""
    # 1. 自己创建的
    my_kbs = db.get_knowledge_bases_by_user(current_user["id"])
    for kb in my_kbs:
        kb["ownership"] = "owner"
        kb["visibility"] = kb.get("visibility", "private")

    # 2. 分享给我的
    shared_kbs = db.get_shared_kbs_for_user(current_user["id"])
    for kb in shared_kbs:
        kb["ownership"] = "shared"
        kb["document_count"] = kb.get("document_count", 0)
        kb["chunk_count"] = kb.get("chunk_count", 0)

    # 3. 公开的（排除自己的）
    public_kbs = db.get_public_kbs()
    for kb in public_kbs:
        if kb["user_id"] != current_user["id"]:
            kb["ownership"] = "public"
            kb["document_count"] = kb.get("document_count", 0)
            kb["chunk_count"] = kb.get("chunk_count", 0)

    # 合并去重
    all_kb_ids = set()
    result = []
    for kb in my_kbs + shared_kbs + public_kbs:
        if kb["id"] not in all_kb_ids:
            all_kb_ids.add(kb["id"])
            result.append(kb)

    return [
        {
            "id": kb["id"],
            "name": kb["name"],
            "description": kb.get("description", ""),
            "document_count": kb.get("document_count", 0),
            "chunk_count": kb.get("chunk_count", 0),
            "created_at": kb["created_at"],
            "visibility": kb.get("visibility", "private"),
            "ownership": kb.get("ownership", "owner"),
            "owner_name": kb.get("owner_name", ""),
            "shared_by_username": kb.get("shared_by_username", ""),
        }
        for kb in result
    ]


@router.get("/knowledge-base/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取知识库详情（支持公共/分享访问）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 判断权限和归属
    if kb["user_id"] == current_user["id"]:
        ownership = "owner"
    elif current_user.get("is_admin"):
        ownership = "owner"
    elif kb.get("visibility") == "public":
        ownership = "public"
    else:
        shared = db.get_shared_users(kb_id)
        if any(s["shared_with_user_id"] == current_user["id"] for s in shared):
            ownership = "shared"
        else:
            raise HTTPException(status_code=403, detail="无权访问该知识库")

    # 获取文档统计
    doc_stats = db.get_documents_by_kb(kb_id)
    doc_count = len(doc_stats)
    chunk_count = sum(d.get("chunk_count", 0) for d in doc_stats)

    return KnowledgeBaseResponse(
        id=kb["id"],
        name=kb["name"],
        description=kb["description"],
        document_count=doc_count,
        chunk_count=chunk_count,
        created_at=kb["created_at"],
        visibility=kb.get("visibility", "private"),
        ownership=ownership,
        owner_name="",
    )


@router.put("/knowledge-base/{kb_id}")
def update_knowledge_base(
    kb_id: int,
    request: KnowledgeBaseUpdate,
    current_user: dict = Depends(get_current_user_from_token),
):
    """更新知识库信息"""
    ensure_kb_ownership(kb_id, current_user["id"])
    db.update_knowledge_base(kb_id, name=request.name, description=request.description)
    return {"message": "更新成功"}


@router.delete("/knowledge-base/{kb_id}")
def delete_knowledge_base(
    kb_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """删除知识库及其所有文档和向量数据"""
    ensure_kb_ownership(kb_id, current_user["id"])

    documents = db.get_documents_by_kb(kb_id)
    for doc in documents:
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])

    delete_knowledge_base_vectors(kb_id)
    db.delete_knowledge_base(kb_id)

    log_action(current_user["id"], "delete_knowledge_base", f"kb_{kb_id}")
    return {"message": "知识库已删除"}


# ==================== 文档接口 ====================

@router.post("/knowledge-base/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_from_token),
):
    """上传文档到指定知识库，自动解析、分块并向量化"""
    ensure_kb_ownership(kb_id, current_user["id"])

    # 验证文件格式
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}（支持: {', '.join(settings.ALLOWED_EXTENSIONS)}）"
        )

    # 保存上传文件
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    content = await file.read()

    # 验证文件大小
    file_size = len(content)
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {settings.MAX_FILE_SIZE_MB}MB）")

    with open(file_path, "wb") as f:
        f.write(content)

    # 创建文档记录
    doc_id = db.create_document(
        filename=file.filename,
        knowledge_base_id=kb_id,
        file_path=file_path,
        file_size=file_size,
        file_type=ext,
    )

    try:
        chunks = process_document(file_path)
        add_documents(kb_id, chunks, file.filename, doc_id)
        db.update_document_status(doc_id, "completed", len(chunks))
    except Exception as e:
        db.update_document_status(doc_id, "failed", 0)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

    log_action(current_user["id"], "upload_document", f"doc_{doc_id}", file.filename)

    doc = db.get_document_by_id(doc_id)
    return DocumentResponse(
        id=doc["id"],
        filename=doc["filename"],
        chunk_count=doc["chunk_count"],
        status=doc["status"],
        file_size=doc.get("file_size", 0),
        file_type=doc.get("file_type", ""),
        created_at=doc["created_at"],
    )


@router.post("/knowledge-base/{kb_id}/documents/batch")
async def upload_documents_batch(
    kb_id: int,
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user_from_token),
):
    """批量上传文档"""
    ensure_kb_ownership(kb_id, current_user["id"])

    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            results.append({"filename": file.filename, "status": "failed", "error": f"不支持的格式: {ext}"})
            continue

        try:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

            content = await file.read()
            file_size = len(content)

            if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                results.append({"filename": file.filename, "status": "failed", "error": "文件过大"})
                continue

            with open(file_path, "wb") as f:
                f.write(content)

            doc_id = db.create_document(
                filename=file.filename,
                knowledge_base_id=kb_id,
                file_path=file_path,
                file_size=file_size,
                file_type=ext,
            )

            chunks = process_document(file_path)
            add_documents(kb_id, chunks, file.filename, doc_id)
            db.update_document_status(doc_id, "completed", len(chunks))

            results.append({"filename": file.filename, "status": "success", "doc_id": doc_id, "chunk_count": len(chunks)})
            log_action(current_user["id"], "upload_document", f"doc_{doc_id}", file.filename)
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return results


@router.get("/knowledge-base/{kb_id}/documents")
def list_documents(
    kb_id: int,
    keyword: str = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取知识库中的所有文档列表（支持搜索）"""
    ensure_kb_readable(kb_id, current_user["id"])
    documents = db.get_documents_by_kb(kb_id)

    if keyword:
        documents = [d for d in documents if keyword.lower() in d["filename"].lower()]

    return [
        DocumentResponse(
            id=doc["id"],
            filename=doc["filename"],
            chunk_count=doc["chunk_count"],
            status=doc["status"],
            file_size=doc.get("file_size", 0),
            file_type=doc.get("file_type", ""),
            created_at=doc["created_at"],
        )
        for doc in documents
    ]


@router.get("/documents/{doc_id}/preview")
def preview_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """文档预览：返回文档内容预览和分块详情"""
    doc = db.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    ensure_kb_readable(doc["knowledge_base_id"], current_user["id"])

    # 获取文档内容预览
    content_preview = ""
    if os.path.exists(doc["file_path"]):
        try:
            content_preview = get_content_preview(doc["file_path"])
        except Exception:
            content_preview = "无法预览"

    # 获取分块详情
    chunks = get_document_chunks(doc["knowledge_base_id"], doc_id)
    chunk_responses = [
        DocumentChunkResponse(chunk_index=c["chunk_index"], content=c["content"])
        for c in chunks
    ]

    return DocumentPreviewResponse(
        id=doc["id"],
        filename=doc["filename"],
        file_type=doc.get("file_type", ""),
        content_preview=content_preview,
        chunks=chunk_responses,
        total_chunks=len(chunk_responses),
    )


@router.post("/documents/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """重新处理文档（删除旧向量，重新解析和向量化）"""
    doc = db.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    kb = db.get_knowledge_base_by_id(doc["knowledge_base_id"])
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权操作该文档")

    if not os.path.exists(doc["file_path"]):
        raise HTTPException(status_code=400, detail="原始文件不存在，无法重新处理")

    try:
        # 删除旧向量
        delete_document_vectors(doc["knowledge_base_id"], doc_id)

        # 重新解析
        chunks = process_document(doc["file_path"])
        add_documents(doc["knowledge_base_id"], chunks, doc["filename"], doc_id)
        db.update_document_status(doc_id, "completed", len(chunks))

        log_action(current_user["id"], "reprocess_document", f"doc_{doc_id}")

        return {"message": "重新处理成功", "chunk_count": len(chunks)}
    except Exception as e:
        db.update_document_status(doc_id, "failed", 0)
        raise HTTPException(status_code=500, detail=f"重新处理失败: {str(e)}")


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """删除指定文档"""
    doc = db.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    kb = db.get_knowledge_base_by_id(doc["knowledge_base_id"])
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权删除该文档")

    if os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])

    delete_document_vectors(doc["knowledge_base_id"], doc_id)
    db.delete_document(doc_id)

    log_action(current_user["id"], "delete_document", f"doc_{doc_id}", doc["filename"])
    return {"message": "文档已删除"}


# ==================== Prompt 模板接口 ====================

@router.get("/prompt-templates")
def list_prompt_templates(
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取 Prompt 模板列表"""
    templates = db.get_prompt_templates(user_id=current_user["id"])
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "system_prompt": t["system_prompt"],
            "default_top_k": t.get("default_top_k", 4),
            "default_temperature": t.get("default_temperature", 0.3),
            "is_default": bool(t["is_default"]),
            "created_at": t["created_at"],
        }
        for t in templates
    ]


@router.post("/prompt-templates")
def create_prompt_template(
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """创建 Prompt 模板"""
    name = request.get("name")
    system_prompt = request.get("system_prompt")
    description = request.get("description", "")
    default_top_k = request.get("default_top_k", 4)
    default_temperature = request.get("default_temperature", 0.3)

    if not name or not system_prompt:
        raise HTTPException(status_code=400, detail="名称和提示词不能为空")

    tmpl_id = db.create_prompt_template(
        name=name,
        system_prompt=system_prompt,
        description=description,
        user_id=current_user["id"],
        default_top_k=default_top_k,
        default_temperature=default_temperature,
    )
    return {"id": tmpl_id, "message": "创建成功"}


@router.delete("/prompt-templates/{tmpl_id}")
def delete_prompt_template(
    tmpl_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """删除 Prompt 模板"""
    template = db.get_prompt_template_by_id(tmpl_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    db.delete_prompt_template(tmpl_id)
    return {"message": "已删除"}


@router.put("/prompt-templates/{tmpl_id}")
def update_prompt_template(
    tmpl_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """更新 Prompt 模板"""
    template = db.get_prompt_template_by_id(tmpl_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    name = request.get("name")
    description = request.get("description")
    system_prompt = request.get("system_prompt")
    default_top_k = request.get("default_top_k")
    default_temperature = request.get("default_temperature")

    if not name and not system_prompt:
        raise HTTPException(status_code=400, detail="名称和提示词不能同时为空")

    db.update_prompt_template(
        tmpl_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
        default_top_k=default_top_k,
        default_temperature=default_temperature,
    )
    return {"message": "更新成功"}
