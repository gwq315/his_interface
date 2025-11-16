# 更新日志 - 2024

## 本次更新内容总结

### 1. 列表排序优化
**需求**：项目管理列表、接口列表、字典列表查询后按ID升序显示，新增加的在最后。

**修改文件**：
- `backend/app/crud.py`

**修改内容**：
- `get_projects()`: 改为 `order_by(Project.id.asc())`
- `get_interfaces()`: 改为 `order_by(Interface.id.asc())`
- `search_interfaces()`: 改为 `order_by(Interface.id.asc())`
- `get_dictionaries()`: 改为 `order_by(Dictionary.id.asc())`

---

### 2. 参数批量导入导出功能
**需求**：在新增/编辑接口页面，入参和出参支持批量导入和导出，提高录入效率。

**修改文件**：
- `frontend/src/components/ParameterTable.vue`

**新增功能**：
- **批量导入**：
  - 支持从 Excel 复制（制表符分隔）
  - 支持 CSV 格式（逗号分隔）
  - 支持竖线分隔（|）和空格分隔
  - 自动识别分隔符和表头
  - 自动解析数据类型（varchar、int、string 等）
  - 自动解析必填字段（是/否、yes/no 等）
  - 实时预览解析结果
- **导出功能**：
  - 导出为 CSV 格式（制表符分隔）
  - 文件名格式：`入参_YYYY-MM-DD.csv` 或 `出参_YYYY-MM-DD.csv`

**列顺序**：字段名 | 参数名称 | 数据类型 | 默认值/长度 | 必填 | 描述 | 示例

---

### 3. 时间戳字段修复
**问题**：创建接口时，`interfaces` 表的 `created_at`、`updated_at` 和 `parameters` 表的 `created_at` 都是 null。

**修改文件**：
- `backend/app/crud.py`

**修复内容**：
- `create_interface()`: 显式设置 `created_at` 和 `updated_at` 为当前时间
- 创建参数时显式设置 `created_at` 为当前时间
- `update_interface()`: 更新参数时设置 `created_at`，更新接口时设置 `updated_at`

---

### 4. 搜索接口序列化问题修复
**问题**：搜索接口时返回 500 错误，响应序列化失败。

**修改文件**：
- `backend/app/api/interfaces.py`

**修复内容**：
- 使用 Pydantic 的 `model_validate` 方法创建 Interface 对象
- 添加错误处理和日志记录
- 确保所有字段（包括 `input_example`、`output_example`）都被正确映射

---

### 5. 创建接口参数验证优化
**问题**：创建接口时，空参数导致验证失败。

**修改文件**：
- `frontend/src/views/InterfaceForm.vue`
- `frontend/src/api/index.js`

**优化内容**：
- 过滤掉完全空的参数（name 和 field_name 都为空）
- 确保必需字段不为空（提供默认值）
- 将空字符串的可选字段改为 null
- 改进错误处理，显示详细的验证错误信息
- 优化数据类型转换（Boolean、Number）

---

### 6. 新增视图定义和备注说明字段
**需求**：在接口新增/编辑页面添加"视图定义"和"备注说明"两个标签页。

**数据库迁移**：
- `backend/migrations/add_view_definition_and_notes_to_interfaces.sql`
  - 添加 `view_definition` 字段（TEXT，存储数据库视图的SQL定义）
  - 添加 `notes` 字段（TEXT，存储HTML格式的备注说明）

**后端修改**：
- `backend/app/models.py`: 添加两个字段到 Interface 模型
- `backend/app/schemas.py`: 添加两个字段到 InterfaceBase、InterfaceCreate、InterfaceUpdate
- `backend/app/crud.py`: 更新创建接口逻辑，保存新字段

**前端修改**：
- `frontend/src/views/InterfaceForm.vue`:
  - 安装富文本编辑器：`quill` 和 `@vueup/vue-quill`
  - 添加"视图定义"标签页：大文本输入框（25行），等宽字体
  - 添加"备注说明"标签页：Quill 富文本编辑器，支持图文混排
  - 更新表单数据模型、加载逻辑和保存逻辑

**富文本编辑器功能**：
- 标题（H1-H6）
- 文本格式（粗体、斜体、下划线、删除线）
- 颜色和背景色
- 列表（有序、无序）
- 对齐方式
- 链接、图片、视频
- 引用、代码块
- 清除格式

---

### 7. 界面优化：示例字段移到标签页
**需求**：将"入参示例"和"出参示例"移到标签页中，使界面更简洁。

**修改文件**：
- `frontend/src/views/InterfaceForm.vue`

**优化内容**：
- 移除标签页外的示例输入区域
- 在标签页中新增"入参示例"和"出参示例"两个标签
- 示例输入框从 4 行增加到 20 行，使用等宽字体

**最终标签页顺序**：
1. 入参
2. 出参
3. 入参示例
4. 出参示例
5. 视图定义
6. 备注说明

---

## 技术栈

### 后端
- FastAPI
- SQLAlchemy ORM
- Pydantic 数据验证

### 前端
- Vue 3
- Element Plus UI
- Vue Router
- Quill 富文本编辑器（@vueup/vue-quill）

---

## 数据库变更

### 新增字段
- `interfaces.view_definition` (TEXT, nullable)
- `interfaces.notes` (TEXT, nullable)

### 迁移脚本
执行 `backend/migrations/add_view_definition_and_notes_to_interfaces.sql` 添加新字段。

---

## 注意事项

1. **数据库迁移**：需要执行迁移脚本添加新字段
2. **富文本编辑器**：已安装 `quill` 和 `@vueup/vue-quill`，确保前端依赖已更新
3. **时间戳**：创建和更新接口时会自动设置时间戳，无需手动处理
4. **参数验证**：空参数会被自动过滤，必需字段会自动填充默认值

---

## 文件清单

### 后端文件
- `backend/app/models.py` - Interface 模型添加新字段
- `backend/app/schemas.py` - Schema 添加新字段
- `backend/app/crud.py` - CRUD 操作更新
- `backend/app/api/interfaces.py` - 搜索接口序列化修复
- `backend/migrations/add_view_definition_and_notes_to_interfaces.sql` - 数据库迁移脚本

### 前端文件
- `frontend/src/components/ParameterTable.vue` - 批量导入导出功能
- `frontend/src/views/InterfaceForm.vue` - 表单优化和新字段
- `frontend/src/api/index.js` - API 错误处理优化
- `frontend/package.json` - 新增依赖（quill, @vueup/vue-quill）

---

## 待办事项

1. ✅ 列表排序优化
2. ✅ 参数批量导入导出
3. ✅ 时间戳字段修复
4. ✅ 搜索接口序列化修复
5. ✅ 参数验证优化
6. ✅ 视图定义和备注说明字段
7. ✅ 界面优化

---

## 下次开发建议

1. 可以考虑添加参数模板功能，保存常用的参数组合
2. 可以考虑添加接口文档导出功能（Word、PDF）
3. 可以考虑添加接口测试功能
4. 可以考虑添加接口版本管理功能

