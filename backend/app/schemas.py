"""
Pydantic模型定义模块（用于API请求和响应验证）

本模块定义了所有API接口的请求和响应模型，使用Pydantic进行数据验证：
1. 请求模型（Create/Update）：用于接收客户端提交的数据
2. 响应模型：用于返回给客户端的数据格式
3. 搜索模型：用于查询条件的传递

Pydantic的优势：
- 自动数据验证
- 类型检查
- 自动生成API文档
- 数据序列化/反序列化

作者: Auto
创建时间: 2024
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, date
from backend.app.models import InterfaceType, ParameterType, DocumentType, UserRole

# 避免循环引用，使用字符串类型注解


# ========== 项目相关 Schema ==========

class ProjectDocument(BaseModel):
    """项目文档模型"""
    name: str = Field(..., description="文档名称")
    version: str = Field(..., description="文档版本")
    update_date: date = Field(..., description="更新日期")
    
    class Config:
        from_attributes = True


class ProjectAttachment(BaseModel):
    """项目附件模型"""
    filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储的文件名（带时间戳）")
    file_path: str = Field(..., description="文件相对路径")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: str = Field(..., description="上传时间（ISO格式）")
    category: str = Field("pdf", description="附件类别：pdf（可预览）或 other（仅下载）")
    can_preview: bool = Field(True, description="是否可以直接在线预览")
    
    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., description="项目名称")
    manager: str = Field(..., description="负责人")
    contact_info: str = Field(..., description="联系方式（可存储多个联系方式，每行一个）")
    documents: Optional[List[Dict[str, Any]]] = Field(default=[], description="项目接口文档列表，每个文档包含：name（文档名称）、version（文档版本）、update_date（更新日期）")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="项目附件列表：支持 pdf（可预览）与 other（仅下载）两类，每个附件包含 filename/stored_filename/file_path/file_size/upload_time/category/can_preview 等信息"
    )
    description: Optional[str] = Field(None, description="项目功能描述")


class ProjectCreate(ProjectBase):
    """创建项目"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目"""
    name: Optional[str] = None
    manager: Optional[str] = None
    contact_info: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None


class Project(ProjectBase):
    """项目响应模型"""
    id: int
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        # 排除关联关系字段，避免循环引用和数据库列不存在的问题
        exclude = {"interfaces", "dictionaries"}


class ProjectDetail(Project):
    """项目详情模型（包含接口和字典列表）"""
    interfaces_count: int = Field(0, description="接口数量")
    dictionaries_count: int = Field(0, description="字典数量")


# ========== 字典相关 Schema ==========
class DictionaryValueBase(BaseModel):
    """字典值基础模型"""
    key: str = Field(..., description="键")
    value: str = Field(..., description="值")
    description: Optional[str] = Field(None, description="描述")
    order_index: int = Field(0, description="排序索引")


class DictionaryValueCreate(DictionaryValueBase):
    """创建字典值"""
    pass


class DictionaryValue(DictionaryValueBase):
    """字典值响应模型"""
    id: int
    dictionary_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DictionaryBase(BaseModel):
    """字典基础模型"""
    project_id: int = Field(..., description="所属项目ID")
    name: str = Field(..., description="字典名称")
    code: str = Field(..., description="字典编码")
    description: Optional[str] = Field(None, description="字典描述")
    interface_id: Optional[int] = Field(None, description="关联接口ID（可选，保留向后兼容）")


class DictionaryCreate(DictionaryBase):
    """创建字典"""
    values: Optional[List[DictionaryValueCreate]] = Field(default=[], description="字典值列表")


class DictionaryUpdate(BaseModel):
    """更新字典"""
    project_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    interface_id: Optional[int] = None


