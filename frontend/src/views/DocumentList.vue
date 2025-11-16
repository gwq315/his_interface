<template>
  <div class="page">
    <div class="toolbar">
      <el-input 
        v-model="searchForm.keyword" 
        placeholder="搜索标题或简要描述" 
        clearable 
        style="max-width: 320px" 
        @keyup.enter="loadData"
      />
      <el-select 
        v-model="searchForm.document_type" 
        placeholder="文档类型" 
        clearable 
        style="width: 120px"
      >
        <el-option label="PDF" value="pdf" />
        <el-option label="图片" value="image" />
      </el-select>
      <el-button type="primary" @click="loadData" :loading="loading">查询</el-button>
      <el-button type="success" @click="openCreate">新建文档</el-button>
    </div>

    <div class="content-layout">
      <!-- 左侧文档列表 -->
      <div class="left-panel">
        <div class="list-header">
          <span>文档列表</span>
          <span class="total-count">共 {{ total }} 条</span>
        </div>
        <div class="list-content" v-loading="loading">
          <div 
            v-for="item in items" 
            :key="item.id"
            class="list-item"
            :class="{ active: selectedDocument?.id === item.id }"
            @click="selectDocument(item)"
            @contextmenu.prevent="handleContextMenu($event, item)"
          >
            <div class="item-header">
              <el-tag 
                :type="item.document_type === 'pdf' ? 'primary' : 'success'" 
                size="small"
                style="margin-right: 8px;"
              >
                {{ item.document_type === 'pdf' ? 'PDF' : '图片' }}
              </el-tag>
              <span class="item-title">{{ item.title }}</span>
            </div>
            <div class="item-description" v-if="item.description">
              {{ item.description }}
            </div>
            <div class="item-actions" @click.stop>
              <el-dropdown trigger="click" @command="handleCommand">
                <el-button link type="primary" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'edit', item }">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'delete', item }" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <el-empty v-if="!loading && items.length === 0" description="暂无文档" :image-size="100" />
        </div>
        <div class="list-footer">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="page"
            small
            @current-change="p => { page = p; loadData(); }"
          />
        </div>
      </div>

      <!-- 右侧预览区域 -->
      <div class="right-panel">
        <div v-if="selectedDocument" class="preview-content">
          <div class="preview-header">
            <div class="preview-title">
              <h3>{{ selectedDocument.title }}</h3>
              <div class="preview-meta">
                <el-tag :type="selectedDocument.document_type === 'pdf' ? 'primary' : 'success'" size="small">
                  {{ selectedDocument.document_type === 'pdf' ? 'PDF' : '图片' }}
                </el-tag>
                <span class="meta-item" v-if="selectedDocument.region">地区：{{ selectedDocument.region }}</span>
                <span class="meta-item" v-if="selectedDocument.person">人员：{{ selectedDocument.person }}</span>
                <span class="meta-item">创建时间：{{ formatDate(selectedDocument.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="preview-body">
            <div v-if="selectedDocument.document_type === 'pdf'" class="pdf-preview">
              <iframe 
                :src="getPreviewUrl(selectedDocument.file_path)" 
                class="preview-iframe"
              />
            </div>
            <div v-else class="image-preview">
              <img 
                :src="getPreviewUrl(selectedDocument.file_path)" 
                class="preview-image"
                alt="预览图片"
                @error="handleImageError"
                @load="handleImageLoad"
              />
              <div v-if="imageLoadError" class="error-message">
                <el-icon><PictureFilled /></el-icon>
                <p>图片加载失败，请检查文件是否存在或网络连接</p>
              </div>
            </div>
            <div v-if="selectedDocument.description" class="preview-description">
              <h4>简要描述</h4>
              <p>{{ selectedDocument.description }}</p>
            </div>
          </div>
        </div>
        <div v-else class="preview-placeholder">
          <el-empty description="请从左侧选择文档进行预览" :image-size="150" />
        </div>
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialog.visible" 
      :title="dialog.isEdit ? '编辑文档' : '新建文档'" 
      width="700px" 
      :close-on-press-escape="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="文档类型" required>
          <el-radio-group v-model="form.document_type" :disabled="dialog.isEdit">
            <el-radio value="pdf">PDF文档</el-radio>
            <el-radio value="image">图片/截图</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="简要描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="form.region" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="人员">
          <el-input v-model="form.person" maxlength="50" show-word-limit />
        </el-form-item>
        
        <!-- 文件上传（仅新建时显示） -->
        <el-form-item v-if="!dialog.isEdit" label="文件" required>
          <div v-if="form.document_type === 'pdf'">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept=".pdf"
            >
              <el-button type="primary" :icon="Upload">选择PDF文件</el-button>
              <template #tip>
                <div class="el-upload__tip" style="color: #999; font-size: 12px; margin-top: 8px;">
                  仅支持PDF格式，最大50MB
                </div>
              </template>
            </el-upload>
            <div v-if="form.file" style="margin-top: 8px; color: #409eff;">
              <el-icon><Document /></el-icon> {{ form.file.name }}
            </div>
          </div>
          <div v-else>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept="image/*"
            >
              <el-button type="primary" :icon="Upload">选择图片文件</el-button>
            </el-upload>
            <div style="margin-top: 12px;">
              <el-button type="success" @click="handlePasteClick" :icon="DocumentCopy">
                从剪贴板粘贴
              </el-button>
            </div>
            <div v-if="form.file" style="margin-top: 8px; color: #409eff;">
              <el-icon><Picture /></el-icon> {{ form.file.name || '剪贴板图片' }}
            </div>
            <div v-if="form.clipboardData" style="margin-top: 8px; color: #67c23a;">
              <el-icon><Check /></el-icon> 已从剪贴板获取图片
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document, Picture, DocumentCopy, Check, MoreFilled, PictureFilled } from '@element-plus/icons-vue'
import { getDocuments, createDocument, updateDocument, deleteDocument, getDocumentPreviewUrl } from '../api/documents'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const imageLoadError = ref(false)

const searchForm = reactive({
  keyword: '',
  document_type: null
})

const form = reactive({
  id: null,
  title: '',
  description: '',
  region: '',
  person: '',
  document_type: 'pdf',
  file: null,
  clipboardData: null
})

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false
})

