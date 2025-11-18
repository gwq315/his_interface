<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索项目名称/负责人/描述" clearable style="max-width: 320px" />
      <el-button type="primary" @click="loadData" :loading="loading">查询</el-button>
      <el-button v-if="canCreate" type="success" @click="openCreate">新建项目</el-button>
    </div>

    <el-table :data="items" v-loading="loading" size="small" border>
      <el-table-column prop="id" label="ID" width="50" />
      <el-table-column prop="name" label="项目名称" min-width="250" />
      <el-table-column prop="manager" label="负责人" width="110" />
      <el-table-column prop="contact_info" label="联系方式" min-width="120" />
      <el-table-column label="备注" width="100">
        <template #default="{ row }">
          {{ (row.documents && Array.isArray(row.documents) && row.documents.length > 0 && row.documents.find(doc => doc.name === '其他备注')) ? '有' : '无' }}
        </template>
      </el-table-column>
      <el-table-column label="附件数量" width="100">
        <template #default="{ row }">{{ (row.attachments || []).length }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button v-if="canOperate(row)" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="viewDocs(row)">备注</el-button>
          <el-button link type="info" @click="viewAttachments(row)">附件</el-button>
          <el-button v-if="canOperate(row)" link type="danger" @click="handleDelete(row)" :loading="row._deleting">删除</el-button>
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

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑项目' : '新建项目'" width="680px" :close-on-press-escape="false">
      <el-form :model="form" label-width="100px">
        <el-form-item label="项目名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="form.manager" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact_info" type="textarea" :rows="3" placeholder="可填写多个联系方式" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="其他备注">
          <el-input v-model="otherNotes" type="textarea" :rows="4" placeholder="请输入其他备注信息" />
        </el-form-item>
        
        <!-- PDF附件上传（仅编辑时显示） -->
        <el-form-item v-if="dialog.isEdit && form.id" label="PDF附件">
          <el-upload
            ref="uploadRef"
            :http-request="uploadPdfAttachment"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforePdfUpload"
            :show-file-list="false"
            accept=".pdf"
            :limit="10"
          >
            <el-button type="primary" :icon="Upload">上传PDF附件</el-button>
            <template #tip>
              <div class="el-upload__tip" style="color: #999; font-size: 12px; margin-top: 8px;">仅支持PDF格式，最大50MB</div>
            </template>
          </el-upload>
          <div v-if="pdfAttachments.length > 0" class="attachment-list">
            <div v-for="att in pdfAttachments" :key="att.stored_filename" class="attachment-row">
              <el-link :href="getAttachmentUrl(att)" target="_blank" type="primary">{{ att.filename }}</el-link>
              <span style="color: #999; font-size: 12px;">({{ formatFileSize(att.file_size) }})</span>
              <el-button link type="danger" size="small" @click="handleDeleteAttachment(att)">删除</el-button>
            </div>
          </div>
        </el-form-item>

        <!-- 其他相关文件上传（仅编辑时显示） -->
        <el-form-item v-if="dialog.isEdit && form.id" label="其他相关文件">
          <el-upload
            :http-request="uploadOtherAttachment"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :before-upload="beforeOtherUpload"
            :show-file-list="false"
            multiple
          >
            <el-button type="primary" :icon="Upload">上传相关文件</el-button>
            <template #tip>
              <div class="el-upload__tip" style="color: #999; font-size: 12px; margin-top: 8px;">支持任意格式，最大50MB，上传后仅支持下载查看</div>
            </template>
          </el-upload>
          <div v-if="otherAttachments.length > 0" class="attachment-list">
            <div v-for="att in otherAttachments" :key="att.stored_filename" class="attachment-row">
              <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ att.filename }}</span>
              <span style="color: #999; font-size: 12px;">({{ formatFileSize(att.file_size) }})</span>
              <el-button link type="primary" size="small" @click="downloadAttachment(att)">下载</el-button>
              <el-button link type="danger" size="small" @click="handleDeleteAttachment(att)">删除</el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 附件查看对话框 -->
    <el-dialog v-model="attachmentsDialog.visible" title="项目附件" width="720px">
      <template v-if="attachmentsDialog.attachments && attachmentsDialog.attachments.length > 0">
        <section class="attachment-section">
          <h4>PDF附件（可预览）</h4>
          <div v-if="dialogPdfAttachments.length > 0">
            <div v-for="att in dialogPdfAttachments" :key="att.stored_filename" class="attachment-card">
              <el-icon style="font-size: 24px; color: #409eff;"><Document /></el-icon>
              <div style="flex: 1;">
                <el-link :href="getAttachmentUrl(att)" target="_blank" type="primary" style="font-size: 14px;">{{ att.filename }}</el-link>
                <div style="color: #999; font-size: 12px; margin-top: 4px;">
                  {{ formatFileSize(att.file_size) }} · {{ formatDate(att.upload_time) }}
                </div>
              </div>
              <el-button link type="danger" @click="handleDeleteAttachmentInDialog(att)">删除</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无PDF附件" />
        </section>

        <el-divider />

        <section class="attachment-section">
          <h4>其他相关文件（下载查看）</h4>
          <div v-if="dialogOtherAttachments.length > 0">
            <div v-for="att in dialogOtherAttachments" :key="att.stored_filename" class="attachment-card">
              <el-icon style="font-size: 24px; color: #67c23a;"><Document /></el-icon>
              <div style="flex: 1;">
                <div style="font-size: 14px; font-weight: 500;">{{ att.filename }}</div>
                <div style="color: #999; font-size: 12px; margin-top: 4px;">
                  {{ formatFileSize(att.file_size) }} · {{ formatDate(att.upload_time) }}
                </div>
              </div>
              <div style="display: flex; flex-direction: column; gap: 4px;">
                <el-button type="primary" link @click="downloadAttachment(att)">下载</el-button>
                <el-button type="danger" link @click="handleDeleteAttachmentInDialog(att)">删除</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无其他相关文件" />
        </section>
      </template>
      <el-empty v-else description="暂无附件" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Upload, Document } from '@element-plus/icons-vue'
