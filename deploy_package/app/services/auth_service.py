"""
认证服务模块
处理用户注册、登录、JWT Token 生成与验证
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from ..config import settings
from ..database import db

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希加密"""
    # bcrypt 限制密码长度为 72 字节，超过部分会被忽略
    # 这里手动截断以避免警告
    password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    # 保持与 hash_password 一致，截断到 72 字节
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """生成 JWT Access Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码并验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def register_user(username: str, password: str) -> dict:
    """
    用户注册
    返回新创建的用户信息，如果用户名已存在则抛出异常
    """
    existing = db.get_user_by_username(username)
    if existing:
        raise ValueError("用户名已存在")

    hashed = hash_password(password)
    user_id = db.create_user(username, hashed)
    user = db.get_user_by_id(user_id)
    return user


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    用户登录认证
    验证用户名密码，成功返回用户信息，失败返回 None
    """
    user = db.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_current_user(token: str) -> Optional[dict]:
    """
    根据 JWT Token 获取当前用户
    """
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.get_user_by_id(int(user_id))
    return user
