<template>
  <div class="purchase-orders">
    <div class="page-header">
      <h2>采购订单</h2>
      <button class="btn-primary" @click="createOrder">
        <span class="icon">+</span>
        新增采购订单
      </button>
    </div>

    <div class="filters">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索采购订单号、供应商..."
        class="search-input"
      />
      <select v-model="statusFilter" class="filter-select">
        <option value="">全部状态</option>
        <option value="pending">待确认</option>
        <option value="confirmed">已确认</option>
        <option value="partial">部分入库</option>
        <option value="completed">已完成</option>
        <option value="cancelled">已取消</option>
      </select>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>采购单号</th>
            <th>供应商</th>
            <th>采购日期</th>
            <th>总金额</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredOrders.length === 0">
            <td colspan="6" class="empty-state">暂无采购订单</td>
          </tr>
          <tr v-for="order in filteredOrders" :key="order.id">
            <td>{{ order.orderNo }}</td>
            <td>{{ order.supplierName }}</td>
            <td>{{ formatDate(order.purchaseDate) }}</td>
            <td class="amount">¥{{ order.totalAmount.toFixed(2) }}</td>
            <td>
              <span :class="['status-badge', order.status]">
                {{ getStatusText(order.status) }}
              </span>
            </td>
            <td class="actions">
              <button @click="viewOrder(order.id)" class="btn-text">查看</button>
              <button @click="editOrder(order.id)" class="btn-text">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const searchQuery = ref('')
const statusFilter = ref('')
const orders = ref([])

const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    const matchesSearch = !searchQuery.value ||
      order.orderNo.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      order.supplierName.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesStatus = !statusFilter.value || order.status === statusFilter.value

    return matchesSearch && matchesStatus
  })
})

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待确认',
    confirmed: '已确认',
    partial: '部分入库',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const createOrder = () => {
  router.push('/admin/purchase/orders/create')
}

const viewOrder = (id) => {
  router.push(`/admin/purchase/orders/${id}`)
}

const editOrder = (id) => {
  router.push(`/admin/purchase/orders/edit/${id}`)
}
</script>

<style scoped>
.purchase-orders {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input,
.filter-select {
  padding: 10px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

.search-input:focus,
.filter-select:focus {
  border-color: #38bdf8;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 14px;
  color: #334155;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 60px 0 !important;
}

.amount {
  font-weight: 600;
  color: #0f172a;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.confirmed {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.partial {
  background: #e0e7ff;
  color: #4338ca;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.cancelled {
  background: #f3f4f6;
  color: #6b7280;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn-text {
  background: none;
  border: none;
  color: #38bdf8;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.btn-text:hover {
  color: #0ea5e9;
  text-decoration: underline;
}
</style>
