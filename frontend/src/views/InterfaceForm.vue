<template>
  <div>
    <el-card>
      <template #header>
        <span>{{ isEdit ? '编辑接口' : '新增接口' }}</span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="10">
          <el-col :span="6">
            <el-form-item label="所属项目" prop="project_id">
              <el-select v-model="form.project_id" placeholder="请选择项目" filterable clearable style="width: 320px;">
                <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="接口类型" prop="interface_type">
              <el-radio-group v-model="form.interface_type">
                <el-radio value="view">视图接口</el-radio>
                <el-radio value="api">API接口</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="HTTP方法" v-if="form.interface_type === 'api'">
              <el-select v-model="form.method" placeholder="请选择" clearable>
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="10">
          <el-col :span="6">
            <el-form-item label="接口编码" prop="code">
              <el-input v-model="form.code" placeholder="请输入接口编码" :disabled="isEdit" />
            </el-form-item>
          </el-col>

          <el-col :span="10">
            <el-form-item label="接口名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入接口名称" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio value="active">启用</el-radio>
                <el-radio value="inactive">禁用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="10">
          <el-col :span="6">
            <el-form-item label="分类">
              <el-input v-model="form.category" placeholder="请输入分类" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="标签">
              <el-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="接口URL">
          <el-input v-model="form.url" placeholder="请输入接口URL" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入接口描述" />
        </el-form-item>

        <!-- 参数管理 -->
        <el-divider>参数管理</el-divider>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="入参" name="input">
            <ParameterTable v-model="form.parameters.input" param-type="input" />
          </el-tab-pane>
          <el-tab-pane label="出参" name="output">
            <ParameterTable v-model="form.parameters.output" param-type="output" />
          </el-tab-pane>
          <el-tab-pane label="入参示例" name="input_example">
            <el-form-item label="入参示例" label-width="0">
              <el-input
                v-model="form.input_example"
                type="textarea"
                :rows="20"
                placeholder="请输入入参样例（JSON或XML格式）&#10;JSON示例：&#10;{&#10;  &quot;patient_id&quot;: &quot;123456&quot;,&#10;  &quot;name&quot;: &quot;张三&quot;&#10;}"
                style="font-family: 'Courier New', monospace;"
              />
            </el-form-item>
          </el-tab-pane>
          <el-tab-pane label="出参示例" name="output_example">
            <el-form-item label="出参示例" label-width="0">
              <el-input
                v-model="form.output_example"
                type="textarea"
                :rows="20"
                placeholder="请输入出参样例（JSON或XML格式）&#10;JSON示例：&#10;{&#10;  &quot;code&quot;: 200,&#10;  &quot;data&quot;: {&#10;    &quot;patient_id&quot;: &quot;123456&quot;,&#10;    &quot;name&quot;: &quot;张三&quot;&#10;  }&#10;}"
                style="font-family: 'Courier New', monospace;"
              />
            </el-form-item>
          </el-tab-pane>
          <el-tab-pane label="视图定义" name="view_definition">
            <el-form-item label="视图定义" label-width="0">
              <el-input
                v-model="form.view_definition"
                type="textarea"
                :rows="25"
                placeholder="请输入数据库视图的SQL定义（纯文本格式）&#10;例如：&#10;CREATE VIEW v_patient AS&#10;SELECT id, name, age FROM patients WHERE status = 'active';"
                style="font-family: 'Courier New', monospace;"
              />
            </el-form-item>
          </el-tab-pane>
          <el-tab-pane label="备注说明" name="notes">
            <el-form-item label="备注说明" label-width="0">
              <div style="border: 1px solid #dcdfe6; border-radius: 4px;">
                <QuillEditor
                  v-model:content="form.notes"
                  contentType="html"
                  :options="editorOptions"
                  style="height: 400px;"
                />
              </div>
              <div style="margin-top: 8px; color: #909399; font-size: 12px;">
                支持富文本编辑，可以插入图片、表格、链接等。用于记录常见操作说明、错误提示等。
              </div>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>

        <el-form-item style="margin-top: 30px;">
          <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { interfaceApi } from '../api/interfaces'
import { projectApi } from '../api/projects'
import ParameterTable from '../components/ParameterTable.vue'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const formRef = ref(null)
const submitting = ref(false)
const activeTab = ref('input')