const selectedDocument = ref(null)
const uploadRef = ref(null)

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: searchForm.keyword || undefined,
      document_type: searchForm.document_type || undefined
    }
    const res = await getDocuments(params)
    items.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 打开新建对话框
function openCreate() {
  dialog.visible = true
  dialog.isEdit = false
  Object.assign(form, {
    id: null,
    title: '',
    description: '',
    region: '',
    person: '',
    document_type: 'pdf',
    file: null,
    clipboardData: null
  })
}

// 打开编辑对话框
function openEdit(row) {
  dialog.visible = true
  dialog.isEdit = true
  Object.assign(form, {
    id: row.id,
    title: row.title,
    description: row.description || '',
    region: row.region || '',
    person: row.person || '',
    document_type: row.document_type,
    file: null,
    clipboardData: null
  })
}

// 文件选择
function handleFileChange(file) {
  form.file = file.raw
  form.clipboardData = null
}

// 剪贴板粘贴
async function handlePasteClick() {
  try {
    // 请求剪贴板权限
    const clipboardItems = await navigator.clipboard.read()
    
    // 查找图片
    for (const item of clipboardItems) {
      for (const type of item.types) {
        if (type.startsWith('image/')) {
          const blob = await item.getType(type)
          const reader = new FileReader()
          reader.onload = () => {
            form.clipboardData = reader.result
            form.file = null
            ElMessage.success('已从剪贴板获取图片')
          }
          reader.readAsDataURL(blob)
          return
        }
      }
    }
    
    ElMessage.warning('剪贴板中没有图片')
  } catch (error) {
    console.error('剪贴板读取失败:', error)
    ElMessage.error('无法读取剪贴板，请确保已授予剪贴板权限')
  }
}

