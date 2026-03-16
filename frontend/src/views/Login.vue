<!-- src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="login-form">
      <h2>AgentHub 登录</h2>
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="0">
        <el-form-item prop="email">
          <el-input 
            v-model="loginForm.email" 
            type="email" 
            placeholder="请输入邮箱"
            size="large"
            clearable
          >
            <template #prefix>📧</template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix>🔒</template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            size="large"
            @click="handleLogin" 
            :loading="loading"
            class="login-btn"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/user'
import { setToken, setUserInfo } from '@/utils/auth'

const router = useRouter()

const loginForm = reactive({
  email: '',
  password: ''
})

const loginRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const loginFormRef = ref(null)
const loading = ref(false)

const handleLogin = async () => {
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loading.value = true
    const res = await login(loginForm)
    
    // 存储token和用户信息
    setToken(res.access_token)
    setUserInfo(res.user_info)
    
    ElMessage.success('登录成功！')
    // 登录成功跳转到主页（新对话页面）
    router.push('/chat')
  } catch (error) {
    ElMessage.error(error || '登录失败，请检查邮箱或密码')
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
  height: 100vh;
  background-color: #f5f5f5;
}

.login-form {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #1989fa;
}

.login-btn {
  width: 100%;
}
</style>