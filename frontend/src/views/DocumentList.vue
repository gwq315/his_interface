<template>
  <div class="page">
    <!-- 搜索条件传送到header -->
    <Teleport to=".header-center">
      <div class="header-search">
        <el-input 
          v-model="searchForm.keyword" 
          placeholder="搜索标题或简要描述" 
          clearable 
          style="max-width: 250px" 
          @keyup.enter="loadData"
        />
        <el-select 
          v-model="searchForm.document_type" 
          placeholder="规范类型" 
          clearable 
          style="width: 120px"
        >
          <el-option label="PDF" value="pdf" />
          <el-option label="图片" value="image" />
        </el-select>
        <el-button type="primary" @click="loadData" :loading="loading">查询</el-button>
        <el-button type="success" @click="openCreate">新建规范</el-button>
      </div>
    </Teleport>
    
    <div class="content-layout">
      <!-- 左侧规范列表 -->
      <div class="left-panel">
        <div class="list-header">
          <span>规范列表</span>
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
          <el-empty v-if="!loading && items.length === 0" description="暂无规范" :image-size="100" />
        </div>
        <div class="list-footer">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="page"
            size="small"
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
            <!-- PDF预览：只显示第一个附件 -->
            <div v-if="selectedDocument.document_type === 'pdf'" class="pdf-preview">
              <iframe 
                :src="getPreviewUrl(getFirstAttachmentPath(selectedDocument))" 
                class="preview-iframe"
              />
            </div>
            <!-- 图片预览：支持多个图片按顺序浏览 -->
            <div v-else class="image-preview">
              <div v-if="getImageAttachments(selectedDocument).length > 0" class="image-viewer">
                <div class="image-container">
                  <!-- 左侧切换箭头（浮动） -->
                  <div 
                    v-if="getImageAttachments(selectedDocument).length > 1"
                    class="nav-arrow nav-arrow-left"
                    :class="{ disabled: currentImageIndex === 0 }"
                    @click="prevImage"
                  >
                    <el-icon><ArrowLeft /></el-icon>
                  </div>
                  
                  <!-- 图片显示区域 -->
                  <div class="image-wrapper">
                    <img 
                      :src="getPreviewUrl(getCurrentImagePath(selectedDocument))" 
                      class="preview-image"
                      :alt="`预览图片 ${currentImageIndex + 1}`"
                      @error="handleImageError"
                      @load="handleImageLoad"
                      @click="openImageViewer"
                      :key="`img-${currentImageIndex}-${getCurrentImagePath(selectedDocument)}`"
                      style="cursor: pointer;"
                    />
                    <div v-if="imageLoadError" class="error-message">
                      <el-icon><PictureFilled /></el-icon>
                      <p>图片加载失败，请检查文件是否存在或网络连接</p>
                    </div>
                  </div>
                  
                  <!-- 图片查看器（弹窗放大） -->
                  <component
                    v-if="imageViewerVisible"
                    :is="ElImageViewer"
                    :url-list="getImageViewerUrlList(selectedDocument)"
                    :initial-index="currentImageIndex"
                    @close="imageViewerVisible = false"
                    @switch="handleImageViewerSwitch"
                  />
                  
                  <!-- 右侧切换箭头（浮动） -->
                  <div 
                    v-if="getImageAttachments(selectedDocument).length > 1"
                    class="nav-arrow nav-arrow-right"
                    :class="{ disabled: currentImageIndex === getImageAttachments(selectedDocument).length - 1 }"
                    @click="nextImage"
                  >
                    <el-icon><ArrowRight /></el-icon>
                  </div>
                  
                  <!-- 图片计数器（浮动在右上角） -->
                  <div v-if="getImageAttachments(selectedDocument).length > 1" class="image-counter-float">
                    第 {{ currentImageIndex + 1 }} / {{ getImageAttachments(selectedDocument).length }}
                  </div>
                </div>
                
                <!-- 缩略图导航（固定在底部，不遮挡图片） -->
                <div v-if="getImageAttachments(selectedDocument).length > 1" class="thumbnail-nav">
                  <div 
                    v-for="(attachment, index) in getImageAttachments(selectedDocument)" 
                    :key="index"
                    class="thumbnail-item"
                    :class="{ active: currentImageIndex === index }"
                    @click="currentImageIndex = index; imageLoadError = false"
                  >
                    <img 
                      :src="getPreviewUrl(attachment.file_path)" 
                      :alt="attachment.filename"
                      class="thumbnail-image"
                    />
                  </div>
                </div>
              </div>
              <div v-else class="no-image">
                <el-empty description="暂无图片附件" :image-size="100" />
              </div>
            </div>
            <div v-if="selectedDocument.description" class="preview-description">
              <h4>简要描述</h4>
              <p>{{ selectedDocument.description }}</p>
            </div>
          </div>
        </div>
        <div v-else class="preview-placeholder">
          <el-empty description="请从左侧选择规范进行预览" :image-size="150" />
        </div>
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialog.visible" 
      :title="dialog.isEdit ? '编辑规范' : '新建规范'" 
      width="700px" 
      :close-on-press-escape="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="规范类型" required>
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
        
        <!-- 文件上传 -->
        <el-form-item :label="dialog.isEdit ? '附件管理' : '文件'" :required="!dialog.isEdit">
          <!-- 新建时：支持多文件上传 -->
          <div v-if="!dialog.isEdit">
            <div v-if="form.document_type === 'pdf'">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :on-change="handleFileChange"
                :show-file-list="true"
                accept=".pdf"
                :limit="1"
              >
                <el-button type="primary" :icon="Upload">选择PDF文件</el-button>
                <template #tip>
                  <div class="el-upload__tip" style="color: #999; font-size: 12px; margin-top: 8px;">
                    仅支持PDF格式，最大50MB，只能上传一个文件
                  </div>
                </template>
              </el-upload>
            </div>
            <div v-else>
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :on-change="handleFileChange"
                :show-file-list="true"
                accept="image/*"
                :multiple="true"
              >
                <el-button type="primary" :icon="Upload">选择图片文件（可多选）</el-button>
                <template #tip>
                  <div class="el-upload__tip" style="color: #999; font-size: 12px; margin-top: 8px;">
                    支持多个图片文件，最大50MB/文件
                  </div>
                </template>
              </el-upload>
            </div>
          </div>
          
          <!-- 编辑时：显示附件列表，支持添加和删除 -->
          <div v-else>
            <div class="attachment-list">
              <div 
                v-for="(attachment, index) in form.attachments" 
                :key="index"
                class="attachment-item"
              >
                <el-icon><Document v-if="form.document_type === 'pdf'" /><Picture v-else /></el-icon>
                <span class="attachment-name">{{ attachment.filename }}</span>
                <el-button 
                  link 
                  type="danger" 
                  size="small"
                  @click="handleDeleteAttachment(index)"
                  :disabled="form.document_type === 'pdf' && form.attachments.length === 1"
                >
                  删除
                </el-button>
              </div>
              <div v-if="form.attachments.length === 0" class="no-attachments">
                暂无附件
              </div>
            </div>
            <div style="margin-top: 12px;">
              <el-upload
                ref="editUploadRef"
                :auto-upload="false"
                :on-change="handleAddAttachment"
                :show-file-list="false"
                :accept="form.document_type === 'pdf' ? '.pdf' : 'image/*'"
              >
                <el-button type="primary" :icon="Upload" size="small">
                  {{ form.document_type === 'pdf' ? '添加PDF文件' : '添加图片文件' }}
                </el-button>
              </el-upload>
              <div v-if="form.document_type === 'pdf'" style="color: #999; font-size: 12px; margin-top: 4px;">
                注意：PDF文件只能有一个附件
              </div>
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
import { ElMessage, ElMessageBox, ElImageViewer } from 'element-plus'
import { Upload, Document, Picture, MoreFilled, PictureFilled, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getDocuments, createDocument, updateDocument, deleteDocument, getDocumentPreviewUrl, addDocumentAttachment, deleteDocumentAttachment } from '../api/documents'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const imageLoadError = ref(false)
const currentImageIndex = ref(0)
const imageViewerVisible = ref(false)

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
  file: null, // 向后兼容：单个文件（用于新建）
  files: [], // 多个文件（用于新建，支持多文件上传）
  attachments: [] // 附件列表（用于编辑）
})

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false
})

