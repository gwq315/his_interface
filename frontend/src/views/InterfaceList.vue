<template>
  <div>
    <!-- 搜索条件传送到header -->
    <Teleport to=".header-center">
      <div class="header-search">
        <el-input v-model="searchForm.keyword" placeholder="搜索接口名称、编码、描述" clearable style="max-width: 250px;" />
        <el-select v-model="searchForm.project_id" placeholder="全部项目" clearable style="width: 200px;">
          <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" @click="handleSearch" :icon="Search">搜索</el-button>
        <el-button type="success" @click="$router.push('/interfaces/add')" :icon="Plus">新增接口</el-button>
      </div>
    </Teleport>
    
    <el-card>
      <template #header>
        <span>接口列表</span>
      </template>

      <el-table :data="interfaceList" v-loading="loading" stripe>
        <el-table-column prop="code" label="接口编码" width="200" />
        <el-table-column prop="name" label="接口名称" min-width="180" />
        <el-table-column prop="interface_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.interface_type === 'api' ? 'success' : 'info'">
              {{ row.interface_type === 'api' ? 'API接口' : '视图接口' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="category" label="分类" width="120" /> -->
        <el-table-column prop="url" label="URL" min-width="200" show-overflow-tooltip />
        <!-- <el-table-column prop="method" label="方法" width="80" /> -->
        <el-table-column prop="status" label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row.id)" :icon="View">查看</el-button>
            <el-button type="warning" link @click="handleEdit(row.id)" :icon="Edit">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row.id)" :icon="Delete">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange" @current-change="handlePageChange" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { interfaceApi } from '../api/interfaces'
import { projectApi } from '../api/projects'
import { getToken } from '../utils/auth'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const dataLoaded = ref(false)
const interfaceList = ref([])
const searchForm = ref({
  keyword: '',
  interface_type: '',
  category: '',
  project_id: undefined
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

// 搜索接口
const handleSearch = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      keyword: searchForm.value.keyword || undefined,
      interface_type: searchForm.value.interface_type || undefined,
      category: searchForm.value.category || undefined,
      project_id: searchForm.value.project_id || undefined
    }
    const response = await interfaceApi.search(params)
    interfaceList.value = response.items
    pagination.value.total = response.total
  } catch (error) {
    ElMessage.error(error.message || '搜索失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const handleReset = () => {
  searchForm.value = {
    keyword: '',
    interface_type: '',
    category: '',
    project_id: undefined
  }
  pagination.value.page = 1
  handleSearch()
}

// 查看详情
const handleView = (id) => {
  router.push(`/interfaces/${id}`)
}

// 编辑
const handleEdit = (id) => {
  router.push(`/interfaces/edit/${id}`)
}

// 删除
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该接口吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await interfaceApi.delete(id)
    ElMessage.success('删除成功')
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 分页变化
const handleSizeChange = () => {
  handleSearch()
}

const handlePageChange = () => {
  handleSearch()
}

const projectOptions = ref([])

// 加载数据的函数
const loadData = async () => {
  // 如果已经加载过，不再重复加载
  if (dataLoaded.value) {
    return
  }
  
  // 检查Token是否存在
  const token = getToken()
  if (!token) {
    return
  }
  
  dataLoaded.value = true
  
  // 加载项目列表
  try {
    projectOptions.value = await projectApi.getList({ limit: 1000 })
  } catch (error) {
    // 如果是401错误，重置dataLoaded状态，以便重试
    if (error.response?.status === 401) {
      dataLoaded.value = false
      return
    }
  }
  // 加载接口列表
  handleSearch()
}

// 监听路由变化，确保在路由完全加载后再加载数据
watch(() => route.path, async () => {
  // 等待下一个tick，确保组件已完全挂载
  await nextTick()
  // 延迟一下，确保Token已准备好
  await new Promise(resolve => setTimeout(resolve, 300))
  loadData()
}, { immediate: false })

onMounted(async () => {
  // 等待下一个tick，确保组件已完全挂载
  await nextTick()
  // 延迟一下，确保Token已准备好
  await new Promise(resolve => setTimeout(resolve, 500))
  loadData()
})
</script>

<style scoped>
.header-search {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
