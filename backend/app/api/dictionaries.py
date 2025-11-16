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
    get_dictionary_values, delete_dictionary_value
)

# 创建API路由器，所有路由的前缀为/api/dictionaries
router = APIRouter(prefix="/api/dictionaries", tags=["字典管理"])


@router.post("/", response_model=Dictionary, status_code=201)
def create_dictionary_endpoint(dictionary: DictionaryCreate, db: Session = Depends(get_db)):
    """创建字典"""
    # 检查编码是否已存在
    existing = get_dictionary_by_code(db, dictionary.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"字典编码 {dictionary.code} 已存在")
    
    return create_dictionary(db, dictionary)


@router.get("/{dictionary_id}", response_model=Dictionary)
def get_dictionary_endpoint(dictionary_id: int, db: Session = Depends(get_db)):
    """获取字典详情"""
    dictionary = get_dictionary(db, dictionary_id)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dictionary


@router.get("/code/{code}", response_model=Dictionary)
def get_dictionary_by_code_endpoint(code: str, db: Session = Depends(get_db)):
    """根据编码获取字典"""
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
    db: Session = Depends(get_db)
):
    """
    获取字典列表
    
    支持项目筛选和关键词搜索。
    关键词会在字典名称、编码、描述中搜索。
    """
    return get_dictionaries(db, skip=skip, limit=limit, project_id=project_id, keyword=keyword)


@router.put("/{dictionary_id}", response_model=Dictionary)
def update_dictionary_endpoint(
    dictionary_id: int,
    dictionary_update: DictionaryUpdate,
    db: Session = Depends(get_db)
):
    """更新字典"""
    dictionary = update_dictionary(db, dictionary_id, dictionary_update)
    if not dictionary:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dictionary


@router.delete("/{dictionary_id}", status_code=204)
def delete_dictionary_endpoint(dictionary_id: int, db: Session = Depends(get_db)):
    """删除字典"""
    success = delete_dictionary(db, dictionary_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典不存在")
    return None


@router.get("/{dictionary_id}/values", response_model=List[DictionaryValue])
def get_dictionary_values_endpoint(dictionary_id: int, db: Session = Depends(get_db)):
    """获取字典值列表"""
    return get_dictionary_values(db, dictionary_id)


@router.delete("/values/{value_id}", status_code=204)
def delete_dictionary_value_endpoint(value_id: int, db: Session = Depends(get_db)):
    """删除字典值"""
    success = delete_dictionary_value(db, value_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典值不存在")
    return None

