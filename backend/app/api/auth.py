"""
用户认证API路由模块

本模块提供用户登录、注册和认证相关的API端点：
1. 用户登录：POST /api/auth/login
2. 用户注册：POST /api/auth/register
3. 获取当前用户信息：GET /api/auth/me
4. 退出登录：POST /api/auth/logout

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.app.schemas import UserLogin, UserCreate, User, Token
from backend.app.crud import authenticate_user, create_user, get_user
from backend.app.utils.auth import create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["用户认证"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    从Token中解析用户信息并返回用户对象
    """
    try:
        token = credentials.credentials
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法获取Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # user_id在Token中是字符串，需要转换为int类型
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建Token
    # JWT的sub字段必须是字符串，所以需要将user.id转换为字符串
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册（人员登记）"""
    try:
        user = create_user(db, user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
def logout():
    """退出登录（前端删除Token即可）"""
    return {"message": "退出成功"}