const selectedDocument = ref(null)
const uploadRef = ref(null)
const editUploadRef = ref(null)

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
    files: [],
    attachments: []
  })
  // 清空上传组件的文件列表
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 打开编辑对话框
function openEdit(row) {
  dialog.visible = true
  dialog.isEdit = true
  // 处理附件列表（向后兼容）
  let attachments = []
  if (row.attachments && row.attachments.length > 0) {
    attachments = row.attachments
  } else if (row.file_path) {
    // 向后兼容：将旧格式转换为新格式
    attachments = [{
      filename: row.file_name || '未知文件',
      stored_filename: row.file_path.split('/').pop() || '',
      file_path: row.file_path,
      file_size: row.file_size || 0,
      mime_type: row.mime_type,
      upload_time: row.created_at || ''
    }]
  }
  Object.assign(form, {
    id: row.id,
    title: row.title,
    description: row.description || '',
    region: row.region || '',
    person: row.person || '',
    document_type: row.document_type,
    file: null,
    attachments: attachments
  })
}

// 文件选择（新建时）
function handleFileChange(file, fileList) {
  // 更新files数组
  form.files = fileList.map(f => f.raw)
  // 向后兼容：保留file字段（取第一个文件）
  form.file = fileList.length > 0 ? fileList[0].raw : null
}

