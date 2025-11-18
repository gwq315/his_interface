<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h2>系统登录</h2>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码（可选）"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button link type="primary" @click="$router.push('/register')" style="width: 100%">
            还没有账号？立即注册
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/auth'
import { setToken, setUser, getToken } from '../utils/auth'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [] // 密码可选
}

const handleLogin = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  loading.value = true
  try {
    const result = await authApi.login(form.username, form.password || undefined)
    if (result && result.access_token) {
      // 记录登录时间，用于判断是否是登录后立即的请求失败
      window.__lastLoginTime = Date.now()
      
      // 保存Token和用户信息
      setToken(result.access_token)
      setUser(result.user)
      
      ElMessage.success('登录成功')
      
      // 等待一下，确保Token已保存到localStorage并且请求拦截器能读取到
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 跳转到原页面或首页
      const redirect = route.query.redirect || '/'
      // 使用replace而不是push，避免在历史记录中留下登录页
      await router.replace(redirect)
    } else {
      ElMessage.error('登录失败：未收到有效的Token')
    }
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || '登录失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

.login-header {
  text-align: center;
}

.login-header h2 {
  margin: 0;
  color: #333;
}
</style>

