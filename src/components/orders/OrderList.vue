<template>
  <div class="order-list">
    <div v-if="orders.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <p>暂无订单数据</p>
    </div>
    <div v-else class="order-grid">
      <OrderCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        :status-type="statusType"
        @edit="handleEdit"
        @delete="handleDelete"
        @update-status="handleUpdateStatus"
        @ship="handleShip"
      />
    </div>
  </div>
</template>

<script setup>
import OrderCard from './OrderCard.vue'

defineProps({
  orders: {
    type: Array,
    default: () => []
  },
  statusType: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const handleEdit = (order) => {
  // 触发编辑事件
  console.log('Edit order:', order)
}

const handleDelete = (orderId) => {
  if (confirm('确定要删除此订单吗？')) {
    // 调用删除 API
    emit('refresh')
  }
}

const handleUpdateStatus = (orderId, newStatus) => {
  // 更新订单状态
  emit('refresh')
}

const handleShip = (orderId) => {
  // 打开出库弹窗
  console.log('Ship order:', orderId)
}
</script>

<style scoped>
.order-list {
  min-height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #999;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.order-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .order-grid {
    grid-template-columns: 1fr;
  }
}
</style>
