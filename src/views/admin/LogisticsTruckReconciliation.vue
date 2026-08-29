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
        <label>选择期数：</label>
        <select v-model="selectedYear" class="filter-select" @change="onFilterChange">
          <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
        </select>
        <select v-model="selectedMonth" class="filter-select" @change="onFilterChange">
          <option v-for="month in months" :key="month" :value="month">{{ month }}月</option>
        </select>
        <select v-model="selectedPeriod" class="filter-select" @change="onFilterChange">
          <option value="1-10">1-10日</option>
          <option value="11-20">11-20日</option>
          <option value="21-31">21-31日</option>
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
            <th class="col-name">客户</th>
            <th class="col-goods">货物信息</th>
            <th class="col-quantity">数量 (kg)</th>
            <th class="col-address">收货地址</th>
            <th class="col-channel">渠道</th>
            <th class="col-logistics-no">车牌号/单号</th>
            <th class="col-price">价格 (¥)</th>
            <th class="col-paid">已支付</th>
            <th class="col-balance">备用金合计</th>
            <th class="col-return">回单回传</th>
            <th class="col-remark">备注</th>
          </tr>
        </thead>
        <tbody>
          <!-- 混合显示订单和备用金记录（按日期排序） -->
          <template v-for="(item, index) in mergedOrdersAndFunds" :key="item.itemType === 'order' ? `order-${item.id}-${item.freightCostIndex}` : `fund-${item.id}`">
            <!-- 订单行 -->
            <tr v-if="item.itemType === 'order'" :class="getRowClass(item)">
              <!-- 只在第一笔运费时显示前面的列，使用 rowspan 合并 -->
              <template v-if="item.freightCostIndex === 0">
                <td class="col-index" :rowspan="item.freightCostTotal">{{ getDisplayIndex(index) }}</td>
                <td class="col-date" :rowspan="item.freightCostTotal">{{ formatDate(item.completed_date) }}</td>
                <td class="col-name" :rowspan="item.freightCostTotal">{{ item.order_client || '-' }}</td>
                <td class="col-goods" :rowspan="item.freightCostTotal">{{ getGoodsName(item) }}</td>
                <td class="col-quantity" :rowspan="item.freightCostTotal">{{ getTotalWeight(item) }}</td>
                <td class="col-address" :rowspan="item.freightCostTotal">
                  <div class="expandable-cell">
                    <span class="cell-text">{{ (item.receiver_address || '-').substring(0, 6) }}</span>
                    <span
                      v-if="item.receiver_address && item.receiver_address.length > 6"
                      class="expand-icon"
                      @click="showAddressDetail(item.receiver_address)"
                    >
                      ▼
                    </span>
                  </div>
                </td>
              </template>
              <!-- 从渠道开始，每笔运费都显示 -->
              <td class="col-channel">{{ getChannelName(item) }}</td>
              <td class="col-logistics-no">{{ getLogisticsNumber(item) }}</td>
              <td class="col-price">¥ {{ getFreightAmountForRow(item).toFixed(2) }}</td>
              <td class="col-paid">
                <!-- 编辑状态 -->
                <input
                  v-if="editingOrderId === item.id && editingFreightIndex === item.freightCostIndex"
                  type="number"
                  class="input-paid"
                  v-model.number="editingPaidAmount"
                  @keyup.enter="savePaidAmount(item)"
                  @blur="cancelOrderEdit"
                />
                <!-- 显示状态 -->
                <span
                  v-else
                  class="paid-amount-text"
                  @dblclick="startEditOrder(item)"
                >
                  {{ getPaidAmount(item) || '-' }}
                </span>
              </td>
              <td class="col-balance">¥ {{ calculateBalance(index).toFixed(2) }}</td>
              <td class="col-return">{{ hasReceipt(item) ? '已传' : '' }}</td>
              <td class="col-remark"></td>
            </tr>

          <!-- 备用金行 -->
          <tr v-else-if="item.itemType === 'fund'" class="row-fund-entry">
            <td class="col-index">{{ index + 1 }}</td>
            <td class="col-date">{{ formatDate(item.date) }}</td>
            <td colspan="7" class="fund-label">备用金转入{{ item.note ? `（${item.note}）` : '' }}</td>
            <td class="fund-amount" :class="{ negative: item.amount < 0 }">
              <!-- 编辑状态 -->
              <input
                v-if="editingFundId === item.id"
                type="number"
                class="input-paid"
                v-model.number="editingFundAmount"
                @keyup.enter="saveFundAmount(item)"
                @blur="cancelFundEdit"
                ref="fundAmountInput"
              />
              <!-- 显示状态 -->
              <span
                v-else
                class="fund-amount-text"
                @dblclick="startEditFund(item)"
              >
                {{ item.amount >= 0 ? '+ ' + item.amount.toFixed(2) : item.amount.toFixed(2) }}
              </span>
            </td>
            <td class="col-balance">¥ {{ calculateBalance(index).toFixed(2) }}</td>
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
        <span class="summary-label">本期笔数：</span>
        <span class="summary-value">{{ totalOrders }} 笔</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">本期运费合计：</span>
        <span class="summary-value total">¥ {{ totalFreight.toFixed(2) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">汇入备用金：</span>
        <span class="summary-value fund">¥ {{ periodReserveFund.toFixed(2) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">期末余额：</span>
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
            <label>类型</label>
            <div class="radio-group">
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="fundType"
                  value="previous"
                  @change="onFundTypeChange"
                />
                <span>上期备用金转入</span>
              </label>
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="fundType"
                  value="current"
                  @change="onFundTypeChange"
                />
                <span>备用金录入</span>
              </label>
            </div>
          </div>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import request from '@/api/request'
import { exportFreightRecords } from '@/utils/excelExport'

const API_BASE_URL = '/api'

// 年份和月份选项
const currentDate = new Date()
const years = ref([2024, 2025, 2026, 2027])
const months = ref([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

// 获取当前日期对应的期数
const getCurrentPeriod = () => {
  const day = currentDate.getDate()
  if (day >= 1 && day <= 10) return '1-10'
  if (day >= 11 && day <= 20) return '11-20'
  return '21-31'
}

// 筛选条件
const selectedYear = ref(currentDate.getFullYear())
const selectedMonth = ref(currentDate.getMonth() + 1)
const selectedPeriod = ref(getCurrentPeriod()) // 根据当前日期自动选择期数

// 数据
const orders = ref([])
const loading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(50)

// 上期备用金
const previousBalance = ref(-6383.61)

// 当前备用金余额
const currentReserveFund = ref(0)

// 模态框控制
const showFundModal = ref(false)
const fundDate = ref('')
const fundAmount = ref('')
const fundNote = ref('')
const fundType = ref('current') // 'previous' 上期备用金转入, 'current' 备用金录入

// 编辑备用金金额
const editingFundId = ref(null)
const editingFundAmount = ref(0)
const fundAmountInput = ref(null)

// 编辑订单已支付金额
const editingOrderId = ref(null)
const editingFreightIndex = ref(null)
const editingPaidAmount = ref(0)
const isSaving = ref(false)

// 本期汇入的备用金
const periodReserveFund = ref(0)

// 本期备用金列表（用于渲染独立行）
const periodFundsList = ref([])

// 日期排序状态：'asc' 升序，'desc' 降序，null 不排序
const dateSortOrder = ref('asc')

// 当前期数文本
const currentPeriodText = computed(() => {
  return `${selectedYear.value}年${selectedMonth.value}月${selectedPeriod.value}期`
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

  // 只显示物流、专车、其它渠道
  result = result.filter(order => {
    const channel = getShippingMethodText(order)
    return channel === '物流' || channel === '专车' || channel === '其它'
  })

  // 期数筛选
  const [startDay, endDay] = selectedPeriod.value.split('-').map(Number)
  result = result.filter(order => {
    if (!order.completed_date) return false

    const orderDate = new Date(order.completed_date)
    const orderYear = orderDate.getFullYear()
    const orderMonth = orderDate.getMonth() + 1
    const orderDay = orderDate.getDate()

    return orderYear === selectedYear.value &&
           orderMonth === selectedMonth.value &&
           orderDay >= startDay &&
           orderDay <= endDay
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
  // 如果订单有多笔运费，则拆分成多行
  paginatedOrders.value.forEach(order => {
    const freightCosts = order.freight_costs || []

    if (freightCosts.length > 0) {
      // 有运费记录，每笔运费一行
      freightCosts.forEach((cost, costIndex) => {
        merged.push({
          ...order,
          itemType: 'order',  // 改为 itemType，避免覆盖订单的 type 字段
          sortDate: order.completed_date || '',
          freightCostIndex: costIndex, // 标记是第几笔运费
          currentFreightCost: cost, // 当前这笔运费的详情
          isMultiFreight: freightCosts.length > 1, // 是否有多笔运费
          freightCostTotal: freightCosts.length // 总共几笔运费
        })
      })
    } else {
      // 没有运费记录，显示一行
      merged.push({
        ...order,
        itemType: 'order',  // 改为 itemType
        sortDate: order.completed_date || '',
        freightCostIndex: 0,
        currentFreightCost: null,
        isMultiFreight: false,
        freightCostTotal: 0
      })
    }
  })

  // 添加备用金记录（标记为 fund 类型）
  periodFundsList.value.forEach(fund => {
    merged.push({
      ...fund,
      itemType: 'fund',  // 改为 itemType
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
  return filteredOrders.value.reduce((sum, order) => {
    // 计算所有运费的总和，而不是只计算第一笔
    if (!order.freight_costs || !Array.isArray(order.freight_costs)) return sum
    const orderTotal = order.freight_costs.reduce((freightSum, cost) => freightSum + (cost.amount || 0), 0)
    return sum + orderTotal
  }, 0)
})

const finalBalance = computed(() => {
  return periodReserveFund.value - totalFreight.value
})

// 获取运费金额（用于向后兼容，但不再用于统计总额）
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
  let balance = 0  // 从0开始，不使用上期余额

  // 遍历到当前索引，计算累计余额
  for (let i = 0; i <= index; i++) {
    const item = mergedOrdersAndFunds.value[i]
    if (item.itemType === 'order') {
      // 订单：从余额中减去已支付金额
      const paidAmount = getPaidAmountNumber(item)
      balance -= paidAmount
    } else if (item.itemType === 'fund') {
      // 备用金：增加金额（可能是正数或负数）
      balance += item.amount
    }
  }

  return balance
}

// 获取已支付金额数值（用于计算）
const getPaidAmountNumber = (item) => {
  if (item.currentFreightCost && item.currentFreightCost.paid_amount !== undefined) {
    return item.currentFreightCost.paid_amount
  }
  return 0
}

// 获取行样式类
const getRowClass = (order) => {
  // 根据订单类型判断：type == 1 为绝缘订单，显示红色字体
  console.log('完整订单对象:', order)
  console.log('订单ID:', order.id, 'type:', order.type, '是否绝缘:', order.type == 1)
  if (order.type == 1) {
    return 'row-insulation'
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
  exportFreightRecords({
    periodText: currentPeriodText.value,
    mergedData: mergedOrdersAndFunds.value,
    totalFreight: totalFreight.value,
    finalBalance: finalBalance.value,
    getDisplayIndex,
    formatDate,
    getGoodsName,
    getTotalWeight,
    getChannelName,
    getLogisticsNumber,
    getFreightAmountForRow,
    getPaidAmount,
    calculateBalance,
    hasReceipt
  })
}

// 获取备用金余额
const fetchReserveFund = async () => {
  try {
    const response = await request({
      url: '/freight-records/reserve-fund/latest',
      method: 'GET',
      params: { type: 'logistics-truck' }
    })
    if (response && response.balance !== undefined) {
      currentReserveFund.value = response.balance
    }
  } catch (error) {
    console.error('获取备用金失败:', error)
  }
}

// 获取本期备用金（当前期数内汇入的备用金）
const fetchPeriodReserveFund = async () => {
  try {
    const [startDay, endDay] = selectedPeriod.value.split('-').map(Number)
    const startDate = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-${String(startDay).padStart(2, '0')}`
    const endDate = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}-${String(endDay).padStart(2, '0')}`

    const response = await request({
      url: '/freight-records/reserve-fund',
      method: 'GET',
      params: {
        type: 'logistics-truck',
        startDate,
        endDate
      }
    })

    if (response && Array.isArray(response)) {
      periodFundsList.value = response
      periodReserveFund.value = response.reduce((sum, fund) => sum + fund.amount, 0)
    }
  } catch (error) {
    console.error('获取本期备用金失败:', error)
  }
}

// 显示录入备用金弹窗
const showAddFundModal = () => {
  // 默认选择"备用金录入"
  fundType.value = 'current'
  // 设置日期为今天
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  fundDate.value = `${year}-${month}-${day}`
  fundAmount.value = ''
  fundNote.value = ''
  showFundModal.value = true
}

// 备用金类型切换处理
const onFundTypeChange = () => {
  if (fundType.value === 'previous') {
    // 上期备用金转入：设置为当前期数的第一天
    const [startDay] = selectedPeriod.value.split('-').map(Number)
    const year = selectedYear.value
    const month = String(selectedMonth.value).padStart(2, '0')
    const day = String(startDay).padStart(2, '0')
    fundDate.value = `${year}-${month}-${day}`
  } else {
    // 备用金录入：设置为今天
    const today = new Date()
    const year = today.getFullYear()
    const month = String(today.getMonth() + 1).padStart(2, '0')
    const day = String(today.getDate()).padStart(2, '0')
    fundDate.value = `${year}-${month}-${day}`
  }
}

// 开始编辑备用金金额
const startEditFund = (fund) => {
  editingFundId.value = fund.id
  editingFundAmount.value = fund.amount
  // 等待DOM更新后聚焦输入框
  nextTick(() => {
    // 查找对应的输入框元素并聚焦
    const inputElement = document.querySelector(`input[type="number"].input-paid`)
    if (inputElement) {
      inputElement.focus()
      inputElement.select()
    }
  })
}

// 取消编辑备用金金额
const cancelFundEdit = () => {
  editingFundId.value = null
  editingFundAmount.value = 0
}

// 保存备用金金额
const saveFundAmount = async (fund) => {
  const newAmount = editingFundAmount.value

  if (newAmount === fund.amount) {
    cancelFundEdit()
    return
  }

  try {
    const username = localStorage.getItem('username') || 'admin'

    // 调用API更新备用金金额
    const response = await fetch(`${API_BASE_URL}/freight-records/reserve-fund/${fund.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Username': encodeURIComponent(username)
      },
      body: JSON.stringify({
        amount: newAmount
      })
    })

    if (!response.ok) {
      throw new Error('更新失败')
    }

    // 更新本地数据
    fund.amount = newAmount

    // 只重新加载备用金数据，不重新加载订单
    await fetchPeriodReserveFund()

    cancelFundEdit()

    alert('修改成功')
  } catch (error) {
    console.error('保存备用金金额失败:', error)
    alert('保存失败，请重试')
    cancelFundEdit()
  }
}

// 获取货物名称（截取前6个字符）
const getGoodsName = (item) => {
  if (!item.goods_name) return '-'
  return item.goods_name.length > 6 ? item.goods_name.substring(0, 6) + '...' : item.goods_name
}

// 获取运费标签（物流、货拉拉等）
const getFreightLabel = (freightCost) => {
  if (!freightCost) return ''
  return freightCost.note || '运费'
}

// 计算显示序号（考虑rowspan合并）
const getDisplayIndex = (index) => {
  let displayIndex = 0
  for (let i = 0; i <= index; i++) {
    const item = mergedOrdersAndFunds.value[i]
    // 只有第一笔运费或备用金行才计数
    if (item.itemType !== 'order' || item.freightCostIndex === 0) {
      displayIndex++
    }
  }
  return displayIndex
}

// 拆分物流信息：获取渠道名称（-号之前）
const getChannelName = (item) => {
  // 优先从 freight_costs 的 note 中获取
  if (item.currentFreightCost && item.currentFreightCost.note) {
    const parts = item.currentFreightCost.note.split('-')
    if (parts.length > 1) {
      return parts[0].trim()
    }
  }

  // 如果 note 没有，从 logistics_no 中获取
  if (item.logistics_no) {
    const parts = item.logistics_no.split('-')
    if (parts.length > 1) {
      return parts[0].trim()
    }
    return item.logistics_no
  }

  return '-'
}

// 拆分物流信息：获取单号（-号之后）
const getLogisticsNumber = (item) => {
  // 优先从 freight_costs 的 note 中获取
  if (item.currentFreightCost && item.currentFreightCost.note) {
    const parts = item.currentFreightCost.note.split('-')
    if (parts.length > 1) {
      return parts.slice(1).join('-').trim()
    }
  }

  // 如果 note 没有，从 logistics_no 中获取
  if (item.logistics_no) {
    const parts = item.logistics_no.split('-')
    if (parts.length > 1) {
      return parts.slice(1).join('-').trim()
    }
  }

  return '-'
}

// 获取当前行的运费金额
const getFreightAmountForRow = (item) => {
  if (item.currentFreightCost) {
    return item.currentFreightCost.amount || 0
  }
  return getFreightAmount(item)
}

// 获取已支付金额
const getPaidAmount = (item) => {
  if (item.currentFreightCost && item.currentFreightCost.paid_amount !== undefined) {
    return item.currentFreightCost.paid_amount.toFixed(2)
  }
  return ''
}

// 开始编辑订单已支付金额
const startEditOrder = (item) => {
  console.log('开始编辑订单:', item.id, '运费索引:', item.freightCostIndex)
  editingOrderId.value = item.id
  editingFreightIndex.value = item.freightCostIndex
  editingPaidAmount.value = item.currentFreightCost?.paid_amount || 0

  // 等待DOM更新后聚焦输入框
  nextTick(() => {
    const inputElement = document.querySelector(`input[type="number"].input-paid`)
    if (inputElement) {
      inputElement.focus()
      inputElement.select()
      console.log('输入框已聚焦')
    } else {
      console.error('未找到输入框')
    }
  })
}

// 取消编辑订单已支付金额
const cancelOrderEdit = () => {
  console.log('取消编辑')
  editingOrderId.value = null
  editingFreightIndex.value = null
  editingPaidAmount.value = 0
}

// 保存订单已支付金额
const savePaidAmount = async (item) => {
  console.log('保存已支付金额:', editingPaidAmount.value)
  const newAmount = editingPaidAmount.value

  if (newAmount === item.currentFreightCost?.paid_amount) {
    console.log('金额未变化，取消编辑')
    cancelOrderEdit()
    return
  }

  // 防止重复提交
  if (isSaving.value) {
    console.log('正在保存中，忽略重复请求')
    return
  }
  isSaving.value = true

  try {
    const username = localStorage.getItem('username') || 'admin'
    console.log('调用API更新...')

    // 添加超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 8000) // 8秒超时

    // 调用API更新订单的已支付金额
    const response = await fetch(`${API_BASE_URL}/orders/${item.id}/paid-amount`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Username': encodeURIComponent(username)
      },
      body: JSON.stringify({
        freightCostIndex: item.freightCostIndex,
        paidAmount: newAmount
      }),
      signal: controller.signal
    })

    clearTimeout(timeoutId)
    console.log('API响应状态:', response.status)

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.message || '更新失败')
    }

    // 更新本地数据（不重新加载）
    if (item.currentFreightCost) {
      item.currentFreightCost.paid_amount = newAmount
    }

    // 同时更新原始订单列表中的数据
    const order = orders.value.find(o => o.id === item.id)
    if (order && order.freight_costs && order.freight_costs[item.freightCostIndex]) {
      order.freight_costs[item.freightCostIndex].paid_amount = newAmount
    }

    cancelOrderEdit()

    console.log('保存成功')
    alert('修改成功')
  } catch (error) {
    console.error('保存已支付金额失败:', error)
    if (error.name === 'AbortError') {
      alert('保存超时，请检查网络连接')
    } else {
      alert('保存失败：' + error.message)
    }
    cancelOrderEdit()
  } finally {
    isSaving.value = false
  }
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
        type: 'logistics-truck',
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

// 审核当前期数
const auditCurrentPeriod = async () => {
  if (filteredOrders.value.length === 0) {
    alert('当前期数没有数据，无法审核')
    return
  }

  const confirmMsg = `确认审核 ${currentPeriodText.value} 的运费记录吗？\n共 ${totalOrders.value} 笔订单，运费合计 ¥${totalFreight.value.toFixed(2)}`

  if (!confirm(confirmMsg)) {
    return
  }

  try {
    // 构建完整的订单信息数组（包含已支付金额）
    const orderDetails = filteredOrders.value.map(order => {
      // 获取订单的所有运费记录及其已支付金额
      const freightDetails = []
      if (order.freight_costs && Array.isArray(order.freight_costs)) {
        order.freight_costs.forEach((freightCost, index) => {
          freightDetails.push({
            freightIndex: index,
            amount: freightCost.amount || 0,
            paidAmount: freightCost.paid_amount || 0,
            note: freightCost.note || '',
            type: freightCost.type || 'freight'
          })
        })
      }

      return {
        id: order.id,
        date: order.completed_date,
        client: order.order_client || '-',
        weight: order.goods_weight || '-',
        address: order.receiver_address || '-',
        channel: getShippingMethodText(order),
        logisticsNo: order.logistics_no || '-',
        freight: getFreightAmount(order),
        hasReceipt: hasReceipt(order),
        freightCosts: freightDetails  // 新增：运费明细和已支付金额
      }
    })

    const response = await request({
      url: '/freight-records',
      method: 'POST',
      data: {
        type: 'logistics-truck',
        year: selectedYear.value,
        month: selectedMonth.value,
        period: selectedPeriod.value,
        orders: orderDetails,
        totalAmount: totalFreight.value,
        reserveFund: finalBalance.value,
        orderCount: totalOrders.value,
        periodFund: periodReserveFund.value,
        reserveFundRecords: periodFundsList.value  // 新增：备用金记录
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

/* 可展开单元格样式 */
.expandable-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

.cell-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expand-icon {
  color: #3b82f6;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.expand-icon:hover {
  color: #2563eb;
  background: #f3f4f6;
  border-radius: 3px;
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

/* 绝缘订单行 - 红色字体 */
.freight-table .row-insulation {
  color: #dc2626 !important;
}

.freight-table .row-insulation td {
  color: #dc2626 !important;
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

.radio-group {
  display: flex;
  gap: 20px;
  margin-top: 8px;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: normal;
}

.radio-label input[type="radio"] {
  margin-right: 6px;
  cursor: pointer;
}

.radio-label span {
  font-size: 14px;
  color: #374151;
}

.freight-index {
  font-size: 12px;
  color: #6b7280;
  font-weight: normal;
}

.paid-amount-text {
  cursor: pointer;
}

.paid-amount-text:hover {
  background: #f3f4f6;
  padding: 2px 4px;
  border-radius: 3px;
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
