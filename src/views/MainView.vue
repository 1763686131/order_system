<template>
  <div class="main-container">
    <!-- 导航栏 -->
    <NavBar
      :current-tab="currentTab"
      @switch-tab="handleSwitchTab"
    />

    <!-- 内容区域 -->
    <div class="content-wrapper">
      <!-- 未完成订单 -->
      <div v-show="currentTab === 0" class="tab-pane">
        <OrderList
          :orders="orderStore.pendingOrders"
          status-type="pending"
          @refresh="loadOrders"
        />
      </div>

      <!-- 已完成订单 -->
      <div v-show="currentTab === 1" class="tab-pane">
        <OrderList
          :orders="orderStore.completedOrders"
          status-type="completed"
          @refresh="loadOrders"
        />
      </div>

      <!-- 已出库订单 -->
      <div v-show="currentTab === 2" class="tab-pane">
        <OrderList
          :orders="orderStore.shippedOrders"
          status-type="shipped"
          @refresh="loadOrders"
        />
      </div>

      <!-- 原材料数据 -->
      <div v-show="currentTab === 3" class="tab-pane">
        <MaterialTimeline />
      </div>
    </div>

    <!-- 悬浮菜单 -->
    <FloatingMenu />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()
import NavBar from '@/components/layout/NavBar.vue'
import OrderList from '@/components/orders/OrderList.vue'
import MaterialTimeline from '@/components/material/MaterialTimeline.vue'
import FloatingMenu from '@/components/layout/FloatingMenu.vue'

const orderStore = useOrderStore()
const currentTab = ref(0)

const handleSwitchTab = (index) => {
  currentTab.value = index
  orderStore.setCurrentTab(index)
}

const loadOrders = async () => {
  try {
    await orderStore.fetchOrders()
  } catch (error) {
    console.error('Failed to load orders:', error)
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.main-container {
  width: 100%;
  min-height: 100vh;
  background: #f5f7fa;
}

.content-wrapper {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.tab-pane {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
