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
          v-model="searchForm.content_type" 
          placeholder="内容类型" 
          clearable 
          style="width: 120px"
        >
          <el-option label="附件" value="attachment" />
          <el-option label="富文本" value="rich_text" />
        </el-select>
        <el-select 
          v-model="searchForm.module" 
          placeholder="模块" 
          clearable 
          style="width: 150px"
        >
          <el-option 
            v-for="module in moduleOptions" 
            :key="module.value" 
            :label="module.label" 
            :value="module.value" 
          />
        </el-select>
        <el-button type="primary" @click="loadData" :loading="loading">查询</el-button>
        <el-button type="success" @click="openCreate">新建常见问题</el-button>
      </div>
    </Teleport>
    
    <div class="content-layout">
      <!-- 左侧常见问题列表 -->
      <div class="left-panel">
        <div class="list-header">
          <span>常见问题列表</span>
          <span class="total-count">共 {{ total }} 条</span>
        </div>
        <div class="list-content" v-loading="loading">
          <div 
            v-for="item in items" 
            :key="item.id"
            class="list-item"
            :class="{ active: selectedFAQ?.id === item.id }"
            @click="selectFAQ(item)"
            @contextmenu.prevent="handleContextMenu($event, item)"
          >
            <div class="item-header">
              <el-tag 
                :type="item.content_type === 'rich_text' ? 'success' : 'primary'" 
                size="small"
                style="margin-right: 4px;"
              >
                {{ item.content_type === 'rich_text' ? '富文本' : '附件' }}
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
          <el-empty v-if="!loading && items.length === 0" description="暂无常见问题" :image-size="100" />
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
        <div v-if="selectedFAQ" class="preview-content">
          <div class="preview-header">
            <div class="preview-title">
              <h3>{{ selectedFAQ.title }}</h3>
              <div class="preview-meta">
                <el-tag :type="selectedFAQ.content_type === 'rich_text' ? 'success' : 'primary'" size="small">
                  {{ selectedFAQ.content_type === 'rich_text' ? '富文本' : '附件' }}
                </el-tag>
                <span class="meta-item" v-if="selectedFAQ.module">模块：{{ selectedFAQ.module }}</span>
                <span class="meta-item" v-if="selectedFAQ.person">人员：{{ selectedFAQ.person }}</span>
                <span class="meta-item">创建时间：{{ formatDate(selectedFAQ.created_at) }}</span>
              </div>
            </div>
          </div>
          <div class="preview-body">
            <!-- 附件类型：PDF预览 -->
            <div v-if="selectedFAQ.content_type === 'attachment' || !selectedFAQ.content_type" class="pdf-preview">
              <iframe 
                :src="getPreviewUrl(getFirstAttachmentPath(selectedFAQ))" 
                class="preview-iframe"
              />
            </div>
            <!-- 富文本类型：显示富文本内容 -->
            <div v-else-if="selectedFAQ.content_type === 'rich_text'" class="rich-text-preview">
              <div class="rich-content" ref="richContentRef" v-html="highlightedContent"></div>
            </div>
            <!-- 向后兼容：图片预览（旧数据） -->
            <div v-else-if="selectedFAQ.document_type === 'image'" class="image-preview">
              <div v-if="getImageAttachments(selectedFAQ).length > 0" class="image-viewer">
                <div class="image-container">
                  <!-- 左侧切换箭头（浮动） -->
                  <div 
                    v-if="getImageAttachments(selectedFAQ).length > 1"
                    class="nav-arrow nav-arrow-left"
                    :class="{ disabled: currentImageIndex === 0 }"
                    @click="prevImage"
                  >
                    <el-icon><ArrowLeft /></el-icon>
                  </div>
                  
                  <!-- 图片显示区域 -->
                  <div class="image-wrapper">
                    <img 
                      :src="getPreviewUrl(getCurrentImagePath(selectedFAQ))" 
                      class="preview-image"
                      :alt="`预览图片 ${currentImageIndex + 1}`"
                      @error="handleImageError"
                      @load="handleImageLoad"
                      @click="openImageViewer"
                      :key="`img-${currentImageIndex}-${getCurrentImagePath(selectedFAQ)}`"
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
                    :url-list="getImageViewerUrlList(selectedFAQ)"
                    :initial-index="currentImageIndex"
                    @close="imageViewerVisible = false"
                    @switch="handleImageViewerSwitch"
                  />
                  
                  <!-- 右侧切换箭头（浮动） -->
                  <div 
                    v-if="getImageAttachments(selectedFAQ).length > 1"
                    class="nav-arrow nav-arrow-right"
                    :class="{ disabled: currentImageIndex === getImageAttachments(selectedFAQ).length - 1 }"
                    @click="nextImage"
                  >
                    <el-icon><ArrowRight /></el-icon>
                  </div>
                  
                  <!-- 图片计数器（浮动在右上角） -->
                  <div v-if="getImageAttachments(selectedFAQ).length > 1" class="image-counter-float">
                    第 {{ currentImageIndex + 1 }} / {{ getImageAttachments(selectedFAQ).length }}
                  </div>
                </div>
                
                <!-- 缩略图导航（固定在底部，不遮挡图片） -->
                <div v-if="getImageAttachments(selectedFAQ).length > 1" class="thumbnail-nav">
                  <div 
                    v-for="(attachment, index) in getImageAttachments(selectedFAQ)" 
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
            <div v-if="selectedFAQ.description" class="preview-description">
              <h4>简要描述</h4>
              <p>{{ selectedFAQ.description }}</p>
            </div>
          </div>
        </div>
        <div v-else class="preview-placeholder">
          <el-empty description="请从左侧选择常见问题进行预览" :image-size="150" />
        </div>
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialog.visible" 
      :title="dialog.isEdit ? '编辑常见问题' : '新建常见问题'" 
      width="80%" 
      :close-on-press-escape="false"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="内容类型" required>
          <el-radio-group v-model="form.content_type" :disabled="dialog.isEdit">
            <el-radio value="attachment">附件类型（PDF）</el-radio>
            <el-radio value="rich_text">富文本类型（图文混排）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
        <el-form-item label="模块">
          <el-select v-model="form.module" placeholder="请选择模块" clearable style="width: 100%">
            <el-option 
              v-for="module in moduleOptions" 
              :key="module.value" 
              :label="module.label" 
              :value="module.value" 
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="人员">
          <el-input v-model="form.person" maxlength="50" show-word-limit />
        </el-form-item>
      </el-col>
    </el-row>
        <el-form-item label="简要描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>        
        
        <!-- 附件类型：文件上传 -->
        <el-form-item 
          v-if="form.content_type === 'attachment' || !form.content_type"
          :label="dialog.isEdit ? '附件管理' : '文件'" 
          :required="!dialog.isEdit"
        >
          <!-- 新建时：PDF文件上传 -->
          <div v-if="!dialog.isEdit">
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
                  仅支持PDF格式，最大100MB，只能上传一个文件
                </div>
              </template>
            </el-upload>
          </div>
          
          <!-- 编辑时：显示附件列表，支持添加和删除 -->
          <div v-else>
            <div class="attachment-list">
              <div 
                v-for="(attachment, index) in form.attachments" 
                :key="index"
                class="attachment-item"
              >
                <el-icon><Document /></el-icon>
                <span class="attachment-name">{{ attachment.filename }}</span>
                <el-button 
                  link 
                  type="danger" 
                  size="small"
                  @click="handleDeleteAttachment(index)"
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
                accept=".pdf"
              >
                <el-button type="primary" :icon="Upload" size="small">添加PDF文件</el-button>
              </el-upload>
              <div style="color: #999; font-size: 12px; margin-top: 4px;">
                注意：附件类型只能有一个PDF文件
              </div>
            </div>
          </div>
        </el-form-item>
        
        <!-- 富文本类型：富文本编辑器 -->
        <el-form-item 
          v-if="form.content_type === 'rich_text'"
          label="富文本内容" 
          :required="!dialog.isEdit"
        >
          <div class="rich-text-editor-wrapper">
            <QuillEditor
              v-model:content="form.rich_content"
              contentType="html"
              :options="editorOptions"
              class="rich-text-editor"
            />
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
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElImageViewer } from 'element-plus'
import { Upload, Document, Picture, MoreFilled, PictureFilled, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import Quill from 'quill'
// 导入 highlight.js（使用标准导入，Vite 会自动处理）
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css' // 使用 GitHub Dark 主题，也可以选择其他主题
import { getFAQs, createFAQ, updateFAQ, deleteFAQ, getFAQPreviewUrl, addFAQAttachment, deleteFAQAttachment } from '../api/faqs'
import { dictionaryApi } from '../api/dictionaries'

// 注意：Quill 2.0 默认支持自定义字号，直接在工具栏配置中指定即可
// 如果需要使用像素值，需要注册自定义 Size 格式化器
const Size = Quill.import('attributors/style/size')
Size.whitelist = ['10px', '12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px', '36px', '48px']
Quill.register(Size, true)

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const imageLoadError = ref(false)
const currentImageIndex = ref(0)
const imageViewerVisible = ref(false)
const moduleOptions = ref([])

const searchForm = reactive({
  keyword: '',
  content_type: null,
  module: null
})

const form = reactive({
  id: null,
  title: '',
  description: '',
  module: '',
  person: '',
  document_type: 'pdf', // 向后兼容字段
  content_type: 'attachment', // 内容类型：attachment 或 rich_text
  rich_content: '', // 富文本内容
  file: null, // 向后兼容：单个文件（用于新建）
  files: [], // 多个文件（用于新建，支持多文件上传）
  attachments: [] // 附件列表（用于编辑）
})

// 预设颜色选项（常用颜色）
const colorOptions = [
  '#000000', // 黑色
  '#333333', // 深灰色
  '#666666', // 灰色
  '#999999', // 浅灰色
  '#ffffff', // 白色
  '#ff0000', // 红色
  '#ff6600', // 橙色
  '#ff9900', // 橙黄色
  '#ffcc00', // 黄色
  '#99cc00', // 黄绿色
  '#66cc00', // 绿色
  '#00cc66', // 青绿色
  '#00cccc', // 青色
  '#0066cc', // 蓝色
  '#3366ff', // 亮蓝色
  '#6600cc', // 紫色
  '#cc00cc', // 紫红色
  '#ff0066', // 粉红色
]

// 预设背景颜色选项
const backgroundOptions = [
  '#ffffff', // 白色
  '#f5f5f5', // 浅灰
  '#e6e6e6', // 灰色
  '#ffcccc', // 浅红
  '#ccffcc', // 浅绿
  '#ccccff', // 浅蓝
  '#ffffcc', // 浅黄
  '#ffccff', // 浅紫
  '#ccffff', // 浅青
  '#000000', // 黑色
  '#ff0000', // 红色
  '#00ff00', // 绿色
  '#0000ff', // 蓝色
  '#ffff00', // 黄色
  '#ff00ff', // 紫色
  '#00ffff', // 青色
]

// 富文本编辑器配置
const editorOptions = {
  theme: 'snow',
  modules: {
    toolbar: [
      // 标题级别（1-6级，false表示普通文本）
      [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
      // 字号大小（使用默认选项，如果需要自定义像素值，需要确保 Size 格式化器正确注册）
      [{ 'size': ['small', false, 'large', 'huge'] }],
      // 字体样式
      ['bold', 'italic', 'underline', 'strike'],
      // 字体颜色和背景色（使用空数组显示完整的颜色选择器）
      [{ 'color': [] }, { 'background': [] }],
      // 列表（有序和无序）
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      // 文本对齐（左、中、右、两端对齐）
      [{ 'align': [] }],
      // 链接和图片
      ['link', 'image'],
      // 引用块和代码块（支持语法高亮）
      ['blockquote', 'code-block'],
      // 清除格式
      ['clean']
      // 其他可选工具栏选项（已注释，可根据需要启用）：
      // [{ 'font': [] }],           // 字体系列
      // ['video'],                   // 视频
      // [{ 'script': 'sub'}, { 'script': 'super' }], // 上标和下标
      // [{ 'indent': '-1'}, { 'indent': '+1' }],     // 缩进
      // [{ 'direction': 'rtl' }],    // 文字方向（从右到左）
    ]
  }
}

const dialog = reactive({
  visible: false,
  isEdit: false,
  saving: false
})

const selectedFAQ = ref(null)
const uploadRef = ref(null)
const editUploadRef = ref(null)
const richContentRef = ref(null)
const highlightedContent = ref('')

// 对代码块应用语法高亮
function highlightCodeBlocks(html) {
  if (!html) return ''
  
  // 创建一个临时 DOM 元素来解析 HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = html
  
  // 查找所有代码块
  const codeBlocks = tempDiv.querySelectorAll('pre code, code')
  
  codeBlocks.forEach((code) => {
    // 如果代码块已经有高亮类，跳过
    if (code.classList.contains('hljs')) return
    
    const codeText = code.textContent || code.innerText
    const language = code.className.match(/language-(\w+)/)?.[1] || 'plaintext'
    
    try {
      // 使用 highlight.js 进行语法高亮
      const highlighted = hljs.highlight(codeText, { 
        language: language === 'plaintext' ? 'plaintext' : language 
      })
      code.innerHTML = highlighted.value
      code.classList.add('hljs')
      if (language !== 'plaintext') {
        code.classList.add(`language-${language}`)
      }
    } catch (e) {
      // 如果高亮失败，使用纯文本模式
      try {
        const highlighted = hljs.highlightAuto(codeText)
        code.innerHTML = highlighted.value
        code.classList.add('hljs')
      } catch (e2) {
        // 如果还是失败，保持原样
        console.warn('Syntax highlighting failed:', e2)
      }
    }
  })
  
  return tempDiv.innerHTML
}

// 监听选中常见问题的变化，应用语法高亮
watch(selectedFAQ, async (newVal) => {
  if (newVal && newVal.content_type === 'rich_text' && newVal.rich_content) {
    await nextTick()
    highlightedContent.value = highlightCodeBlocks(newVal.rich_content)
  } else {
    highlightedContent.value = newVal?.rich_content || ''
  }
}, { immediate: true })

// 加载模块字典
async function loadModuleOptions() {
  try {
    // 尝试获取编码为 FAQ_MODULE 的字典
    const dict = await dictionaryApi.getByCode('FAQ_MODULE')
    if (dict && dict.values && dict.values.length > 0) {
      moduleOptions.value = dict.values.map(v => ({
        label: v.value,
        value: v.value
      }))
    } else {
      // 如果字典不存在或为空，使用空数组
      moduleOptions.value = []
    }
  } catch (error) {
    // 如果字典不存在，忽略错误，使用空数组
    moduleOptions.value = []
  }
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: searchForm.keyword || undefined,
      document_type: 'pdf', // 向后兼容，统一使用pdf
      module: searchForm.module || undefined
    }
    const res = await getFAQs(params)
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
    module: '',
    person: '',
    document_type: 'pdf', // 向后兼容字段
    content_type: 'attachment', // 默认附件类型
    rich_content: '', // 富文本内容
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
    module: row.module || '',
    person: row.person || '',
    document_type: row.document_type || 'pdf', // 向后兼容
    content_type: row.content_type || 'attachment', // 内容类型
    rich_content: row.rich_content || '', // 富文本内容
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
    const res = await addFAQAttachment(form.id, file.raw)
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
    const res = await deleteFAQAttachment(form.id, attachment.stored_filename)
    form.attachments = (res.data?.attachments || res.data || res).attachments || []
    ElMessage.success('附件删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || error.message || '删除附件失败')
    }
  }
}

