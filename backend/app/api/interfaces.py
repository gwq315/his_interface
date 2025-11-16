"""
接口管理API路由模块

本模块提供接口管理的所有RESTful API端点：
1. 创建接口：POST /api/interfaces/
2. 获取接口详情：GET /api/interfaces/{id}
3. 根据编码获取接口：GET /api/interfaces/code/{code}
4. 搜索接口：POST /api/interfaces/search
5. 获取接口列表：GET /api/interfaces/
6. 更新接口：PUT /api/interfaces/{id}
7. 删除接口：DELETE /api/interfaces/{id}

所有端点都使用FastAPI的自动文档生成功能，可在/docs查看。

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.app.schemas import (
    Interface, InterfaceCreate, InterfaceUpdate, InterfaceSearch, InterfaceListResponse
)
from backend.app.crud import (
    create_interface, get_interface, get_interface_by_code,
    get_interfaces, search_interfaces, update_interface, delete_interface
)

# 创建API路由器，所有路由的前缀为/api/interfaces
router = APIRouter(prefix="/api/interfaces", tags=["接口管理"])


@router.post("/", response_model=Interface, status_code=201)
def create_interface_endpoint(interface: InterfaceCreate, db: Session = Depends(get_db)):
    """
    创建新接口
    
    请求体包含接口基本信息和参数列表（可选）。
    接口编码必须唯一，如果已存在会返回400错误。
    
    Args:
        interface: 接口创建模型，包含接口信息和参数列表
        db: 数据库会话（自动注入）
        
    Returns:
        Interface: 创建成功的接口对象（包含关联的参数）
        
    Raises:
        HTTPException 400: 接口编码已存在
    """
    # 检查接口编码是否已存在（编码必须唯一）
    existing = get_interface_by_code(db, interface.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"接口编码 {interface.code} 已存在")
    
    # 创建接口（包含关联的参数）
    return create_interface(db, interface)


@router.get("/{interface_id}", response_model=Interface)
def get_interface_endpoint(interface_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取接口详情
    
    返回接口的完整信息，包括：
    - 接口基本信息
    - 所有参数（入参和出参）
    - 关联的字典
    
    Args:
        interface_id: 接口ID（路径参数）
        db: 数据库会话（自动注入）
        
    Returns:
        Interface: 接口对象
        
    Raises:
        HTTPException 404: 接口不存在
    """
    interface = get_interface(db, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    return interface


@router.get("/code/{code}", response_model=Interface)
def get_interface_by_code_endpoint(code: str, db: Session = Depends(get_db)):
    """
    根据编码获取接口详情
    
    接口编码是唯一标识，用于快速查找接口。
    常用于通过编码快速查询接口信息。
    
    Args:
        code: 接口编码（路径参数，如"PATIENT_QUERY"）
        db: 数据库会话（自动注入）
        
    Returns:
        Interface: 接口对象
        
    Raises:
        HTTPException 404: 接口不存在
    """
    interface = get_interface_by_code(db, code)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    return interface


@router.post("/search", response_model=InterfaceListResponse)
def search_interfaces_endpoint(search: InterfaceSearch, db: Session = Depends(get_db)):
    """
    搜索接口（支持多条件组合查询和分页）
    
    支持以下搜索条件：
    - 关键词：在接口名称、编码、描述中搜索
    - 接口类型：view或api
    - 分类：按接口分类筛选
    - 标签：支持多个标签（逗号分隔）
    - 状态：active或inactive
    
    返回分页结果，包含总数和当前页数据。
    
    Args:
        search: 搜索条件模型，包含所有筛选条件和分页信息
        db: 数据库会话（自动注入）
        
    Returns:
        InterfaceListResponse: 包含总数、页码、每页数量和接口列表的响应对象
    """
    items, total = search_interfaces(db, search)
    
    # 手动构建可序列化的字典列表，避免访问关联关系
    # 使用 Pydantic 的 model_validate 来创建 Interface 对象，但需要处理关联关系
    from backend.app.schemas import Interface
    serializable_items = []
    
    for it in items:
        try:
            # 构建字典，确保所有字段都正确
            interface_data = {
                "id": it.id,
                "project_id": it.project_id,
                "name": it.name,
                "code": it.code,
                "description": it.description,
                "interface_type": it.interface_type,
                "url": it.url,
                "method": it.method,
                "category": it.category,
                "tags": it.tags,
                "status": it.status,
                "input_example": getattr(it, "input_example", None),
                "output_example": getattr(it, "output_example", None),
                "created_at": it.created_at,
                "updated_at": it.updated_at,
                "parameters": [],  # 列表页不返回参数，使用空列表
                "dictionaries": [],  # 列表页不返回字典，使用空列表
                "project": None,  # 列表页不返回项目详情
            }
            # 使用 Pydantic 创建对象
            interface_obj = Interface.model_validate(interface_data)
            serializable_items.append(interface_obj)
        except Exception as e:
            # 如果验证失败，记录错误但继续处理其他项
            import logging
            logging.error(f"Error serializing interface {it.id}: {str(e)}")
            # 跳过有问题的项
            continue

    return InterfaceListResponse(
        total=total,
        page=search.page,
        page_size=search.page_size,
        items=serializable_items
    )


@router.get("/", response_model=List[Interface])
def list_interfaces_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取接口列表（简单分页）
    
    返回接口列表，支持分页。
    注意：此接口不包含搜索功能，如需搜索请使用/search端点。
    
    Args:
        skip: 跳过的记录数（查询参数，默认0）
        limit: 返回的最大记录数（查询参数，默认100）
        db: 数据库会话（自动注入）
        
    Returns:
        List[Interface]: 接口列表
    """
    return get_interfaces(db, skip=skip, limit=limit)


@router.put("/{interface_id}", response_model=Interface)
def update_interface_endpoint(
    interface_id: int,
    interface_update: InterfaceUpdate,
    db: Session = Depends(get_db)
):
    """
    更新接口信息（部分更新）
    
    只更新请求体中提供的字段，未提供的字段保持不变。
    如果提供了parameters，会替换所有现有参数。
    
    Args:
        interface_id: 要更新的接口ID（路径参数）
        interface_update: 更新数据模型（所有字段都是可选的）
        db: 数据库会话（自动注入）
        
    Returns:
        Interface: 更新后的接口对象
        
    Raises:
        HTTPException 404: 接口不存在
    """
    interface = update_interface(db, interface_id, interface_update)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    return interface


@router.delete("/{interface_id}", status_code=204)
def delete_interface_endpoint(interface_id: int, db: Session = Depends(get_db)):
    """
    删除接口
    
    删除接口时会自动删除所有关联的参数（级联删除）。
    注意：此操作不可恢复，请谨慎使用。
    
    Args:
        interface_id: 要删除的接口ID（路径参数）
        db: 数据库会话（自动注入）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 接口不存在
    """
    success = delete_interface(db, interface_id)
    if not success:
        raise HTTPException(status_code=404, detail="接口不存在")
    return None

