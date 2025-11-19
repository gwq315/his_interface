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
from backend.app.models import Project, Interface, Parameter, Dictionary, DictionaryValue, Document, FAQ, User, UserRole
from backend.app.schemas import (
    ProjectCreate, ProjectUpdate,
    InterfaceCreate, InterfaceUpdate,
    ParameterCreate, ParameterUpdate,
    DictionaryCreate, DictionaryUpdate,
    DictionaryValueBase,
    InterfaceSearch,
    DocumentCreate, DocumentUpdate, DocumentSearch,
    FAQCreate, FAQUpdate, FAQSearch,
    UserCreate, UserUpdate
)
from backend.app.utils.auth import verify_password


# ========== 项目相关 CRUD 操作 ==========

def create_project(db: Session, project: ProjectCreate, creator_id: Optional[int] = None) -> Project:
    """
    创建新项目
    
    创建项目时会自动设置创建人ID（如果提供），用于权限控制。
    项目创建成功后，会自动记录创建时间。
    
    Args:
        db: 数据库会话对象
        project: 项目创建模型，包含项目基本信息（名称、负责人、联系方式等）
        creator_id: 创建人ID（可选），如果提供则设置为项目的创建人
        
    Returns:
        Project: 创建成功的项目对象，包含自动生成的ID和创建时间
        
    Note:
        - 项目创建时会自动设置created_at和updated_at时间戳
        - 创建人ID用于后续的权限控制
    """
    # 将Pydantic模型转换为字典，并添加创建人ID
    project_dict = project.model_dump()
    project_dict['creator_id'] = creator_id
    
    # 创建项目对象并保存到数据库
    db_project = Project(**project_dict)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
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


def get_projects(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    keyword: Optional[str] = None,
    user_id: Optional[int] = None,
    is_admin: bool = False
) -> List[Project]:
    """
    获取项目列表（支持关键词搜索和权限过滤）
    
    根据用户角色和权限过滤项目列表：
    - 管理员可以看到所有项目
    - 普通用户只能看到管理员创建的项目、自己创建的项目和没有创建人的项目
    
    Args:
        db: 数据库会话对象
        skip: 跳过的记录数（用于分页，默认0）
        limit: 返回的最大记录数（默认100）
        keyword: 关键词（可选，用于在项目名称、负责人、描述中搜索）
        user_id: 当前用户ID（可选，用于权限过滤）
        is_admin: 是否是管理员（用于权限过滤）
        
    Returns:
        List[Project]: 项目列表，根据权限和关键词过滤后的结果
        
    权限规则说明：
    - 管理员（is_admin=True）：返回所有项目，不进行权限过滤
    - 普通用户（is_admin=False）：只能看到：
      * 自己创建的项目（creator_id == user_id）
      * 管理员创建的项目（creator_id在管理员ID列表中）
      * 没有创建人的项目（creator_id为None，兼容旧数据）
    """
    from sqlalchemy.orm import noload
    from backend.app.models import User, UserRole
    query = db.query(Project)
    
    # 权限过滤：普通用户只能看到有权限访问的项目
    if not is_admin and user_id is not None:
        # 获取所有管理员用户的ID列表（使用子查询提高性能）
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 过滤条件：当前用户创建的项目 OR 管理员创建的项目 OR 没有创建人的项目
        query = query.filter(
            (Project.creator_id == user_id) | 
            (Project.creator_id.in_(admin_users)) | 
            (Project.creator_id.is_(None))
        )
    
    # 避免加载关联关系（interfaces和dictionaries），防止查询不存在的列
    # 这样可以提高查询性能，避免N+1查询问题
    query = query.options(noload(Project.interfaces), noload(Project.dictionaries))
    
    # 关键词搜索：在项目名称、负责人、描述中模糊匹配
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Project.name.like(keyword_pattern),
                Project.manager.like(keyword_pattern),
                Project.description.like(keyword_pattern)
            )
        )
    
    # 按ID升序排列，然后分页返回
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

