<template>
  <div>
    <div style="margin-bottom: 10px; display: flex; gap: 8px;">
      <el-button type="primary" size="small" @click="handleAdd" :icon="Plus">添加参数</el-button>
      <el-button type="success" size="small" @click="handleBatchImport" :icon="Upload">批量导入</el-button>
      <el-button type="info" size="small" @click="handleExport" :icon="Download">导出</el-button>
    </div>

    <el-table :data="params" border>
      <el-table-column prop="field_name" label="字段名" width="150">
        <template #default="{ row }">
          <el-input v-model="row.field_name" size="small" placeholder="字段名" @blur="handleCellChange" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="参数名称" width="150">
        <template #default="{ row }">
          <el-input v-model="row.name" size="small" placeholder="参数名称" @blur="handleCellChange" />
        </template>
      </el-table-column>
      <el-table-column prop="data_type" label="数据类型" width="120">
        <template #default="{ row }">
          <el-select v-model="row.data_type" size="small" placeholder="类型" @change="handleCellChange">
            <el-option label="string" value="string" />
            <el-option label="int" value="int" />
            <el-option label="float" value="float" />
            <el-option label="boolean" value="boolean" />
            <el-option label="object" value="object" />
            <el-option label="array" value="array" />
            <el-option label="varchar" value="varchar" />
            <el-option label="datetime" value="datetime" />
            <el-option label="date" value="date" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="default_value" label="默认长度" width="120" v-if="paramType === 'input'">
        <template #default="{ row }">
          <el-input v-model="row.default_value" size="small" placeholder="默认长度" @blur="handleCellChange" />
        </template>
      </el-table-column>
      <el-table-column prop="required" label="必填" width="80" v-if="paramType === 'input'">
        <template #default="{ row }">
          <el-checkbox v-model="row.required" @change="handleCellChange" />
        </template>
      </el-table-column>
      
      <el-table-column prop="description" label="描述" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.description" size="small" placeholder="描述" @blur="handleCellChange" />
        </template>
      </el-table-column>
      <el-table-column prop="example" label="示例" width="150">
        <template #default="{ row }">
          <el-input v-model="row.example" size="small" placeholder="示例值" @blur="handleCellChange" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ $index }">
          <el-button type="danger" link size="small" @click="handleDelete($index)" :icon="Delete">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="importDialogVisible" :title="`批量导入${paramType === 'input' ? '入参' : '出参'}`" width="900px">
      <el-alert
        title="使用说明"
        type="info"
        :closable="false"
        style="margin-bottom: 15px;"
      >
        <div style="line-height: 1.8;">
          <p><strong>支持格式：</strong></p>
          <ul style="margin: 5px 0; padding-left: 20px;">
            <li>从 Excel 复制表格数据（制表符分隔）</li>
            <li>CSV 格式（逗号分隔）</li>
            <li>空格分隔的数据</li>
          </ul>
          <p style="margin-top: 10px;"><strong>列顺序建议：</strong>字段名 | 参数名称 | 数据类型 | 默认值/长度 | 必填 | 描述 | 示例</p>
          <p style="margin-top: 5px;"><strong>注意：</strong>第一行可以是表头（会自动识别），也可以直接是数据。数据类型会自动识别常见格式（如 varchar、int、string 等）。</p>
        </div>
      </el-alert>

      <el-form label-width="100px">
        <el-form-item label="粘贴数据">
          <el-input
            v-model="importText"
            type="textarea"
            :rows="10"
            placeholder="请从 Excel 或其他表格中复制数据并粘贴到这里&#10;例如：&#10;patient_id	患者ID	string		是	患者唯一标识	12345&#10;patient_name	患者姓名	varchar	50	是	患者姓名	张三"
            @input="handleImportTextChange"
          />
        </el-form-item>
      </el-form>

      <div v-if="parsedData.length > 0" style="margin-top: 20px;">
        <el-divider>预览（共 {{ parsedData.length }} 条）</el-divider>
        <el-table :data="parsedData" border max-height="300" size="small">
          <el-table-column prop="field_name" label="字段名" width="120" />
          <el-table-column prop="name" label="参数名称" width="120" />
          <el-table-column prop="data_type" label="数据类型" width="100" />
          <el-table-column prop="default_value" label="默认值" width="100" v-if="paramType === 'input'" />
          <el-table-column prop="required" label="必填" width="80" v-if="paramType === 'input'">
            <template #default="{ row }">
              {{ row.required ? '是' : '否' }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="150" />
          <el-table-column prop="example" label="示例" width="120" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmImport" :disabled="parsedData.length === 0">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus, Delete, Upload, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  paramType: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

// 使用ref创建响应式数组，确保数据变化能被正确追踪
const params = ref([])
// 标记是否正在从props更新，避免循环更新
const isUpdatingFromProps = ref(false)

// 批量导入相关
const importDialogVisible = ref(false)
const importText = ref('')
const parsedData = ref([])

// 初始化函数
const initParams = () => {
  const initialValue = props.modelValue || []
  isUpdatingFromProps.value = true
  params.value = initialValue.length > 0 ? initialValue.map(p => ({ ...p })) : []
  isUpdatingFromProps.value = false
}

// 监听props变化，更新本地数据
watch(() => props.modelValue, (newVal, oldVal) => {
  const newLength = newVal?.length || 0
  const currentLength = params.value.length
  
  // 检查数组引用是否改变，或者长度是否改变
  const referenceChanged = newVal !== oldVal
  const lengthChanged = newLength !== currentLength
  
  // 如果引用改变或长度改变，则更新
  const shouldUpdate = referenceChanged || lengthChanged
  
  if (!shouldUpdate) {
    return
  }
  
  // 更新本地数据
  if (newVal && Array.isArray(newVal) && newVal.length > 0) {
    params.value = newVal.map(p => ({ ...p }))
  } else {
    params.value = []
  }
}, { immediate: true })

// 组件挂载时不再需要单独初始化，watch 的 immediate: true 已经处理了

// 添加参数
const handleAdd = () => {
  params.value.push({
    name: '',
    field_name: '',
    data_type: 'string',
    required: false,
    default_value: '',
    description: '',
    example: '',
    order_index: params.value.length,
    dictionary_id: null
  })
  // 使用深拷贝避免引用问题
  emit('update:modelValue', params.value.map(p => ({ ...p })))
}

// 删除参数
const handleDelete = (index) => {
  params.value.splice(index, 1)
  // 更新排序索引
  params.value.forEach((p, i) => {
    p.order_index = i
  })
  // 使用深拷贝避免引用问题
  emit('update:modelValue', params.value.map(p => ({ ...p })))
}

// 处理表格单元格值变化（延迟emit，避免频繁更新）
let updateTimer = null
const handleCellChange = () => {
  // 清除之前的定时器
  if (updateTimer) {
    clearTimeout(updateTimer)
  }
  // 延迟emit，避免每次输入都触发更新
  updateTimer = setTimeout(() => {
    // 使用深拷贝避免引用问题
    const newValue = params.value.map(p => ({ ...p }))
    // 检查值是否真的改变了（避免循环更新）
    const currentValue = props.modelValue || []
    if (JSON.stringify(newValue) !== JSON.stringify(currentValue)) {
      emit('update:modelValue', newValue)
    }
  }, 300)
}

// 打开批量导入对话框
const handleBatchImport = () => {
  importDialogVisible.value = true
  importText.value = ''
  parsedData.value = []
}

// 解析数据类型
const parseDataType = (typeStr) => {
  if (!typeStr) return 'string'
  const lower = typeStr.toLowerCase().trim()
  // 常见类型映射
  const typeMap = {
    'varchar': 'varchar',
    'char': 'varchar',
    'string': 'string',
    'text': 'string',
    'int': 'int',
    'integer': 'int',
    'number': 'int',
    'float': 'float',
    'double': 'float',
    'decimal': 'float',
    'bool': 'boolean',
    'boolean': 'boolean',
    'date': 'date',
    'datetime': 'datetime',
    'timestamp': 'datetime',
    'object': 'object',
    'json': 'object',
    'array': 'array',
    'list': 'array'
  }
  return typeMap[lower] || 'string'
}

// 解析必填字段
const parseRequired = (requiredStr) => {
  if (!requiredStr) return false
  const lower = requiredStr.toString().toLowerCase().trim()
  return lower === '是' || lower === 'yes' || lower === 'true' || lower === '1' || lower === '必填' || lower === 'y'
}

// 检测分隔符
const detectDelimiter = (text) => {
  const lines = text.split('\n').filter(line => line.trim())
  if (lines.length === 0) return '\t'
  
  const firstLine = lines[0]
  const delimiters = ['\t', ',', '|', '  '] // 制表符、逗号、竖线、双空格
  
  let maxCount = 0
  let bestDelimiter = '\t'
  
  for (const delim of delimiters) {
    const count = firstLine.split(delim).length
    if (count > maxCount && count > 1) {
      maxCount = count
      bestDelimiter = delim
    }
  }
  
  return bestDelimiter
}

// 处理导入文本变化
const handleImportTextChange = () => {
  if (!importText.value.trim()) {
    parsedData.value = []
    return
  }
  
  try {
    const lines = importText.value.split('\n').filter(line => line.trim())
    if (lines.length === 0) {
      parsedData.value = []
      return
    }
    
    const delimiter = detectDelimiter(importText.value)
    let startIndex = 0
    
    // 检查第一行是否是表头（如果包含"字段名"、"参数名称"等关键词，则跳过）
    const firstLine = lines[0].toLowerCase()
    if (firstLine.includes('字段') || firstLine.includes('field') || 
        firstLine.includes('参数') || firstLine.includes('param') ||
        firstLine.includes('名称') || firstLine.includes('name') ||
        firstLine.includes('类型') || firstLine.includes('type')) {
      startIndex = 1
    }
    
    const data = []
    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue
      
      const parts = line.split(delimiter).map(p => p.trim())
      if (parts.length < 2) continue // 至少需要字段名和参数名称
      
      // 根据列数智能解析
      // 默认顺序：字段名 | 参数名称 | 数据类型 | 默认值 | 必填 | 描述 | 示例
      const param = {
        field_name: parts[0] || '',
        name: parts[1] || '',
        data_type: parseDataType(parts[2] || 'string'),
        default_value: parts[3] || '',
        required: props.paramType === 'input' ? parseRequired(parts[4] || '') : false,
        description: parts[5] || '',
        example: parts[6] || '',
        order_index: params.value.length + data.length,
        dictionary_id: null
      }
      
      // 如果字段名或参数名称为空，跳过
      if (!param.field_name && !param.name) continue
      
      data.push(param)
    }
    
    parsedData.value = data
  } catch (error) {
    console.error('解析数据失败:', error)
    ElMessage.error('解析数据失败，请检查格式')
    parsedData.value = []
  }
}