class Dictionary(DictionaryBase):
    """字典响应模型"""
    id: int
    project: Optional[Project] = None
    values: List[DictionaryValue] = []
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 参数相关 Schema ==========
class ParameterBase(BaseModel):
    """参数基础模型"""
    name: str = Field(..., description="参数名称")
    field_name: str = Field(..., description="字段名")
    data_type: str = Field(..., description="数据类型")
    param_type: ParameterType = Field(..., description="参数类型")
    required: bool = Field(False, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    description: Optional[str] = Field(None, description="参数描述")
    example: Optional[str] = Field(None, description="示例值")
    order_index: int = Field(0, description="排序索引")
    dictionary_id: Optional[int] = Field(None, description="关联字典ID")


class ParameterCreate(ParameterBase):
    """创建参数"""
    pass


class ParameterUpdate(BaseModel):
    """更新参数"""
    name: Optional[str] = None
    field_name: Optional[str] = None
    data_type: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None
    order_index: Optional[int] = None
    dictionary_id: Optional[int] = None


class Parameter(ParameterBase):
    """参数响应模型"""
    id: int
    interface_id: int
    created_at: datetime
    dictionary: Optional[Dictionary] = None

    class Config:
        from_attributes = True


# ========== 接口相关 Schema ==========
class InterfaceBase(BaseModel):
    """接口基础模型"""
    # 为兼容历史数据，基础模型允许 project_id 为空
    project_id: Optional[int] = Field(None, description="所属项目ID")
    name: str = Field(..., description="接口名称")
    code: str = Field(..., description="接口编码")
    description: Optional[str] = Field(None, description="接口描述")
    interface_type: InterfaceType = Field(..., description="接口类型")
    url: Optional[str] = Field(None, description="接口URL")
    method: Optional[str] = Field(None, description="HTTP方法")
    category: Optional[str] = Field(None, description="接口分类")
    tags: Optional[str] = Field(None, description="标签（逗号分隔）")
    status: str = Field("active", description="状态")
    input_example: Optional[str] = Field(None, description="入参样例，JSON或XML格式的示例数据")
    output_example: Optional[str] = Field(None, description="出参样例，JSON或XML格式的示例数据")
    view_definition: Optional[str] = Field(None, description="视图定义，存储数据库视图的SQL定义，纯文本格式")
    notes: Optional[str] = Field(None, description="备注说明，支持HTML格式，用于存储常见操作说明、错误提示等图文内容")


class InterfaceCreate(InterfaceBase):
    """创建接口"""
    # 创建时必须提供 project_id
    project_id: int = Field(..., description="所属项目ID")
    parameters: Optional[List[ParameterCreate]] = Field(default=[], description="参数列表")


class InterfaceUpdate(BaseModel):
    """更新接口"""
    project_id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    interface_type: Optional[InterfaceType] = None
    url: Optional[str] = None
    method: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None
    input_example: Optional[str] = None
    output_example: Optional[str] = None
    view_definition: Optional[str] = None
    notes: Optional[str] = None
    parameters: Optional[List[ParameterCreate]] = Field(None, description="参数列表（可选，如果提供则替换所有参数）")


class Interface(InterfaceBase):
    """接口响应模型"""
    id: int
    project: Optional[Project] = None
    parameters: List[Parameter] = []
    dictionaries: List[Dictionary] = []
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 查询相关 Schema ==========
class InterfaceSearch(BaseModel):
    """接口搜索模型"""
    project_id: Optional[int] = Field(None, description="项目ID")
    keyword: Optional[str] = Field(None, description="关键词（搜索名称、编码、描述）")
    interface_type: Optional[InterfaceType] = Field(None, description="接口类型")
    category: Optional[str] = Field(None, description="分类")
    tags: Optional[str] = Field(None, description="标签")
    status: Optional[str] = Field(None, description="状态")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class InterfaceListResponse(BaseModel):
    """接口列表响应"""
    total: int
    page: int
    page_size: int
    items: List[Interface]


# ========== 文档/截图相关 Schema ==========

class DocumentAttachment(BaseModel):
    """文档附件模型"""
    filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储的文件名（带时间戳）")
    file_path: str = Field(..., description="文件相对路径")
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    upload_time: str = Field(..., description="上传时间（ISO格式）")
    
    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="简要描述")
    region: Optional[str] = Field(None, max_length=50, description="地区")
    person: Optional[str] = Field(None, max_length=50, description="人员")
    document_type: DocumentType = Field(..., description="文档类型")


