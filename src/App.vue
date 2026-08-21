<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(() => {
  // 尝试从 localStorage 恢复登录状态
  const savedUser = localStorage.getItem('local_user')
  if (savedUser) {
    try {
      const userData = JSON.parse(savedUser)
      userStore.setUser(userData)
    } catch (e) {
      console.error('Failed to parse user data:', e)
    }
  }
})
</script>

<style>
/* 全局样式已在 main.css 中导入 */
</style>
