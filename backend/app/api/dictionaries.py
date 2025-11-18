"""
字典管理API路由模块

本模块提供字典管理的所有RESTful API端点：
1. 创建字典：POST /api/dictionaries/
2. 获取字典详情：GET /api/dictionaries/{dictionary_id}
3. 根据编码获取字典：GET /api/dictionaries/code/{code}
4. 获取字典列表：GET /api/dictionaries/
5. 更新字典：PUT /api/dictionaries/{dictionary_id}
6. 删除字典：DELETE /api/dictionaries/{dictionary_id}
7. 获取字典值列表：GET /api/dictionaries/{dictionary_id}/values
8. 删除字典值：DELETE /api/dictionaries/values/{value_id}

字典用于定义参数的取值范围，如性别、状态、类型等。

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.app.schemas import Dictionary, DictionaryCreate, DictionaryUpdate, DictionaryValue
from backend.app.crud import (
    create_dictionary, get_dictionary, get_dictionary_by_code,
    get_dictionaries, update_dictionary, delete_dictionary,
    get_dictionary_values, delete_dictionary_value, batch_update_dictionary_values
)
from backend.app.schemas import DictionaryValueBase
from backend.app.api.auth import get_current_user
from backend.app.models import User
from backend.app.utils.permissions import check_resource_permission

# 创建API路由器，所有路由的前缀为/api/dictionaries
router = APIRouter(prefix="/api/dictionaries", tags=["字典管理"])


@router.post("/", response_model=Dictionary, status_code=201)
def create_dictionary_endpoint(
    dictionary: DictionaryCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新字典
    
    创建字典时会自动设置创建人为当前登录用户。
    字典编码必须唯一，如果已存在会返回400错误。
    
    权限说明：
    - 所有登录用户都可以创建字典
    - 创建的字典会自动设置创建人为当前登录用户
    
    Args:
        dictionary: 字典创建模型，包含字典基本信息和字典值列表（可选）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Dictionary: 创建成功的字典对象（包含关联的字典值）
        
    Raises:
        HTTPException 400: 字典编码已存在
    """
    # 检查字典编码是否已存在（编码必须唯一）
    existing = get_dictionary_by_code(db, dictionary.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"字典编码 {dictionary.code} 已存在")
    
    # 创建字典（包含关联的字典值），设置创建人ID为当前登录用户
    return create_dictionary(db, dictionary, creator_id=current_user.id)