const form = reactive({
  project_id: undefined,
  code: '',
  name: '',
  interface_type: 'api',
  method: 'POST',
  url: '',
  category: '',
  tags: '',
  status: 'active',
  description: '',
  input_example: '',
  output_example: '',
  view_definition: '',
  notes: '',
  parameters: {
    input: [],
    output: []
  }
})

// 富文本编辑器配置
const editorOptions = {
  theme: 'snow',
  placeholder: '请输入备注说明，支持富文本格式...',
  modules: {
    toolbar: [
      [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }],
      [{ 'align': [] }],
      ['link', 'image', 'video'],
      ['blockquote', 'code-block'],
      ['clean']
    ]
  }
}

const rules = {
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  code: [{ required: true, message: '请输入接口编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入接口名称', trigger: 'blur' }],
  interface_type: [{ required: true, message: '请选择接口类型', trigger: 'change' }]
}

// 加载接口数据
const loadInterface = async () => {
  try {
    const interfaceId = route.params.id
    if (!interfaceId) {
      ElMessage.error('接口ID不存在')
      router.back()
      return
    }

    const data = await interfaceApi.getById(interfaceId)
    console.log('InterfaceForm: API response data:', data)
    console.log('InterfaceForm: Parameters from API:', data.parameters)

    form.project_id = data.project?.id || data.project_id
    form.code = data.code
    form.name = data.name
    form.interface_type = data.interface_type
    form.method = data.method || 'POST'
    form.url = data.url || ''
    form.category = data.category || ''
    form.tags = data.tags || ''
    form.status = data.status
    form.description = data.description || ''
    form.input_example = data.input_example || ''
    form.output_example = data.output_example || ''
    form.view_definition = data.view_definition || ''
    form.notes = data.notes || ''

    // 分离入参和出参 - 确保正确处理数据
    const parameters = data.parameters || []
    console.log('InterfaceForm: Total parameters:', parameters.length)

    // 清空现有参数
    form.parameters.input = []
    form.parameters.output = []

    // 处理入参
    const inputParams = parameters
      .filter(p => p.param_type === 'input')
      .map(p => ({
        name: p.name || '',
        field_name: p.field_name || '',
        data_type: p.data_type || 'string',
        required: p.required !== undefined ? p.required : false,
        default_value: p.default_value || '',
        description: p.description || '',
        example: p.example || '',
        order_index: p.order_index !== undefined ? p.order_index : 0,
        dictionary_id: p.dictionary_id || null
      }))
      .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))

    // 处理出参
    const outputParams = parameters
      .filter(p => p.param_type === 'output')
      .map(p => ({
        name: p.name || '',
        field_name: p.field_name || '',
        data_type: p.data_type || 'string',
        required: false,
        default_value: '',
        description: p.description || '',
        example: p.example || '',
        order_index: p.order_index !== undefined ? p.order_index : 0,
        dictionary_id: p.dictionary_id || null
      }))
      .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))

    // 使用 nextTick 确保响应式更新
    await nextTick()

    // 直接替换数组，创建新数组引用以触发子组件的 watcher
    // 使用深拷贝避免引用问题
    form.parameters.input = inputParams.map(p => ({ ...p }))
    form.parameters.output = outputParams.map(p => ({ ...p }))

    // 再次等待 DOM 更新
    await nextTick()

    console.log('InterfaceForm: Processed input parameters:', form.parameters.input.length, 'items')
    console.log('InterfaceForm: Processed output parameters:', form.parameters.output.length, 'items')
    console.log('InterfaceForm: Form parameters object:', form.parameters)
  } catch (error) {
    console.error('Load interface error details:', error)
    console.error('Error response:', error.response)
    console.error('Error message:', error.message)
    const errorMsg = error.response?.data?.detail || error.message || '加载失败'
    ElMessage.error(errorMsg)
    // 不要立即返回，让用户看到错误信息
    // router.back()
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    submitting.value = true

    const submitData = {
      project_id: form.project_id,
      code: form.code,
      name: form.name,
      interface_type: form.interface_type,
      method: form.method,
      url: form.url,
      category: form.category,
      tags: form.tags,
      status: form.status,
      description: form.description,
      input_example: form.input_example,
      output_example: form.output_example,
      view_definition: form.view_definition || null,
      notes: form.notes || null,
      parameters: [
        // 过滤掉空参数（name 和 field_name 都为空或只有空格的参数）
        ...form.parameters.input
          .filter(p => {
            const hasName = p.name && p.name.trim()
            const hasFieldName = p.field_name && p.field_name.trim()
            return hasName || hasFieldName
          })
          .map((p, index) => {
            const name = (p.name && p.name.trim()) || `参数${index + 1}`
            const fieldName = (p.field_name && p.field_name.trim()) || `param_${index}`
            return {
              name: name,
              field_name: fieldName,
              data_type: (p.data_type && p.data_type.trim()) || 'string',
              param_type: 'input',
              required: p.required !== undefined ? Boolean(p.required) : false,
              default_value: (p.default_value && p.default_value.trim()) || null,
              description: (p.description && p.description.trim()) || null,
              example: (p.example && p.example.trim()) || null,
              order_index: p.order_index !== undefined ? Number(p.order_index) : index,
              dictionary_id: p.dictionary_id ? Number(p.dictionary_id) : null
            }
          }),
        ...form.parameters.output
          .filter(p => {
            const hasName = p.name && p.name.trim()
            const hasFieldName = p.field_name && p.field_name.trim()
            return hasName || hasFieldName
          })
          .map((p, index) => {
            const name = (p.name && p.name.trim()) || `参数${form.parameters.input.length + index + 1}`
            const fieldName = (p.field_name && p.field_name.trim()) || `param_${form.parameters.input.length + index}`
            return {
              name: name,
              field_name: fieldName,
              data_type: (p.data_type && p.data_type.trim()) || 'string',
              param_type: 'output',
              required: false,
              default_value: (p.default_value && p.default_value.trim()) || null,
              description: (p.description && p.description.trim()) || null,
              example: (p.example && p.example.trim()) || null,
              order_index: p.order_index !== undefined ? Number(p.order_index) : form.parameters.input.length + index,
              dictionary_id: p.dictionary_id ? Number(p.dictionary_id) : null
            }
          })
      ]
    }

    console.log('InterfaceForm: Submitting data:', {
      ...submitData,
      parameters_count: submitData.parameters.length,
      input_count: form.parameters.input.length,
      output_count: form.parameters.output.length
    })

    if (isEdit.value) {
      const interfaceId = route.params.id
      if (!interfaceId) {
        ElMessage.error('接口ID不存在')
        return
      }
      await interfaceApi.update(interfaceId, submitData)
      ElMessage.success('更新成功')
    } else {
      try {
        await interfaceApi.create(submitData)
        ElMessage.success('创建成功')
      } catch (error) {
        // 详细记录错误信息
        console.error('Create interface error:', error)
        console.error('Error response:', error.response)
        console.error('Error data:', error.response?.data)
        
        // 处理 FastAPI 验证错误和业务逻辑错误
        let errorMessage = '创建失败'
        if (error.response?.data) {
          const errorData = error.response.data
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // Pydantic 验证错误
              const errors = errorData.detail.map(e => {
                const field = e.loc ? e.loc.join('.') : 'unknown'
                return `${field}: ${e.msg}`
              }).join('; ')
              errorMessage = `验证失败: ${errors}`
            } else if (typeof errorData.detail === 'string') {
              // 业务逻辑错误（如编码已存在）
              errorMessage = errorData.detail
            }
          }
        } else if (error.message) {
          errorMessage = error.message
        }
        
        // 显示错误信息（如果是编码已存在，显示更长时间）
        if (errorMessage.includes('接口编码') && errorMessage.includes('已存在')) {
          ElMessage.error({
            message: errorMessage,
            duration: 5000,
            showClose: true
          })
        } else {
          ElMessage.error(errorMessage)
        }
        throw error // 重新抛出以便上层处理
      }
    }

    // 跳转到接口列表页面
    router.push({ name: 'InterfaceListRoute' })
  } catch (error) {
    if (error !== false) { // 表单验证失败会返回false
      ElMessage.error(error.message || '保存失败')
    }
  } finally {
    submitting.value = false
  }
}

const projectOptions = ref([])

onMounted(async () => {
  // 加载项目选项
  try {
    projectOptions.value = await projectApi.getList({ limit: 1000 })
  } catch (e) {
    // 忽略下拉失败
  }
  // 如果是编辑模式，加载接口数据
  if (isEdit.value) {
    await loadInterface()
  }
})
</script>