// 检查富文本内容是否为空（去除HTML标签后检查）
function isRichContentEmpty(content) {
  if (!content) return true
  // 去除HTML标签，只保留文本内容
  const textContent = content.replace(/<[^>]*>/g, '').trim()
  // 检查是否只包含空白字符或换行符
  return !textContent || textContent.length === 0
}

// 提交表单
async function submit() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  
  // 验证内容类型
  if (form.content_type === 'attachment') {
    // 附件类型：新建时必须上传文件
    if (!dialog.isEdit && (!form.files || form.files.length === 0)) {
      ElMessage.warning('请选择PDF文件')
      return
    }
  } else if (form.content_type === 'rich_text') {
    // 富文本类型：必须提供富文本内容
    if (isRichContentEmpty(form.rich_content)) {
      ElMessage.warning('请输入富文本内容')
      return
    }
  }
  
  dialog.saving = true
  try {
    let res
    if (dialog.isEdit) {
      // 更新
      res = await updateFAQ(form.id, {
        title: form.title,
        description: form.description,
        module: form.module,
        person: form.person,
        content_type: form.content_type,
        rich_content: form.content_type === 'rich_text' ? form.rich_content : null
      })
      ElMessage.success('更新成功')
      // 更新选中的常见问题信息
      if (selectedFAQ.value && selectedFAQ.value.id === form.id) {
        Object.assign(selectedFAQ.value, {
          title: form.title,
          description: form.description,
          module: form.module,
          person: form.person,
          content_type: form.content_type,
          rich_content: form.rich_content
        })
      }
    } else {
      // 创建
      if (form.content_type === 'rich_text') {
        // 富文本类型：使用 JSON 方式提交
        const jsonData = {
          title: form.title,
          description: form.description || '',
          module: form.module || '',
          person: form.person || '',
          document_type: 'pdf', // 向后兼容，统一使用pdf
          content_type: form.content_type,
          rich_content: form.rich_content || ''
        }
        res = await createFAQ(jsonData, true)
      } else {
        // 附件类型：使用 FormData 方式提交
        const formData = new FormData()
        formData.append('title', form.title)
        formData.append('description', form.description || '')
        formData.append('module', form.module || '')
        formData.append('person', form.person || '')
        formData.append('document_type', 'pdf') // 向后兼容，统一使用pdf
        formData.append('content_type', form.content_type)
        
        // 添加PDF文件
        if (form.files && form.files.length > 0) {
          form.files.forEach(file => {
            formData.append('files', file)
          })
        }
        
        res = await createFAQ(formData, false)
      }
      ElMessage.success('创建成功')
    }
    
    dialog.visible = false
    await loadData()
    
    // 如果是新建，选中新创建的常见问题
    if (!dialog.isEdit && res) {
      const newItem = items.value.find(item => item.id === res.id)
      if (newItem) {
        selectFAQ(newItem)
      }
    }
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || '操作失败'
    ElMessage.error(errorMessage)
  } finally {
    dialog.saving = false
  }
}

