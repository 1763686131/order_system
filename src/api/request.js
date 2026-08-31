import axios from 'axios'
import { useUserStore } from '@/stores/user'

// 根据环境设置 baseURL
const getBaseURL = () => {
  // 生产环境：使用相对路径（前端和后端在同一域名下）
  // 开发环境：使用 Vite 代理
  if (import.meta.env.PROD) {
    // 生产环境：假设前端和后端在同一服务器
    return '/api'
  } else {
    // 开发环境：通过 Vite 代理
    return '/api'
  }
}

const request = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.isLoggedIn) {
      config.headers['Username'] = String(userStore.username)
      config.headers['Role'] = String(userStore.role)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default request
