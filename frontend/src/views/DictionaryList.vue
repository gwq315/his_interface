<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>字典管理</span>
          <el-button type="primary" @click="handleAdd" :icon="Plus">新增字典</el-button>
        </div>
      </template>

      <div style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
        <el-select v-model="projectId" placeholder="全部项目" clearable style="width: 220px;">
          <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索字典名称/编码/描述" clearable style="max-width: 260px;" />
        <el-button type="primary" @click="loadDictionaries" :loading="loading">查询</el-button>
      </div>

      <el-table :data="dictionaryList" v-loading="loading" stripe>
        <el-table-column prop="code" label="字典编码" width="140" />
        <el-table-column prop="name" label="字典名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="字典值数量" width="120">
          <template #default="{ row }">
            {{ row.values?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewValues(row)" :icon="View">查看值</el-button>
            <el-button type="warning" link @click="handleEdit(row)" :icon="Edit">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row.id)" :icon="Delete">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 字典值对话框 -->
    <el-dialog v-model="dictDialogVisible" title="字典值" width="600px">
      <el-table :data="currentDictValues" border>
        <el-table-column prop="key" label="键" width="150" />
        <el-table-column prop="value" label="值" width="200" />
        <el-table-column prop="description" label="描述" />
      </el-table>
    </el-dialog>

    <!-- 新增/编辑字典对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑字典' : '新增字典'" width="720px" :close-on-press-escape="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="项目" prop="project_id">
          <el-select v-model="form.project_id" placeholder="请选择项目" filterable clearable style="width: 320px;">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="10">
        <el-form-item label="字典编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入字典编码" :disabled="isEdit" />
        </el-form-item>
        </el-col>
        <el-col :span="14">
        <el-form-item label="字典名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入字典名称" />
        </el-form-item> 
        </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>

        <el-divider>字典值（可选）</el-divider>
        <div class="values-toolbar">
          <el-button size="small" type="primary" @click="addValueRow">新增行</el-button>
        </div>
        <el-table :data="form.values" size="small" border>
          <el-table-column label="#" width="50">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="键" width="180">
            <template #default="{ row }">
              <el-input v-model="row.key" placeholder="键" />
            </template>
          </el-table-column>
          <el-table-column label="值" width="220">
            <template #default="{ row }">
              <el-input v-model="row.value" placeholder="值" />
            </template>
          </el-table-column>
          <el-table-column label="描述">
            <template #default="{ row }">
              <el-input v-model="row.description" placeholder="描述" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90">
            <template #default="{ $index }">
              <el-button link type="danger" @click="removeValueRow($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="submitDictionary">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { dictionaryApi } from '../api/dictionaries'
import { projectApi } from '../api/projects'

const loading = ref(false)
const dictionaryList = ref([])
const dictDialogVisible = ref(false)
const currentDictValues = ref([])

// 新增/编辑对话框数据
const dialogVisible = ref(false)
const dialogSaving = ref(false)
const isEdit = ref(false)
const editingDictionaryId = ref(null)
const formRef = ref()
const form = ref({
  project_id: undefined,
  name: '',
  code: '',
  description: '',
  interface_id: undefined,
  values: []
})
const rules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  name: [{ required: true, message: '请输入字典名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入字典编码', trigger: 'blur' }]
}

// 加载字典列表
const keyword = ref('')
const projectId = ref()
const projectOptions = ref([])

const loadDictionaries = async () => {
  loading.value = true
  try {
    dictionaryList.value = await dictionaryApi.getList({ project_id: projectId.value || undefined, keyword: keyword.value || undefined })
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  editingDictionaryId.value = null
  form.value = { project_id: undefined, name: '', code: '', description: '', interface_id: undefined, values: [] }
  dialogVisible.value = true
}

const addValueRow = () => {
  form.value.values.push({ key: '', value: '', description: '', order_index: (form.value.values?.length || 0) + 1 })
}

const removeValueRow = (idx) => {
  form.value.values.splice(idx, 1)
}

const submitDictionary = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  dialogSaving.value = true
  try {
    // 仅提交有内容的字典值
    const values = (form.value.values || []).filter(v => v.key && v.value).map((v, idx) => ({
      key: v.key,
      value: v.value,
      description: v.description || '',
      order_index: v.order_index || idx + 1
    }))
    
    if (isEdit.value) {
      // 编辑模式：更新字典基本信息和字典值
      await dictionaryApi.update(editingDictionaryId.value, {
        project_id: form.value.project_id,
        name: form.value.name,
        description: form.value.description || '',
        interface_id: form.value.interface_id || undefined
      })
      
      // 批量更新字典值
      if (values.length > 0) {
        await dictionaryApi.batchUpdateValues(editingDictionaryId.value, values)
      } else {
        // 如果没有字典值，清空所有字典值
        await dictionaryApi.batchUpdateValues(editingDictionaryId.value, [])
      }
      
      ElMessage.success('更新成功')
    } else {
      // 新增模式
      await dictionaryApi.create({
        project_id: form.value.project_id,
        name: form.value.name,
        code: form.value.code,
        description: form.value.description || '',
        interface_id: form.value.interface_id || undefined,
        values
      })
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    await loadDictionaries()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    dialogSaving.value = false
  }
}

// 查看字典值
const handleViewValues = (dictionary) => {
  currentDictValues.value = dictionary.values || []
  dictDialogVisible.value = true
}

// 编辑
const handleEdit = async (row) => {
  isEdit.value = true
  editingDictionaryId.value = row.id
  
  try {
    // 加载字典详情（包含字典值）
    const dictionary = await dictionaryApi.getById(row.id)
    
    // 填充表单数据
    form.value = {
      project_id: dictionary.project_id,
      name: dictionary.name,
      code: dictionary.code,
      description: dictionary.description || '',
      interface_id: dictionary.interface_id || undefined,
      values: (dictionary.values || []).map(v => ({
        id: v.id,
        key: v.key,
        value: v.value,
        description: v.description || '',
        order_index: v.order_index || 0
      }))
    }
    
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.message || '加载字典详情失败')
  }
}

// 删除
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该字典吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await dictionaryApi.delete(id)
    ElMessage.success('删除成功')
    loadDictionaries()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

onMounted(async () => {
  // 加载项目列表
  try {
    projectOptions.value = await projectApi.getList({ limit: 1000 })
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
  // 加载字典列表
  loadDictionaries()
})
</script>

<style scoped>
.values-toolbar { margin-bottom: 8px; }
</style>

