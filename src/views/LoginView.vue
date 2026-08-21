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

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    alert('请填入账号密码！')
    return
  }

  loading.value = true

  try {
    const resData = await userStore.login(username.value, password.value)

    if (resData.success) {
      router.push('/main')
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

<style scoped>
.login-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 360px;
  max-width: 90%;
}

.login-box h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

.login-box input {
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.login-box input:focus {
  border-color: #667eea;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
