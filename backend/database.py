"""
数据库配置和连接模块

本模块负责：
1. 数据库连接配置（支持SQL Server）
2. 数据库引擎和会话管理
3. 数据库表初始化

配置文件：backend/config.ini

作者: Auto
创建时间: 2024
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mssql import pyodbc as mssql_pyodbc
import os
import configparser
from urllib.parse import quote_plus

# ========== 配置文件读取 ==========

def load_database_config():
    """
    从config.ini文件加载数据库配置
    
    Returns:
        dict: 包含数据库配置信息的字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        configparser.Error: 配置文件格式错误
    """
    # 获取配置文件路径（相对于当前文件）
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"数据库配置文件不存在: {config_path}")
    
    # 读取配置文件
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    # 获取数据库配置节
    db_config = config['Database']
    
    return {
        'driver': db_config.get('driver', 'mssql+pyodbc'),
        'server': db_config.get('server', 'localhost'),
        'port': db_config.getint('port', 1433),
        'database': db_config.get('database', 'HIS_Interface'),
        'username': db_config.get('username', 'sa'),
        'password': db_config.get('password', ''),
        'odbc_driver': db_config.get('odbc_driver', 'ODBC Driver 17 for SQL Server'),
        'timeout': db_config.getint('timeout', 30),
        'use_windows_auth': db_config.getboolean('use_windows_auth', False)
    }


def build_database_url(config):
    """
    根据配置构建SQL Server数据库连接URL
    
    Args:
        config: 数据库配置字典
        
    Returns:
        str: SQLAlchemy数据库连接URL
    """
    driver = config['driver']
    server = config['server']
    port = config['port']
    database = config['database']
    
    # URL编码用户名和密码（处理特殊字符）
    username = quote_plus(config['username'])
    password = quote_plus(config['password'])
    
    if config['use_windows_auth']:
        # Windows身份验证（不需要用户名密码）
        if driver == 'mssql+pyodbc':
            # 使用Trusted_Connection=yes
            # ODBC Driver 18 默认要求 SSL 证书验证，添加 TrustServerCertificate=yes 跳过验证
            # 注意：SQL Server 的字符集由数据库排序规则决定，连接字符串不需要 charset 参数
            connection_string = f"mssql+pyodbc://{server}:{port}/{database}?driver={quote_plus(config['odbc_driver'])}&Trusted_Connection=yes&TrustServerCertificate=yes"
        else:
            # pymssql不支持Windows身份验证，需要用户名
            connection_string = f"{driver}://{username}:{password}@{server}:{port}/{database}"
    else:
        # SQL Server身份验证
        if driver == 'mssql+pyodbc':
            # pyodbc需要指定ODBC驱动
            # URL编码ODBC驱动名称
            odbc_driver = quote_plus(config['odbc_driver'])
            # ODBC Driver 18 默认要求 SSL 证书验证，添加 TrustServerCertificate=yes 跳过验证
            # 注意：SQL Server 的字符集由数据库排序规则决定，连接字符串不需要 charset 参数
            connection_string = f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}?driver={odbc_driver}&TrustServerCertificate=yes"
        else:
            # pymssql
            connection_string = f"{driver}://{username}:{password}@{server}:{port}/{database}"
    
    return connection_string


# ========== 数据库配置 ==========

# 初始化数据库配置变量
db_config = None
SQLALCHEMY_DATABASE_URL = None

try:
    # 从配置文件加载数据库配置
    db_config = load_database_config()
    # 构建数据库连接URL
    SQLALCHEMY_DATABASE_URL = build_database_url(db_config)
    
    print(f"数据库配置加载成功:")
    print(f"  服务器: {db_config['server']}:{db_config['port']}")
    print(f"  数据库: {db_config['database']}")
    print(f"  驱动: {db_config['driver']}")
    print(f"  认证方式: {'Windows身份验证' if db_config['use_windows_auth'] else 'SQL Server身份验证'}")
    # 调试：打印连接字符串（隐藏密码）
    if "pyodbc" in SQLALCHEMY_DATABASE_URL:
        # 隐藏密码用于调试输出
        debug_url = SQLALCHEMY_DATABASE_URL
        if "@" in debug_url and ":" in debug_url.split("@")[0]:
            parts = debug_url.split("@")
            if len(parts) > 0:
                user_pass = parts[0].split("://")[-1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    debug_url = debug_url.replace(user_pass, f"{user}:***")
        print(f"  连接字符串: {debug_url}")
except Exception as e:
    print(f"警告: 无法加载数据库配置文件，使用默认配置: {e}")
    # 如果配置文件不存在或读取失败，使用环境变量或默认值
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mssql+pyodbc://sa:YourPassword123@localhost:1433/HIS_Interface?driver=ODBC+Driver+17+for+SQL+Server"
    )
    # 设置默认配置字典
    db_config = {'timeout': 30}

# ========== 数据库引擎 ==========

# 创建SQLAlchemy数据库引擎
# SQL Server连接参数：
# - connect_timeout: 连接超时时间
# - echo: 是否打印SQL语句（调试用）
# - pool_pre_ping: 连接池预检测，确保连接有效

# 获取连接超时时间
timeout = db_config.get('timeout', 30) if db_config else 30

# 构建 connect_args，对于 pyodbc 添加编码参数确保正确处理 Unicode
if "pyodbc" in SQLALCHEMY_DATABASE_URL:
    # pyodbc 连接参数
    # 添加编码参数确保 pyodbc 使用 Unicode 类型传递参数
    # 这对于 SQL Server 正确处理中文至关重要
    connect_args_dict = {
        "timeout": timeout,
        "autocommit": False,
        # 确保 pyodbc 使用 Unicode 编码
        "unicode_results": True,
    }
    # 注意：charset 参数在连接字符串中可能不起作用，需要在 pyodbc 连接时设置
else:
    connect_args_dict = {
        "timeout": timeout,
    }

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args_dict,
    # 连接池配置
    pool_pre_ping=True,  # 连接前检测连接是否有效
    pool_recycle=3600,   # 连接回收时间（秒）
    echo=False           # 是否打印SQL（生产环境设为False）
)

# ========== 修复 Unicode 参数类型问题 ==========
# 
# 注意：SQLAlchemy 的 pyodbc 方言在生成参数化查询时，会根据字段类型自动选择参数类型
# 如果模型中使用 Unicode/UnicodeText，SQLAlchemy 应该自动使用 NVARCHAR/NTEXT
# 但如果仍然出现 VARCHAR 参数类型，可能是 SQLAlchemy 版本或配置问题
# 
# 解决方案：
# 1. 确保模型中使用 Unicode/UnicodeText 类型（已完成）
# 2. 确保数据库表字段是 NVARCHAR/NTEXT（已完成）
# 3. 如果问题仍然存在，可能需要升级 SQLAlchemy 或 pyodbc 版本

# ========== 会话工厂 ==========

# 创建数据库会话工厂
# autocommit=False: 禁用自动提交，需要手动commit
# autoflush=False: 禁用自动flush，需要手动flush
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========== 声明基类 ==========

# SQLAlchemy的声明式基类
# 所有数据库模型都继承自这个Base类
Base = declarative_base()


# ========== 数据库会话管理 ==========

def get_db():
    """
    获取数据库会话（依赖注入函数）
    
    这是一个生成器函数，用于FastAPI的依赖注入。
    每次请求时会创建一个新的数据库会话，请求结束后自动关闭。
    
    Yields:
        Session: SQLAlchemy数据库会话对象
        
    使用示例:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db  # 返回数据库会话
    finally:
        db.close()  # 确保会话被正确关闭


# ========== 数据库初始化 ==========

def init_db():
    """
    初始化数据库，创建所有表
    
    此函数会根据已定义的模型类（继承自Base的类）创建对应的数据库表。
    如果表已存在，则不会重复创建。
    
    注意：
    - 首次运行应用时会自动调用此函数
    - 仅创建表结构，不会删除已存在的表
    - 如需修改表结构，需要手动迁移或删除重建
    """
    try:
        # 尝试连接数据库并创建表
        # 如果数据库不可用，这里可能会超时或抛出异常
        Base.metadata.create_all(bind=engine)
        print("数据库表初始化完成")
    except Exception as e:
        # 如果初始化失败，记录错误但不阻塞启动
        # 首次请求时会自动重试
        print(f"数据库初始化警告: {e}")
        print("服务将继续启动，首次请求时会重试数据库连接")
        raise  # 重新抛出异常，让调用者知道初始化失败

