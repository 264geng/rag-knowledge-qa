"""
管理后台路由模块
用户管理、系统统计、操作日志查看
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..database import db
from ..models.schemas import (
    AdminUserResponse, SystemStatsResponse, LogResponse,
)
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin", tags=["管理后台"])
security = HTTPBearer()


def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """获取当前用户并验证管理员权限"""
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/users")
def list_users(
    current_user: dict = Depends(get_admin_user),
):
    """获取所有用户列表"""
    users = db.get_all_users()
    result = []
    for user in users:
        stats = db.get_user_stats(user["id"])
        result.append(AdminUserResponse(
            id=user["id"],
            username=user["username"],
            is_admin=bool(user.get("is_admin")),
            knowledge_base_count=stats["knowledge_base_count"],
            document_count=stats["document_count"],
            conversation_count=stats["conversation_count"],
            created_at=user["created_at"],
        ))
    return result


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user),
):
    """删除用户"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete_user(user_id)
    return {"message": "用户已删除"}


@router.put("/users/{user_id}/role")
def toggle_user_role(
    user_id: int,
    current_user: dict = Depends(get_admin_user),
):
    """切换用户管理员角色"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_admin_status = not bool(user.get("is_admin"))
    db.update_user_admin(user_id, new_admin_status)
    return {"message": "角色已更新", "is_admin": new_admin_status}


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(
    current_user: dict = Depends(get_admin_user),
):
    """获取系统统计信息"""
    stats = db.get_system_stats()
    return SystemStatsResponse(**stats)


@router.get("/logs")
def get_operation_logs(
    page: int = 1,
    page_size: int = 20,
    user_id: int = None,
    current_user: dict = Depends(get_admin_user),
):
    """获取操作日志"""
    logs = db.get_logs(page=page, page_size=page_size, user_id=user_id)
    # 获取总数
    conn = db._get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT COUNT(*) as cnt FROM operation_logs WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT COUNT(*) as cnt FROM operation_logs")
    total = cursor.fetchone()["cnt"]
    conn.close()
    return {
        "items": [
            LogResponse(
                id=log["id"],
                user_id=log["user_id"],
                username=log["username"],
                action=log["action"],
                target=log.get("target", ""),
                detail=log.get("detail", ""),
                created_at=log["created_at"],
            )
            for log in logs
        ],
        "total": total,
    }


# ==================== 内容审核 ====================

@router.get("/review/knowledge-bases")
def get_review_kbs(
    current_user: dict = Depends(get_admin_user),
):
    """获取需要审核的知识库（pending + public + rejected）"""
    kbs = db.get_pending_review_kbs()
    result = []
    for kb in kbs:
        votes = db.get_kb_votes(kb["id"])
        result.append({
            "id": kb["id"],
            "name": kb["name"],
            "description": kb.get("description", ""),
            "visibility": kb.get("visibility", "private"),
            "owner_name": kb.get("owner_name", ""),
            "reject_reason": kb.get("reject_reason", ""),
            "likes": votes.get("likes", 0),
            "dislikes": votes.get("dislikes", 0),
            "document_count": kb.get("document_count", 0),
            "created_at": kb["created_at"],
        })
    return result


@router.put("/review/knowledge-bases/{kb_id}/approve")
def approve_kb(
    kb_id: int,
    current_user: dict = Depends(get_admin_user),
):
    """审核通过（pending → public）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    db.update_kb_visibility(kb_id, "public")
    return {"message": "已审核通过"}


@router.put("/review/knowledge-bases/{kb_id}/reject")
def reject_kb(
    kb_id: int,
    request: dict = None,
    current_user: dict = Depends(get_admin_user),
):
    """打回公开申请（pending → rejected）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    reason = ""
    if request:
        reason = request.get("reason", "")
    db.update_kb_visibility(kb_id, "rejected", reason)
    return {"message": "已打回"}


@router.put("/review/knowledge-bases/{kb_id}/takedown")
def takedown_kb(
    kb_id: int,
    current_user: dict = Depends(get_admin_user),
):
    """下架知识库（改为私有）"""
    kb = db.get_knowledge_base_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    db.update_kb_visibility(kb_id, "private")
    return {"message": "已下架"}


@router.get("/review/reports")
def get_reports(
    status: str = None,
    current_user: dict = Depends(get_admin_user),
):
    """获取举报列表"""
    return db.get_reports(status=status)


@router.put("/review/reports/{report_id}/resolve")
def resolve_report(
    report_id: int,
    request: dict,
    current_user: dict = Depends(get_admin_user),
):
    """处理举报"""
    action = request.get("action", "resolved")
    reason = request.get("reason", "")
    db.update_report_status(report_id, action, reason)
    return {"message": "已处理"}