class DocumentCreate(DocumentBase):
    """创建文档"""
    pass


class DocumentUpdate(BaseModel):
    """更新文档"""
    title: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = Field(None, max_length=50)
    person: Optional[str] = Field(None, max_length=50)


class Document(DocumentBase):
    """文档响应模型"""
    id: int
    file_path: Optional[str] = Field(None, description="文件路径（向后兼容字段，新数据使用attachments）")
    file_name: Optional[str] = Field(None, description="文件名（向后兼容字段，新数据使用attachments）")
    file_size: Optional[int] = Field(None, description="文件大小（向后兼容字段，新数据使用attachments）")
    mime_type: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = Field(default=[], description="附件列表，JSON格式，包含文件名、存储路径、大小、MIME类型、上传时间等信息")
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentSearch(BaseModel):
    """文档搜索模型"""
    keyword: Optional[str] = Field(None, description="关键词（搜索标题、简要描述）")
    document_type: Optional[DocumentType] = Field(None, description="文档类型")
    region: Optional[str] = Field(None, description="地区")
    person: Optional[str] = Field(None, description="人员")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    page: int
    page_size: int
    items: List[Document]


# ========== 常见问题相关 Schema ==========

class FAQAttachment(BaseModel):
    """常见问题附件模型"""
    filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储的文件名（带时间戳）")
    file_path: str = Field(..., description="文件相对路径")
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    upload_time: str = Field(..., description="上传时间（ISO格式）")
    
    class Config:
        from_attributes = True


class FAQBase(BaseModel):
    """常见问题基础模型"""
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="简要描述")
    module: Optional[str] = Field(None, max_length=50, description="模块")
    person: Optional[str] = Field(None, max_length=50, description="人员")
    document_type: DocumentType = Field(..., description="文档类型")


class FAQCreate(FAQBase):
    """创建常见问题"""
    pass


class FAQUpdate(BaseModel):
    """更新常见问题"""
    title: Optional[str] = None
    description: Optional[str] = None
    module: Optional[str] = Field(None, max_length=50)
    person: Optional[str] = Field(None, max_length=50)


class FAQ(FAQBase):
    """常见问题响应模型"""
    id: int
    file_path: Optional[str] = Field(None, description="文件路径（向后兼容字段，新数据使用attachments）")
    file_name: Optional[str] = Field(None, description="文件名（向后兼容字段，新数据使用attachments）")
    file_size: Optional[int] = Field(None, description="文件大小（向后兼容字段，新数据使用attachments）")
    mime_type: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = Field(default=[], description="附件列表，JSON格式，包含文件名、存储路径、大小、MIME类型、上传时间等信息")
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FAQSearch(BaseModel):
    """常见问题搜索模型"""
    keyword: Optional[str] = Field(None, description="关键词（搜索标题、简要描述）")
    document_type: Optional[DocumentType] = Field(None, description="文档类型")
    module: Optional[str] = Field(None, description="模块")
    person: Optional[str] = Field(None, description="人员")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class FAQListResponse(BaseModel):
    """常见问题列表响应"""
    total: int
    page: int
    page_size: int
    items: List[FAQ]


# ========== 用户相关 Schema ==========

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., description="用户名", max_length=50)
    name: str = Field(..., description="姓名", max_length=100)
    role: UserRole = Field(UserRole.USER, description="用户角色")


class UserCreate(UserBase):
    """创建用户"""
    password: Optional[str] = Field(None, description="密码（可选，不限制长度）")


class UserUpdate(BaseModel):
    """更新用户"""
    name: Optional[str] = Field(None, description="姓名", max_length=100)
    password: Optional[str] = Field(None, description="密码（可选，不限制长度）")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否启用")


class User(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: Optional[str] = Field(None, description="密码（可选）")


class Token(BaseModel):
    """Token响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: User = Field(..., description="用户信息")

