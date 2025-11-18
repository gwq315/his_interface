<template>
  <el-container v-if="showLayout" style="height: 100vh">
    <el-header style="background-color: #409eff; color: white; display: flex; align-items: center; justify-content: space-between; padding: 0 20px;">
      <h1 style="margin: 0; font-size: 20px;">医院HIS系统接口文档管理系统</h1>
      <div style="display: flex; align-items: center; gap: 15px;">
        <span v-if="currentUser">{{ currentUser.name }} ({{ currentUser.role === 'admin' ? '管理员' : '普通人员' }})</span>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="140px" style="background-color: #f5f5f5; border-right: 1px solid #e4e7ed;">
        <el-menu :default-active="activeMenu" router style="border-right: none;">
          <el-menu-item index="/projects">
            <el-icon>
              <Folder />
            </el-icon>
            <span>项目管理</span>
          </el-menu-item>
          <el-menu-item index="/">
            <el-icon>
              <Document />
            </el-icon>
            <span>接口列表</span>
          </el-menu-item>
          <!-- <el-menu-item index="/interfaces/add">
            <el-icon>
              <Plus />
            </el-icon>
            <span>新增接口</span>
          </el-menu-item> -->
          <el-menu-item index="/dictionaries">
            <el-icon>
              <Collection />
            </el-icon>
            <span>字典管理</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon>
              <FolderOpened />
            </el-icon>
            <span>文档/截图</span>
          </el-menu-item>
          <el-menu-item index="/faqs">
            <el-icon>
              <QuestionFilled />
            </el-icon>
            <span>常见问题</span>
          </el-menu-item>

        </el-menu>
      </el-aside>
      <el-main style="padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
  <router-view v-else />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Collection, Folder, FolderOpened, QuestionFilled } from '@element-plus/icons-vue'
import { getUser, removeToken, setUser, getToken } from './utils/auth'
import { authApi } from './api/auth'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const currentUser = ref(null)
let tokenVerificationTimer = null

// 是否显示布局（登录和注册页面不显示布局）
const showLayout = computed(() => {
  return route.path !== '/login' && route.path !== '/register'
})

// 验证Token的函数
const verifyToken = async (skipDelay = false) => {
  // 清除之前的定时器
  if (tokenVerificationTimer) {
    clearTimeout(tokenVerificationTimer)
    tokenVerificationTimer = null
  }
  
  // 只在非登录/注册页面时验证Token
  if (route.path === '/login' || route.path === '/register') {
    return
  }
  
  const token = getToken()
  const user = getUser()
  
  if (!token) {
    // 没有Token且不在登录页，跳转到登录页
    if (route.path !== '/login') {
      router.push('/login')
    }
    return
  }
  
  if (user) {
    currentUser.value = user
  }
  
  // 延迟验证Token，避免登录后立即验证导致循环
  // skipDelay为true时立即验证（用于路由切换时）
  const delay = skipDelay ? 0 : 1000
  tokenVerificationTimer = setTimeout(async () => {
    // 再次检查路由和Token
    const currentPath = route.path
    const currentToken = getToken()
    
    if (currentPath === '/login' || currentPath === '/register' || !currentToken) {
      return
    }
    
    try {
      const userInfo = await authApi.getCurrentUser()
      currentUser.value = userInfo
      // 更新本地存储的用户信息
      setUser(userInfo)
    } catch (error) {
      // Token无效，清除本地存储
      removeToken()
      currentUser.value = null
      // 如果不在登录页，跳转到登录页
      if (currentPath !== '/login') {
        router.push('/login')
      }
    }
  }, delay)
}

// 监听路由变化，在路由切换时验证Token（跳过延迟，因为路由已经切换完成）
watch(() => route.path, (newPath, oldPath) => {
  // 如果是从登录页跳转过来的，延迟验证，给Token保存和请求准备时间
  if (oldPath === '/login' || oldPath === '/register') {
    // 从登录页跳转过来，延迟更长时间，确保Token已准备好
    setTimeout(() => {
      verifyToken(false) // 使用延迟
    }, 1500) // 延迟1.5秒，确保登录流程完全完成
  } else {
    verifyToken(true) // 立即验证
  }
}, { immediate: false })

onMounted(() => {
  // 首次加载时延迟验证
  verifyToken(false)
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    removeToken()
    currentUser.value = null
    ElMessage.success('退出成功')
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('退出失败:', error)
    }
  }
}
</script>
