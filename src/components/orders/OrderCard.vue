<template>
  <div class="order-card" :class="`status-${statusType}`">
    <div class="order-header">
      <div class="order-id">订单 #{{ order.id }}</div>
      <div class="order-type-badge" :class="`type-${order.type}`">
        {{ order.type === 0 ? '中固' : '绝缘' }}
      </div>
    </div>

    <div class="order-body">
      <div class="info-row">
        <span class="label">客户归属：</span>
        <span class="value">{{ order.client || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="label">收货人：</span>
        <span class="value">{{ order.receiver_name || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="label">联系电话：</span>
        <span class="value">{{ order.receiver_phone }}</span>
      </div>
      <div class="info-row">
        <span class="label">收货地址：</span>
        <span class="value address">{{ order.receiver_address }}</span>
      </div>
      <div class="info-row">
        <span class="label">货物信息：</span>
        <span class="value">{{ order.goods_name }}</span>
      </div>
      <div class="info-row">
        <span class="label">重量/数量：</span>
        <span class="value">{{ order.goods_weight }} / {{ order.goods_quantity || '-' }}</span>
      </div>
      <div v-if="order.remark" class="info-row">
        <span class="label">备注：</span>
        <span class="value remark">{{ order.remark }}</span>
      </div>
    </div>

    <div class="order-footer">
      <div class="order-date">{{ formatDate(order.created_at) }}</div>
      <div class="order-actions">
        <button
          v-if="statusType === 'pending'"
          class="btn-action btn-complete"
          @click="$emit('update-status', order.id, 1)"
        >
          完成
        </button>
        <button
          v-if="statusType === 'completed'"
          class="btn-action btn-ship"
          @click="$emit('ship', order.id)"
        >
          出库
        </button>
        <button
          class="btn-action btn-edit"
          @click="$emit('edit', order)"
        >
          编辑
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  order: {
    type: Object,
    required: true
  },
  statusType: {
    type: String,
    required: true
  }
})

defineEmits(['edit', 'delete', 'update-status', 'ship'])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.order-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  border-left: 4px solid #1890ff;
}

.order-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.order-card.status-pending {
  border-left-color: #faad14;
}

.order-card.status-completed {
  border-left-color: #52c41a;
}

.order-card.status-shipped {
  border-left-color: #1890ff;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.order-id {
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.order-type-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.order-type-badge.type-0 {
  background: #e6f7ff;
  color: #1890ff;
}

.order-type-badge.type-1 {
  background: #fff7e6;
  color: #fa8c16;
}

.order-body {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row .label {
  color: #666;
  min-width: 80px;
  flex-shrink: 0;
}

.info-row .value {
  color: #333;
  flex: 1;
}

.info-row .value.address {
  word-break: break-all;
}

.info-row .value.remark {
  color: #fa8c16;
  font-style: italic;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.order-date {
  font-size: 12px;
  color: #999;
}

.order-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-complete {
  background: #52c41a;
  color: white;
}

.btn-complete:hover {
  background: #73d13d;
}

.btn-ship {
  background: #1890ff;
  color: white;
}

.btn-ship:hover {
  background: #40a9ff;
}

.btn-edit {
  background: #f0f0f0;
  color: #333;
}

.btn-edit:hover {
  background: #d9d9d9;
}
</style>
