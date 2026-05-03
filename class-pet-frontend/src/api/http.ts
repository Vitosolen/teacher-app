import axios, { AxiosError, type AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

export const http: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

// 请求拦截：注入 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 跳登录，其他错误统一弹 toast
// 例外：登录/注册接口的错误一律交给组件自行处理（避免错误被吞）
http.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError<{ detail?: string }>) => {
    const url = error.config?.url ?? ''
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/register')

    if (isAuthCall) {
      // 登录/注册失败由 LoginView 内联展示
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else {
      const detail = error.response?.data?.detail
      ElMessage.error(detail || error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)
