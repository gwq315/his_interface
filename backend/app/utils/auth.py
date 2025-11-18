"""
认证工具模块

提供密码验证和Token生成等功能。

作者: Auto
创建时间: 2024
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from backend.app.models import User, UserRole

# JWT配置
SECRET_KEY = "Chnyo.com@2018"  # 生产环境应使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天（单位内部使用，不需要自动退出）


def verify_password(plain_password: Optional[str], stored_password: Optional[str]) -> bool:
    """
    验证密码（明文比较）
    
    Args:
        plain_password: 用户输入的密码（可以为None或空字符串）
        stored_password: 数据库中存储的密码（可以为None或空字符串）
        
    Returns:
        bool: 密码匹配返回True，否则返回False
    """
    # 处理None和空字符串
    plain = plain_password if plain_password else ""
    stored = stored_password if stored_password else ""
    
    # 如果两个密码都为空，认为匹配
    if not plain and not stored:
        return True
    
    # 如果只有一个为空，不匹配
    if not plain or not stored:
        return False
    
    # 明文比较
    return plain == stored


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