@router.get("/{dictionary_id}", response_model=Dictionary)
def get_dictionary_endpoint(dictionary_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取字典详情
    
    返回字典的完整信息，包括：
    - 字典基本信息（名称、编码、描述等）
    - 所有字典值（value列表）
    
    Args:
        dictionary_id: 字典ID（路径参数）
        db: 数据库会话对象（自动注入）
        
    Returns:
        Dictionary: 字典对象，包含所有字典值
        
    Raises:
        HTTPException 404: 字典不存在
    """
    dictionary = get_dictionary(db, dictionary_id)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dictionary


@router.get("/code/{code}", response_model=Dictionary)
def get_dictionary_by_code_endpoint(code: str, db: Session = Depends(get_db)):
    """
    根据编码获取字典详情
    
    字典编码是唯一标识，用于快速查找字典。
    常用于通过编码快速查询字典信息。
    
    Args:
        code: 字典编码（路径参数，如"GENDER"、"STATUS"）
        db: 数据库会话对象（自动注入）
        
    Returns:
        Dictionary: 字典对象，包含所有字典值
        
    Raises:
        HTTPException 404: 字典不存在
    """
    dictionary = get_dictionary_by_code(db, code)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dictionary


@router.get("/", response_model=List[Dictionary])
def list_dictionaries_endpoint(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    project_id: Optional[int] = Query(None, description="项目ID（可选，用于筛选特定项目的字典）"),
    keyword: Optional[str] = Query(None, description="关键词（可选，搜索字典名称、编码、描述）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取字典列表（支持项目筛选、关键词搜索和分页）
    
    支持以下筛选条件：
    - 项目筛选：按项目ID筛选特定项目的字典
    - 关键词搜索：在字典名称、编码、描述中模糊匹配
    
    权限规则：
    - 管理员可以看到所有字典
    - 普通用户只能看到：
      * 管理员创建的字典
      * 自己创建的字典
      * 没有创建人的字典（兼容旧数据）
    
    Args:
        skip: 跳过的记录数（用于分页，默认0）
        limit: 返回的最大记录数（默认100，最大1000）
        project_id: 项目ID（可选，用于筛选特定项目的字典）
        keyword: 关键词（可选，用于在字典名称、编码、描述中搜索）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        List[Dictionary]: 字典列表，根据权限和筛选条件过滤后的结果
    """
    # 调用CRUD函数获取字典列表，传入用户ID和角色信息用于权限过滤
    return get_dictionaries(
        db, 
        skip=skip, 
        limit=limit, 
        project_id=project_id, 
        keyword=keyword,
        user_id=current_user.id,
        is_admin=current_user.role.value == 'admin'
    )


@router.put("/{dictionary_id}", response_model=Dictionary)
def update_dictionary_endpoint(
    dictionary_id: int,
    dictionary_update: DictionaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新字典信息（部分更新）
    
    支持部分更新，只更新请求体中提供的字段，未提供的字段保持不变。
    如果提供了values，会替换所有现有字典值。
    
    权限规则：
    - 管理员可以更新所有字典
    - 普通用户只能更新自己创建的字典（创建人是user类型的）
    - 普通用户不能更新管理员创建的字典
    
    Args:
        dictionary_id: 要更新的字典ID（路径参数）
        dictionary_update: 字典更新模型（所有字段都是可选的）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Dictionary: 更新后的字典对象
        
    Raises:
        HTTPException 404: 字典不存在
        HTTPException 403: 无权操作此字典
    """
    # 先获取字典，检查权限
    dictionary = get_dictionary(db, dictionary_id)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    
    # 检查权限：使用权限检查函数验证用户是否有权限更新此字典
    if not check_resource_permission(dictionary.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此字典")
    
    # 执行更新操作
    dictionary = update_dictionary(db, dictionary_id, dictionary_update)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dictionary


@router.delete("/{dictionary_id}", status_code=204)
def delete_dictionary_endpoint(
    dictionary_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除字典
    
    删除字典时会自动删除所有关联的字典值（级联删除）。
    注意：此操作不可恢复，请谨慎使用。
    
    权限规则：
    - 管理员可以删除所有字典
    - 普通用户只能删除自己创建的字典（创建人是user类型的）
    - 普通用户不能删除管理员创建的字典
    
    Args:
        dictionary_id: 要删除的字典ID（路径参数）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 字典不存在
        HTTPException 403: 无权操作此字典
    """
    # 先获取字典，检查权限
    dictionary = get_dictionary(db, dictionary_id)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    
    # 检查权限：使用权限检查函数验证用户是否有权限删除此字典
    if not check_resource_permission(dictionary.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此字典")
    
    # 执行删除操作（会级联删除关联的字典值）
    success = delete_dictionary(db, dictionary_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典不存在")
    return None


@router.get("/{dictionary_id}/values", response_model=List[DictionaryValue])
def get_dictionary_values_endpoint(dictionary_id: int, db: Session = Depends(get_db)):
    """
    获取字典值列表
    
    返回指定字典的所有字典值，包括值的编码、名称、排序等信息。
    
    Args:
        dictionary_id: 字典ID（路径参数）
        db: 数据库会话对象（自动注入）
        
    Returns:
        List[DictionaryValue]: 字典值列表，按sort_order排序
        
    Raises:
        HTTPException 404: 字典不存在（由CRUD函数处理）
    """
    return get_dictionary_values(db, dictionary_id)


@router.delete("/values/{value_id}", status_code=204)
def delete_dictionary_value_endpoint(value_id: int, db: Session = Depends(get_db)):
    """
    删除字典值
    
    删除指定的字典值。注意：此操作不可恢复，请谨慎使用。
    
    Args:
        value_id: 要删除的字典值ID（路径参数）
        db: 数据库会话对象（自动注入）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 字典值不存在
    """
    success = delete_dictionary_value(db, value_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典值不存在")
    return None


@router.put("/{dictionary_id}/values", response_model=List[DictionaryValue])
def batch_update_dictionary_values_endpoint(
    dictionary_id: int,
    values: List[DictionaryValueBase],
    db: Session = Depends(get_db)
):
    """
    批量更新字典值
    
    替换指定字典的所有字典值。请求体中的字典值列表会完全替换现有的字典值。
    如果请求体为空列表，则会删除所有字典值。
    
    注意：此操作会替换所有现有字典值，请确保请求体包含所有需要保留的字典值。
    
    Args:
        dictionary_id: 字典ID（路径参数）
        values: 字典值列表（请求体），每个字典值包含编码、名称、排序等信息
        db: 数据库会话对象（自动注入）
        
    Returns:
        List[DictionaryValue]: 更新后的字典值列表
        
    Raises:
        HTTPException 404: 字典不存在
    """
    # 检查字典是否存在
    dictionary = get_dictionary(db, dictionary_id)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    
    # 批量更新字典值（会替换所有现有字典值）
    return batch_update_dictionary_values(db, dictionary_id, values)

