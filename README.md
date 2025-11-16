# 医院HIS系统接口文档管理系统

## 项目简介

这是一个专门用于管理医院HIS系统接口文档的系统，支持：
- 接口信息管理（视图接口、API接口）
- 接口规范文档（入参、出参、字典）
- 快速查询和搜索
- 数据导入导出

## 技术栈

### 后端
- **FastAPI**: 高性能Python Web框架
- **SQLAlchemy**: ORM数据库操作
- **SQL Server**: 数据库（通过ODBC驱动连接）
- **Pydantic**: 数据验证

### 前端
- **Vue 3**: 前端框架
- **Element Plus**: UI组件库
- **Axios**: HTTP客户端

## 项目结构

```
HIS_interface/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── models.py     # 数据库模型
│   │   ├── schemas.py    # Pydantic模型
│   │   ├── crud.py       # 数据库操作
│   │   ├── api/          # API路由
│   │   └── main.py       # FastAPI应用入口
│   ├── database.py       # 数据库配置
│   ├── config.ini        # 数据库配置文件
│   └── requirements.txt  # 依赖包
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   ├── components/   # 通用组件
│   │   ├── api/          # API调用
│   │   └── main.js       # 入口文件
│   └── package.json
├── venv/                 # Python虚拟环境（不提交到版本控制）
├── data/                 # 数据文件（导入导出）
├── setup_venv.bat        # 创建虚拟环境脚本
├── activate_venv.bat     # 激活虚拟环境脚本
├── start_backend.bat     # 启动后端服务脚本
├── start_frontend.bat    # 启动前端服务脚本
└── README.md

```

## 快速开始

### 环境要求
- Python 3.8+（推荐Python 3.11或3.12，Python 3.13可能遇到pyodbc编译问题）
- Node.js 16+
- npm 或 yarn
- SQL Server 2012或更高版本
- ODBC Driver for SQL Server（如果使用pyodbc）
- Windows CMD（Windows系统）

**注意**: 如果使用Python 3.13，pyodbc可能需要预编译wheel文件或使用pymssql替代。详见 `backend/PYODBC_INSTALL.md`

### 1. 创建Python虚拟环境（推荐）

**Windows CMD:**

```cmd
setup_venv.bat
```

**手动创建（如果脚本无法运行）:**

```cmd
REM 创建虚拟环境
python -m venv venv

REM 激活虚拟环境
venv\Scripts\activate.bat

REM 设置编码环境变量（防止乱码）
set PYTHONIOENCODING=utf-8
chcp 65001

REM 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..
```

**如果pyodbc安装失败**，请参考：
- `backend/PYODBC_INSTALL.md` - pyodbc安装问题解决
- `fix_pyodbc.bat` - 自动修复脚本

### 2. 安装前端依赖（如果未安装）
```cmd
cd frontend
npm install
cd ..
```

### 3. 配置数据库连接

**方式一：使用配置文件（推荐）**

1. 复制配置文件模板：
```cmd
cd backend
copy config.ini.example config.ini
```

2. 编辑 `backend/config.ini`，修改数据库连接信息：
```ini
[Database]
server = localhost          # SQL Server服务器地址
port = 1433                # 端口
database = HIS_Interface   # 数据库名
username = sa              # 用户名
password = YourPassword    # 密码
odbc_driver = ODBC Driver 17 for SQL Server
```

**方式二：使用环境变量**

设置环境变量 `DATABASE_URL`：
```cmd
set DATABASE_URL=mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server
```

### 4. 创建数据库

在SQL Server中创建数据库：
```sql
CREATE DATABASE HIS_Interface;
```

### 5. 初始化数据库表
首次运行后端服务会自动创建数据库表。

### 6. 启动后端服务

**Windows CMD（推荐）:**
```cmd
start_backend.bat
```

**Linux/Mac:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**手动启动（确保虚拟环境已激活）:**
```cmd
REM 激活虚拟环境
venv\Scripts\activate.bat

REM 启动服务
cd backend
python -m uvicorn backend.app.main:app --reload --port 8000
```

后端服务启动后，访问 http://localhost:8000/docs 查看API文档

### 7. 启动前端服务

**Windows CMD（推荐）:**
```cmd
start_frontend.bat
```

**Linux/Mac:**
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

**手动启动:**
```cmd
cd frontend
npm run dev
```

访问 http://localhost:5173 查看界面

## 虚拟环境使用说明

### 激活虚拟环境

每次打开新的CMD终端时，需要先激活虚拟环境：

```cmd
activate_venv.bat
```

或者手动激活：
```cmd
venv\Scripts\activate.bat
```

激活后，终端提示符前会显示 `(venv)`。

### 停用虚拟环境

