"""
数据库模型定义模块

本模块定义了所有数据库表的ORM模型：
1. Interface - 接口表：存储接口基本信息
2. Parameter - 参数表：存储接口的入参和出参
3. Dictionary - 字典表：存储字典定义
4. DictionaryValue - 字典值表：存储字典的键值对

每个模型类对应数据库中的一张表，使用SQLAlchemy ORM进行映射。

作者: Auto
创建时间: 2024
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime, JSON, Unicode, UnicodeText
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum

# SQL Server 需要使用 Unicode 类型来支持中文
# Unicode 在 SQL Server 中映射为 NVARCHAR，支持 Unicode 字符（包括中文）
# 在其他数据库中，Unicode 等同于 String
# 对于存储中文的字段，统一使用 Unicode/UnicodeText


# ========== 枚举类型定义 ==========

class Project(Base):
    """
    项目表模型
    
    存储项目信息，每个项目可以包含多个接口和字典。
    项目是接口和字典的顶层分类，用于组织和管理相关的接口和字典。
    
    表名: projects
    
    字段说明:
    - id: 主键，自增
    - name: 项目名称（必填，最大200字符）
    - manager: 负责人（必填，最大100字符）
    - contact_info: 联系方式（必填，文本类型，可存储多个联系方式）
    - documents: 项目接口文档列表（JSON格式，存储多个文档信息）
                  每个文档包含：文档名称、文档版本、更新日期
    - description: 项目功能描述（可选，文本类型）
    - created_at: 创建时间（自动生成）
    - updated_at: 更新时间（自动更新）
    
    关联关系:
    - interfaces: 一对多关系，一个项目可以有多个接口
    - dictionaries: 一对多关系，一个项目可以有多个字典
    """
    __tablename__ = "projects"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 基本信息字段（使用 Unicode 支持中文）
    name = Column(Unicode(200), nullable=False, index=True, comment="项目名称，如'医保接口'、'首页上传'")
    manager = Column(Unicode(100), nullable=False, comment="负责人姓名")
    contact_info = Column(UnicodeText, nullable=False, comment="联系方式，可存储多个联系方式，每行一个或JSON格式")
    
    # 文档字段（JSON格式存储多个文档）
    # 格式示例：[{"name": "接口文档v1.0", "version": "1.0", "update_date": "2024-01-01"}, ...]
    documents = Column(JSON, nullable=True, comment="项目接口文档列表，JSON格式，包含文档名称、版本、更新日期")
    
    # 附件字段（JSON格式存储附件信息）
    # 格式示例：[{"filename": "文档.pdf", "stored_filename": "1704067200_文档.pdf", "file_path": "uploads/projects/1/1704067200_文档.pdf", "file_size": 1024000, "upload_time": "2024-01-01T10:00:00"}, ...]
    attachments = Column(JSON, nullable=True, comment="项目附件列表，JSON格式，包含文件名、存储路径、大小、上传时间等信息")
    
    # 描述字段（使用 UnicodeText 支持中文）
    description = Column(UnicodeText, comment="项目功能描述，详细说明项目的用途和功能")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间，每次修改时自动更新")
    
    # ========== 关联关系定义 ==========
    
    # 接口关联：一个项目可以有多个接口
    interfaces = relationship("Interface", back_populates="project", cascade="all, delete-orphan")
    
    # 字典关联：一个项目可以有多个字典
    dictionaries = relationship("Dictionary", back_populates="project", cascade="all, delete-orphan")


class InterfaceType(str, enum.Enum):
    """
    接口类型枚举
    
    用于区分不同类型的接口：
    - VIEW: 视图接口（通过数据库视图对接）
    - API: API接口（通过HTTP/HTTPS接口对接）
    """
    VIEW = "view"  # 视图接口：通过数据库视图进行数据对接
    API = "api"    # API接口：通过HTTP/HTTPS接口进行数据对接


class ParameterType(str, enum.Enum):
    """
    参数类型枚举
    
    用于区分参数的类型：
    - INPUT: 入参（接口的输入参数）
    - OUTPUT: 出参（接口的返回参数）
    """
    INPUT = "input"   # 入参：接口的输入参数
    OUTPUT = "output" # 出参：接口的返回参数


class Interface(Base):
    """
    接口表模型
    
    存储医院HIS系统的接口信息，包括视图接口和API接口。
    每个接口属于一个项目，可以包含多个参数（入参和出参），也可以关联多个字典。
    
    表名: interfaces
    
    字段说明:
    - id: 主键，自增
    - project_id: 所属项目ID（外键，必填）
    - name: 接口名称（必填，最大200字符）
    - code: 接口编码（必填，唯一，最大100字符，有索引）
    - description: 接口描述（可选，文本类型）
    - interface_type: 接口类型（必填，枚举：view/api）
    - url: 接口URL（可选，最大500字符）
    - method: HTTP方法（可选，如GET/POST/PUT/DELETE，仅API接口需要）
    - category: 接口分类（可选，最大100字符，如"患者管理"、"医嘱管理"）
    - tags: 标签（可选，最大500字符，多个标签用逗号分隔）
    - status: 状态（默认active，可选值：active/inactive）
    - created_at: 创建时间（自动生成）
    - updated_at: 更新时间（自动更新）
    
    关联关系:
    - project: 多对一关系，多个接口属于一个项目
    - parameters: 一对多关系，一个接口可以有多个参数
    - dictionaries: 一对多关系，一个接口可以关联多个字典（保留向后兼容）
    """
    __tablename__ = "interfaces"

    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 项目关联字段（新增）
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True, comment="所属项目ID，外键关联projects表")
    
    # 基本信息字段（使用 Unicode 支持中文）
    name = Column(Unicode(200), nullable=False, comment="接口名称，如'患者查询接口'")
    code = Column(Unicode(100), unique=True, nullable=False, index=True, comment="接口编码，唯一标识，可能包含中文，如'PATIENT_QUERY'或'患者查询'")
    description = Column(UnicodeText, comment="接口描述，详细说明接口的用途和功能")
    interface_type = Column(Enum(InterfaceType), nullable=False, comment="接口类型：view（视图接口）或api（API接口）")
    
    # URL和方法字段（主要用于API接口，使用 Unicode 支持中文路径）
    url = Column(Unicode(500), comment="接口URL，视图接口为视图名，API接口为HTTP地址，可能包含中文路径或参数")
    method = Column(String(10), comment="HTTP方法，仅API接口需要，如GET/POST/PUT/DELETE")
    
    # 分类和标签字段（用于组织和搜索，使用 Unicode 支持中文）
    category = Column(Unicode(100), comment="接口分类，如'患者管理'、'医嘱管理'、'收费管理'等")
    tags = Column(Unicode(500), comment="标签，多个标签用逗号分隔，如'患者,查询,常用'")
    
    # 状态字段
    status = Column(String(20), default="active", comment="状态：active（启用）或inactive（禁用）")
    
    # 参数样例字段（用于存储接口的入参和出参示例，使用 UnicodeText 支持中文）
    input_example = Column(UnicodeText, nullable=True, comment="入参样例，JSON或XML格式的示例数据")
    output_example = Column(UnicodeText, nullable=True, comment="出参样例，JSON或XML格式的示例数据")
    
    # 视图定义和备注说明字段（使用 UnicodeText 支持中文）
    view_definition = Column(UnicodeText, nullable=True, comment="视图定义，存储数据库视图的SQL定义，纯文本格式")
    notes = Column(UnicodeText, nullable=True, comment="备注说明，支持HTML格式，用于存储常见操作说明、错误提示等图文内容")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间，每次修改时自动更新")

    # ========== 关联关系定义 ==========
    
    # 项目关联：多个接口属于一个项目
    project = relationship("Project", back_populates="interfaces")
    
    # 参数关联：一个接口可以有多个参数（入参和出参）
    # cascade="all, delete-orphan": 删除接口时，自动删除所有关联的参数
    parameters = relationship("Parameter", back_populates="interface", cascade="all, delete-orphan")
    
    # 字典关联：一个接口可以关联多个字典（可选，保留向后兼容）
    dictionaries = relationship("Dictionary", back_populates="interface")


class Parameter(Base):
    """
    参数表模型（入参/出参）
    
    存储接口的输入参数和输出参数信息。
    每个参数可以关联一个字典，用于定义参数的取值范围。
    
    表名: parameters
    
    字段说明:
    - id: 主键，自增
    - interface_id: 所属接口ID（外键，必填）
    - name: 参数名称（必填，最大200字符，如"患者ID"）
    - field_name: 字段名（必填，最大100字符，如"patient_id"）
    - data_type: 数据类型（必填，如string/int/float/boolean/object/array）
    - param_type: 参数类型（必填，枚举：input/output）
    - required: 是否必填（默认False，仅入参有意义）
    - default_value: 默认值（可选，最大500字符）
    - description: 参数描述（可选，文本类型）
    - example: 示例值（可选，最大500字符）
    - order_index: 排序索引（默认0，用于控制参数显示顺序）
    - dictionary_id: 关联字典ID（可选，外键）
    - created_at: 创建时间（自动生成）
    
    关联关系:
    - interface: 多对一关系，多个参数属于一个接口
    - dictionary: 多对一关系，参数可以关联一个字典（可选）
    """
    __tablename__ = "parameters"

    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 接口关联字段
    interface_id = Column(Integer, ForeignKey("interfaces.id"), nullable=False, comment="所属接口ID，外键关联interfaces表")
    
    # 参数基本信息字段（name 和 field_name 使用 Unicode 支持中文）
    name = Column(Unicode(200), nullable=False, comment="参数名称，中文名称，如'患者ID'、'患者姓名'")
    field_name = Column(Unicode(100), nullable=False, comment="字段名，接口中的实际字段名，可能包含中文，如'patient_id'、'patient_name'或'患者ID'")
    data_type = Column(Unicode(50), nullable=False, comment="数据类型：string（字符串）/int（整数）/float（浮点数）/boolean（布尔值）/object（对象）/array（数组），可能包含中文")
    param_type = Column(Enum(ParameterType), nullable=False, comment="参数类型：input（入参）或output（出参）")
    
    # 入参特有字段（对出参无意义，但数据库字段统一）
    required = Column(Boolean, default=False, comment="是否必填，仅对入参有意义，True表示必填，False表示可选")
    default_value = Column(Unicode(500), comment="默认值，仅对入参有意义，当参数未提供时使用此默认值")
    
    # 描述和示例字段（使用 Unicode 支持中文）
    description = Column(UnicodeText, comment="参数描述，详细说明参数的用途、格式、约束等")
    example = Column(Unicode(500), comment="示例值，提供参数的示例数据，便于理解和使用")
    
    # 排序字段
    order_index = Column(Integer, default=0, comment="排序索引，用于控制参数在列表中的显示顺序，数字越小越靠前")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")

    # ========== 关联关系定义 ==========
    
    # 接口关联：多个参数属于一个接口
    interface = relationship("Interface", back_populates="parameters")
    
    # 字典关联：参数可以关联一个字典（可选）
    # 例如：性别参数可以关联性别字典，状态参数可以关联状态字典
    dictionary_id = Column(Integer, ForeignKey("dictionaries.id"), nullable=True, comment="关联字典ID，外键关联dictionaries表，可选")
    dictionary = relationship("Dictionary", back_populates="parameters")


class Dictionary(Base):
    """
    字典表模型
    
    存储字典定义信息。字典用于定义参数的取值范围，如性别、状态、类型等。
    每个字典属于一个项目，可以包含多个字典值（键值对），也可以关联到接口（可选）。
    
    表名: dictionaries
    
    字段说明:
    - id: 主键，自增
    - project_id: 所属项目ID（外键，必填）
    - name: 字典名称（必填，最大200字符，如"性别字典"）
    - code: 字典编码（必填，唯一，最大100字符，有索引，如"GENDER"）
    - description: 字典描述（可选，文本类型）
    - interface_id: 关联接口ID（可选，外键，保留向后兼容）
    - created_at: 创建时间（自动生成）
    - updated_at: 更新时间（自动更新）
    
    关联关系:
    - project: 多对一关系，多个字典属于一个项目
    - interface: 多对一关系，字典可以关联到一个接口（可选，保留向后兼容）
    - values: 一对多关系，一个字典可以有多个字典值
    - parameters: 一对多关系，多个参数可以关联到同一个字典
    """
    __tablename__ = "dictionaries"

    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 项目关联字段（新增）
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True, comment="所属项目ID，外键关联projects表")
    
    # 基本信息字段（使用 Unicode 支持中文）
    name = Column(Unicode(200), nullable=False, comment="字典名称，中文名称，如'性别字典'、'状态字典'")
    code = Column(Unicode(100), unique=True, nullable=False, index=True, comment="字典编码，唯一标识，可能包含中文，如'GENDER'、'STATUS'或'性别'、'状态'")
    description = Column(UnicodeText, comment="字典描述，说明字典的用途和适用场景")
    
    # 接口关联字段（可选，保留向后兼容）
    interface_id = Column(Integer, ForeignKey("interfaces.id"), nullable=True, comment="关联接口ID，外键关联interfaces表，可选，表示该字典专用于某个接口")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间，每次修改时自动更新")

    # ========== 关联关系定义 ==========
    
    # 项目关联：多个字典属于一个项目
    project = relationship("Project", back_populates="dictionaries")
    
    # 接口关联：字典可以关联到一个接口（可选，保留向后兼容）
    interface = relationship("Interface", back_populates="dictionaries")
    
    # 字典值关联：一个字典可以有多个字典值（键值对）
    # cascade="all, delete-orphan": 删除字典时，自动删除所有关联的字典值
    values = relationship("DictionaryValue", back_populates="dictionary", cascade="all, delete-orphan")
    
    # 参数关联：多个参数可以关联到同一个字典
    parameters = relationship("Parameter", back_populates="dictionary")


class DictionaryValue(Base):
    """
    字典值表模型
    
    存储字典的键值对信息。每个字典值属于一个字典，表示该字典的一个可选值。
    例如：性别字典可以有"1:男"和"2:女"两个字典值。
    
    表名: dictionary_values
    
    字段说明:
    - id: 主键，自增
    - dictionary_id: 所属字典ID（外键，必填）
    - key: 键（必填，最大100字符，如"1"、"MALE"）
    - value: 值（必填，最大500字符，如"男"、"男性"）
    - description: 描述（可选，文本类型）
    - order_index: 排序索引（默认0，用于控制字典值显示顺序）
    - created_at: 创建时间（自动生成）
    
    关联关系:
    - dictionary: 多对一关系，多个字典值属于一个字典
    """
    __tablename__ = "dictionary_values"

    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 字典关联字段
    dictionary_id = Column(Integer, ForeignKey("dictionaries.id"), nullable=False, comment="所属字典ID，外键关联dictionaries表")
    
    # 键值对字段（key、value 和 description 都使用 Unicode 支持中文）
    key = Column(Unicode(100), nullable=False, comment="键，字典值的键，可能包含中文，如'1'、'MALE'、'ACTIVE'或'男'、'启用'等")
    value = Column(Unicode(500), nullable=False, comment="值，字典值的值，如'男'、'男性'、'启用'等，通常是中文描述")
    description = Column(UnicodeText, comment="描述，对字典值的详细说明，可选")
    
    # 排序字段
    order_index = Column(Integer, default=0, comment="排序索引，用于控制字典值在列表中的显示顺序，数字越小越靠前")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")

    # ========== 关联关系定义 ==========
    
    # 字典关联：多个字典值属于一个字典
    dictionary = relationship("Dictionary", back_populates="values")


class DocumentType(str, enum.Enum):
    """
    文档类型枚举
    
    用于区分不同类型的文档：
    - PDF: PDF文档
    - IMAGE: 图片（截图）
    """
    PDF = "pdf"      # PDF文档
    IMAGE = "image"  # 图片（截图）


class Document(Base):
    """
    文档/截图表模型
    
    存储文档和截图信息，用于集中保存和管理。
    每个文档/截图包含标题、简要描述、地区、人员等信息。
    
    表名: documents
    
    字段说明:
    - id: 主键，自增
    - title: 标题（必填，最大200字符）
    - description: 简要描述（可选，文本类型）
    - region: 地区（可选，最大50字符）
    - person: 人员（可选，最大50字符）
    - document_type: 文档类型（必填，枚举：pdf/image）
    - file_path: 文件路径（必填，最大500字符）
    - file_name: 原始文件名（必填，最大200字符）
    - file_size: 文件大小（字节）
    - mime_type: MIME类型（可选，最大100字符，如application/pdf、image/png）
    - created_at: 创建时间（自动生成）
    - updated_at: 更新时间（自动更新）
    """
    __tablename__ = "documents"
    
    # 主键字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID，自增")
    
    # 基本信息字段（使用 Unicode 支持中文）
    title = Column(Unicode(200), nullable=False, index=True, comment="标题，用于搜索和显示")
    description = Column(UnicodeText, comment="简要描述，用于搜索和显示")
    
    # 来源信息字段（使用 Unicode 支持中文）
    region = Column(Unicode(50), comment="地区，文档/截图来源地区")
    person = Column(Unicode(50), comment="人员，文档/截图来源人员")
    
    # 文档类型字段
    document_type = Column(Enum(DocumentType), nullable=False, comment="文档类型：pdf（PDF文档）或image（图片/截图）")
    
    # 文件信息字段（使用 Unicode 支持中文路径和文件名）
    file_path = Column(Unicode(500), nullable=False, comment="文件相对路径，可能包含中文，如：uploads/documents/1/1704067200_文档.pdf")
    file_name = Column(Unicode(200), nullable=False, comment="原始文件名，可能包含中文")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    mime_type = Column(String(100), comment="MIME类型，如application/pdf、image/png、image/jpeg")
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间，自动记录")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间，每次修改时自动更新")
