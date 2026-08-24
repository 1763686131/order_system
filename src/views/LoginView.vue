<template>
  <div class="login-overlay">
    <div class="login-box">
      <h2>系统登录</h2>
      <input
        v-model="username"
        placeholder="请输入账号ID"
        @keyup.enter="handleLogin"
      />
      <input
        v-model="password"
        type="password"
        placeholder="请输入密码"
        @keyup.enter="handleLogin"
      />
      <button
        class="btn-primary"
        @click="handleLogin"
        :disabled="loading"
      >
        {{ loading ? '登录中...' : '登 录' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useNomiStore } from '@/stores/nomi'

const router = useRouter()
const userStore = useUserStore()
const nomiStore = useNomiStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  const usernameInput = username.value.trim()
  const passwordInput = password.value.trim()
  if (!usernameInput || !passwordInput) {
    alert('请填入账号密码！')
    return
  }

  loading.value = true

  try {
    const resData = await userStore.login(usernameInput, passwordInput)

    if (resData.success) {
      router.push('/main')
      setTimeout(() => {
        nomiStore.showWelcomeMessage(`欢迎回来，${userStore.name || userStore.username} 主人！`)
      }, 1000)
    } else {
      alert(resData.message || '凭证错误，登录失败')
    }
  } catch (error) {
    console.error('Login error:', error)
    alert('本地服务端连接失败，请检查系统。')
  } finally {
    loading.value = false
  }
}
</script>