```cmd
deactivate
```

### 常用命令

```cmd
REM 查看Python版本
python --version

REM 查看已安装的包
pip list

REM 安装新包
pip install package_name

REM 更新依赖
pip install --upgrade -r backend\requirements.txt

REM 更新requirements.txt
pip freeze > backend\requirements.txt
```

## 功能特性

### 1. 接口管理
- 支持视图接口和API接口两种类型
- 接口基本信息（名称、描述、URL、方法等）
- 接口分类和标签

### 2. 参数管理
- 入参管理（字段名、类型、必填、默认值、描述）
- 出参管理（字段名、类型、描述）
- 参数字典关联

### 3. 字典管理
- 字典定义（名称、编码、描述）
- 字典值管理（键值对）

### 4. 查询功能
- 全文搜索（接口名、描述、参数）
- 分类筛选
- 标签筛选
- 高级查询（按类型、状态等）

### 5. 数据导入导出
- Excel格式导入导出
- JSON格式导入导出
- 批量操作

## API文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 数据库设计

### 核心表结构
- **interfaces**: 接口表
- **parameters**: 参数表（入参/出参）
- **dictionaries**: 字典表
- **dictionary_values**: 字典值表

详见 `backend/app/models.py`

## 使用示例

### 添加一个接口

1. 点击"新增接口"按钮
2. 填写接口基本信息：
   - 接口编码：`PATIENT_QUERY`
   - 接口名称：`患者查询接口`
   - 接口类型：选择 `API接口`
   - HTTP方法：选择 `POST`
   - URL：`/api/patient/query`
   - 分类：`患者管理`
3. 添加入参：
   - 字段名：`patient_id`，类型：`string`，必填：是
   - 字段名：`name`，类型：`string`，必填：否
4. 添加出参：
   - 字段名：`patient_info`，类型：`object`
   - 字段名：`status`，类型：`string`
5. 保存

### 搜索接口

1. 在接口列表页的搜索栏输入关键词，如"患者"
2. 可以选择接口类型、分类进行筛选
3. 点击搜索按钮查看结果

### 导出数据

访问后端API：
- JSON格式：http://localhost:8000/api/import-export/export/json
- Excel格式：http://localhost:8000/api/import-export/export/excel

## 其他工具推荐

如果不想自建系统，也可以考虑以下工具：

### 1. Postman
- 适合API接口管理
- 支持接口测试
- 缺点：不支持视图接口，字典管理不便

### 2. Swagger/OpenAPI
- 标准化的API文档
- 需要代码中维护
- 不适合已有文档整理

### 3. Confluence/Wiki
- 文档管理方便
- 搜索功能强大
- 缺点：结构化数据管理不便

**但推荐使用自建系统，因为：**
- ✅ 完全符合业务需求
- ✅ 支持视图接口和API接口统一管理
- ✅ 完善的字典管理
- ✅ 灵活的查询功能

## 常见问题

### Q: 虚拟环境激活失败？
A: 
1. 确保虚拟环境已创建：运行 `setup_venv.bat`
2. 检查虚拟环境目录是否存在：`dir venv`
3. 如果不存在，重新运行 `setup_venv.bat`

### Q: 如何修改数据库连接？
A: 修改 `backend/config.ini` 文件中的数据库配置，包括服务器地址、端口、数据库名、用户名、密码等。

### Q: 如何安装ODBC驱动？
A: 
- Windows: 从Microsoft官网下载并安装 "ODBC Driver 17 for SQL Server"
- Linux: 按照Microsoft文档安装相应驱动
- 或者使用pymssql驱动（不需要ODBC驱动），修改config.ini中的driver为mssql+pymssql

### Q: 如何使用Windows身份验证？
A: 在config.ini中设置 `use_windows_auth = True`，并确保运行程序的Windows用户有SQL Server访问权限。

### Q: 如何修改端口？
A: 
- 后端：修改启动命令中的 `--port` 参数
- 前端：修改 `frontend/vite.config.js` 中的 `server.port`

### Q: 如何确认虚拟环境已激活？
A: 
- 终端提示符前应该显示 `(venv)`
- 运行 `where python` 应该指向 `venv\Scripts\python.exe`

### Q: 如何添加新的Python依赖？
A: 
```cmd
REM 激活虚拟环境
venv\Scripts\activate.bat

REM 安装新包
pip install package_name

REM 更新requirements.txt
pip freeze > backend\requirements.txt
```

## 开发计划

- [ ] 接口版本管理
- [ ] 接口变更历史
- [ ] 接口测试功能
- [ ] 权限管理
- [ ] 数据导入功能完善
- [ ] 接口文档自动生成（Markdown/PDF）

## 许可证

MIT License