// 添加附件（编辑时）
async function handleAddAttachment(file) {
  // PDF类型只能有一个附件
  if (form.document_type === 'pdf' && form.attachments.length > 0) {
    ElMessage.warning('PDF文档只能有一个附件')
    // 清空上传组件的文件列表
    if (editUploadRef.value) {
      editUploadRef.value.clearFiles()
    }
    return
  }
  
  try {
    const res = await addDocumentAttachment(form.id, file.raw)
    form.attachments = (res.data?.attachments || res.data || res).attachments || []
    ElMessage.success('附件添加成功')
    // 清空上传组件的文件列表，避免显示覆盖问题
    if (editUploadRef.value) {
      editUploadRef.value.clearFiles()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || error.message || '添加附件失败')
    // 出错时也清空上传组件
    if (editUploadRef.value) {
      editUploadRef.value.clearFiles()
    }
  }
}

// 删除附件（编辑时）
async function handleDeleteAttachment(index) {
  // PDF类型至少需要一个附件
  if (form.document_type === 'pdf' && form.attachments.length === 1) {
    ElMessage.warning('PDF文档至少需要一个附件')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要删除这个附件吗？', '提示', {
      type: 'warning'
    })
    
    const attachment = form.attachments[index]
    const res = await deleteDocumentAttachment(form.id, attachment.stored_filename)
    form.attachments = (res.data?.attachments || res.data || res).attachments || []
    ElMessage.success('附件删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || error.message || '删除附件失败')
    }
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
    if (!form.files || form.files.length === 0) {
      ElMessage.warning('请选择文件')
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
      // 创建 - 支持多文件上传
      const formData = new FormData()
      formData.append('title', form.title)
      formData.append('description', form.description || '')
      formData.append('region', form.region || '')
      formData.append('person', form.person || '')
      formData.append('document_type', form.document_type)
      
      // 添加所有文件
      if (form.files && form.files.length > 0) {
        form.files.forEach(file => {
          formData.append('files', file)
        })
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
  // 重置图片加载错误状态和索引
  imageLoadError.value = false
  currentImageIndex.value = 0
}

// 获取附件列表（向后兼容）
function getAttachments(document) {
  if (document.attachments && document.attachments.length > 0) {
    return document.attachments
  } else if (document.file_path) {
    // 向后兼容
    return [{
      filename: document.file_name || '未知文件',
      stored_filename: document.file_path.split('/').pop() || '',
      file_path: document.file_path,
      file_size: document.file_size || 0,
      mime_type: document.mime_type,
      upload_time: document.created_at || ''
    }]
  }
  return []
}

// 获取第一个附件路径（用于PDF）
function getFirstAttachmentPath(document) {
  const attachments = getAttachments(document)
  return attachments.length > 0 ? attachments[0].file_path : document.file_path || ''
}

// 获取图片附件列表
function getImageAttachments(document) {
  if (!document) return []
  
  const attachments = getAttachments(document)
  
  // 如果文档类型是image，返回所有附件（因为都是图片）
  if (document.document_type === 'image') {
    return attachments
  }
  
  // 否则，只返回mime_type是image/开头的附件
  return attachments.filter(att => {
    const mimeType = att.mime_type || ''
    // 也检查文件扩展名，以防mime_type缺失
    const filePath = att.file_path || ''
    const isImageByMime = mimeType.startsWith('image/')
    const isImageByExt = /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(filePath)
    return isImageByMime || isImageByExt
  })
}

// 获取当前显示的图片路径
function getCurrentImagePath(document) {
  if (!document) return ''
  
  const imageAttachments = getImageAttachments(document)
  if (imageAttachments.length > 0) {
    // 确保索引在有效范围内
    const index = Math.max(0, Math.min(currentImageIndex.value, imageAttachments.length - 1))
    const attachment = imageAttachments[index]
    if (attachment && attachment.file_path) {
      return attachment.file_path
    }
  }
  
  // 向后兼容：如果没有附件，使用file_path
  return document.file_path || ''
}

// 上一张图片
function prevImage() {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
    imageLoadError.value = false
  }
}

