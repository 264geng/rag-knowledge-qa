"""
用户认证路由模块
处理注册、登录、修改密码、用户统计、获取当前用户信息
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    ChangePasswordRequest, UserStatsResponse,
)
from ..services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..database import db
from ..services.logger_service import log_action

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """从请求头的 Bearer Token 中解析当前用户"""
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )
    return user


@router.post("/register", response_model=UserResponse)
def api_register(request: UserRegister):
    """用户注册"""
    if len(request.username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6个字符")

    try:
        user = register_user(request.username, request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return UserResponse(
        id=user["id"],
        username=user["username"],
        is_admin=bool(user.get("is_admin")),
        created_at=user["created_at"],
    )


@router.post("/login", response_model=TokenResponse)
def api_login(request: UserLogin):
    """用户登录"""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token = create_access_token(data={"sub": str(user["id"])})

    log_action(user["id"], "login", "user", f"{user['username']} 登录")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            is_admin=bool(user.get("is_admin")),
            created_at=user["created_at"],
        ),
    )


@router.get("/me", response_model=UserResponse)
def api_me(current_user: dict = Depends(get_current_user_from_token)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        is_admin=bool(current_user.get("is_admin")),
        created_at=current_user["created_at"],
    )


@router.put("/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_from_token),
):
    """修改密码"""
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6个字符")

    if not verify_password(request.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="原密码错误")

    new_hashed = hash_password(request.new_password)
    db.update_user_password(current_user["id"], new_hashed)

    log_action(current_user["id"], "change_password", "user")
    return {"message": "密码修改成功"}


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(current_user: dict = Depends(get_current_user_from_token)):
    """获取当前用户统计信息"""
    stats = db.get_user_stats(current_user["id"])
    return UserStatsResponse(**stats)
