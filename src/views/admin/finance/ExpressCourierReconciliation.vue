<template>
  <div class="reconciliation-page">
    <!-- 备用金显示栏 -->
    <div class="reserve-fund-bar">
      <div class="fund-info">
        <span class="fund-label">运费备用金：</span>
        <span class="fund-value">¥ {{ currentReserveFund.toFixed(2) }}</span>
      </div>
      <button class="btn-add-fund" @click="showAddFundModal">录入备用金</button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>选择月份：</label>
        <select v-model="selectedYear" class="filter-select" @change="onFilterChange">
          <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
        </select>
        <select v-model="selectedMonth" class="filter-select" @change="onFilterChange">
          <option v-for="month in months" :key="month" :value="month">{{ month }}月</option>
        </select>
      </div>
      <div class="period-display">
        <span class="period-text">{{ currentPeriodText }}</span>
      </div>
      <button class="btn-audit" @click="auditCurrentPeriod">审核</button>
      <button class="btn-export" @click="exportData">导出</button>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="freight-table">
        <thead>
          <tr>
            <th class="col-index">序号</th>
            <th class="col-date sortable" @click="toggleDateSort">
              日期
              <span class="sort-icon">{{ getSortIcon() }}</span>
            </th>
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
            <td colspan="6" class="balance-label">上期备用金转入</td>
            <td></td>
            <td>
              <input
                type="number"
                class="input-paid"
                v-model.number="previousBalance"
                placeholder="0"
              />
            </td>
            <td class="balance-amount negative">¥ {{ previousBalance.toFixed(2) }}</td>
            <td></td>
            <td></td>
            <td></td>
          </tr>

          <!-- 混合显示订单和备用金记录（按日期排序） -->
          <template v-for="(item, index) in mergedOrdersAndFunds" :key="item.id || item.fundId">
            <!-- 订单行 -->
            <tr v-if="item.type === 'order'" :class="getRowClass(item)">
              <td class="col-index">{{ index + 2 }}</td>
              <td class="col-date">{{ formatDate(item.completed_date) }}</td>
              <td class="col-name">{{ item.order_client || '-' }}</td>
              <td class="col-quantity">{{ getTotalWeight(item) }}</td>
              <td class="col-address">
                <span
                  v-if="item.receiver_address && item.receiver_address.length > 6"
                  class="address-text clickable"
                  @click="showAddressDetail(item.receiver_address)"
                >
                  {{ item.receiver_address.substring(0, 6) }}...
              </span>
              <span v-else>{{ order.receiver_address || '-' }}</span>
            </td>
            <td class="col-channel">{{ getShippingMethodText(order) }}</td>
            <td class="col-logistics-no">
              <span v-if="order.logistics_no">{{ order.logistics_no }}</span>
              <span v-else>-</span>
            </td>
            <td class="col-channel">{{ getShippingMethodText(item) }}</td>
            <td class="col-logistics-no">
              <span v-if="item.logistics_no">{{ item.logistics_no }}</span>
              <span v-else>-</span>
            </td>
            <td class="col-price">¥ {{ getFreightAmount(item).toFixed(2) }}</td>
            <td class="col-paid">
              <input type="text" class="input-paid" placeholder="-" />
            </td>
            <td class="col-balance">¥ {{ calculateBalance(index).toFixed(2) }}</td>
            <td class="col-memo"></td>
            <td class="col-return">{{ hasReceipt(item) ? '已传' : '' }}</td>
            <td class="col-remark"></td>
          </tr>

          <!-- 备用金行 -->
          <tr v-else-if="item.type === 'fund'" class="row-fund-entry">
            <td class="col-index">{{ index + 2 }}</td>
            <td class="col-date">{{ formatDate(item.date) }}</td>
            <td colspan="6" class="fund-label">备用金转入{{ item.note ? `（${item.note}）` : '' }}</td>
            <td class="fund-amount">+ {{ item.amount.toFixed(2) }}</td>
            <td></td>
            <td class="col-balance">¥ {{ calculateBalance(index).toFixed(2) }}</td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
        </template>

          <tr v-if="paginatedOrders.length === 0">
            <td colspan="13" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">📦</span>
                <p>暂无数据</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 统计信息 -->
    <div class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">本月笔数：</span>
        <span class="summary-value">{{ totalOrders }} 笔</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">本月运费合计：</span>
        <span class="summary-value total">¥ {{ totalFreight.toFixed(2) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">汇入备用金：</span>
        <span class="summary-value fund">¥ {{ periodReserveFund.toFixed(2) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">月末余额：</span>
        <span class="summary-value balance" :class="{ negative: finalBalance < 0 }">
          ¥ {{ finalBalance.toFixed(2) }}
        </span>
      </div>
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

    <!-- 备用金录入弹窗 -->
    <div v-if="showFundModal" class="modal-overlay" @click="closeFundModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>录入备用金</h3>
          <button class="btn-close" @click="closeFundModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>日期</label>
            <input
              v-model="fundDate"
              type="date"
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <label>金额（¥）</label>
            <input
              v-model="fundAmount"
              type="number"
              step="0.01"
              placeholder="请输入金额"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea
              v-model="fundNote"
              placeholder="选填"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeFundModal">取消</button>
          <button class="btn-confirm" @click="submitReserveFund">确认录入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

// 年份和月份选项
const currentDate = new Date()
const years = ref([2024, 2025, 2026, 2027])
const months = ref([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

// 筛选条件
const selectedYear = ref(currentDate.getFullYear())
const selectedMonth = ref(currentDate.getMonth() + 1)

// 数据
const orders = ref([])
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(50)

// 上期备用金
const previousBalance = ref(-3000.00)

// 当前备用金余额
const currentReserveFund = ref(0)

// 模态框控制
const showFundModal = ref(false)
const fundDate = ref('')
const fundAmount = ref('')
const fundNote = ref('')

// 本期汇入的备用金
const periodReserveFund = ref(0)

// 本期备用金列表（用于渲染独立行）
const periodFundsList = ref([])

// 日期排序状态：'asc' 升序，'desc' 降序，null 不排序
const dateSortOrder = ref('asc')

// 当前期数文本
const currentPeriodText = computed(() => {
  return `${selectedYear.value}年${selectedMonth.value}月对账单`
})

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

  // 只显示零担快运、快递渠道
  result = result.filter(order => {
    const channel = getShippingMethodText(order)
    return channel === '零担快运' || channel === '快递'
  })

  // 月份筛选
  result = result.filter(order => {
    if (!order.completed_date) return false

    const orderDate = new Date(order.completed_date)
    const orderYear = orderDate.getFullYear()
    const orderMonth = orderDate.getMonth() + 1

    return orderYear === selectedYear.value && orderMonth === selectedMonth.value
  })

  // 按日期排序
  if (dateSortOrder.value === 'asc') {
    result.sort((a, b) => {
      const dateA = a.completed_date || ''
      const dateB = b.completed_date || ''
      return dateA.localeCompare(dateB)
    })
  } else if (dateSortOrder.value === 'desc') {
    result.sort((a, b) => {
      const dateA = a.completed_date || ''
      const dateB = b.completed_date || ''
      return dateB.localeCompare(dateA)
    })
  }

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

// 合并订单和备用金记录（按日期排序）
const mergedOrdersAndFunds = computed(() => {
  const merged = []

  // 添加订单（标记为 order 类型）
  paginatedOrders.value.forEach(order => {
    merged.push({
      ...order,
      type: 'order',
      sortDate: order.completed_date || ''
    })
  })

  // 添加备用金记录（标记为 fund 类型）
  periodFundsList.value.forEach(fund => {
    merged.push({
      ...fund,
      type: 'fund',
      fundId: fund.id,
      sortDate: fund.date || ''
    })
  })

  // 根据排序状态排序
  if (dateSortOrder.value === 'asc') {
    merged.sort((a, b) => a.sortDate.localeCompare(b.sortDate))
  } else if (dateSortOrder.value === 'desc') {
    merged.sort((a, b) => b.sortDate.localeCompare(a.sortDate))
  }

  return merged
})

// 统计数据
const totalFreight = computed(() => {
  return filteredOrders.value.reduce((sum, order) => sum + getFreightAmount(order), 0)
})

const finalBalance = computed(() => {
  return periodReserveFund.value - totalFreight.value
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

// 计算累计余额（上期余额 + 当前及之前所有备用金）
const calculateRunningBalance = (fundIndex) => {
  let balance = previousBalance.value
  for (let i = 0; i <= fundIndex; i++) {
    balance += periodFundsList.value[i].amount
  }
  return balance
}

// 切换日期排序
const toggleDateSort = () => {
  if (dateSortOrder.value === null) {
    dateSortOrder.value = 'asc'
  } else if (dateSortOrder.value === 'asc') {
    dateSortOrder.value = 'desc'
  } else {
    dateSortOrder.value = null
  }
}

// 获取排序图标
const getSortIcon = () => {
  if (dateSortOrder.value === 'asc') return '↑'
  if (dateSortOrder.value === 'desc') return '↓'
  return '↕'
}

// 获取第一条数据的日期
const getFirstDate = () => {
  if (paginatedOrders.value.length === 0) return '-'
  return formatDate(paginatedOrders.value[0].completed_date)
}

// 获取行索引
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

// 计算混合列表中的累计余额
const calculateBalance = (index) => {
  let balance = previousBalance.value

  // 遍历到当前索引，计算累计余额
  for (let i = 0; i <= index; i++) {
    const item = mergedOrdersAndFunds.value[i]
    if (item.type === 'order') {
      // 订单：扣除运费
      balance -= getFreightAmount(item)
    } else if (item.type === 'fund') {
      // 备用金：增加金额
      balance += item.amount
    }
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

// 筛选变化
const onFilterChange = () => {
  currentPage.value = 1
  fetchPeriodReserveFund()
}

// 分页操作
const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

// 导出数据
const exportData = () => {
  alert('导出功能开发中...')
}

// 获取备用金余额
const fetchReserveFund = async () => {
  try {
    const response = await request({
      url: '/freight-records/reserve-fund/latest',
      method: 'GET',
      params: { type: 'express-courier' }
    })
    if (response && response.balance !== undefined) {
      currentReserveFund.value = response.balance
    }
  } catch (error) {
    console.error('获取备用金失败:', error)
  }
}

// 获取本月备用金（当前月份内汇入的备用金）
const fetchPeriodReserveFund = async () => {
  try {
    const startDate = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-01`
    const lastDay = new Date(selectedYear.value, selectedMonth.value, 0).getDate()
    const endDate = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

    const response = await request({
      url: '/freight-records/reserve-fund',
      method: 'GET',
      params: {
        type: 'express-courier',
        startDate,
        endDate
      }
    })

    if (response && Array.isArray(response)) {
      periodFundsList.value = response
      periodReserveFund.value = response.reduce((sum, fund) => sum + fund.amount, 0)
    }
  } catch (error) {
    console.error('获取本月备用金失败:', error)
  }
}

// 显示录入备用金弹窗
const showAddFundModal = () => {
  // 设置日期为当前选择月份的第一天
  const year = selectedYear.value
  const month = String(selectedMonth.value).padStart(2, '0')
  fundDate.value = `${year}-${month}-01`
  fundAmount.value = ''
  fundNote.value = ''
  showFundModal.value = true
}

// 关闭备用金弹窗
const closeFundModal = () => {
  showFundModal.value = false
}

// 提交备用金
const submitReserveFund = async () => {
  if (!fundDate.value) {
    alert('请选择日期')
    return
  }

  if (!fundAmount.value || isNaN(fundAmount.value)) {
    alert('请输入有效的金额')
    return
  }

  try {
    const response = await request({
      url: '/freight-records/reserve-fund',
      method: 'POST',
      data: {
        type: 'express-courier',
        date: fundDate.value,
        amount: parseFloat(fundAmount.value),
        note: fundNote.value
      }
    })

    if (response && response.success) {
      alert('备用金录入成功')
      closeFundModal()
      await fetchReserveFund()
      await fetchPeriodReserveFund()
    }
  } catch (error) {
    console.error('录入备用金失败:', error)
    alert('录入备用金失败')
  }
}

// 审核当前月份
const auditCurrentPeriod = async () => {
  if (filteredOrders.value.length === 0) {
    alert('当前月份没有数据，无法审核')
    return
  }

  const confirmMsg = `确认审核 ${currentPeriodText.value} 吗？\n共 ${totalOrders.value} 笔订单，运费合计 ¥${totalFreight.value.toFixed(2)}`

  if (!confirm(confirmMsg)) {
    return
  }

  try {
    // 构建完整的订单信息数组
    const orderDetails = filteredOrders.value.map(order => ({
      id: order.id,
      date: order.completed_date,
      client: order.order_client || '-',
      weight: order.goods_weight || '-',
      address: order.receiver_address || '-',
      channel: getShippingMethodText(order),
      logisticsNo: order.logistics_no || '-',
      freight: getFreightAmount(order),
      hasReceipt: hasReceipt(order)
    }))

    const response = await request({
      url: '/freight-records',
      method: 'POST',
      data: {
        type: 'express-courier',
        year: selectedYear.value,
        month: selectedMonth.value,
        period: null,
        orders: orderDetails,
        totalAmount: totalFreight.value,
        reserveFund: finalBalance.value,
        orderCount: totalOrders.value,
        periodFund: periodReserveFund.value
      }
    })

    if (response && response.success) {
      alert('审核成功！运费记录已保存')
    }
  } catch (error) {
    console.error('审核失败:', error)
    alert('审核失败')
  }
}

onMounted(() => {
  fetchOrders()
  fetchReserveFund()
  fetchPeriodReserveFund()
})
</script>

<style scoped>
.reconciliation-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 备用金显示栏 */
.reserve-fund-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.fund-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fund-label {
  font-size: 16px;
  color: #6b7280;
  font-weight: 500;
}

.fund-value {
  font-size: 20px;
  font-weight: 600;
  color: #059669;
}

.btn-add-fund {
  padding: 8px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-add-fund:hover {
  background: #2563eb;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-item label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  cursor: pointer;
}

.filter-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.period-display {
  flex: 1;
  text-align: center;
}

.period-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
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
}

.btn-export:hover {
  background: #059669;
}

.btn-audit {
  padding: 8px 20px;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-audit:hover {
  background: #d97706;
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

/* 可排序的表头 */
.freight-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.freight-table th.sortable:hover {
  background: #f3f4f6;
}

.sort-icon {
  margin-left: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.freight-table td {
  padding: 10px 16px;
  font-size: 13px;
  color: #1f2937;
  border-bottom: 1px solid #e5e7eb;
  border-left: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
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
  background: #ffffff;
  font-weight: 600;
}

.row-balance-transfer:hover {
  background: #f9fafb;
}

/* 备用金录入行样式 */
.row-fund-entry {
  background: #ffffff;
  font-weight: 500;
}

.row-fund-entry:hover {
  background: #f9fafb;
}

.row-fund-entry td {
  border-left: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
}

.fund-label {
  text-align: center;
  color: #1f2937;
}

.fund-amount {
  color: #10b981;
  font-weight: 600;
  text-align: center;
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

/* 统计栏 */
.summary-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 32px;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-label {
  font-size: 14px;
  color: #6b7280;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.summary-value.total {
  color: #059669;
}

.summary-value.fund {
  color: #3b82f6;
}

.summary-value.balance {
  color: #059669;
}

.summary-value.balance.negative {
  color: #dc2626;
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

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.btn-close {
  font-size: 24px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  resize: vertical;
}

.form-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel {
  padding: 8px 20px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-confirm {
  padding: 8px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-confirm:hover {
  background: #2563eb;
}
</style>