// 下一张图片
function nextImage() {
  const imageAttachments = getImageAttachments(selectedDocument.value)
  if (currentImageIndex.value < imageAttachments.length - 1) {
    currentImageIndex.value++
    imageLoadError.value = false
  }
}

// 处理右键菜单
function handleContextMenu(event, item) {
  // 预留接口，可在此添加右键菜单功能
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
function handleImageError() {
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

// 删除规范
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个规范吗？', '提示', {
      type: 'warning'
    })
    
    row._deleting = true
    await deleteDocument(row.id)
    ElMessage.success('删除成功')
    
    // 如果删除的是当前选中的规范，清空选中
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
  padding: 1px;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.header-search {
  display: flex;
  align-items: center;
  gap: 10px;
}

.content-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 左侧规范列表 */
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
  padding: 6px 6px;
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

/* 附件列表样式 */
.attachment-list {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  background: #fafafa;
  min-height: 60px;
  max-height: 200px;
  overflow-y: auto;
}

.attachment-item {
  display: flex;
  align-items: center;
  padding: 8px;
  margin-bottom: 4px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.attachment-item:last-child {
  margin-bottom: 0;
}

.attachment-item .el-icon {
  margin-right: 8px;
  color: #409eff;
}

.attachment-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-attachments {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 14px;
}

/* 图片查看器样式 */
.image-viewer {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  padding: 0;
  position: relative;
}

.image-container {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
  overflow: hidden;
}

.image-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: auto;
  padding: 0;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: block;
}

/* 浮动导航箭头 */
.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.nav-arrow:hover {
  background: #409eff;
  color: #fff;
  transform: translateY(-50%) scale(1.1);
}

.nav-arrow.disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: rgba(255, 255, 255, 0.5);
}

.nav-arrow.disabled:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #409eff;
  transform: translateY(-50%) scale(1);
}

.nav-arrow-left {
  left: 20px;
}

.nav-arrow-right {
  right: 20px;
}

.nav-arrow .el-icon {
  font-size: 24px;
  color: #409eff;
}

.nav-arrow:hover .el-icon {
  color: #fff;
}

.nav-arrow.disabled .el-icon {
  color: #c0c4cc;
}

/* 浮动计数器 */
.image-counter-float {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  z-index: 10;
  backdrop-filter: blur(4px);
}

.no-image {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-height: 400px;
}

/* 缩略图导航（固定在底部） */
.thumbnail-nav {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(245, 247, 250, 0.3);
  border-top: 1px solid rgba(220, 223, 230, 0.3);
  overflow-x: auto;
  justify-content: center;
  flex-wrap: wrap;
  backdrop-filter: blur(2px);
  z-index: 5;
}

.thumbnail-item {
  width: 60px;
  height: 60px;
  border: 2px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
}

.thumbnail-item:hover {
  border-color: #409eff;
  transform: scale(1.1);
}

.thumbnail-item.active {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>

