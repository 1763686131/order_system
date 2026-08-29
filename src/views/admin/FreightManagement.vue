<template>
  <div class="freight-management">
    <!-- 数据表格 -->
    <div class="table-container">
      <table class="freight-table">
        <thead>
          <tr>
            <th class="col-index">序号</th>
            <th class="col-date">日期</th>
            <th class="col-name">名称</th>
            <th class="col-quantity">数量 (kg)</th>
            <th class="col-address">收货地址</th>
            <th class="col-channel">渠道</th>
            <th class="col-logistics-no">车牌号/单号</th>
            <th class="col-price">价格 (¥)</th>
            <th class="col-paid">已支付</th>
            <th class="col-balance">备用金合计</th>
            <th class="col-memo">货跟</th>
            <th class="col-return">回单回传</th>
            <th class="col-remark">备注</th>
          </tr>
        </thead>
        <tbody>
          <!-- 上期备用金转入行 -->
          <tr v-if="paginatedOrders.length > 0" class="row-balance-transfer">
            <td class="col-index">1</td>
            <td class="col-date">{{ getFirstDate() }}</td>
            <td colspan="7" class="balance-label">上期备用金转入</td>
            <td class="balance-amount negative">¥ {{ previousBalance.toFixed(2) }}</td>
            <td class="balance-amount negative">¥ {{ previousBalance.toFixed(2) }}</td>
            <td></td>
            <td></td>
            <td></td>
          </tr>

          <!-- 数据行 -->
          <tr v-for="(order, index) in paginatedOrders" :key="order.id" :class="getRowClass(order)">
            <td class="col-index">{{ getRowIndex(index) }}</td>
            <td class="col-date">{{ formatDate(order.completed_date) }}</td>
            <td class="col-name">{{ order.order_client || '-' }}</td>
            <td class="col-quantity">{{ getTotalWeight(order) }}</td>
            <td class="col-address">
              <span
                v-if="order.receiver_address && order.receiver_address.length > 6"
                class="address-text clickable"
                @click="showAddressDetail(order.receiver_address)"
              >
                {{ order.receiver_address.substring(0, 6) }}...
              </span>
              <span v-else>{{ order.receiver_address || '-' }}</span>
            </td>
            <td class="col-channel">{{ getShippingMethodText(order) }}</td>
            <td class="col-logistics-no">
              <span v-if="order.logistics_no">{{ order.logistics_no }}</span>
              <span v-else>-</span>
            </td>
            <td class="col-price">¥ {{ getFreightAmount(order).toFixed(2) }}</td>
            <td class="col-paid">
              <input type="text" class="input-paid" placeholder="-" />
            </td>
            <td class="col-balance">¥ {{ getRunningBalance(index).toFixed(2) }}</td>
            <td class="col-memo"></td>
            <td class="col-return">{{ hasReceipt(order) ? '已传' : '' }}</td>
            <td class="col-remark"></td>
          </tr>

          <tr v-if="paginatedOrders.length === 0">
            <td colspan="13" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">📦</span>
                <p>暂无运费数据</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <div class="pagination-info">
        <span>共 {{ totalOrders }} 条记录</span>
      </div>
      <div class="pagination-controls">
        <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

// 当前用户
const currentUser = computed(() => userStore.user?.username || '管理员')

// 筛选
const filters = ref({
  startDate: '',
  endDate: '',
  channel: '' // 货拉拉/物流/运满满
})

// 数据
const orders = ref([])
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(50)

// 上期备用金
const previousBalance = ref(-6383.61)

// 加载订单数据
const fetchOrders = async () => {
  loading.value = true
  try {
    const response = await request({
      url: '/orders',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      // 只显示已出库且有运费数据的订单
      orders.value = response.filter(order =>
        order.status === 'shipped' &&
        order.freight_costs &&
        Array.isArray(order.freight_costs) &&
        order.freight_costs.length > 0
      )
    }
  } catch (error) {
    console.error('获取订单失败:', error)
  } finally {
    loading.value = false
  }
}

// 筛选后的订单
const filteredOrders = computed(() => {
  let result = [...orders.value]

  // 日期筛选
  if (filters.value.startDate) {
    result = result.filter(order => {
      const orderDate = order.completed_date ? order.completed_date.split(' ')[0] : ''
      return orderDate >= filters.value.startDate
    })
  }
  if (filters.value.endDate) {
    result = result.filter(order => {
      const orderDate = order.completed_date ? order.completed_date.split(' ')[0] : ''
      return orderDate <= filters.value.endDate
    })
  }

  // 渠道筛选
  if (filters.value.channel) {
    result = result.filter(order => {
      const channel = getShippingMethodText(order)
      return channel === filters.value.channel
    })
  }

  // 按日期排序
  result.sort((a, b) => {
    const dateA = a.completed_date || ''
    const dateB = b.completed_date || ''
    return dateA.localeCompare(dateB)
  })

  return result
})

// 分页数据
const totalOrders = computed(() => filteredOrders.value.length)
const totalPages = computed(() => Math.ceil(totalOrders.value / pageSize.value))
const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredOrders.value.slice(start, end)
})

