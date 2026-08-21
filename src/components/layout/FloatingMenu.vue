<template>
  <div class="fab-container">
    <!-- 悬浮菜单 -->
    <transition name="fab-menu">
      <div v-show="menuOpen" class="fab-menu">
        <div
          v-if="userStore.hasPerm('material.add')"
          class="fab-item"
          @click="handleAction('addMaterial')"
        >
          录入原材料数据
        </div>
        <div
          v-if="userStore.hasPerm('pending.add')"
          class="fab-item"
          @click="handleAction('addOrder')"
        >
          录入订单信息
        </div>
        <div class="fab-item" @click="handleAction('searchOrder')">
          搜索订单
        </div>
        <div
          v-if="userStore.hasPerm('system.user_manage')"
          class="fab-item"
          @click="handleAction('manageUsers')"
        >
          账户控制
        </div>
        <div class="fab-item" style="color: #ff4d4f;" @click="handleLogout">
          退出登录
        </div>
      </div>
    </transition>

    <!-- AI 气泡 -->
    <transition name="bubble">
      <div v-show="bubbleVisible" class="ai-speech-bubble">
        {{ bubbleText }}
      </div>
    </transition>

    <!-- AI 小圆脸 -->
    <div
      class="ai-face"
      :class="{ active: menuOpen }"
      @click="toggleMenu"
    >
      <div class="face-inner">
        <div class="eye left"></div>
        <div class="eye right"></div>
        <div class="mouth"></div>
      </div>
    </div>

    <!-- 弹窗组件 -->
    <CreateOrderModal v-model:visible="showCreateOrder" />
    <SearchOrderModal v-model:visible="showSearchOrder" />
    <UploadMaterialModal v-model:visible="showUploadMaterial" />
    <UserManageModal v-model:visible="showUserManage" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import CreateOrderModal from '@/components/orders/CreateOrderModal.vue'
import SearchOrderModal from '@/components/orders/SearchOrderModal.vue'
import UploadMaterialModal from '@/components/material/UploadMaterialModal.vue'
import UserManageModal from '@/components/user/UserManageModal.vue'

const router = useRouter()
const userStore = useUserStore()

const menuOpen = ref(false)
const bubbleVisible = ref(false)
const bubbleText = ref('准备接入大模型...')

const showCreateOrder = ref(false)
const showSearchOrder = ref(false)
const showUploadMaterial = ref(false)
const showUserManage = ref(false)

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const handleAction = (action) => {
  menuOpen.value = false

  switch (action) {
    case 'addMaterial':
      showUploadMaterial.value = true
      break
    case 'addOrder':
      showCreateOrder.value = true
      break
    case 'searchOrder':
      showSearchOrder.value = true
      break
    case 'manageUsers':
      showUserManage.value = true
      break
  }
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout()
    router.push('/login')
  }
}

onMounted(() => {
  setTimeout(() => {
    bubbleText.value = `欢迎回来，${userStore.name || userStore.username} 主人！`
    bubbleVisible.value = true
    setTimeout(() => {
      bubbleVisible.value = false
    }, 4000)
  }, 1000)
})
</script>

<style scoped>
.fab-container {
  position: fixed;
  right: 30px;
  bottom: 30px;
  z-index: 1000;
}

.fab-menu {
  position: absolute;
  bottom: 80px;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  min-width: 180px;
}

.fab-item {
  padding: 14px 20px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.fab-item:last-child {
  border-bottom: none;
}

.fab-item:hover {
  background: #f5f5f5;
}

.ai-face {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-face:hover {
  transform: scale(1.1);
}

.ai-face.active {
  transform: rotate(90deg);
}

.face-inner {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye {
  position: absolute;
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  top: 18px;
}

.eye.left {
  left: 16px;
}

.eye.right {
  right: 16px;
}

.mouth {
  position: absolute;
  width: 20px;
  height: 10px;
  border: 2px solid white;
  border-top: none;
  border-radius: 0 0 20px 20px;
  bottom: 14px;
}

.ai-speech-bubble {
  position: absolute;
  bottom: 80px;
  right: 70px;
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 13px;
  color: #333;
  white-space: nowrap;
  max-width: 250px;
}

.ai-speech-bubble::after {
  content: '';
  position: absolute;
  bottom: 20px;
  right: -8px;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 8px 0 8px 8px;
  border-color: transparent transparent transparent white;
}

/* 动画 */
.fab-menu-enter-active,
.fab-menu-leave-active {
  transition: all 0.3s;
}

.fab-menu-enter-from,
.fab-menu-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.bubble-enter-active,
.bubble-leave-active {
  transition: all 0.3s;
}

.bubble-enter-from,
.bubble-leave-to {
  opacity: 0;
  transform: scale(0.8);
}
</style>
