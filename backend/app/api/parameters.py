"""
参数管理API路由模块

本模块提供参数管理的所有RESTful API端点：
1. 创建参数：POST /api/parameters/interface/{interface_id}
2. 获取参数详情：GET /api/parameters/{parameter_id}
3. 获取接口的参数列表：GET /api/parameters/interface/{interface_id}
4. 更新参数：PUT /api/parameters/{parameter_id}
5. 删除参数：DELETE /api/parameters/{parameter_id}

参数分为入参（input）和出参（output）两种类型。

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.app.schemas import Parameter, ParameterCreate, ParameterUpdate
from backend.app.crud import (
    create_parameter, get_parameter, get_parameters_by_interface,
    update_parameter, delete_parameter
)

# 创建API路由器，所有路由的前缀为/api/parameters
router = APIRouter(prefix="/api/parameters", tags=["参数管理"])


@router.post("/interface/{interface_id}", response_model=Parameter, status_code=201)
def create_parameter_endpoint(
    interface_id: int,
    parameter: ParameterCreate,
    db: Session = Depends(get_db)
):
    """
    为指定接口创建新参数
    
    参数可以是入参（input）或出参（output）。
    创建参数时可以关联字典（可选）。
    
    Args:
        interface_id: 接口ID（路径参数）
        parameter: 参数创建模型，包含参数的所有信息
        db: 数据库会话（自动注入）
        
    Returns:
        Parameter: 创建成功的参数对象
    """
    return create_parameter(db, interface_id, parameter)


@router.get("/{parameter_id}", response_model=Parameter)
def get_parameter_endpoint(parameter_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取参数详情
    
    返回参数的完整信息，包括关联的字典（如果存在）。
    
    Args:
        parameter_id: 参数ID（路径参数）
        db: 数据库会话（自动注入）
        
    Returns:
        Parameter: 参数对象
        
    Raises:
        HTTPException 404: 参数不存在
    """
    parameter = get_parameter(db, parameter_id)
    if not parameter:
        raise HTTPException(status_code=404, detail="参数不存在")
    return parameter


@router.get("/interface/{interface_id}", response_model=List[Parameter])
def get_interface_parameters_endpoint(
    interface_id: int,
    param_type: str = None,
    db: Session = Depends(get_db)
):
    """
    获取指定接口的参数列表
    
    可以按参数类型筛选（input或output）。
    如果不指定类型，返回所有参数。
    参数按order_index排序。
    
    Args:
        interface_id: 接口ID（路径参数）
        param_type: 参数类型（查询参数，可选，值为"input"或"output"）
        db: 数据库会话（自动注入）
        
    Returns:
        List[Parameter]: 参数列表，按order_index排序
    """
    return get_parameters_by_interface(db, interface_id, param_type)


@router.put("/{parameter_id}", response_model=Parameter)
def update_parameter_endpoint(
    parameter_id: int,
    parameter_update: ParameterUpdate,
    db: Session = Depends(get_db)
):
    """
    更新参数信息（部分更新）
    
    只更新请求体中提供的字段，未提供的字段保持不变。
    
    Args:
        parameter_id: 要更新的参数ID（路径参数）
        parameter_update: 更新数据模型（所有字段都是可选的）
        db: 数据库会话（自动注入）
        
    Returns:
        Parameter: 更新后的参数对象
        
    Raises:
        HTTPException 404: 参数不存在
    """
    parameter = update_parameter(db, parameter_id, parameter_update)
    if not parameter:
        raise HTTPException(status_code=404, detail="参数不存在")
    return parameter


@router.delete("/{parameter_id}", status_code=204)
def delete_parameter_endpoint(parameter_id: int, db: Session = Depends(get_db)):
    """
    删除参数
    
    注意：删除参数不会影响关联的字典，只是断开参数与字典的关联。
    
    Args:
        parameter_id: 要删除的参数ID（路径参数）
        db: 数据库会话（自动注入）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 参数不存在
    """
    success = delete_parameter(db, parameter_id)
    if not success:
        raise HTTPException(status_code=404, detail="参数不存在")
    return None

