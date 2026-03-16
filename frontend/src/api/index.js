import axios from 'axios'
import { getToken, clearAuth } from '@/utils/auth'

const service = axios.create({
  baseURL: 'http://localhost:8000',  // 你的后端地址
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})

// 请求拦截器：添加 Token
service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理错误
service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errMsg = error.response?.data?.detail || '请求失败'
    if (error.response?.status === 401) {
      clearAuth()
      window.location.href = '/'
    }
    return Promise.reject(errMsg)
  }
)

export default service