import { projectApi } from '../api/projects'
import { isAdmin, canOperateProject, getUser } from '../utils/auth'

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')

const dialog = ref({ visible: false, isEdit: false, saving: false })
const form = ref({ id: null, name: '', manager: '', contact_info: '', description: '', documents: [], attachments: [] })
const otherNotes = ref('')
const uploadRef = ref()
const attachmentsDialog = ref({ visible: false, attachments: [], projectId: null })
const getAttachmentCategory = (attachment) => {
  if (!attachment) return 'pdf'
  if (attachment.category) return attachment.category
  if (typeof attachment.can_preview === 'boolean') {
    return attachment.can_preview ? 'pdf' : 'other'
  }
  return 'pdf'
}

const filterAttachments = (list, category) => {
  return (list || []).filter(att => getAttachmentCategory(att) === category)
}

const pdfAttachments = computed(() => filterAttachments(form.value.attachments, 'pdf'))
const otherAttachments = computed(() => filterAttachments(form.value.attachments, 'other'))

// 权限检查
const canCreate = computed(() => {
  // 所有登录用户都可以创建项目
  return getUser() !== null
})

const canOperate = (project) => {
  // 管理员可以操作所有项目，普通用户只能操作自己创建的项目
  return canOperateProject(project)
}
const dialogPdfAttachments = computed(() => filterAttachments(attachmentsDialog.value.attachments, 'pdf'))
const dialogOtherAttachments = computed(() => filterAttachments(attachmentsDialog.value.attachments, 'other'))

const loadData = async () => {
  loading.value = true
  try {
    const res = await projectApi.getList({ skip: (page.value - 1) * pageSize.value, limit: pageSize.value, keyword: keyword.value || undefined })
    // 后端当前返回 List<Project>，无总数；先简单使用长度
    items.value = res
    total.value = res.length
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 延迟加载，确保Token已准备好
  await new Promise(resolve => setTimeout(resolve, 100))
  loadData()
})