// 确认导入
const handleConfirmImport = () => {
  if (parsedData.value.length === 0) {
    ElMessage.warning('没有可导入的数据')
    return
  }
  
  // 批量添加到参数列表
  const startIndex = params.value.length
  parsedData.value.forEach((param, index) => {
    params.value.push({
      ...param,
      order_index: startIndex + index
    })
  })
  
  // 更新排序索引
  params.value.forEach((p, i) => {
    p.order_index = i
  })
  
  // 触发更新
  emit('update:modelValue', params.value.map(p => ({ ...p })))
  
  ElMessage.success(`成功导入 ${parsedData.value.length} 条参数`)
  importDialogVisible.value = false
  importText.value = ''
  parsedData.value = []
}

// 导出参数
const handleExport = () => {
  if (params.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  // 构建 CSV 格式数据
  const headers = ['字段名', '参数名称', '数据类型', '默认值', '必填', '描述', '示例']
  const rows = params.value.map(p => [
    p.field_name || '',
    p.name || '',
    p.data_type || '',
    p.default_value || '',
    props.paramType === 'input' ? (p.required ? '是' : '否') : '',
    p.description || '',
    p.example || ''
  ])
  
  // 转换为 CSV 格式
  const csvContent = [
    headers.join('\t'),
    ...rows.map(row => row.join('\t'))
  ].join('\n')
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `${paramType === 'input' ? '入参' : '出参'}_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('导出成功')
}
</script>

