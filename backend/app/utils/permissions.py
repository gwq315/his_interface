"""
权限验证工具模块

提供权限验证装饰器和依赖项，用于控制API访问权限。

作者: Auto
创建时间: 2024
"""

from functools import wraps
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models import User, UserRole
from backend.app.api.auth import get_current_user
from backend.database import get_db


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def check_project_permission(project_creator_id: Optional[int], current_user: User) -> bool:
    """
    检查项目权限
    
    规则：
    - 管理员可以操作所有项目
    - 普通用户只能操作自己创建的项目
    
    Args:
        project_creator_id: 项目创建人ID
        current_user: 当前用户
        
    Returns:
        bool: 有权限返回True，无权限返回False
    """
    # 管理员可以操作所有项目
    if current_user.role == UserRole.ADMIN:
        return True
    
    # 普通用户只能操作自己创建的项目
    if project_creator_id is None:
        # 如果项目没有创建人，只有管理员可以操作
        return False
    
    return project_creator_id == current_user.id


def require_project_permission(project_creator_id: Optional[int]):
    """
    要求项目权限的依赖项
    
    使用方式：
    @router.put("/{project_id}")
    def update_project(
        project_id: int,
        current_user: User = Depends(get_current_user),
        _: None = Depends(lambda: require_project_permission(project_creator_id))
    ):
        ...
    """
    def _check_permission(current_user: User = Depends(get_current_user)):
        if not check_project_permission(project_creator_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此项目"
            )
        return current_user
    return _check_permission


def check_resource_permission(creator_id: Optional[int], current_user: User, db: Session, allow_read: bool = False) -> bool:
    """
    检查资源权限（通用函数，适用于所有资源类型）
    
    用于检查用户是否有权限操作（修改/删除）指定的资源。
    此函数适用于接口、字典、文档、常见问题等所有资源类型。
    
    权限规则：
    - 管理员可以操作所有资源
    - 普通用户：
      - 如果资源创建人是admin：不能修改/删除（allow_read参数控制是否允许读取）
      - 如果资源创建人是user：只有创建人自己可以修改/删除
      - 如果资源没有创建人：只有管理员可以操作
    
    Args:
        creator_id: 资源创建人ID（可选）
        current_user: 当前登录用户对象
        db: 数据库会话对象
        allow_read: 是否允许普通用户读取admin创建的资源（默认False）
                    - False：不允许普通用户操作admin创建的资源（用于修改/删除操作）
                    - True：允许普通用户读取admin创建的资源（用于查询操作）
        
    Returns:
        bool: 有权限返回True，无权限返回False
        
    使用示例：
        # 检查是否有权限修改接口
        if check_resource_permission(interface.creator_id, current_user, db, allow_read=False):
            # 执行修改操作
            ...
        
        # 检查是否有权限查询接口
        if check_resource_permission(interface.creator_id, current_user, db, allow_read=True):
            # 执行查询操作
            ...
    """
    # 管理员可以操作所有资源
    # 兼容枚举值和字符串值两种形式
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    if user_role == UserRole.ADMIN.value or user_role == 'admin':
        return True
    
    # 如果资源没有创建人，只有管理员可以操作
    if creator_id is None:
        return False
    
    # 获取创建人信息，用于判断创建人的角色
    from backend.app.crud import get_user
    creator = get_user(db, creator_id)
    
    if creator is None:
        # 创建人不存在，只有管理员可以操作
        return False
    
    # 如果创建人是admin，普通用户不能修改/删除
    # allow_read参数控制是否允许普通用户读取admin创建的资源
    creator_role = creator.role.value if hasattr(creator.role, 'value') else creator.role
    if creator_role == UserRole.ADMIN.value or creator_role == 'admin':
        return allow_read
    
    # 如果创建人是user，只有创建人自己可以操作
    return creator_id == current_user.id


def require_resource_permission(creator_id: Optional[int], allow_read: bool = False):
    """
    要求资源权限的依赖项（通用函数）
    
    使用方式：
    @router.put("/{resource_id}")
    def update_resource(
        resource_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        # 先获取资源，然后检查权限
        resource = get_resource(db, resource_id)
        if not check_resource_permission(resource.creator_id, current_user, db, allow_read):
            raise HTTPException(status_code=403, detail="无权操作此资源")
        ...
    """
    # 注意：这个函数现在主要用于文档说明，实际使用时应该直接调用check_resource_permission
    pass