// 提交表单
async function submit() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  
  if (!dialog.isEdit) {
    // 新建
    if (!form.file && !form.clipboardData) {
      ElMessage.warning('请选择文件或从剪贴板粘贴图片')
      return
    }
  }
  
  dialog.saving = true
  try {
    let res
    if (dialog.isEdit) {
      // 更新
      res = await updateDocument(form.id, {
        title: form.title,
        description: form.description,
        region: form.region,
        person: form.person
      })
      ElMessage.success('更新成功')
      // 更新选中的文档信息
      if (selectedDocument.value && selectedDocument.value.id === form.id) {
        Object.assign(selectedDocument.value, {
          title: form.title,
          description: form.description,
          region: form.region,
          person: form.person
        })
      }
    } else {
      // 创建
      const formData = new FormData()
      formData.append('title', form.title)
      formData.append('description', form.description || '')
      formData.append('region', form.region || '')
      formData.append('person', form.person || '')
      formData.append('document_type', form.document_type)
      
      if (form.file) {
        formData.append('file', form.file)
      } else if (form.clipboardData) {
        formData.append('clipboard_data', form.clipboardData)
      }
      
      res = await createDocument(formData)
      ElMessage.success('创建成功')
    }
    
    dialog.visible = false
    await loadData()
    
    // 如果是新建，选中新创建的文档
    if (!dialog.isEdit && res) {
      const newItem = items.value.find(item => item.id === res.id)
      if (newItem) {
        selectDocument(newItem)
      }
    }
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    dialog.saving = false
  }
}

// 选择文档
function selectDocument(item) {
  selectedDocument.value = item
  // 重置图片加载错误状态
  imageLoadError.value = false
}

// 处理右键菜单
function handleContextMenu(event, item) {
  // 可以在这里添加右键菜单功能
}

// 处理下拉菜单命令
function handleCommand(command) {
  const { action, item } = command
  if (action === 'edit') {
    openEdit(item)
  } else if (action === 'delete') {
    handleDelete(item)
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 图片加载错误处理
function handleImageError(event) {
  imageLoadError.value = true
}

// 图片加载成功处理
function handleImageLoad() {
  imageLoadError.value = false
}

// 获取预览URL
function getPreviewUrl(filePath) {
  return getDocumentPreviewUrl(filePath)
}

// 删除文档
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '提示', {
      type: 'warning'
    })
    
    row._deleting = true
    await deleteDocument(row.id)
    ElMessage.success('删除成功')
    
    // 如果删除的是当前选中的文档，清空选中
    if (selectedDocument.value && selectedDocument.value.id === row.id) {
      selectedDocument.value = null
    }
    
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  } finally {
    row._deleting = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page {
  padding: 20px;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
  flex-shrink: 0;
}

.content-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 左侧文档列表 */
.left-panel {
  width: 350px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
}

.list-header {
  padding: 12px 16px;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
  font-weight: 500;
}

.total-count {
  font-size: 12px;
  color: #909399;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.list-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  background: #fff;
}

.list-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.list-item.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

.item-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.item-title {
  flex: 1;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-description {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}

.item-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.list-item:hover .item-actions {
  opacity: 1;
}

.list-footer {
  padding: 12px;
  border-top: 1px solid #dcdfe6;
  display: flex;
  justify-content: center;
  background: #f5f7fa;
}

/* 右侧预览区域 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  overflow: hidden;
  min-width: 0;
}

.preview-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid #dcdfe6;
  background: #f5f7fa;
  flex-shrink: 0;
}

.preview-title h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
}

.preview-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 12px;
  color: #909399;
}

.preview-body {
  flex: 1;
  overflow: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.pdf-preview {
  flex: 1;
  min-height: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  min-height: 600px;
}

.image-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.error-message {
  text-align: center;
  color: #f56c6c;
  padding: 40px;
}

.error-message .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.preview-description {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.preview-description h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.preview-description p {
  margin: 0;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
}

.preview-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #fafafa;
}
</style>

