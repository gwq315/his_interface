# 医院HIS系统接口文档管理系统 - 设计文档

## 一、项目概述

### 1.1 业务背景
医院HIS系统需要对接各种外部接口，包括：
- 视图接口（通过数据库视图对接）
- API接口（通过HTTP/HTTPS接口对接）

每个接口都有：
- 接口规范文档
- 入参定义
- 出参定义
- 关联字典

需要一个统一的管理系统来：
- 集中管理所有接口文档
- 快速查询接口信息
- 维护接口规范
- 管理字典数据

### 1.2 解决方案

#### 方案一：使用现有工具
**推荐工具：**
1. **Postman** - API文档管理
   - 优点：功能强大，支持接口测试
   - 缺点：不适合视图接口，字典管理不便
   
2. **Swagger/OpenAPI** - API文档
   - 优点：标准规范，自动生成文档
   - 缺点：需要代码中维护，不适合已有接口文档整理

3. **Confluence/Wiki** - 文档管理
   - 优点：易于使用，搜索方便
   - 缺点：结构化数据管理不便，查询不够灵活

4. **自建系统** ✅ **推荐**
   - 优点：完全定制，符合业务需求，支持视图和API，字典管理完善
   - 缺点：需要开发维护

#### 方案二：自建系统（本方案）

## 二、系统架构设计

### 2.1 技术选型

**后端：**
- FastAPI：高性能Python Web框架，自动生成API文档
- SQLAlchemy：ORM框架，支持多种数据库
- SQLite/PostgreSQL：数据库（开发用SQLite，生产用PostgreSQL）

**前端：**
- Vue 3：现代化前端框架
- Element Plus：企业级UI组件库
- Axios：HTTP客户端

### 2.2 数据库设计

#### 核心表结构

1. **interfaces（接口表）**
   - 存储接口基本信息
   - 支持视图接口和API接口两种类型
   - 包含分类、标签等元数据

2. **parameters（参数表）**
   - 存储接口的入参和出参
   - 关联到接口和字典
   - 支持排序和必填标识

3. **dictionaries（字典表）**
   - 存储字典定义
   - 可关联到接口（可选）

4. **dictionary_values（字典值表）**
   - 存储字典的键值对
   - 支持排序

### 2.3 功能模块

#### 1. 接口管理
- 接口CRUD操作
- 接口分类和标签
- 接口状态管理（启用/禁用）

#### 2. 参数管理
- 入参管理（字段、类型、必填、默认值）
- 出参管理（字段、类型、描述）
- 参数与字典关联

#### 3. 字典管理
- 字典定义
- 字典值管理
- 字典关联

#### 4. 查询功能
- 全文搜索（接口名、编码、描述）
- 分类筛选
- 标签筛选
- 类型筛选（视图/API）
- 分页查询

#### 5. 数据导入导出
- JSON格式导入导出
- Excel格式导入导出
- 批量操作

## 三、API设计

### 3.1 接口管理API

```
GET    /api/interfaces/              # 获取接口列表
POST   /api/interfaces/              # 创建接口
GET    /api/interfaces/{id}          # 获取接口详情
PUT    /api/interfaces/{id}          # 更新接口
DELETE /api/interfaces/{id}          # 删除接口
GET    /api/interfaces/code/{code}   # 根据编码获取接口
POST   /api/interfaces/search        # 搜索接口
```

### 3.2 参数管理API

```
GET    /api/parameters/interface/{interface_id}  # 获取接口参数
POST   /api/parameters/interface/{interface_id}  # 创建参数
GET    /api/parameters/{id}                       # 获取参数详情
PUT    /api/parameters/{id}                       # 更新参数
DELETE /api/parameters/{id}                       # 删除参数
```

### 3.3 字典管理API

```
GET    /api/dictionaries/              # 获取字典列表
POST   /api/dictionaries/              # 创建字典
GET    /api/dictionaries/{id}          # 获取字典详情
PUT    /api/dictionaries/{id}          # 更新字典
DELETE /api/dictionaries/{id}          # 删除字典
GET    /api/dictionaries/code/{code}   # 根据编码获取字典
GET    /api/dictionaries/{id}/values   # 获取字典值列表
```

### 3.4 导入导出API

```
GET  /api/import-export/export/json   # 导出JSON
GET  /api/import-export/export/excel  # 导出Excel
POST /api/import-export/import/json   # 导入JSON（待实现）
POST /api/import-export/import/excel  # 导入Excel（待实现）
```

## 四、前端界面设计

### 4.1 页面结构

1. **接口列表页**
   - 搜索栏（关键词、类型、分类）
   - 接口列表表格
   - 分页组件
   - 操作按钮（查看、编辑、删除）

2. **接口详情页**
   - 接口基本信息
   - 入参表格
   - 出参表格
   - 关联字典

3. **接口表单页**
   - 接口基本信息表单
   - 入参管理（表格编辑）
   - 出参管理（表格编辑）

4. **字典管理页**
   - 字典列表
   - 字典值查看

### 4.2 UI特性

- 响应式设计，支持不同屏幕尺寸
- 清晰的表格展示
- 便捷的搜索和筛选
- 友好的操作提示

## 五、使用场景

### 5.1 添加新接口
1. 进入"新增接口"页面
2. 填写接口基本信息（编码、名称、类型、URL等）
3. 添加入参和出参
4. 关联字典（可选）
5. 保存

### 5.2 查询接口
1. 在接口列表页使用搜索功能
2. 可以按关键词、类型、分类筛选
3. 点击接口查看详细信息

### 5.3 导出数据
1. 访问导出API或前端导出按钮
2. 选择导出格式（JSON/Excel）
3. 下载文件

## 六、扩展建议

### 6.1 功能扩展
- 接口版本管理
- 接口变更历史
- 接口测试功能
- 接口调用日志
- 权限管理
- 接口文档自动生成（Markdown/PDF）

### 6.2 性能优化
- 数据库索引优化
- 缓存机制（Redis）
- 全文搜索（Elasticsearch）
- 分页优化

### 6.3 部署建议
- 使用Docker容器化部署
- 使用Nginx反向代理
- 数据库使用PostgreSQL
- 配置定期备份

## 七、对比其他方案

| 特性 | 自建系统 | Postman | Swagger | Confluence |
|------|---------|---------|---------|------------|
| 视图接口支持 | ✅ | ❌ | ❌ | ✅ |
| 字典管理 | ✅ | ❌ | ❌ | ⚠️ |
| 结构化查询 | ✅ | ⚠️ | ⚠️ | ⚠️ |
| 自定义字段 | ✅ | ⚠️ | ⚠️ | ✅ |
| 成本 | 开发成本 | 免费/付费 | 免费 | 付费 |
| 维护 | 需要 | 无需 | 需要 | 无需 |

**结论：** 对于医院HIS系统的接口文档管理需求，自建系统是最佳选择，因为：
1. 支持视图接口和API接口统一管理
2. 完善的字典管理功能
3. 灵活的查询和筛选
4. 完全符合业务需求