def create_interface(db: Session, interface: InterfaceCreate, creator_id: Optional[int] = None) -> Interface:
    """
    创建新接口
    
    此函数会创建一个新的接口记录，并同时创建关联的参数（如果提供）。
    接口编码必须唯一，如果已存在会抛出异常（由调用方处理）。
    
    创建接口时会自动设置创建人ID（如果提供），用于权限控制。
    
    Args:
        db: 数据库会话对象
        interface: 接口创建模型，包含接口基本信息和参数列表
        creator_id: 创建人ID（可选），如果提供则设置为接口的创建人
        
    Returns:
        Interface: 创建成功的接口对象（包含关联的参数）
        
    Raises:
        如果接口编码已存在，调用方应检查并抛出HTTPException
        
    Note:
        - 接口创建时会自动设置created_at和updated_at时间戳
        - 创建人ID用于后续的权限控制
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
        creator_id=creator_id,
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


def search_interfaces(db: Session, search: InterfaceSearch, user_id: Optional[int] = None, is_admin: bool = False) -> tuple[List[Interface], int]:
    """
    搜索接口（支持多条件组合查询和权限过滤）
    
    支持以下搜索条件：
    1. 关键词搜索：在接口名称、编码、描述中搜索
    2. 接口类型筛选：view或api
    3. 分类筛选：按接口分类筛选
    4. 标签筛选：支持多个标签（逗号分隔）
    5. 状态筛选：active或inactive
    6. 项目筛选：按项目ID筛选
    
    同时会根据用户权限过滤接口：
    - 管理员可以看到所有接口
    - 普通用户只能看到管理员创建的接口、自己创建的接口和没有创建人的接口
    - 如果指定了project_id，会检查用户是否有权限访问该项目
    
    搜索结果按ID升序排列，支持分页。
    
    Args:
        db: 数据库会话对象
        search: 搜索条件模型，包含所有筛选条件和分页信息
        user_id: 当前用户ID（可选，用于权限过滤）
        is_admin: 是否是管理员（用于权限过滤）
        
    Returns:
        tuple[List[Interface], int]: (接口列表, 总记录数)
        
    权限规则说明：
    - 管理员（is_admin=True）：返回所有接口，不进行权限过滤
    - 普通用户（is_admin=False）：只能看到：
      * 自己创建的接口（creator_id == user_id）
      * 管理员创建的接口（creator_id在管理员ID列表中）
      * 没有创建人的接口（creator_id为None，兼容旧数据）
      * 属于有权限访问的项目的接口
    """
    # 构建基础查询
    query = db.query(Interface)

    # ========== 项目筛选和权限过滤 ==========
    if search.project_id:
        # 如果指定了项目ID，需要检查用户是否有权限访问该项目
        if not is_admin and user_id is not None:
            # 获取项目信息
            project = db.query(Project).filter(Project.id == search.project_id).first()
            if project:
                # 如果项目没有创建人（creator_id为None），允许访问（兼容旧数据）
                if project.creator_id is not None:
                    # 获取创建人信息，检查权限
                    creator = db.query(User).filter(User.id == project.creator_id).first()
                    if creator:
                        # 如果创建人不是管理员也不是当前用户，则无权访问
                        # 返回空结果，避免泄露项目存在信息
                        if creator.role != UserRole.ADMIN and project.creator_id != user_id:
                            return [], 0
        # 过滤指定项目的接口
        query = query.filter(Interface.project_id == search.project_id)
    elif not is_admin and user_id is not None:
        # 如果没有指定项目ID，需要根据项目权限过滤接口
        # 普通用户只能看到属于他们有权限访问的项目的接口
        # 获取所有管理员用户的ID列表
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 获取用户有权限访问的项目ID列表
        # 包括：自己创建的项目、管理员创建的项目、没有创建人的项目
        allowed_project_ids = db.query(Project.id).filter(
            (Project.creator_id == user_id) | 
            (Project.creator_id.in_(admin_users)) | 
            (Project.creator_id.is_(None))
        ).subquery()
        
        # 只返回属于有权限访问的项目的接口
        query = query.filter(Interface.project_id.in_(allowed_project_ids))

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

    # ========== 接口创建人权限过滤 ==========
    # 在项目权限过滤的基础上，进一步根据接口创建人过滤
    if not is_admin and user_id is not None:
        # 普通用户：只能看到管理员创建的和自己创建的接口
        # 获取所有管理员用户的ID列表
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 过滤条件：当前用户创建的接口 OR 管理员创建的接口 OR 没有创建人的接口
        query = query.filter(
            (Interface.creator_id == user_id) | 
            (Interface.creator_id.in_(admin_users)) | 
            (Interface.creator_id.is_(None))
        )

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

def create_dictionary(db: Session, dictionary: DictionaryCreate, creator_id: Optional[int] = None) -> Dictionary:
    """
    创建新字典
    
    此函数会创建一个新的字典记录，并同时创建关联的字典值（如果提供）。
    字典编码必须唯一。
    
    创建字典时会自动设置创建人ID（如果提供），用于权限控制。
    
    Args:
        db: 数据库会话对象
        dictionary: 字典创建模型，包含字典基本信息和字典值列表
        creator_id: 创建人ID（可选），如果提供则设置为字典的创建人
        
    Returns:
        Dictionary: 创建成功的字典对象（包含关联的字典值）
        
    Note:
        - 字典创建时会自动设置created_at和updated_at时间戳
        - 创建人ID用于后续的权限控制
    """
    # 创建字典对象
    db_dictionary = Dictionary(
        project_id=dictionary.project_id,
        name=dictionary.name,
        code=dictionary.code,
        description=dictionary.description,
        interface_id=dictionary.interface_id,  # 可选的接口关联（保留向后兼容）
        creator_id=creator_id
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


def get_dictionaries(db: Session, skip: int = 0, limit: int = 100, project_id: Optional[int] = None, keyword: Optional[str] = None, user_id: Optional[int] = None, is_admin: bool = False) -> List[Dictionary]:
    """
    获取字典列表（分页，支持项目筛选、关键词搜索和权限过滤）
    
    根据用户角色和权限过滤字典列表：
    - 管理员可以看到所有字典
    - 普通用户只能看到管理员创建的字典、自己创建的字典和没有创建人的字典
    
    Args:
        db: 数据库会话对象
        skip: 跳过的记录数（用于分页，默认0）
        limit: 返回的最大记录数（默认100）
        project_id: 项目ID（可选，用于筛选特定项目的字典）
        keyword: 关键词（可选，用于在字典名称、编码、描述中搜索）
        user_id: 当前用户ID（可选，用于权限过滤）
        is_admin: 是否是管理员（用于权限过滤）
        
    Returns:
        List[Dictionary]: 字典列表，根据权限和筛选条件过滤后的结果
        
    权限规则说明：
    - 管理员（is_admin=True）：返回所有字典，不进行权限过滤
    - 普通用户（is_admin=False）：只能看到：
      * 自己创建的字典（creator_id == user_id）
      * 管理员创建的字典（creator_id在管理员ID列表中）
      * 没有创建人的字典（creator_id为None，兼容旧数据）
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
    
    # 权限过滤：普通用户只能看到有权限访问的字典
    if not is_admin and user_id is not None:
        # 获取所有管理员用户的ID列表（使用子查询提高性能）
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 过滤条件：当前用户创建的字典 OR 管理员创建的字典 OR 没有创建人的字典
        query = query.filter(
            (Dictionary.creator_id == user_id) | 
            (Dictionary.creator_id.in_(admin_users)) | 
            (Dictionary.creator_id.is_(None))
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


def update_dictionary_value(db: Session, value_id: int, value_data: DictionaryValueBase) -> Optional[DictionaryValue]:
    """
    更新字典值
    
    更新指定的字典值（键值对）。
    
    Args:
        db: 数据库会话对象
        value_id: 要更新的字典值ID
        value_data: 字典值数据，包含key、value等信息
        
    Returns:
        Optional[DictionaryValue]: 更新后的字典值对象，如果字典值不存在则返回None
    """
    db_value = db.query(DictionaryValue).filter(DictionaryValue.id == value_id).first()
    if not db_value:
        return None

    # 更新字段
    db_value.key = value_data.key
    db_value.value = value_data.value
    db_value.description = value_data.description
    db_value.order_index = value_data.order_index

    db.commit()
    db.refresh(db_value)
    return db_value


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


def batch_update_dictionary_values(db: Session, dictionary_id: int, values: List[DictionaryValueBase]) -> List[DictionaryValue]:
    """
    批量更新字典值
    
    删除所有现有字典值，然后创建新的字典值列表。
    这样可以简化前端的更新逻辑。
    
    Args:
        db: 数据库会话对象
        dictionary_id: 字典ID
        values: 新的字典值列表
        
    Returns:
        List[DictionaryValue]: 更新后的字典值列表
    """
    # 删除所有现有字典值
    db.query(DictionaryValue).filter(DictionaryValue.dictionary_id == dictionary_id).delete()
    
    # 创建新的字典值
    new_values = []
    for idx, value_data in enumerate(values):
        db_value = DictionaryValue(
            dictionary_id=dictionary_id,
            key=value_data.key,
            value=value_data.value,
            description=value_data.description,
            order_index=value_data.order_index if value_data.order_index else idx + 1
        )
        db.add(db_value)
        new_values.append(db_value)
    
    db.commit()
    
    # 刷新所有新创建的值
    for value in new_values:
        db.refresh(value)
    
    return new_values


# ========== 文档/截图相关 CRUD 操作 ==========

def create_document(db: Session, document: DocumentCreate, file_path: str, file_name: str, file_size: int, mime_type: Optional[str] = None, creator_id: Optional[int] = None) -> Document:
    """
    创建新文档/截图
    
    创建文档时会自动设置创建人ID（如果提供），用于权限控制。
    文档信息包括文件路径、文件名、大小等元数据。
    
    Args:
        db: 数据库会话对象
        document: 文档创建模型，包含文档基本信息（标题、描述、地区、人员等）
        file_path: 文件相对路径（相对于项目根目录）
        file_name: 原始文件名（用户上传时的文件名）
        file_size: 文件大小（字节）
        mime_type: MIME类型（可选，如application/pdf、image/png）
        creator_id: 创建人ID（可选），如果提供则设置为文档的创建人
        
    Returns:
        Document: 创建成功的文档对象，包含所有文档信息和文件元数据
        
    Note:
        - 文档创建时会自动设置created_at和updated_at时间戳
        - 创建人ID用于后续的权限控制
    """
    db_document = Document(
        **document.model_dump(),
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        creator_id=creator_id
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


def search_documents(db: Session, search: DocumentSearch, user_id: Optional[int] = None, is_admin: bool = False) -> tuple[List[Document], int]:
    """
    搜索文档列表（支持关键词、类型、地区、人员筛选、分页和权限过滤）
    
    根据用户角色和权限过滤文档列表：
    - 管理员可以看到所有文档
    - 普通用户只能看到管理员创建的文档、自己创建的文档和没有创建人的文档
    
    Args:
        db: 数据库会话对象
        search: 搜索条件模型，包含所有筛选条件和分页信息
        user_id: 当前用户ID（可选，用于权限过滤）
        is_admin: 是否是管理员（用于权限过滤）
        
    Returns:
        tuple[List[Document], int]: (文档列表, 总记录数)
        
    权限规则说明：
    - 管理员（is_admin=True）：返回所有文档，不进行权限过滤
    - 普通用户（is_admin=False）：只能看到：
      * 自己创建的文档（creator_id == user_id）
      * 管理员创建的文档（creator_id在管理员ID列表中）
      * 没有创建人的文档（creator_id为None，兼容旧数据）
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
    
    # 权限过滤：普通用户只能看到有权限访问的文档
    if not is_admin and user_id is not None:
        # 获取所有管理员用户的ID列表（使用子查询提高性能）
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 过滤条件：当前用户创建的文档 OR 管理员创建的文档 OR 没有创建人的文档
        query = query.filter(
            (Document.creator_id == user_id) | 
            (Document.creator_id.in_(admin_users)) | 
            (Document.creator_id.is_(None))
        )
    
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


# ========== 常见问题相关 CRUD 操作 ==========

def create_faq(db: Session, faq: FAQCreate, file_path: Optional[str] = None, file_name: Optional[str] = None, file_size: Optional[int] = None, mime_type: Optional[str] = None, creator_id: Optional[int] = None) -> FAQ:
    """
    创建新常见问题
    
    创建常见问题时会自动设置创建人ID（如果提供），用于权限控制。
    常见问题信息包括文件路径、文件名、大小等元数据（附件类型）或富文本内容（富文本类型）。
    
    Args:
        db: 数据库会话对象
        faq: 常见问题创建模型，包含常见问题基本信息（标题、描述、模块、人员等）
        file_path: 文件相对路径（相对于项目根目录，仅附件类型需要）
        file_name: 原始文件名（用户上传时的文件名，仅附件类型需要）
        file_size: 文件大小（字节，仅附件类型需要）
        mime_type: MIME类型（可选，如application/pdf，仅附件类型需要）
        creator_id: 创建人ID（可选），如果提供则设置为常见问题的创建人
        
    Returns:
        FAQ: 创建成功的常见问题对象，包含所有常见问题信息和文件元数据或富文本内容
        
    Note:
        - 常见问题创建时会自动设置created_at和updated_at时间戳
        - 创建人ID用于后续的权限控制
        - 富文本类型不需要文件相关参数
    """
    db_faq = FAQ(
        **faq.model_dump(),
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        creator_id=creator_id
    )
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq


def get_faq(db: Session, faq_id: int) -> Optional[FAQ]:
    """
    根据ID获取常见问题
    
    Args:
        db: 数据库会话对象
        faq_id: 常见问题ID
        
    Returns:
        FAQ: 常见问题对象，如果不存在返回None
    """
    return db.query(FAQ).filter(FAQ.id == faq_id).first()


def search_faqs(db: Session, search: FAQSearch, user_id: Optional[int] = None, is_admin: bool = False) -> tuple[List[FAQ], int]:
    """
    搜索常见问题列表（支持关键词、类型、模块、人员筛选、分页和权限过滤）
    
    根据用户角色和权限过滤常见问题列表：
    - 管理员可以看到所有常见问题
    - 普通用户只能看到管理员创建的常见问题、自己创建的常见问题和没有创建人的常见问题
    
    Args:
        db: 数据库会话对象
        search: 搜索条件模型，包含所有筛选条件和分页信息
        user_id: 当前用户ID（可选，用于权限过滤）
        is_admin: 是否是管理员（用于权限过滤）
        
    Returns:
        tuple[List[FAQ], int]: (常见问题列表, 总记录数)
        
    权限规则说明：
    - 管理员（is_admin=True）：返回所有常见问题，不进行权限过滤
    - 普通用户（is_admin=False）：只能看到：
      * 自己创建的常见问题（creator_id == user_id）
      * 管理员创建的常见问题（creator_id在管理员ID列表中）
      * 没有创建人的常见问题（creator_id为None，兼容旧数据）
    """
    query = db.query(FAQ)
    
    # 关键词搜索（标题、简要描述）
    if search.keyword:
        keyword_pattern = f"%{search.keyword}%"
        query = query.filter(
            or_(
                FAQ.title.like(keyword_pattern),
                FAQ.description.like(keyword_pattern)
            )
        )
    
    # 文档类型筛选
    if search.document_type:
        query = query.filter(FAQ.document_type == search.document_type)
    
    # 模块筛选
    if search.module:
        query = query.filter(FAQ.module == search.module)
    
    # 人员筛选
    if search.person:
        query = query.filter(FAQ.person == search.person)
    
    # 权限过滤：普通用户只能看到有权限访问的常见问题
    if not is_admin and user_id is not None:
        # 获取所有管理员用户的ID列表（使用子查询提高性能）
        admin_users = db.query(User.id).filter(User.role == UserRole.ADMIN).subquery()
        
        # 过滤条件：当前用户创建的常见问题 OR 管理员创建的常见问题 OR 没有创建人的常见问题
        query = query.filter(
            (FAQ.creator_id == user_id) | 
            (FAQ.creator_id.in_(admin_users)) | 
            (FAQ.creator_id.is_(None))
        )
    
    # 获取总数
    total = query.count()
    
    # 分页
    skip = (search.page - 1) * search.page_size
    items = query.order_by(FAQ.created_at.desc()).offset(skip).limit(search.page_size).all()
    
    return items, total


def update_faq(db: Session, faq_id: int, faq_update: FAQUpdate) -> Optional[FAQ]:
    """
    更新常见问题信息
    
    Args:
        db: 数据库会话对象
        faq_id: 常见问题ID
        faq_update: 常见问题更新模型
        
    Returns:
        FAQ: 更新后的常见问题对象，如果不存在返回None
    """
    db_faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not db_faq:
        return None
    
    # 更新字段（只更新提供的字段）
    update_data = faq_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_faq, field, value)
    
    db.commit()
    db.refresh(db_faq)
    return db_faq


def delete_faq(db: Session, faq_id: int) -> bool:
    """
    删除常见问题
    
    删除指定的常见问题记录（不删除文件，文件需要单独删除）。
    
    Args:
        db: 数据库会话对象
        faq_id: 要删除的常见问题ID
        
    Returns:
        bool: 删除成功返回True，常见问题不存在返回False
    """
    db_faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not db_faq:
        return False
    
    db.delete(db_faq)
    db.commit()
    return True


# ========== 用户相关 CRUD 操作 ==========

def create_user(db: Session, user: UserCreate) -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话对象
        user: 用户创建模型
        
    Returns:
        User: 创建成功的用户对象
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise ValueError(f"用户名 {user.username} 已存在")
    
    # 创建用户对象（密码明文存储）
    db_user = User(
        username=user.username,
        password_hash=user.password if user.password else None,  # 如果没有密码，存储None
        name=user.name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: Optional[str] = None) -> Optional[User]:
    """
    验证用户登录（明文密码比较）
    
    Args:
        db: 数据库会话对象
        username: 用户名
        password: 密码（可选，可以为None或空字符串）
        
    Returns:
        Optional[User]: 验证成功返回用户对象，失败返回None
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not user.is_active:
        return None
    
    # 明文密码比较
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    更新用户信息
    
    Args:
        db: 数据库会话对象
        user_id: 用户ID
        user_update: 用户更新模型
        
    Returns:
        Optional[User]: 更新后的用户对象，如果不存在返回None
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # 更新字段
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        # 密码明文存储，如果为空则存储None
        password_value = update_data.pop("password")
        update_data["password_hash"] = password_value if password_value else None
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """
    删除用户
    
    Args:
        db: 数据库会话对象
        user_id: 用户ID
        
    Returns:
        bool: 删除成功返回True，用户不存在返回False
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