// 获取运费金额
const getFreightAmount = (order) => {
  if (!order.freight_costs || !Array.isArray(order.freight_costs)) return 0
  const freightItem = order.freight_costs.find(item => item.type === 'freight')
  return freightItem ? (freightItem.amount || 0) : 0
}

// 获取总重量
const getTotalWeight = (order) => {
  return order.goods_weight || '-'
}

// 获取发货方式
// 获取发货方式（与物流列表保持一致）
const getShippingMethodText = (order) => {
  const methodMap = { 0: '物流', 1: '零担快运', 2: '快递', 3: '专车', 4: '其它' }

  if (order.shipping_method !== undefined && order.shipping_method !== '') {
    let method = methodMap[order.shipping_method] || '其它'
    if (order.shipping_method === 4 && order.shipping_custom) {
      method = order.shipping_custom
    }
    return method
  } else if (order.logistics_type) {
    return order.logistics_type
  }
  return '其它'
}

// 判断是否有回单
const hasReceipt = (order) => {
  return order.receipt_img_url && order.receipt_img_url.trim() !== ''
}

// 显示地址详情
const showAddressDetail = (address) => {
  alert(`收货地址：\n${address}`)
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = dateStr.split(' ')[0]
  const parts = date.split('-')
  if (parts.length === 3) {
    return `${parseInt(parts[1])}月${parseInt(parts[2])}日`
  }
  return date
}

// 获取第一条数据的日期
const getFirstDate = () => {
  if (paginatedOrders.value.length === 0) return '-'
  return formatDate(paginatedOrders.value[0].shipped_date)
}

// 获取行索引（加上上期备用金行）
const getRowIndex = (index) => {
  return index + 2
}

// 获取累计余额
const getRunningBalance = (index) => {
  let balance = previousBalance.value
  for (let i = 0; i <= index; i++) {
    balance -= getFreightAmount(paginatedOrders.value[i])
  }
  return balance
}

// 获取行样式类
const getRowClass = (order) => {
  const clientName = order.order_client || ''
  if (clientName.includes('余总')) {
    return 'row-highlight-red'
  }
  return ''
}

// 分页操作
const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    channel: ''
  }
  currentPage.value = 1
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.freight-management {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 标题栏 */
.page-header {
  text-align: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

/* 信息栏 */
.info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.info-left,
.info-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #1f2937;
}

.date-input {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.date-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.date-separator {
  color: #9ca3af;
}

/* 操作按钮栏 */
.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.btn-action {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
  font-weight: 500;
}

.btn-unpaid {
  background: #a855f7;
}

.btn-unpaid:hover {
  background: #9333ea;
}

.btn-logistics {
  background: #3b82f6;
}

.btn-logistics:hover {
  background: #2563eb;
}

.btn-full {
  background: #10b981;
}

.btn-full:hover {
  background: #059669;
}

.btn-reset {
  padding: 8px 20px;
  background: #f3f4f6;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-reset:hover {
  background: #e5e7eb;
}

.btn-export {
  padding: 8px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  margin-left: auto;
}

.btn-export:hover {
  background: #059669;
}

/* 表格 */
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
  margin-bottom: 16px;
}

.freight-table {
  width: 100%;
  border-collapse: collapse;
}

.freight-table th {
  padding: 12px 16px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.freight-table td {
  padding: 10px 16px;
  font-size: 13px;
  color: #1f2937;
  border-bottom: 1px solid #e5e7eb;
  text-align: center;
}

.freight-table tbody tr:hover {
  background: #f9fafb;
}

/* 列宽 */
.col-index { width: 60px; }
.col-date { width: 100px; }
.col-name { width: 150px; }
.col-quantity { width: 100px; }
.col-address { width: 220px; text-align: left; }
.col-channel { width: 90px; }
.col-logistics-no { width: 140px; }
.col-price { width: 100px; }
.col-paid { width: 100px; }
.col-balance { width: 120px; }
.col-memo { width: 80px; }
.col-return { width: 100px; }
.col-remark { width: 120px; }

/* 输入框 */
.input-paid {
  width: 80px;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  text-align: center;
  outline: none;
  transition: all 0.3s;
}

.input-paid:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 地址可点击 */
.address-text.clickable {
  color: #3b82f6;
  cursor: pointer;
  text-decoration: underline;
}

.address-text.clickable:hover {
  color: #2563eb;
}

/* 特殊行样式 */
.row-balance-transfer {
  background: #dbeafe;
  font-weight: 600;
}

.row-balance-transfer:hover {
  background: #bfdbfe;
}

.row-highlight-red {
  background: #fee2e2;
}

.row-highlight-red:hover {
  background: #fecaca;
}

.balance-label {
  text-align: center;
  font-weight: 600;
  color: #1f2937;
}

.balance-amount {
  font-weight: 600;
}

.balance-amount.negative {
  color: #dc2626;
}

.col-address {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
}

.empty-content p {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-info {
  font-size: 14px;
  color: #6b7280;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-btn {
  padding: 6px 16px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}
</style>
