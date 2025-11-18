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
from backend.app.api.auth import get_current_user
from backend.app.models import User
from backend.app.utils.permissions import check_resource_permission

# 创建API路由器，所有路由的前缀为/api/interfaces
router = APIRouter(prefix="/api/interfaces", tags=["接口管理"])


@router.post("/", response_model=Interface, status_code=201)
def create_interface_endpoint(
    interface: InterfaceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新接口
    
    请求体包含接口基本信息和参数列表（可选）。
    接口编码必须唯一，如果已存在会返回400错误。
    
    Args:
        interface: 接口创建模型，包含接口信息和参数列表
        db: 数据库会话（自动注入）
        current_user: 当前登录用户
        
    Returns:
        Interface: 创建成功的接口对象（包含关联的参数）
        
    Raises:
        HTTPException 400: 接口编码已存在
    """
    # 检查接口编码是否已存在（编码必须唯一）
    existing = get_interface_by_code(db, interface.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"接口编码 {interface.code} 已存在")
    
    # 创建接口（包含关联的参数），设置创建人ID
    return create_interface(db, interface, creator_id=current_user.id)


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
    # 获取接口对象（包含关联的参数）
    db_interface = get_interface(db, interface_id)
    if not db_interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    
    # 手动构建响应对象，避免自动序列化关联关系时出错
    # 这样可以避免访问不存在的列或循环引用问题
    try:
        # 使用Parameter schema构建参数列表
        from backend.app.schemas import Parameter
        parameters_list = []
        if db_interface.parameters:
            for param in db_interface.parameters:
                try:
                    # 使用Parameter schema创建参数对象
                    param_data = {
                        "id": param.id,
                        "name": param.name,
                        "field_name": param.field_name,
                        "data_type": param.data_type,
                        "param_type": param.param_type,
                        "required": param.required,
                        "default_value": param.default_value,
                        "description": param.description,
                        "example": param.example,
                        "order_index": param.order_index,
                        "dictionary_id": param.dictionary_id,
                        "created_at": param.created_at,
                        "updated_at": param.updated_at
                    }
                    parameters_list.append(Parameter.model_validate(param_data))
                except Exception as param_error:
                    # 如果某个参数序列化失败，记录错误但继续处理其他参数
                    import logging
                    logging.warning(f"Error serializing parameter {param.id}: {str(param_error)}")
                    continue
        
        # 构建接口响应对象
        interface_data = {
            "id": db_interface.id,
            "project_id": db_interface.project_id,
            "name": db_interface.name,
            "code": db_interface.code,
            "description": db_interface.description,
            "interface_type": db_interface.interface_type,
            "url": db_interface.url,
            "method": db_interface.method,
            "category": db_interface.category,
            "tags": db_interface.tags,
            "status": db_interface.status,
            "input_example": getattr(db_interface, "input_example", None),
            "output_example": getattr(db_interface, "output_example", None),
            "view_definition": getattr(db_interface, "view_definition", None),
            "notes": getattr(db_interface, "notes", None),
            "creator_id": getattr(db_interface, "creator_id", None),
            "created_at": db_interface.created_at,
            "updated_at": db_interface.updated_at,
            "parameters": parameters_list,
            "project": None,  # 不返回项目详情，避免循环引用
            "dictionaries": []  # 不返回字典列表，避免性能问题
        }
        
        # 使用Pydantic创建响应对象
        return Interface.model_validate(interface_data)
    except Exception as e:
        # 如果序列化失败，记录错误并返回通用错误
        import logging
        logging.error(f"Error serializing interface {interface_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取接口详情失败: {str(e)}")


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
    # 先根据编码获取接口，然后根据ID获取完整信息（包含参数）
    db_interface = get_interface_by_code(db, code)
    if not db_interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    
    # 使用get_interface获取完整信息（包含参数）
    db_interface = get_interface(db, db_interface.id)
    if not db_interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    
    # 手动构建响应对象，避免自动序列化关联关系时出错
    try:
        # 使用Parameter schema构建参数列表
        from backend.app.schemas import Parameter
        parameters_list = []
        if db_interface.parameters:
            for param in db_interface.parameters:
                try:
                    # 使用Parameter schema创建参数对象
                    param_data = {
                        "id": param.id,
                        "name": param.name,
                        "field_name": param.field_name,
                        "data_type": param.data_type,
                        "param_type": param.param_type,
                        "required": param.required,
                        "default_value": param.default_value,
                        "description": param.description,
                        "example": param.example,
                        "order_index": param.order_index,
                        "dictionary_id": param.dictionary_id,
                        "created_at": param.created_at,
                        "updated_at": param.updated_at
                    }
                    parameters_list.append(Parameter.model_validate(param_data))
                except Exception as param_error:
                    # 如果某个参数序列化失败，记录错误但继续处理其他参数
                    import logging
                    logging.warning(f"Error serializing parameter {param.id}: {str(param_error)}")
                    continue
        
        # 构建接口响应对象
        interface_data = {
            "id": db_interface.id,
            "project_id": db_interface.project_id,
            "name": db_interface.name,
            "code": db_interface.code,
            "description": db_interface.description,
            "interface_type": db_interface.interface_type,
            "url": db_interface.url,
            "method": db_interface.method,
            "category": db_interface.category,
            "tags": db_interface.tags,
            "status": db_interface.status,
            "input_example": getattr(db_interface, "input_example", None),
            "output_example": getattr(db_interface, "output_example", None),
            "view_definition": getattr(db_interface, "view_definition", None),
            "notes": getattr(db_interface, "notes", None),
            "creator_id": getattr(db_interface, "creator_id", None),
            "created_at": db_interface.created_at,
            "updated_at": db_interface.updated_at,
            "parameters": parameters_list,
            "project": None,  # 不返回项目详情，避免循环引用
            "dictionaries": []  # 不返回字典列表，避免性能问题
        }
        
        # 使用Pydantic创建响应对象
        return Interface.model_validate(interface_data)
    except Exception as e:
        # 如果序列化失败，记录错误并返回通用错误
        import logging
        logging.error(f"Error serializing interface by code {code}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取接口详情失败: {str(e)}")


@router.post("/search", response_model=InterfaceListResponse)
def search_interfaces_endpoint(
    search: InterfaceSearch, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    items, total = search_interfaces(
        db, 
        search, 
        user_id=current_user.id, 
        is_admin=current_user.role.value == 'admin'
    )
    
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
                "creator_id": getattr(it, "creator_id", None),
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
def list_interfaces_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取接口列表（简单分页）
    
    返回接口列表，支持分页。
    注意：此接口不包含搜索功能，如需搜索请使用/search端点。
    
    权限规则：
    - 管理员可以看到所有接口
    - 普通用户只能看到管理员创建的和自己创建的接口
    
    Args:
        skip: 跳过的记录数（查询参数，默认0）
        limit: 返回的最大记录数（查询参数，默认100）
        db: 数据库会话（自动注入）
        current_user: 当前登录用户
        
    Returns:
        List[Interface]: 接口列表
    """
    # 使用search_interfaces来实现权限过滤
    from backend.app.schemas import InterfaceSearch
    search = InterfaceSearch(page=1, page_size=limit)
    items, _ = search_interfaces(
        db, 
        search, 
        user_id=current_user.id, 
        is_admin=current_user.role.value == 'admin'
    )
    # 手动构建响应对象
    from backend.app.schemas import Interface
    serializable_items = []
    for it in items:
        try:
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
                "creator_id": getattr(it, "creator_id", None),
                "created_at": it.created_at,
                "updated_at": it.updated_at,
                "parameters": [],
                "dictionaries": [],
                "project": None,
            }
            interface_obj = Interface.model_validate(interface_data)
            serializable_items.append(interface_obj)
        except Exception as e:
            import logging
            logging.error(f"Error serializing interface {it.id}: {str(e)}")
            continue
    
    return serializable_items[skip:skip+limit]  # 应用skip分页


