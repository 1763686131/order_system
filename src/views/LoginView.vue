<template>
  <div class="login-wrapper">
    <main class="auth-page">
      <section class="auth-panel" aria-labelledby="auth-title">
      <header class="auth-header">
        <div class="brand-mark" aria-hidden="true">订</div>
        <div>
          <p class="eyebrow">订单管理系统</p>
          <h1 id="auth-title">
            {{ setupRequired ? '创建超级管理员' : '登录系统' }}
          </h1>
          <p class="auth-subtitle">
            {{
              setupRequired
                ? '当前数据库没有有效的超级管理员，请先完成系统初始化。'
                : '使用已分配的账号进入对应工作台。'
            }}
          </p>
        </div>
      </header>

      <div v-if="checking" class="checking-state">
        正在检查系统初始化状态...
      </div>

      <form v-else-if="setupRequired" class="auth-form" @submit.prevent="handleBootstrap">
        <label class="field">
          <span>管理员姓名</span>
          <input
            v-model.trim="setupForm.displayName"
            autocomplete="name"
            placeholder="用于后台显示和操作留痕"
          />
        </label>
        <label class="field">
          <span>登录账号</span>
          <input
            v-model.trim="setupForm.username"
            autocomplete="username"
            placeholder="请设置超级管理员账号"
          />
        </label>
        <label class="field">
          <span>登录密码</span>
          <input
            v-model="setupForm.password"
            type="password"
            autocomplete="new-password"
            placeholder="至少 8 位"
          />
        </label>
        <label class="field">
          <span>确认密码</span>
          <input
            v-model="setupForm.confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="再次输入登录密码"
          />
        </label>
        <p v-if="message" class="form-message" :class="{ error: messageType === 'error' }">
          {{ message }}
        </p>
        <button class="primary-button" type="submit" :disabled="submitting">
          {{ submitting ? '正在创建...' : '创建超级管理员' }}
        </button>
      </form>

      <form v-else class="auth-form" @submit.prevent="handleLogin">
        <label class="field">
          <span>登录账号</span>
          <input
            ref="loginAccountInput"
            v-model.trim="loginForm.username"
            autocomplete="username"
            placeholder="请输入登录账号"
          />
        </label>
        <label class="field">
          <span>登录密码</span>
          <input
            v-model="loginForm.password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入登录密码"
          />
        </label>
        <p v-if="message" class="form-message" :class="{ error: messageType === 'error' }">
          {{ message }}
        </p>
        <button class="primary-button" type="submit" :disabled="submitting">
          {{ submitting ? '正在登录...' : '登录' }}
        </button>
      </form>
    </section>
  </main>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { getDefaultAdminPath } from '@/utils/adminAccess'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const checking = ref(true)
const setupRequired = ref(false)
const submitting = ref(false)
const message = ref('')
const messageType = ref('info')
const loginAccountInput = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

const setupForm = reactive({
  displayName: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const setMessage = (text, type = 'error') => {
  message.value = text
  messageType.value = type
}

const checkBootstrapStatus = async () => {
  checking.value = true
  try {
    const response = await request.get('/auth/bootstrap-status')
    setupRequired.value = Boolean(response.setupRequired)
  } catch (error) {
    setMessage(error?.response?.data?.message || '无法连接到系统服务')
  } finally {
    checking.value = false
  }
}

const handleBootstrap = async () => {
  if (!setupForm.displayName || !setupForm.username) {
    setMessage('请填写管理员姓名和登录账号')
    return
  }
  if (setupForm.password.length < 8) {
    setMessage('登录密码至少需要 8 位')
    return
  }
  if (setupForm.password !== setupForm.confirmPassword) {
    setMessage('两次输入的密码不一致')
    return
  }

  submitting.value = true
  message.value = ''
  try {
    const response = await request.post('/auth/bootstrap', setupForm)
    loginForm.username = setupForm.username
    loginForm.password = ''
    setupRequired.value = false
    setMessage(response.message || '超级管理员创建成功，请登录', 'success')
    await nextTick()
    loginAccountInput.value?.focus()
  } catch (error) {
    setMessage(error?.response?.data?.message || '创建超级管理员失败')
    if (error?.response?.status === 409) await checkBootstrapStatus()
  } finally {
    submitting.value = false
  }
}

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    setMessage('请输入账号和密码')
    return
  }

  submitting.value = true
  message.value = ''
  try {
    await userStore.login(loginForm.username, loginForm.password)
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : ''
    const target = redirect || (
      userStore.canAccessAdmin ? getDefaultAdminPath(userStore) : '/main'
    )
    await router.replace(target)
  } catch (error) {
    setMessage(error?.response?.data?.message || '登录失败，请检查账号和密码')
  } finally {
    submitting.value = false
  }
}

onMounted(checkBootstrapStatus)
</script>

<style>
/* 覆盖全局 body 样式，确保登录页不受影响 */
body {
  padding: 0 !important;
  overflow: auto !important;
}
</style>

<style scoped>
.login-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
}

.auth-page {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --border: #dfe5ec;
  --text: #172033;
  --text-secondary: #596579;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--text);
  background:
    linear-gradient(90deg, rgba(15, 159, 120, 0.08) 1px, transparent 1px),
    linear-gradient(rgba(15, 159, 120, 0.08) 1px, transparent 1px),
    #f3f6f8;
  background-size: 32px 32px;
}

.auth-panel {
  width: min(100%, 420px);
  padding: 30px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 50px rgba(23, 32, 51, 0.12);
}

.auth-header {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 14px;
  align-items: start;
  margin-bottom: 26px;
}

.brand-mark {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: var(--accent);
  font-size: 22px;
  font-weight: 800;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 24px;
  line-height: 1.3;
}

.auth-subtitle {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.auth-form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 7px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
}

.field input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  outline: none;
  color: var(--text);
  background: #fff;
  font: inherit;
  box-sizing: border-box;
}

.field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.12);
}

.primary-button {
  height: 42px;
  border: 1px solid var(--accent, #0f9f78);
  border-radius: 6px;
  color: #fff;
  background: var(--accent, #0f9f78);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.primary-button:hover:not(:disabled) {
  border-color: var(--accent-dark, #08745a);
  background: var(--accent-dark, #08745a);
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.checking-state,
.form-message {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid #b8eadb;
  border-radius: 6px;
  color: #08745a;
  background: var(--accent-soft);
  font-size: 13px;
  line-height: 1.6;
}

.form-message.error {
  border-color: #f3b8bd;
  color: #b4232f;
  background: #fff2f3;
}

@media (max-width: 520px) {
  .auth-page {
    align-items: start;
    padding: 16px;
  }

  .auth-panel {
    margin-top: 8vh;
    padding: 22px;
  }
}
</style>