const openCreate = () => {
  dialog.value = { visible: true, isEdit: false, saving: false }
  form.value = { id: null, name: '', manager: '', contact_info: '', description: '', documents: [], attachments: [] }
  otherNotes.value = ''
}

const openEdit = (row) => {
  dialog.value = { visible: true, isEdit: true, saving: false }
  form.value = { ...row }
  // 如果 documents 是数组且包含备注信息，提取备注文本；否则使用空字符串
  if (row.documents && Array.isArray(row.documents) && row.documents.length > 0) {
    // 尝试从 documents 中提取备注文本（兼容旧数据格式）
    const notesDoc = row.documents.find(doc => doc.name === '备注' || doc.name === '其他备注')
    otherNotes.value = notesDoc ? (notesDoc.description || notesDoc.value || '') : ''
  } else {
    otherNotes.value = ''
  }
}

// 将备注文本转换为 documents 格式（兼容后端 JSON 字段）
const formatNotesToDocuments = () => {
  // 如果有备注内容，将其存储为文档格式；否则返回空数组
  if (otherNotes.value && otherNotes.value.trim()) {
    return [{ name: '其他备注', description: otherNotes.value.trim(), update_date: new Date().toISOString().split('T')[0] }]
  }
  return []
}

const submit = async () => {
  dialog.value.saving = true
  try {
    const payload = { ...form.value, documents: formatNotesToDocuments() }
    if (dialog.value.isEdit && form.value.id) {
      await projectApi.update(form.value.id, payload)
      ElMessage.success('更新成功')
      dialog.value.visible = false
      await loadData()
    } else {
      // 创建项目
      const newProject = await projectApi.create(payload)
      ElMessage.success('创建成功')
      
      // 创建API已经返回了完整的项目数据，直接使用，无需再次查询
      form.value = { ...newProject }
      // 更新备注显示
      if (newProject.documents && Array.isArray(newProject.documents) && newProject.documents.length > 0) {
        const notesDoc = newProject.documents.find(doc => doc.name === '其他备注')
        otherNotes.value = notesDoc ? (notesDoc.description || notesDoc.value || '') : ''
      } else {
        otherNotes.value = ''
      }
      dialog.value.isEdit = true
      
      // 异步刷新列表，不阻塞用户操作
      loadData().catch(err => {
        console.error('刷新列表失败:', err)
        // 不显示错误，因为项目已经创建成功
      })
      
      // 不关闭对话框，让用户可以继续上传附件
      ElMessage.info('项目创建成功，您现在可以上传附件了')
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    dialog.value.saving = false
  }
}

const viewDocs = (row) => {
  // 显示其他备注内容
  let notesContent = ''
  if (row.documents && Array.isArray(row.documents) && row.documents.length > 0) {
    const notesDoc = row.documents.find(doc => doc.name === '其他备注')
    notesContent = notesDoc ? (notesDoc.description || notesDoc.value || '') : ''
  }
  ElMessageBox.alert(
    notesContent || '暂无备注',
    '其他备注',
    { dangerouslyUseHTMLString: false }
  )
}

const viewAttachments = (row) => {
  attachmentsDialog.value = {
    visible: true,
    attachments: row.attachments || [],
    projectId: row.id
  }
}

const getAttachmentUrl = (attachment) => {
  // 始终使用file_path构建URL，使用相对路径通过 nginx 代理访问
  // 不依赖file_url，因为数据库中可能存储了错误的绝对路径（旧数据）
  if (!attachment || !attachment.file_path) {
    console.error('附件数据无效:', attachment)
    return '#'
  }
  
  const filePath = attachment.file_path.replace(/\\/g, '/')
  // 确保路径以/开头
  const relativePath = filePath.startsWith('/') ? filePath : `/${filePath}`
  
  // 使用相对路径，通过 nginx 代理访问（生产环境）或 vite 代理访问（开发环境）
  // 这样不需要知道具体的端口号，nginx/vite 会自动代理到后端
  return relativePath
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const beforeUpload = (file, category = 'pdf') => {
  if (category === 'pdf') {
    const isPDF = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    if (!isPDF) {
      ElMessage.error('仅支持PDF格式文件！')
      return false
    }
  }
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过50MB！')
    return false
  }
  return true
}

const beforePdfUpload = (file) => beforeUpload(file, 'pdf')
const beforeOtherUpload = (file) => beforeUpload(file, 'other')

const handleUpload = async (options, category = 'pdf') => {
  const { file } = options
  try {
    const response = await projectApi.uploadAttachment(form.value.id, file, category)
    return response
  } catch (error) {
    throw error
  }
}

const uploadPdfAttachment = (options) => handleUpload(options, 'pdf')
const uploadOtherAttachment = (options) => handleUpload(options, 'other')

const handleUploadSuccess = (response) => {
  ElMessage.success('附件上传成功')
  // 重新加载项目数据以获取最新附件列表
  if (form.value.id) {
    projectApi.getById(form.value.id).then(res => {
      form.value.attachments = res.attachments || []
    })
  }
  // 如果是查看对话框，也刷新
  if (attachmentsDialog.value.visible && attachmentsDialog.value.projectId) {
    projectApi.getById(attachmentsDialog.value.projectId).then(res => {
      attachmentsDialog.value.attachments = res.attachments || []
    })
  }
  // 刷新列表，更新 row.attachments，避免点击列表的“附件/文档”看到旧数据
  loadData().catch(() => {})
}

const handleUploadError = (error) => {
  ElMessage.error('附件上传失败：' + (error.message || '未知错误'))
}

const handleDeleteAttachment = async (attachment) => {
  try {
    await ElMessageBox.confirm(`确定要删除附件「${attachment.filename}」吗？`, '提示', { type: 'warning' })
    
    await projectApi.deleteAttachment(form.value.id, attachment.stored_filename)
    ElMessage.success('删除成功')
    
    // 重新加载项目数据
    const res = await projectApi.getById(form.value.id)
    form.value.attachments = res.attachments || []
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const handleDeleteAttachmentInDialog = async (attachment) => {
  try {
    await ElMessageBox.confirm(`确定要删除附件「${attachment.filename}」吗？`, '提示', { type: 'warning' })
    
    await projectApi.deleteAttachment(attachmentsDialog.value.projectId, attachment.stored_filename)
    ElMessage.success('删除成功')
    
    // 重新加载项目数据
    const res = await projectApi.getById(attachmentsDialog.value.projectId)
    attachmentsDialog.value.attachments = res.attachments || []
    
    // 如果正在编辑该项目，也更新表单中的附件列表
    if (dialog.value.visible && form.value.id === attachmentsDialog.value.projectId) {
      form.value.attachments = res.attachments || []
    }
    
    // 刷新列表
    await loadData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const downloadAttachment = (attachment) => {
  const url = getAttachmentUrl(attachment)
  if (!url || url === '#') {
    ElMessage.error('无法获取下载地址')
    return
  }
  const link = document.createElement('a')
  link.href = url
  link.download = attachment.filename || attachment.stored_filename || '附件'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除项目「${row.name}」？此操作不可恢复。`, '提示', { type: 'warning' })
  } catch {
    return
  }
  row._deleting = true
  try {
    await projectApi.delete(row.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    row._deleting = false
  }
}
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; }
.pager { margin-top: 12px; display: flex; justify-content: flex-end; }
.attachment-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.attachment-row { display: flex; align-items: center; gap: 8px; }
.attachment-section { margin-bottom: 16px; }
.attachment-section h4 { margin: 0 0 8px; font-size: 14px; font-weight: 600; }
.attachment-card { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #e4e7ed; border-radius: 4px; margin-bottom: 12px; }
</style>