@router.put("/{interface_id}", response_model=Interface)
def update_interface_endpoint(
    interface_id: int,
    interface_update: InterfaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新接口信息（部分更新）
    
    只更新请求体中提供的字段，未提供的字段保持不变。
    如果提供了parameters，会替换所有现有参数。
    
    权限规则：
    - 管理员可以更新所有接口
    - 普通用户只能更新自己创建的接口（创建人是user类型的）
    
    Args:
        interface_id: 要更新的接口ID（路径参数）
        interface_update: 更新数据模型（所有字段都是可选的）
        db: 数据库会话（自动注入）
        current_user: 当前登录用户
        
    Returns:
        Interface: 更新后的接口对象
        
    Raises:
        HTTPException 404: 接口不存在
        HTTPException 403: 无权操作此接口
    """
    # 先获取接口，检查权限
    interface = get_interface(db, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    
    # 检查权限
    if not check_resource_permission(interface.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此接口")
    
    interface = update_interface(db, interface_id, interface_update)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    return interface


@router.delete("/{interface_id}", status_code=204)
def delete_interface_endpoint(
    interface_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除接口
    
    删除接口时会自动删除所有关联的参数（级联删除）。
    注意：此操作不可恢复，请谨慎使用。
    
    权限规则：
    - 管理员可以删除所有接口
    - 普通用户只能删除自己创建的接口（创建人是user类型的）
    
    Args:
        interface_id: 要删除的接口ID（路径参数）
        db: 数据库会话（自动注入）
        current_user: 当前登录用户
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 接口不存在
        HTTPException 403: 无权操作此接口
    """
    # 先获取接口，检查权限
    interface = get_interface(db, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="接口不存在")
    
    # 检查权限
    if not check_resource_permission(interface.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此接口")
    
    success = delete_interface(db, interface_id)
    if not success:
        raise HTTPException(status_code=404, detail="接口不存在")
    return None

