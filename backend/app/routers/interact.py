"""
互动路由模块
知识库分享、点赞/踩、文档举报、收藏、用户搜索
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..database import db
from ..services.auth_service import get_current_user
from ..services.logger_service import log_action

router = APIRouter(prefix="/api/interact", tags=["互动"])
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    return user


def ensure_kb_access(kb_id: int, user: dict):
    """验证用户对知识库的访问权限"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 管理员可以访问所有
    if user.get("is_admin"):
        return kb

    # 创建者可以访问自己的
    if kb["user_id"] == user["id"]:
        return kb

    # 公开知识库所有人可访问
    if kb.get("visibility") == "public":
        return kb

    # 分享的知识库被分享者可访问
    shared = db.get_shared_users(kb_id)
    if any(s["shared_with_user_id"] == user["id"] for s in shared):
        return kb

    raise HTTPException(status_code=403, detail="无权访问该知识库")


# ==================== 分享接口 ====================

@router.get("/users/search")
def search_users(
    keyword: str = "",
    current_user: dict = Depends(get_current_user_from_token),
):
    """搜索用户（用于分享）"""
    if len(keyword) < 1:
        return []
    users = db.search_users(keyword)
    # 排除自己
    return [{"id": u["id"], "username": u["username"]} for u in users if u["id"] != current_user["id"]]


@router.post("/knowledge-base/{kb_id}/share")
def share_knowledge_base(
    kb_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """分享知识库给指定用户"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有创建者可以分享")

    target_user_id = request.get("user_id")
    if not target_user_id:
        raise HTTPException(status_code=400, detail="请指定分享用户")

    target_user = db.get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 传递分享者 ID
    db.share_knowledge_base(kb_id, target_user_id, current_user["id"])

    # 如果是第一次分享，更新状态为 shared
    if kb.get("visibility") == "private" or not kb.get("visibility"):
        db.update_kb_visibility(kb_id, "shared")

    log_action(current_user["id"], "share_kb", f"kb_{kb_id}", f"分享给 {target_user['username']}")
    return {"message": f"已分享给 {target_user['username']}"}


@router.delete("/knowledge-base/{kb_id}/share/{user_id}")
def unshare_knowledge_base(
    kb_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """取消分享"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有创建者可以取消分享")

    db.unshare_knowledge_base(kb_id, user_id)
    return {"message": "已取消分享"}


@router.get("/knowledge-base/{kb_id}/shares")
def get_shares(
    kb_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取知识库的分享列表"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有创建者可以查看分享列表")

    return db.get_shared_users(kb_id)


@router.put("/knowledge-base/{kb_id}/visibility")
def set_visibility(
    kb_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """设置知识库可见性（private/public）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb or kb["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有创建者可以设置可见性")

    visibility = request.get("visibility", "private")
    if visibility not in ("private", "public", "shared"):
        raise HTTPException(status_code=400, detail="无效的可见性值")

    # 用户设为公开时，改为 pending 等待管理员审核
    if visibility == "public":
        visibility = "pending"

    db.update_kb_visibility(kb_id, visibility)
    return {"message": "可见性已更新" + ("，等待管理员审核" if visibility == "pending" else "")}


# ==================== 点赞/踩接口 ====================

@router.post("/knowledge-base/{kb_id}/vote")
def vote_kb(
    kb_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """点赞或踩知识库"""
    vote_type = request.get("vote_type")
    if vote_type not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="无效的投票类型")

    # 检查是否已投票，如果已投同类型则取消
    current_vote = db.get_user_vote(kb_id, current_user["id"])
    if current_vote == vote_type:
        db.remove_vote(kb_id, current_user["id"])
        return {"message": "已取消", "vote": None}
    else:
        db.vote_knowledge_base(kb_id, current_user["id"], vote_type)
        return {"message": "投票成功", "vote": vote_type}


@router.get("/knowledge-base/{kb_id}/votes")
def get_votes(
    kb_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取知识库的投票统计"""
    votes = db.get_kb_votes(kb_id)
    user_vote = db.get_user_vote(kb_id, current_user["id"])
    return {**votes, "user_vote": user_vote}


# ==================== 文档举报接口 ====================

@router.post("/document/{doc_id}/report")
def report_document(
    doc_id: int,
    request: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """举报文档"""
    doc = db.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    reason = request.get("reason", "")
    db.report_document(doc_id, current_user["id"], reason)
    log_action(current_user["id"], "report_document", f"doc_{doc_id}", reason[:100])
    return {"message": "举报已提交，管理员将尽快审核"}


# ==================== 文档收藏接口 ====================

@router.post("/document/{doc_id}/favorite")
def toggle_favorite(
    doc_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """收藏/取消收藏文档"""
    doc = db.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if db.is_favorited(doc_id, current_user["id"]):
        db.unfavorite_document(doc_id, current_user["id"])
        return {"message": "已取消收藏", "favorited": False}
    else:
        db.favorite_document(doc_id, current_user["id"])
        return {"message": "已收藏", "favorited": True}


# ==================== 知识库收藏 ====================

@router.post("/knowledge-base/{kb_id}/favorite")
def toggle_kb_favorite(
    kb_id: int,
    current_user: dict = Depends(get_current_user_from_token),
):
    """收藏/取消收藏知识库"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    if db.is_kb_favorited(kb_id, current_user["id"]):
        db.unfavorite_knowledge_base(kb_id, current_user["id"])
        return {"message": "已取消收藏", "favorited": False}
    else:
        db.favorite_knowledge_base(kb_id, current_user["id"])
        return {"message": "已收藏", "favorited": True}


@router.get("/favorites")
def get_favorites(
    current_user: dict = Depends(get_current_user_from_token),
):
    """获取我的收藏列表（知识库 + 文档）"""
    kb_favs = db.get_user_kb_favorites(current_user["id"])
    doc_favs = db.get_user_favorites(current_user["id"])

    result = []
    for kb in kb_favs:
        result.append({
            "type": "knowledge_base",
            "id": kb["id"],
            "name": kb["name"],
            "description": kb.get("description", ""),
            "owner_name": kb.get("owner_name", ""),
            "created_at": kb["created_at"],
        })
    for doc in doc_favs:
        result.append({
            "type": "document",
            "id": doc["id"],
            "name": doc["filename"],
            "kb_id": doc["knowledge_base_id"],
            "kb_name": doc.get("kb_name", ""),
            "created_at": doc["created_at"],
        })
    return result
