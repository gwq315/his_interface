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

    <el-table :data="items" v-loading="loading" size="small" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="description" label="简要描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="region" label="地区" width="120" />
      <el-table-column prop="person" label="人员" width="120" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="row.document_type === 'pdf' ? 'primary' : 'success'">
            {{ row.document_type === 'pdf' ? 'PDF' : '图片' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="previewDocument(row)">预览</el-button>
          <el-button link type="warning" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)" :loading="row._deleting">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        background
        layout="prev, pager, next, ->, total"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="p => { page = p; loadData(); }"
      />
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

    <!-- 预览对话框 -->
    <el-dialog 
      v-model="previewDialog.visible" 
      :title="previewDialog.title" 
      width="90%" 
      :close-on-click-modal="false"
    >
      <div v-if="previewDialog.document" style="text-align: center;">
        <div v-if="previewDialog.document.document_type === 'pdf'" style="height: 80vh;">
          <iframe 
            :src="getPreviewUrl(previewDialog.document.file_path)" 
            style="width: 100%; height: 100%; border: none;"
          />
        </div>
        <div v-else>
          <img 
            :src="getPreviewUrl(previewDialog.document.file_path)" 
            style="max-width: 100%; max-height: 80vh;"
            alt="预览图片"
            @error="handleImageError"
            @load="handleImageLoad"
          />
          <div v-if="imageLoadError" style="color: #f56c6c; margin-top: 20px;">
            图片加载失败，请检查文件是否存在或网络连接
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Document, Picture, DocumentCopy, Check } from '@element-plus/icons-vue'
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

const previewDialog = reactive({
  visible: false,
  title: '',
  document: null
})

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
    if (dialog.isEdit) {
      // 更新
      await updateDocument(form.id, {
        title: form.title,
        description: form.description,
        region: form.region,
        person: form.person
      })
      ElMessage.success('更新成功')
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
      
      await createDocument(formData)
      ElMessage.success('创建成功')
    }
    
    dialog.visible = false
    loadData()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    dialog.saving = false
  }
}

// 预览文档
function previewDocument(row) {
  previewDialog.visible = true
  previewDialog.title = row.title
  previewDialog.document = row
  // 重置图片加载错误状态
  imageLoadError.value = false
}

// 图片加载错误处理
function handleImageError(event) {
  console.error('图片加载失败:', event.target.src)
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
    loadData()
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
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}

.pager {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

