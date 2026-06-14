"""
操作日志服务模块
记录用户的关键操作
"""

from ..database import db


def log_action(user_id: int, action: str, target: str = "", detail: str = ""):
    """记录操作日志"""
    try:
        db.create_log(user_id, action, target, detail)
    except Exception:
        pass  # 日志记录失败不应影响主流程
