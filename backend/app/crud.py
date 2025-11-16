"""
数据库操作模块（CRUD）

本模块包含所有数据库的增删改查操作，采用Repository模式：
1. 接口相关操作：创建、查询、更新、删除接口
2. 参数相关操作：创建、查询、更新、删除参数
3. 字典相关操作：创建、查询、更新、删除字典
4. 字典值相关操作：创建、查询、删除字典值

CRUD操作说明：
- Create: 创建新记录
- Read: 查询记录（支持多种查询方式）
- Update: 更新记录（支持部分更新）
- Delete: 删除记录

作者: Auto
创建时间: 2024
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List
from datetime import datetime
from backend.app.models import Project, Interface, Parameter, Dictionary, DictionaryValue, Document
from backend.app.schemas import (
    ProjectCreate, ProjectUpdate,
    InterfaceCreate, InterfaceUpdate,
    ParameterCreate, ParameterUpdate,
    DictionaryCreate, DictionaryUpdate,
    DictionaryValueBase,
    InterfaceSearch,
    DocumentCreate, DocumentUpdate, DocumentSearch
)


# ========== 项目相关 CRUD 操作 ==========

def create_project(db: Session, project: ProjectCreate) -> Project:
    """
    创建新项目
    
    Args:
        db: 数据库会话对象
        project: 项目创建模型
        
    Returns:
        Project: 创建成功的项目对象
    """
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # 避免加载关联关系（如果数据库表结构还未更新）
    # 使用expunge_all清除会话中的关联对象缓存
    return db_project


def get_project(db: Session, project_id: int, load_relations: bool = False) -> Optional[Project]:
    """
    根据ID获取项目
    
    Args:
        db: 数据库会话对象
        project_id: 项目ID
        load_relations: 是否加载关联关系（interfaces和dictionaries），默认False避免查询不存在列
        
    Returns:
        Project: 项目对象，如果不存在返回None
    """
    from sqlalchemy.orm import noload
    query = db.query(Project).filter(Project.id == project_id)
    
    if not load_relations:
        # 使用noload避免加载关联关系，防止查询不存在的列
        query = query.options(noload(Project.interfaces), noload(Project.dictionaries))
    
    return query.first()


def get_projects(db: Session, skip: int = 0, limit: int = 100, keyword: Optional[str] = None) -> List[Project]:
    """
    获取项目列表（支持关键词搜索）
    
    Args:
        db: 数据库会话对象
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        keyword: 关键词（搜索项目名称、负责人）
        
    Returns:
        List[Project]: 项目列表
    """
    from sqlalchemy.orm import noload
    query = db.query(Project)
    
    # 避免加载关联关系，防止查询不存在的列
    query = query.options(noload(Project.interfaces), noload(Project.dictionaries))
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Project.name.like(keyword_pattern),
                Project.manager.like(keyword_pattern),
                Project.description.like(keyword_pattern)
            )
        )
    
    return query.order_by(Project.id.asc()).offset(skip).limit(limit).all()


def get_projects_count(db: Session, keyword: Optional[str] = None) -> int:
    """
    获取项目总数（支持关键词搜索）
    
    Args:
        db: 数据库会话对象
        keyword: 关键词
        
    Returns:
        int: 项目总数
    """
    query = db.query(Project)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Project.name.like(keyword_pattern),
                Project.manager.like(keyword_pattern),
                Project.description.like(keyword_pattern)
            )
        )
    
    return query.count()


def update_project(db: Session, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
    """
    更新项目信息
    
    Args:
        db: 数据库会话对象
        project_id: 项目ID
        project_update: 项目更新模型（只包含需要更新的字段）
        
    Returns:
        Project: 更新后的项目对象，如果项目不存在返回None
    """
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """
    删除项目（会级联删除关联的接口和字典）
    
    Args:
        db: 数据库会话对象
        project_id: 项目ID
        
    Returns:
        bool: 删除成功返回True，项目不存在返回False
    """
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True


# ========== 接口相关 CRUD 操作 ==========

def create_interface(db: Session, interface: InterfaceCreate) -> Interface:
    """
    创建新接口
    
    此函数会创建一个新的接口记录，并同时创建关联的参数（如果提供）。
    接口编码必须唯一，如果已存在会抛出异常（由调用方处理）。
    
    Args:
        db: 数据库会话对象
        interface: 接口创建模型，包含接口基本信息和参数列表
        
    Returns:
        Interface: 创建成功的接口对象（包含关联的参数）
        
    Raises:
        如果接口编码已存在，调用方应检查并抛出HTTPException
    """
    # 创建接口对象
    now = datetime.now()
    db_interface = Interface(
        project_id=interface.project_id,
        name=interface.name,
        code=interface.code,
        description=interface.description,
        interface_type=interface.interface_type,
        url=interface.url,
        method=interface.method,
        category=interface.category,
        tags=interface.tags,
        status=interface.status,
        input_example=interface.input_example,
        output_example=interface.output_example,
        view_definition=interface.view_definition,
        notes=interface.notes,
        created_at=now,
        updated_at=now
    )
    db.add(db_interface)
    db.flush()  # 执行flush以获取接口ID（用于后续创建关联参数）

    # 批量创建关联参数（如果提供）
    if interface.parameters:
        param_now = datetime.now()
        for param_data in interface.parameters:
            db_param = Parameter(
                interface_id=db_interface.id,  # 关联到刚创建的接口
                name=param_data.name,
                field_name=param_data.field_name,
                data_type=param_data.data_type,
                param_type=param_data.param_type,  # input或output
                required=param_data.required,
                default_value=param_data.default_value,
                description=param_data.description,
                example=param_data.example,
                order_index=param_data.order_index,
                dictionary_id=param_data.dictionary_id,  # 可选的字典关联
                created_at=param_now
            )
            db.add(db_param)

    # 提交事务（保存所有更改）
    db.commit()
    
    # 使用 joinedload 重新查询接口及其参数，确保所有字段（包括 created_at）都被正确加载
    from sqlalchemy.orm import joinedload
    db_interface = db.query(Interface).options(joinedload(Interface.parameters)).filter(Interface.id == db_interface.id).first()
    
    return db_interface


def get_interface(db: Session, interface_id: int) -> Optional[Interface]:
    """
    根据ID获取接口详情
    
    Args:
        db: 数据库会话对象
        interface_id: 接口ID
        
    Returns:
        Optional[Interface]: 找到的接口对象，如果不存在则返回None
    """
    from sqlalchemy.orm import joinedload
    # 使用joinedload预加载parameters关系，避免N+1查询问题
    return db.query(Interface).options(joinedload(Interface.parameters)).filter(Interface.id == interface_id).first()


def get_interface_by_code(db: Session, code: str) -> Optional[Interface]:
    """
    根据编码获取接口
    
    接口编码是唯一标识，用于快速查找接口。
    
    Args:
        db: 数据库会话对象
        code: 接口编码（如"PATIENT_QUERY"）
        
    Returns:
        Optional[Interface]: 找到的接口对象，如果不存在则返回None
    """
    return db.query(Interface).filter(Interface.code == code).first()


def get_interfaces(db: Session, skip: int = 0, limit: int = 100, project_id: Optional[int] = None) -> List[Interface]:
    """
    获取接口列表（分页，支持项目筛选）
    
    Args:
        db: 数据库会话对象
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数（默认100）
        project_id: 项目ID（可选，用于筛选特定项目的接口）
        
    Returns:
        List[Interface]: 接口列表
    """
    query = db.query(Interface)
    if project_id:
        query = query.filter(Interface.project_id == project_id)
    return query.order_by(Interface.id.asc()).offset(skip).limit(limit).all()


def search_interfaces(db: Session, search: InterfaceSearch) -> tuple[List[Interface], int]:
    """
    搜索接口（支持多条件组合查询）
    
    支持以下搜索条件：
    1. 关键词搜索：在接口名称、编码、描述中搜索
    2. 接口类型筛选：view或api
    3. 分类筛选：按接口分类筛选
    4. 标签筛选：支持多个标签（逗号分隔）
    5. 状态筛选：active或inactive
    
    搜索结果按创建时间倒序排列，支持分页。
    
    Args:
        db: 数据库会话对象
        search: 搜索条件模型，包含所有筛选条件和分页信息
        
    Returns:
        tuple[List[Interface], int]: (接口列表, 总记录数)
    """
    # 构建基础查询
    query = db.query(Interface)

    # ========== 项目筛选 ==========
    if search.project_id:
        query = query.filter(Interface.project_id == search.project_id)

    # ========== 关键词搜索（模糊匹配） ==========
    # 在接口名称、编码、描述中搜索包含关键词的记录
    if search.keyword:
        keyword_filter = or_(
            Interface.name.contains(search.keyword),      # 名称包含关键词
            Interface.code.contains(search.keyword),      # 编码包含关键词
            Interface.description.contains(search.keyword)  # 描述包含关键词
        )
        query = query.filter(keyword_filter)

    # ========== 接口类型筛选 ==========
    if search.interface_type:
        query = query.filter(Interface.interface_type == search.interface_type)

    # ========== 分类筛选 ==========
    if search.category:
        query = query.filter(Interface.category == search.category)

    # ========== 标签筛选（支持多个标签） ==========
    if search.tags:
        # 将逗号分隔的标签字符串转换为列表
        tag_list = [tag.strip() for tag in search.tags.split(",")]
        # 每个标签都要匹配（AND关系）
        for tag in tag_list:
            query = query.filter(Interface.tags.contains(tag))

    # ========== 状态筛选 ==========
    if search.status:
        query = query.filter(Interface.status == search.status)

    # ========== 获取总数（在分页之前） ==========
    total = query.count()

    # ========== 分页处理 ==========
    offset = (search.page - 1) * search.page_size  # 计算偏移量
    # 按ID升序排列，然后分页（新增加的在最后）
    items = query.order_by(Interface.id.asc()).offset(offset).limit(search.page_size).all()

    return items, total


def update_interface(db: Session, interface_id: int, interface_update: InterfaceUpdate) -> Optional[Interface]:
    """
    更新接口信息（部分更新）
    
    只更新提供的字段，未提供的字段保持不变。
    使用model_dump(exclude_unset=True)只获取已设置的字段。
    如果提供了parameters，则替换所有现有参数。
    
    Args:
        db: 数据库会话对象
        interface_id: 要更新的接口ID
        interface_update: 更新数据模型（所有字段都是可选的）
        
    Returns:
        Optional[Interface]: 更新后的接口对象，如果接口不存在则返回None
        
    注意：
    - 如果提供了parameters，会删除所有现有参数并创建新参数
    - 删除接口时会自动删除所有关联的参数（级联删除）
    """
    db_interface = get_interface(db, interface_id)
    if not db_interface:
        return None

    # 只获取已设置的字段（部分更新）
    update_data = interface_update.model_dump(exclude_unset=True)
    
    # 如果提供了parameters，先处理参数更新
    parameters = update_data.pop('parameters', None)
    if parameters is not None:
        # 删除所有现有参数
        from backend.app.models import Parameter
        param_now = datetime.now()
        db.query(Parameter).filter(Parameter.interface_id == interface_id).delete()
        # 创建新参数（parameters 是字典列表，因为来自 model_dump()）
        for param_data in parameters:
            # param_data 是字典，直接使用字典访问或解包
            db_param = Parameter(
                interface_id=interface_id,
                name=param_data.get('name', ''),
                field_name=param_data.get('field_name', ''),
                data_type=param_data.get('data_type', 'string'),
                param_type=param_data.get('param_type'),
                required=param_data.get('required', False),
                default_value=param_data.get('default_value'),
                description=param_data.get('description'),
                example=param_data.get('example'),
                order_index=param_data.get('order_index', 0),
                dictionary_id=param_data.get('dictionary_id'),
                created_at=param_now
            )
            db.add(db_param)
    
    # 动态更新所有提供的字段（除了parameters）
    for field, value in update_data.items():
        setattr(db_interface, field, value)
    
    # 更新 updated_at 时间戳
    db_interface.updated_at = datetime.now()

    db.commit()  # 提交更改
    
    # 使用 joinedload 重新查询接口及其参数，确保所有字段（包括 created_at）都被正确加载
    from sqlalchemy.orm import joinedload
    db_interface = db.query(Interface).options(joinedload(Interface.parameters)).filter(Interface.id == interface_id).first()
    
    return db_interface


def delete_interface(db: Session, interface_id: int) -> bool:
    """
    删除接口
    
    删除接口时会自动删除所有关联的参数（通过cascade级联删除）。
    
    Args:
        db: 数据库会话对象
        interface_id: 要删除的接口ID
        
    Returns:
        bool: 删除成功返回True，接口不存在返回False
    """
    db_interface = get_interface(db, interface_id)
    if not db_interface:
        return False

    # 删除接口（级联删除关联的参数）
    db.delete(db_interface)
    db.commit()
    return True


# ========== 参数相关 CRUD 操作 ==========

def create_parameter(db: Session, interface_id: int, parameter: ParameterCreate) -> Parameter:
    """
    创建新参数
    
    为指定接口创建一个新参数（入参或出参）。
    参数可以关联字典（可选）。
    
    Args:
        db: 数据库会话对象
        interface_id: 所属接口ID
        parameter: 参数创建模型，包含参数的所有信息
        
    Returns:
        Parameter: 创建成功的参数对象
    """
    db_parameter = Parameter(
        interface_id=interface_id,
        name=parameter.name,
        field_name=parameter.field_name,
        data_type=parameter.data_type,
        param_type=parameter.param_type,
        required=parameter.required,
        default_value=parameter.default_value,
        description=parameter.description,
        example=parameter.example,
        order_index=parameter.order_index,
        dictionary_id=parameter.dictionary_id
    )
    db.add(db_parameter)
    db.commit()
    db.refresh(db_parameter)
    return db_parameter


def get_parameter(db: Session, parameter_id: int) -> Optional[Parameter]:
    """
    根据ID获取参数详情
    
    Args:
        db: 数据库会话对象
        parameter_id: 参数ID
        
    Returns:
        Optional[Parameter]: 找到的参数对象，如果不存在则返回None
    """
    return db.query(Parameter).filter(Parameter.id == parameter_id).first()


def get_parameters_by_interface(db: Session, interface_id: int, param_type: Optional[str] = None) -> List[Parameter]:
    """
    获取指定接口的参数列表
    
    可以按参数类型筛选（input或output）。
    如果不指定类型，返回所有参数。
    参数按order_index排序。
    
    Args:
        db: 数据库会话对象
        interface_id: 接口ID
        param_type: 参数类型（可选，值为"input"或"output"）
        
    Returns:
        List[Parameter]: 参数列表，按order_index排序
    """
    query = db.query(Parameter).filter(Parameter.interface_id == interface_id)
    if param_type:
        query = query.filter(Parameter.param_type == param_type)
    return query.order_by(Parameter.order_index, Parameter.id).all()


def update_parameter(db: Session, parameter_id: int, parameter_update: ParameterUpdate) -> Optional[Parameter]:
    """
    更新参数信息（部分更新）
    
    只更新提供的字段，未提供的字段保持不变。
    
    Args:
        db: 数据库会话对象
        parameter_id: 要更新的参数ID
        parameter_update: 更新数据模型（所有字段都是可选的）
        
    Returns:
        Optional[Parameter]: 更新后的参数对象，如果参数不存在则返回None
    """
    db_parameter = get_parameter(db, parameter_id)
    if not db_parameter:
        return None

    # 只获取已设置的字段（部分更新）
    update_data = parameter_update.model_dump(exclude_unset=True)
    # 动态更新所有提供的字段
    for field, value in update_data.items():
        setattr(db_parameter, field, value)

    db.commit()
    db.refresh(db_parameter)
    return db_parameter


def delete_parameter(db: Session, parameter_id: int) -> bool:
    """
    删除参数
    
    删除参数不会影响关联的字典，只是断开参数与字典的关联。
    
    Args:
        db: 数据库会话对象
        parameter_id: 要删除的参数ID
        
    Returns:
        bool: 删除成功返回True，参数不存在返回False
    """
    db_parameter = get_parameter(db, parameter_id)
    if not db_parameter:
        return False

    db.delete(db_parameter)
    db.commit()
    return True


# ========== 字典相关 CRUD 操作 ==========

def create_dictionary(db: Session, dictionary: DictionaryCreate) -> Dictionary:
    """
    创建新字典
    
    此函数会创建一个新的字典记录，并同时创建关联的字典值（如果提供）。
    字典编码必须唯一。
    
    Args:
        db: 数据库会话对象
        dictionary: 字典创建模型，包含字典基本信息和字典值列表
        
    Returns:
        Dictionary: 创建成功的字典对象（包含关联的字典值）
    """
    # 创建字典对象
    db_dictionary = Dictionary(
        project_id=dictionary.project_id,
        name=dictionary.name,
        code=dictionary.code,
        description=dictionary.description,
        interface_id=dictionary.interface_id  # 可选的接口关联（保留向后兼容）
    )
    db.add(db_dictionary)
    db.flush()  # 执行flush以获取字典ID（用于后续创建关联的字典值）

    # 批量创建关联的字典值（如果提供）
    if dictionary.values:
        for value_data in dictionary.values:
            db_value = DictionaryValue(
                dictionary_id=db_dictionary.id,  # 关联到刚创建的字典
                key=value_data.key,
                value=value_data.value,
                description=value_data.description,
                order_index=value_data.order_index
            )
            db.add(db_value)

    db.commit()
    db.refresh(db_dictionary)
    return db_dictionary


def get_dictionary(db: Session, dictionary_id: int) -> Optional[Dictionary]:
    """
    根据ID获取字典详情
    
    Args:
        db: 数据库会话对象
        dictionary_id: 字典ID
        
    Returns:
        Optional[Dictionary]: 找到的字典对象，如果不存在则返回None
    """
    return db.query(Dictionary).filter(Dictionary.id == dictionary_id).first()


def get_dictionary_by_code(db: Session, code: str) -> Optional[Dictionary]:
    """
    根据编码获取字典
    
    字典编码是唯一标识，用于快速查找字典。
    
    Args:
        db: 数据库会话对象
        code: 字典编码（如"GENDER"）
        
    Returns:
        Optional[Dictionary]: 找到的字典对象，如果不存在则返回None
    """
    return db.query(Dictionary).filter(Dictionary.code == code).first()


def get_dictionaries(db: Session, skip: int = 0, limit: int = 100, project_id: Optional[int] = None, keyword: Optional[str] = None) -> List[Dictionary]:
    """
    获取字典列表（分页，支持项目筛选和关键词搜索）
    
    Args:
        db: 数据库会话对象
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数（默认100）
        project_id: 项目ID（可选，用于筛选特定项目的字典）
        keyword: 关键词（可选，搜索字典名称、编码、描述）
        
    Returns:
        List[Dictionary]: 字典列表
    """
    query = db.query(Dictionary)
    
    if project_id:
        query = query.filter(Dictionary.project_id == project_id)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Dictionary.name.like(keyword_pattern),
                Dictionary.code.like(keyword_pattern),
                Dictionary.description.like(keyword_pattern)
            )
        )
    
    return query.order_by(Dictionary.id.asc()).offset(skip).limit(limit).all()


def update_dictionary(db: Session, dictionary_id: int, dictionary_update: DictionaryUpdate) -> Optional[Dictionary]:
    """
    更新字典信息（部分更新）
    
    只更新提供的字段，未提供的字段保持不变。
    注意：此函数不更新字典值，字典值需要单独管理。
    
    Args:
        db: 数据库会话对象
        dictionary_id: 要更新的字典ID
        dictionary_update: 更新数据模型（所有字段都是可选的）
        
    Returns:
        Optional[Dictionary]: 更新后的字典对象，如果字典不存在则返回None
    """
    db_dictionary = get_dictionary(db, dictionary_id)
    if not db_dictionary:
        return None

    # 只获取已设置的字段（部分更新）
    update_data = dictionary_update.model_dump(exclude_unset=True)
    # 动态更新所有提供的字段
    for field, value in update_data.items():
        setattr(db_dictionary, field, value)

    db.commit()
    db.refresh(db_dictionary)
    return db_dictionary


def delete_dictionary(db: Session, dictionary_id: int) -> bool:
    """
    删除字典
    
    删除字典时会自动删除所有关联的字典值（通过cascade级联删除）。
    
    Args:
        db: 数据库会话对象
        dictionary_id: 要删除的字典ID
        
    Returns:
        bool: 删除成功返回True，字典不存在返回False
    """
    db_dictionary = get_dictionary(db, dictionary_id)
    if not db_dictionary:
        return False

    # 删除字典（级联删除关联的字典值）
    db.delete(db_dictionary)
    db.commit()
    return True


# ========== 字典值相关 CRUD 操作 ==========

def create_dictionary_value(db: Session, dictionary_id: int, value_data: DictionaryValueBase) -> DictionaryValue:
    """
    创建新字典值
    
    为指定字典创建一个新的键值对。
    
    Args:
        db: 数据库会话对象
        dictionary_id: 所属字典ID
        value_data: 字典值数据，包含key、value等信息
        
    Returns:
        DictionaryValue: 创建成功的字典值对象
    """
    db_value = DictionaryValue(
        dictionary_id=dictionary_id,
        key=value_data.key,
        value=value_data.value,
        description=value_data.description,
        order_index=value_data.order_index
    )
    db.add(db_value)
    db.commit()
    db.refresh(db_value)
    return db_value


def get_dictionary_values(db: Session, dictionary_id: int) -> List[DictionaryValue]:
    """
    获取指定字典的所有字典值列表
    
    字典值按order_index排序，便于按顺序显示。
    
    Args:
        db: 数据库会话对象
        dictionary_id: 字典ID
        
    Returns:
        List[DictionaryValue]: 字典值列表，按order_index排序
    """
    return db.query(DictionaryValue).filter(
        DictionaryValue.dictionary_id == dictionary_id
    ).order_by(DictionaryValue.order_index, DictionaryValue.id).all()


def delete_dictionary_value(db: Session, value_id: int) -> bool:
    """
    删除字典值
    
    删除指定的字典值（键值对）。
    
    Args:
        db: 数据库会话对象
        value_id: 要删除的字典值ID
        
    Returns:
        bool: 删除成功返回True，字典值不存在返回False
    """
    db_value = db.query(DictionaryValue).filter(DictionaryValue.id == value_id).first()
    if not db_value:
        return False

    db.delete(db_value)
    db.commit()
    return True


# ========== 文档/截图相关 CRUD 操作 ==========

def create_document(db: Session, document: DocumentCreate, file_path: str, file_name: str, file_size: int, mime_type: Optional[str] = None) -> Document:
    """
    创建新文档/截图
    
    Args:
        db: 数据库会话对象
        document: 文档创建模型
        file_path: 文件相对路径
        file_name: 原始文件名
        file_size: 文件大小（字节）
        mime_type: MIME类型（可选）
        
    Returns:
        Document: 创建成功的文档对象
    """
    db_document = Document(
        **document.model_dump(),
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_document(db: Session, document_id: int) -> Optional[Document]:
    """
    根据ID获取文档
    
    Args:
        db: 数据库会话对象
        document_id: 文档ID
        
    Returns:
        Document: 文档对象，如果不存在返回None
    """
    return db.query(Document).filter(Document.id == document_id).first()


def search_documents(db: Session, search: DocumentSearch) -> tuple[List[Document], int]:
    """
    搜索文档列表（支持关键词、类型、地区、人员筛选和分页）
    
    Args:
        db: 数据库会话对象
        search: 搜索条件模型
        
    Returns:
        tuple: (文档列表, 总记录数)
    """
    query = db.query(Document)
    
    # 关键词搜索（标题、简要描述）
    if search.keyword:
        keyword_pattern = f"%{search.keyword}%"
        query = query.filter(
            or_(
                Document.title.like(keyword_pattern),
                Document.description.like(keyword_pattern)
            )
        )
    
    # 文档类型筛选
    if search.document_type:
        query = query.filter(Document.document_type == search.document_type)
    
    # 地区筛选
    if search.region:
        query = query.filter(Document.region == search.region)
    
    # 人员筛选
    if search.person:
        query = query.filter(Document.person == search.person)
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (search.page - 1) * search.page_size
    items = query.order_by(Document.created_at.desc()).offset(skip).limit(search.page_size).all()
    
    return items, total


def update_document(db: Session, document_id: int, document_update: DocumentUpdate) -> Optional[Document]:
    """
    更新文档信息
    
    Args:
        db: 数据库会话对象
        document_id: 文档ID
        document_update: 文档更新模型
        
    Returns:
        Document: 更新后的文档对象，如果不存在返回None
    """
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if not db_document:
        return None
    
    # 更新字段（只更新提供的字段）
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)
    
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int) -> bool:
    """
    删除文档
    
    删除指定的文档记录（不删除文件，文件需要单独删除）。
    
    Args:
        db: 数据库会话对象
        document_id: 要删除的文档ID
        
    Returns:
        bool: 删除成功返回True，文档不存在返回False
    """
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if not db_document:
        return False
    
    db.delete(db_document)
    db.commit()
    return True