// 选择常见问题
function selectFAQ(item) {
  selectedFAQ.value = item
  // 重置图片加载错误状态和索引
  imageLoadError.value = false
  currentImageIndex.value = 0
}

// 获取附件列表（向后兼容）
function getAttachments(faq) {
  if (faq.attachments && faq.attachments.length > 0) {
    return faq.attachments
  } else if (faq.file_path) {
    // 向后兼容
    return [{
      filename: faq.file_name || '未知文件',
      stored_filename: faq.file_path.split('/').pop() || '',
      file_path: faq.file_path,
      file_size: faq.file_size || 0,
      mime_type: faq.mime_type,
      upload_time: faq.created_at || ''
    }]
  }
  return []
}

// 获取第一个附件路径（用于PDF）
function getFirstAttachmentPath(faq) {
  const attachments = getAttachments(faq)
  return attachments.length > 0 ? attachments[0].file_path : faq.file_path || ''
}

// 获取图片附件列表
function getImageAttachments(faq) {
  if (!faq) return []
  
  const attachments = getAttachments(faq)
  
  // 如果文档类型是image，返回所有附件（因为都是图片）
  if (faq.document_type === 'image') {
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
function getCurrentImagePath(faq) {
  if (!faq) return ''
  
  const imageAttachments = getImageAttachments(faq)
  if (imageAttachments.length > 0) {
    // 确保索引在有效范围内
    const index = Math.max(0, Math.min(currentImageIndex.value, imageAttachments.length - 1))
    const attachment = imageAttachments[index]
    if (attachment && attachment.file_path) {
      return attachment.file_path
    }
  }
  
  // 向后兼容：如果没有附件，使用file_path
  return faq.file_path || ''
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
  const imageAttachments = getImageAttachments(selectedFAQ.value)
  if (currentImageIndex.value < imageAttachments.length - 1) {
    currentImageIndex.value++
    imageLoadError.value = false
  }
}

// 打开图片查看器（弹窗放大）
function openImageViewer() {
  const imageAttachments = getImageAttachments(selectedFAQ.value)
  if (imageAttachments.length > 0) {
    imageViewerVisible.value = true
  }
}

// 获取图片查看器的URL列表
function getImageViewerUrlList(faq) {
  if (!faq) return []
  const imageAttachments = getImageAttachments(faq)
  return imageAttachments.map(att => getPreviewUrl(att.file_path))
}

// 图片查看器切换图片
function handleImageViewerSwitch(index) {
  currentImageIndex.value = index
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
  return getFAQPreviewUrl(filePath)
}

// 删除常见问题
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个常见问题吗？', '提示', {
      type: 'warning'
    })
    
    row._deleting = true
    await deleteFAQ(row.id)
    ElMessage.success('删除成功')
    
    // 如果删除的是当前选中的常见问题，清空选中
    if (selectedFAQ.value && selectedFAQ.value.id === row.id) {
      selectedFAQ.value = null
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

onMounted(async () => {
  await loadModuleOptions()
  await loadData()
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

/* 左侧常见问题列表 */
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
  padding: 6px 4px;
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
  gap: 8px;
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

/* 富文本预览样式 */
.rich-text-preview {
  flex: 1;
  min-height: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: auto;
  padding: 20px;
  background: #fff;
}

.rich-content {
  width: 100%;
  min-height: 200px;
  line-height: 1.6;
  color: #303133;
}

.rich-content :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 10px 0;
}

.rich-content :deep(p) {
  margin: 10px 0;
}

.rich-content :deep(h1),
.rich-content :deep(h2),
.rich-content :deep(h3),
.rich-content :deep(h4),
.rich-content :deep(h5),
.rich-content :deep(h6) {
  margin: 20px 0 10px 0;
  font-weight: bold;
}

.rich-content :deep(ul),
.rich-content :deep(ol) {
  margin: 10px 0;
  padding-left: 30px;
}

.rich-content :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding-left: 15px;
  margin: 10px 0;
  color: #606266;
}

/* 代码块样式 */
.rich-content :deep(pre) {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.45;
}

.rich-content :deep(pre code) {
  background: transparent;
  padding: 0;
  border: none;
  font-size: inherit;
  color: inherit;
  white-space: pre;
  word-wrap: normal;
}

.rich-content :deep(code) {
  background: #f6f8fa;
  border: 1px solid #d1d9e0;
  border-radius: 3px;
  padding: 2px 6px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 85%;
  color: #e83e8c;
}

.rich-content :deep(pre code) {
  background: transparent;
  border: none;
  padding: 0;
  color: #c9d1d9;
}

/* highlight.js 样式覆盖 */
.rich-content :deep(.hljs) {
  display: block;
  overflow-x: auto;
  padding: 0;
  background: transparent;
}

.rich-content :deep(.hljs-keyword),
.rich-content :deep(.hljs-selector-tag),
.rich-content :deep(.hljs-built_in),
.rich-content :deep(.hljs-name),
.rich-content :deep(.hljs-tag) {
  color: #ff7b72;
}

.rich-content :deep(.hljs-string),
.rich-content :deep(.hljs-title),
.rich-content :deep(.hljs-section),
.rich-content :deep(.hljs-attribute),
.rich-content :deep(.hljs-literal),
.rich-content :deep(.hljs-template-tag),
.rich-content :deep(.hljs-template-variable),
.rich-content :deep(.hljs-type),
.rich-content :deep(.hljs-addition) {
  color: #a5d6ff;
}

.rich-content :deep(.hljs-comment),
.rich-content :deep(.hljs-quote),
.rich-content :deep(.hljs-deletion),
.rich-content :deep(.hljs-meta) {
  color: #8b949e;
}

.rich-content :deep(.hljs-number),
.rich-content :deep(.hljs-regexp),
.rich-content :deep(.hljs-symbol),
.rich-content :deep(.hljs-variable) {
  color: #79c0ff;
}

.rich-content :deep(.hljs-function),
.rich-content :deep(.hljs-title.function_) {
  color: #d2a8ff;
}

/* 富文本编辑器样式 */
.rich-text-editor-wrapper {
  width: 100%;
  display: block;
}

.rich-text-editor {
  width: 85%;
  display: flex;
  flex-direction: column;
}

/* 确保工具栏在顶部 */
.rich-text-editor :deep(.ql-toolbar) {
  order: 1;
  border-bottom: 1px solid #ccc;
}

/* 确保编辑容器在工具栏下方 */
.rich-text-editor :deep(.ql-container) {
  order: 2;
  height: 200px;
  border-top: none;
}

.rich-text-editor :deep(.ql-editor) {
  min-height: 200px;
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
  position: relative;
  z-index: 1;
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

