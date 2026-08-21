<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="searchOrderModal"
      class="search-modal-overlay"
    >
      <span class="search-close-btn" @click="handleClose">&times;</span>
      <div class="search-modal-wrapper">
        <div class="search-header-area">
          <div class="search-input-pill-group">
            <input
              v-model="searchQuery"
              type="text"
              id="searchInput"
              class="search-pill-input"
              placeholder="请输入订单号、客户姓名或电话..."
              autocomplete="off"
              @keyup.enter="performSearch"
            />
            <button class="search-pill-btn" @click="performSearch">搜索</button>
          </div>
        </div>

        <div id="searchResults" class="search-results-list">
          <div v-if="searching" style="text-align: center; padding: 40px; color: #999;">
            搜索中...
          </div>
          <div v-else-if="searchResults.length === 0 && hasSearched" style="text-align: center; padding: 40px; color: #999;">
            未找到匹配的订单
          </div>
          <div v-else-if="searchResults.length > 0">
            <div
              v-for="order in searchResults"
              :key="order.id"
              class="search-result-item"
              @click="viewOrderDetail(order)"
            >
              <div class="search-result-header">
                <span class="search-result-id">订单 #{{ order.id }}</span>
                <span class="search-result-status" :class="getStatusClass(order.status)">
                  {{ getStatusText(order.status) }}
                </span>
              </div>
              <div class="search-result-body">
                <div class="search-result-row">
                  <strong>客户:</strong> {{ order.order_client || '未命名' }}
                </div>
                <div class="search-result-row">
                  <strong>收货人:</strong> {{ order.receiver_name || '未填' }} - {{ order.receiver_phone || '未填' }}
                </div>
                <div class="search-result-row">
                  <strong>日期:</strong> {{ order.date || '未知' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'

const visible = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const hasSearched = ref(false)

const orderStore = useOrderStore()

// 执行搜索
const performSearch = () => {
  const query = searchQuery.value.trim()
  if (!query) return

  searching.value = true
  hasSearched.value = true

  // 从 orderStore 中搜索
  const allOrders = orderStore.allOrders
  const results = allOrders.filter(order => {
    const idMatch = order.id && order.id.toString().includes(query)
    const clientMatch = order.order_client && order.order_client.toLowerCase().includes(query.toLowerCase())
    const nameMatch = order.receiver_name && order.receiver_name.toLowerCase().includes(query.toLowerCase())
    const phoneMatch = order.receiver_phone && order.receiver_phone.includes(query)

    return idMatch || clientMatch || nameMatch || phoneMatch
  })

  setTimeout(() => {
    searchResults.value = results
    searching.value = false
  }, 300)
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    pending: '未完成',
    completed: '已完成',
    shipped: '已出库'
  }
  return statusMap[status] || '未知'
}

// 获取状态样式类
const getStatusClass = (status) => {
  return `status-${status}`
}

// 查看订单详情
const viewOrderDetail = (order) => {
  handleClose()
  // 触发编辑订单弹窗
  window.openEditOrderModal(order.id)
}

// 打开弹窗
const open = () => {
  searchQuery.value = ''
  searchResults.value = []
  hasSearched.value = false
  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 暴露方法
defineExpose({
  open
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('open-search-order-modal', () => {
    open()
  })
})
</script>

<style scoped>
.search-result-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.search-result-item:hover {
  background: #f5f5f5;
}

.search-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.search-result-id {
  font-weight: bold;
  color: #333;
}

.search-result-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-completed {
  background: #e6f7ff;
  color: #1890ff;
}

.status-shipped {
  background: #f6ffed;
  color: #52c41a;
}

.search-result-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-result-row {
  font-size: 14px;
  color: #666;
}
</style>
