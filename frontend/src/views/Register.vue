<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="register-header">
          <h2>人员登记</h2>
        </div>
      </template>
      
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名（用于登录）" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码（可选，不限制长度）"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="form.confirmPassword" 
            type="password" 
            placeholder="请再次输入密码（如果填写了密码）"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width: 100%">
            注册
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button link type="primary" @click="$router.push('/login')" style="width: 100%">
            已有账号？立即登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  name: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  // 如果填写了密码，需要确认密码一致
  if (form.password && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { max: 100, message: '姓名长度不能超过100个字符', trigger: 'blur' }
  ],
  password: [
    // 密码可选，不限制长度
  ],
  confirmPassword: [
    // 确认密码可选，但如果填写了密码，需要确认
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  
  // 如果填写了密码但确认密码不一致，提示错误
  if (form.password && form.password !== form.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  loading.value = true
  try {
    await authApi.register({
      username: form.username,
      name: form.name,
      password: form.password || undefined, // 如果密码为空，传undefined
      role: 'user' // 默认注册为普通用户
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 500px;
}

.register-header {
  text-align: center;
}

.register-header h2 {
  margin: 0;
  color: #333;
}
</style>

