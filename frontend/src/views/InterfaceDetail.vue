<template>
  <div>
    <el-card v-loading="loading">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>接口详情</span>
          <div>
            <el-button @click="$router.back()">返回</el-button>
            <el-button type="primary" @click="handleEdit">编辑</el-button>
          </div>
        </div>
      </template>

      <div v-if="interfaceData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="接口编码">{{ interfaceData.code }}</el-descriptions-item>
          <el-descriptions-item label="接口名称">{{ interfaceData.name }}</el-descriptions-item>
          <el-descriptions-item label="接口类型">
            <el-tag :type="interfaceData.interface_type === 'api' ? 'success' : 'info'">
              {{ interfaceData.interface_type === 'api' ? 'API接口' : '视图接口' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="HTTP方法">{{ interfaceData.method || '-' }}</el-descriptions-item>
          <el-descriptions-item label="接口URL">{{ interfaceData.url || '-' }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ interfaceData.category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标签">{{ interfaceData.tags || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="interfaceData.status === 'active' ? 'success' : 'info'">
              {{ interfaceData.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ interfaceData.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 备注说明 -->
        <div v-if="interfaceData.notes" style="margin-top: 30px;">
          <h3>备注说明</h3>
          <div 
            v-html="interfaceData.notes" 
            style="padding: 15px; background-color: #f5f7fa; border-radius: 4px; border: 1px solid #e4e7ed;"
          ></div>
        </div>

        <!-- 视图定义 -->
        <div v-if="interfaceData.view_definition" style="margin-top: 30px;">
          <h3>视图定义</h3>
          <el-input
            :model-value="interfaceData.view_definition || ''"
            type="textarea"
            :rows="10"
            readonly
            placeholder="暂无视图定义"
            style="font-family: 'Courier New', monospace;"
          />
        </div>

        <!-- 参数示例 -->
        <div style="margin-top: 30px;">
          <h3>参数示例</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <div style="margin-bottom: 16px;">
                <h4 style="margin-bottom: 8px; color: #606266;">入参示例</h4>
                <el-input
                  :model-value="interfaceData.input_example || ''"
                  type="textarea"
                  :rows="8"
                  readonly
                  placeholder="暂无入参示例"
                  style="font-family: 'Courier New', monospace;"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div style="margin-bottom: 16px;">
                <h4 style="margin-bottom: 8px; color: #606266;">出参示例</h4>
                <el-input
                  :model-value="interfaceData.output_example || ''"
                  type="textarea"
                  :rows="8"
                  readonly
                  placeholder="暂无出参示例"
                  style="font-family: 'Courier New', monospace;"
                />
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 入参 -->
        <div style="margin-top: 30px;">
          <h3>入参</h3>
          <el-table :data="inputParams" border style="margin-top: 10px;">
            <el-table-column prop="field_name" label="字段名" width="150" />
            <el-table-column prop="name" label="参数名称" width="150" />
            <el-table-column prop="data_type" label="数据类型" width="100" />
            <el-table-column prop="default_value" label="数据长度" width="120" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="example" label="示例" width="150" />
          </el-table>
        </div>

        <!-- 出参 -->
        <div style="margin-top: 30px;">
          <h3>出参</h3>
          <el-table :data="outputParams" border style="margin-top: 10px;">
            <el-table-column prop="field_name" label="字段名" width="150" />
            <el-table-column prop="name" label="参数名称" width="150" />
            <el-table-column prop="data_type" label="数据类型" width="100" />
            <el-table-column prop="description" label="描述" min-width="300" />
            <el-table-column prop="example" label="示例" width="150" />
          </el-table>
        </div>

        <!-- 关联字典 -->
        <div v-if="interfaceData.dictionaries && interfaceData.dictionaries.length > 0" style="margin-top: 30px;">
          <h3>关联字典</h3>
          <el-table :data="interfaceData.dictionaries" border style="margin-top: 10px;">
            <el-table-column prop="code" label="字典编码" width="150" />
            <el-table-column prop="name" label="字典名称" width="200" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="字典值" width="200">
              <template #default="{ row }">
                <el-button type="primary" link @click="showDictionaryValues(row)">查看字典值</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 字典值对话框 -->
    <el-dialog v-model="dictDialogVisible" title="字典值" width="600px">
      <el-table :data="currentDictValues" border>
        <el-table-column prop="key" label="键" width="150" />
        <el-table-column prop="value" label="值" width="200" />
        <el-table-column prop="description" label="描述" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { interfaceApi } from '../api/interfaces'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const interfaceData = ref(null)
const dictDialogVisible = ref(false)
const currentDictValues = ref([])

const inputParams = computed(() => {
  if (!interfaceData.value) return []
  return interfaceData.value.parameters
    .filter(p => p.param_type === 'input')
    .sort((a, b) => a.order_index - b.order_index)
})

const outputParams = computed(() => {
  if (!interfaceData.value) return []
  return interfaceData.value.parameters
    .filter(p => p.param_type === 'output')
    .sort((a, b) => a.order_index - b.order_index)
})

// 加载接口详情
const loadInterface = async () => {
  loading.value = true
  try {
    interfaceData.value = await interfaceApi.getById(route.params.id)
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 编辑
const handleEdit = () => {
  router.push(`/interfaces/edit/${route.params.id}`)
}

// 显示字典值
const showDictionaryValues = (dictionary) => {
  currentDictValues.value = dictionary.values || []
  dictDialogVisible.value = true
}

onMounted(() => {
  loadInterface()
})
</script>

<style scoped>
h3 {
  margin-bottom: 10px;
  color: #409eff;
}
</style>

