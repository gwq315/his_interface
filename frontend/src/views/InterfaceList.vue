<template>
  <div>
    <div style="margin-bottom: 20px;">
      <el-card>
        <el-form :model="searchForm" inline>
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="搜索接口名称、编码、描述" clearable style="width: 300px;" />
          </el-form-item>
          <el-form-item label="项目">
            <el-select v-model="searchForm.project_id" placeholder="全部项目" clearable style="width: 200px;">
              <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <!-- <el-form-item label="接口类型">
            <el-select v-model="searchForm.interface_type" placeholder="全部" clearable style="width: 150px;">
              <el-option label="视图接口" value="view" />
              <el-option label="API接口" value="api" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-input
              v-model="searchForm.category"
              placeholder="分类"
              clearable
              style="width: 150px;"
            />
          </el-form-item> -->
          <el-form-item>
            <el-button type="primary" @click="handleSearch" :icon="Search">搜索</el-button>
            <el-button @click="handleReset" :icon="Refresh">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <el-card>
      <!-- <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>接口列表</span>
          <el-button type="primary" @click="$router.push('/interfaces/add')" :icon="Plus">新增接口</el-button>
        </div>
      </template> -->
      <template #header>
        <div style="display: flex; align-items: center; gap: 20px;">
          <span>接口列表</span>

          <el-button type="primary" @click="$router.push('/interfaces/add')" :icon="Plus">新增接口</el-button>

        </div>
      </template>

      <el-table :data="interfaceList" v-loading="loading" stripe>
        <el-table-column prop="code" label="接口编码" width="120" />
        <el-table-column prop="name" label="接口名称" min-width="180" />
        <el-table-column prop="interface_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.interface_type === 'api' ? 'success' : 'info'">
              {{ row.interface_type === 'api' ? 'API接口' : '视图接口' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="category" label="分类" width="120" /> -->
        <el-table-column prop="url" label="URL" min-width="100" show-overflow-tooltip />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { interfaceApi } from '../api/interfaces'
import { projectApi } from '../api/projects'

const router = useRouter()

const loading = ref(false)
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

onMounted(async () => {
  // 加载项目列表
  try {
    projectOptions.value = await projectApi.getList({ limit: 1000 })
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
  // 加载接口列表
  handleSearch()
})
</script>
