"""
数据库迁移脚本：添加project_id字段

此脚本用于在现有数据库中添加project_id字段。
如果数据库可以重建，建议直接删除重建（更简单）。

执行方式：
1. 使用SQL Server Management Studio (SSMS)执行
2. 或者使用Python脚本执行（见下方）

作者: Auto
创建时间: 2024
"""

import pyodbc
import configparser
import os
from pathlib import Path

def load_database_config():
    """加载数据库配置"""
    config_path = Path(__file__).parent / "config.ini"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    db_config = config['Database']
    
    return {
        'server': db_config.get('server', 'localhost'),
        'port': db_config.getint('port', 1433),
        'database': db_config.get('database', 'HIS_Interface'),
        'username': db_config.get('username', 'sa'),
        'password': db_config.get('password', ''),
        'odbc_driver': db_config.get('odbc_driver', 'ODBC Driver 17 for SQL Server'),
        'use_windows_auth': db_config.getboolean('use_windows_auth', False)
    }

def get_connection_string(config):
    """构建连接字符串"""
    if config['use_windows_auth']:
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['server']},{config['port']};DATABASE={config['database']};Trusted_Connection=yes;"
    else:
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['server']},{config['port']};DATABASE={config['database']};UID={config['username']};PWD={config['password']};"

def execute_migration():
    """执行迁移"""
    try:
        config = load_database_config()
        conn_str = get_connection_string(config)
        
        print("正在连接数据库...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print("开始执行数据库迁移...")
        
        # 1. 创建projects表
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[projects]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[projects] (
                    [id] INT IDENTITY(1,1) PRIMARY KEY,
                    [name] NVARCHAR(200) NOT NULL,
                    [manager] NVARCHAR(100) NOT NULL,
                    [contact_info] NTEXT NOT NULL,
                    [documents] NVARCHAR(MAX) NULL,
                    [description] NTEXT NULL,
                    [created_at] DATETIME2 DEFAULT GETDATE(),
                    [updated_at] DATETIME2 DEFAULT GETDATE()
                )
                CREATE INDEX IX_projects_name ON [dbo].[projects]([name])
                PRINT 'Projects表创建成功'
            END
        """)
        conn.commit()
        print("✓ Projects表检查完成")
        
        # 2. 添加interfaces表的project_id列
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[interfaces]') AND name = 'project_id')
            BEGIN
                ALTER TABLE [dbo].[interfaces] ADD [project_id] INT NULL
                CREATE INDEX IX_interfaces_project_id ON [dbo].[interfaces]([project_id])
                PRINT '已添加interfaces.project_id列'
            END
        """)
        conn.commit()
        print("✓ Interfaces表迁移完成")
        
        # 3. 添加dictionaries表的project_id列
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[dictionaries]') AND name = 'project_id')
            BEGIN
                ALTER TABLE [dbo].[dictionaries] ADD [project_id] INT NULL
                CREATE INDEX IX_dictionaries_project_id ON [dbo].[dictionaries]([project_id])
                PRINT '已添加dictionaries.project_id列'
            END
        """)
        conn.commit()
        print("✓ Dictionaries表迁移完成")
        
        cursor.close()
        conn.close()
        
        print("\n数据库迁移完成！")
        print("注意：如果interfaces和dictionaries表中有旧数据，需要手动设置project_id")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        raise

if __name__ == "__main__":
    execute_migration()

