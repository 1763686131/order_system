<template>
  <div class="debt-details-page">
    <!-- 顶部汇总卡片 -->
    <div class="summary-card">
      <div class="summary-header">
        <div class="summary-title">
          <h2>{{ displayTargetName }}</h2>
          <span class="target-label">{{ targetLabel }}</span>
        </div>
        <button type="button" class="close-button" @click="handleClose" title="返回上一级">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"></path>
          </svg>
        </button>
      </div>
        <div class="summary-stats">
        <div class="stat-box">
          <span class="stat-label">{{ type === 'receivable' ? '应收欠款' : '应付欠款' }}</span>
          <strong class="stat-value">{{ formatMoney(totalReceivable) }}</strong>
        </div>
        <div class="stat-operator">=</div>
        <div class="stat-box">
          <span class="stat-label">期初欠款</span>
          <strong class="stat-value">{{ formatMoney(initialDebt) }}</strong>
        </div>
        <div class="stat-operator">+</div>
        <div class="stat-box">
          <span class="stat-label">{{ type === 'receivable' ? '增加应收欠款' : '增加应付欠款' }}</span>
          <strong class="stat-value">{{ formatMoney(totalIncrease) }}</strong>
        </div>
        <div class="stat-operator">-</div>
        <div class="stat-box">
          <span class="stat-label">{{ type === 'receivable' ? '收回欠款' : '支付欠款' }}</span>
          <strong class="stat-value">{{ formatMoney(totalRecovered) }}</strong>
        </div>
        <div class="stat-operator">-</div>
        <div class="stat-box">
          <span class="stat-label">优惠</span>
          <strong class="stat-value">{{ formatMoney(totalDiscount) }}</strong>
        </div>
        <div class="stat-box stored-balance-stat">
          <span class="stat-label">当前储值</span>
          <strong class="stat-value">{{ formatMoney(storedBalance) }}</strong>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <section class="content-section">
      <!-- 工具栏 -->
      <header class="toolbar">
        <form class="search-form" @submit.prevent="handleSearch">
          <label class="field-group">
            <span>业务类型</span>
            <select v-model="filters.businessType">
              <option value="">全部类型</option>
              <option value="ORDER">销售订单</option>
              <option value="RETURN">退货单</option>
              <option value="PAYMENT">收款单</option>
              <option value="INITIAL">期初欠款</option>
              <option value="BALANCE">储值调整</option>
            </select>
          </label>

          <label class="field-group">
            <span>开始日期</span>
            <input
              v-model="filters.startDate"
              type="date"
              placeholder="请选择开始日期"
            />
          </label>

          <label class="field-group">
            <span>结束日期</span>
            <input
              v-model="filters.endDate"
              type="date"
              placeholder="请选择结束日期"
            />
          </label>

          <div class="search-actions">
            <button class="button button-secondary" type="button" @click="handleReset">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M3 12a9 9 0 1 0 3-6.7"></path>
                <path d="M3 4v6h6"></path>
              </svg>
              重置
            </button>
            <button class="button button-primary" type="submit">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="m20 20-3.7-3.7"></path>
              </svg>
              搜索
            </button>
          </div>
        </form>

        <div class="toolbar-actions">
          <button
            class="icon-button"
            type="button"
            title="时间排序"
            @click="toggleSort"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="m19 12-7 7-7-7" v-if="sortOrder === 'asc'"></path>
              <path d="m5 12 7-7 7 7" v-else></path>
            </svg>
          </button>
          <button
            class="icon-button"
            type="button"
            title="刷新"
            :disabled="loading"
            @click="loadData"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button
            class="icon-button"
            type="button"
            title="导出表格"
            @click="exportTable"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>
          <button
            class="button button-primary"
            type="button"
            @click="sendStatement"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m22 2-7 20-4-9-9-4Z"></path>
              <path d="M22 2 11 13"></path>
            </svg>
            发送对账单
          </button>
        </div>
      </header>

      <!-- 数据表格 -->
      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="index-column">序号</th>
              <th class="date-column">业务日期</th>
              <th class="doc-number-column">单据编号</th>
              <th class="type-column">业务类型</th>
              <th class="product-column">商品详情</th>
              <th class="quantity-column">数量</th>
              <th class="unit-column">单位</th>
              <th class="price-column">单价</th>
              <th class="money-column">原单欠款</th>
              <th class="money-column">部分付款</th>
              <th class="money-column">{{ type === 'receivable' ? '应收欠款' : '应付欠款' }}</th>
              <th class="money-column">当前欠款</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 12" :key="cell"><span></span></td>
              </tr>
            </template>

            <tr v-else-if="pagedRecords.length === 0">
              <td colspan="12" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>没有符合条件的欠款记录</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>

            <template v-else>
              <template v-for="(item, index) in pagedRecords" :key="item.id">
                <!-- 主行 -->
                <tr
                  class="main-row"
                  :class="{ 'has-products': item.products && item.products.length > 1, 'expanded': expandedRows[item.id] }"
                  @click="item.products && item.products.length > 1 ? toggleRow(item.id) : null"
                >
                  <td class="index-cell">{{ (currentPage - 1) * pageSize + index + 1 }}</td>
                  <td class="date-cell">
                    <span>{{ formatDate(item.businessDate) }}</span>
                  </td>
                  <td class="doc-number-cell">
                    <strong>{{ item.docNumber }}</strong>
                  </td>
                  <td class="type-cell">
                    <span class="type-badge" :class="`type-${item.businessType.toLowerCase()}`">
                      {{ formatBusinessType(item.businessType) }}
                    </span>
                  </td>
                  <td class="product-cell">
                    <div class="product-content">
                      <span class="product-text" v-if="item.products && item.products.length > 0">
                        {{ getDisplayProduct(item, 0).name }}
                        <span v-if="item.products.length > 1" class="more-badge">+{{ item.products.length - 1 }}</span>
                      </span>
                      <span v-else class="empty-text">-</span>
                      <svg
                        v-if="item.products && item.products.length > 1"
                        class="expand-icon"
                        :class="{ rotated: expandedRows[item.id] }"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path d="m6 9 6 6 6-6"></path>
                      </svg>
                    </div>
                  </td>
                  <td class="quantity-cell">
                    <span v-if="item.products && item.products.length > 0">
                      {{ getDisplayProduct(item, 0).quantity || 1 }}
                    </span>
                    <span v-else class="empty-text">-</span>
                  </td>
                  <td class="unit-cell">
                    <span v-if="item.products && item.products.length > 0">
                      {{ getDisplayProduct(item, 0).unit || '个' }}
                    </span>
                    <span v-else class="empty-text">-</span>
                  </td>
                  <td class="price-cell">
                    <span v-if="item.products && item.products.length > 0">
                      {{ formatMoney(getDisplayProduct(item, 0).price) }}
                    </span>
                    <span v-else class="empty-text">-</span>
                   </td>
                   <td class="money-cell">
                     <template v-if="expandedRows[item.id] && item.products && item.products.length > 1">
                       <span v-if="item.businessType === 'ORDER' || item.businessType === 'INITIAL'">
                         {{ formatMoney(calculateProductOriginalAmount(item, getDisplayProductIndex(item, 0))) }}
                       </span>
                       <span v-else class="empty-text">-</span>
                     </template>
                     <template v-else>
                       <span v-if="item.businessType === 'ORDER' || item.businessType === 'INITIAL'">
                         {{ formatMoney(item.orderAmount) }}
                       </span>
                       <span v-else class="empty-text">-</span>
                     </template>
                  </td>
                  <td class="money-cell">
                    <span v-if="item.businessType === 'ORDER' && item.paidAmount > 0">{{ formatMoney(item.paidAmount) }}</span>
                    <span v-else-if="item.businessType === 'BALANCE'">{{ formatMoney(item.balanceAmount) }}</span>
                    <span v-else class="empty-text">-</span>
                  </td>
                  <td class="money-cell" :class="item.debtAmount > 0 ? 'increase-amount' : 'decrease-amount'">
                    <template v-if="expandedRows[item.id] && item.products && item.products.length > 1">
                      {{ formatMoney(calculateProductDebt(item, getDisplayProductIndex(item, 0))) }}
                    </template>
                    <template v-else>
                      <span v-if="item.businessType !== 'BALANCE'">{{ formatMoney(item.debtAmount) }}</span>
                      <span v-else class="empty-text">-</span>
                    </template>
                  </td>
                  <td class="money-cell current-debt-cell">
                    <template v-if="expandedRows[item.id] && item.products && item.products.length > 1">
                      <strong>{{ formatMoney(calculateProductCurrentDebt(item, getDisplayProductIndex(item, 0))) }}</strong>
                    </template>
                    <template v-else>
                      <strong>{{ formatMoney(item.currentDebt) }}</strong>
                    </template>
                  </td>
                </tr>

                <!-- 展开的商品行 -->
                <template v-if="expandedRows[item.id] && item.products && item.products.length > 1">
                  <tr
                    v-for="productIndex in getDisplayProductIndexes(item).slice(1)"
                    :key="`${item.id}-product-${productIndex}`"
                    class="expanded-product-row"
                  >
                    <td class="index-cell"></td>
                    <td class="date-cell expanded-meta-cell">
                      {{ formatDate(item.businessDate) }}
                    </td>
                    <td class="doc-number-cell expanded-meta-cell">
                      {{ item.docNumber || '-' }}
                    </td>
                    <td class="type-cell"></td>
                    <td class="product-cell">{{ item.products[productIndex].name }}</td>
                    <td class="quantity-cell">{{ item.products[productIndex].quantity || 1 }}</td>
                    <td class="unit-cell">{{ item.products[productIndex].unit || '个' }}</td>
                    <td class="price-cell">{{ formatMoney(item.products[productIndex].price) }}</td>
                    <td class="money-cell">
                      <span v-if="item.businessType === 'ORDER' || item.businessType === 'INITIAL'">
                        {{ formatMoney(calculateProductOriginalAmount(item, productIndex)) }}
                      </span>
                      <span v-else class="empty-text">-</span>
                    </td>
                    <td class="money-cell"></td>
                    <td class="money-cell" :class="calculateProductDebt(item, productIndex) > 0 ? 'increase-amount' : 'decrease-amount'">
                      {{ formatMoney(calculateProductDebt(item, productIndex)) }}
                    </td>
                    <td class="money-cell current-debt-cell">
                      <strong>{{ formatMoney(calculateProductCurrentDebt(item, productIndex)) }}</strong>
                    </td>
                  </tr>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>

      <!-- 底部分页 -->
      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredRecords.length }}</strong> 条欠款记录
        </span>
        <div class="pagination">
          <select v-model.number="pageSize" aria-label="每页显示数量" @change="currentPage = 1">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="50">50 条/页</option>
          </select>
          <button
            type="button"
            title="上一页"
            :disabled="currentPage <= 1"
            @click="currentPage -= 1"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m15 18-6-6 6-6"></path>
            </svg>
          </button>
          <span class="page-number">{{ currentPage }} / {{ totalPages }}</span>
          <button
            type="button"
            title="下一页"
            :disabled="currentPage >= totalPages"
            @click="currentPage += 1"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m9 18 6-6-6-6"></path>
            </svg>
          </button>
        </div>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const handleClose = () => {
  router.back()
}

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['receivable', 'payable'].includes(value)
  },
  targetId: {
    type: [String, Number],
    required: true
  },
  targetName: {
    type: String,
    default: ''
  }
})

const records = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const sortOrder = ref('desc')
const expandedRows = reactive({})
const customerInfo = ref({})
const summary = ref({
  initialDebt: 0,
  receivableIncrease: 0,
  debtRecovered: 0,
  discountAmount: 0,
  storedBalance: 0,
  receivable: 0
})

const filters = reactive({
  businessType: '',
  startDate: '',
  endDate: ''
})

const targetLabel = computed(() => {
  return props.type === 'receivable' ? '客户' : '供应商'
})

const displayTargetName = computed(() => {
  return props.targetName || customerInfo.value.customerName || `客户#${props.targetId}`
})

const filteredRecords = computed(() => {
  const result = records.value.filter((record) => {
    if (filters.businessType && record.businessType !== filters.businessType) {
      return false
    }
    const date = String(record.businessDate || '').slice(0, 10)
    if (filters.startDate && date < filters.startDate) return false
    if (filters.endDate && date > filters.endDate) return false
    return true
  })

  return result.sort((left, right) => {
    const dateResult = String(left.businessDate || '').localeCompare(
      String(right.businessDate || '')
    )
    if (dateResult !== 0) {
      // sortOrder === 'desc' 表示降序,时间近的在前(大的在前)
      // sortOrder === 'asc' 表示升序,时间远的在前(小的在前)
      return sortOrder.value === 'asc' ? dateResult : -dateResult
    }
    const leftId = Number(left.transactionId)
    const rightId = Number(right.transactionId)
    const idResult = (
      (Number.isFinite(leftId) ? leftId : 0)
      - (Number.isFinite(rightId) ? rightId : 0)
    )
    if (idResult === 0) {
      const textResult = String(left.id || '').localeCompare(String(right.id || ''))
      return sortOrder.value === 'asc' ? textResult : -textResult
    }
    return sortOrder.value === 'asc' ? idResult : -idResult
  })
})

const totalReceivable = computed(() => {
  return summary.value.receivable ?? customerInfo.value.receivable ?? 0
})

const initialDebt = computed(() => {
  return summary.value.initialDebt ?? customerInfo.value.initialReceivable ?? 0
})

const totalIncrease = computed(() => summary.value.receivableIncrease ?? 0)
const totalRecovered = computed(() => summary.value.debtRecovered ?? 0)
const totalDiscount = computed(() => 0)
const storedBalance = computed(() => (
  summary.value.storedBalance ?? customerInfo.value.storedBalance ?? 0
))

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value))
})

const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

const formatMoney = (value) => {
  const num = Number(value || 0)
  return `¥${num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return String(dateStr).slice(0, 10)
}

const formatBusinessType = (type) => {
  const typeMap = {
    ORDER: '销售订单',
    RETURN: '退货单',
    PAYMENT: '收款单',
    INITIAL: '期初欠款',
    BALANCE: '储值调整'
  }
  return typeMap[type] || type
}

const getDisplayProductIndexes = (item) => {
  const productCount = item?.products?.length || 0
  const indexes = Array.from({ length: productCount }, (_, index) => index)

  // 单据排序方向同时作用于商品分摊行：
  // 远到近保持录入顺序，近到远反向展示，保证展开后的行也参与排序。
  return sortOrder.value === 'desc' ? indexes.reverse() : indexes
}

const getDisplayProductIndex = (item, displayIndex) => {
  return getDisplayProductIndexes(item)[displayIndex] ?? 0
}

const getDisplayProduct = (item, displayIndex) => {
  const productIndex = getDisplayProductIndex(item, displayIndex)
  return item?.products?.[productIndex] || {}
}

const calculateProductOriginalAmount = (item, productIndex) => {
  const product = item?.products?.[productIndex]
  if (!product) return 0

  const quantity = product.quantity == null ? 1 : Number(product.quantity)
  return Number(product.price || 0) * quantity
}

const calculateProductDebt = (item, productIndex) => {
  const product = item.products?.[productIndex]
  if (!product) return 0
  if (product.allocatedDebt != null) return product.allocatedDebt

  const products = item.products || []
  const total = products.reduce(
    (sum, current) => sum + Number(current.subtotal ?? (current.quantity || 0) * (current.price || 0)),
    0
  )
  if (!total) return Number(item.debtAmount || 0) / products.length
  return Number(item.debtAmount || 0) * Number(product.subtotal || 0) / total
}

const calculateProductCurrentDebt = (item, productIndex) => {
  const products = item?.products || []
  if (!item || !products[productIndex]) return item?.currentDebt ?? 0

  // 当前欠款是流水累计值：先还原本单发生前的欠款，再按商品分摊金额逐项累加。
  // 不直接读取商品上的 cumulativeDebt，避免旧数据或重复分摊造成当前欠款跳变。
  const debtBefore = Number(item.currentDebt || 0) - Number(item.debtAmount || 0)
  const debtThroughProduct = products
    .slice(0, productIndex + 1)
    .reduce(
      (sum, product, index) => sum + Number(calculateProductDebt(item, index) || 0),
      debtBefore
    )

  return Number(debtThroughProduct.toFixed(2))
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleReset = () => {
  filters.businessType = ''
  filters.startDate = ''
  filters.endDate = ''
  currentPage.value = 1
}

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

const toggleRow = (itemId) => {
  expandedRows[itemId] = !expandedRows[itemId]
}

const exportTable = () => {
  const header = ['业务日期', '单据编号', '业务类型', '商品信息', '数量', '单位', '单价', '本单欠款', '当前欠款']
  const rows = filteredRecords.value.map((record) => {
    const firstProduct = getDisplayProduct(record, 0)
    return [
      formatDate(record.businessDate),
      record.docNumber || '',
      formatBusinessType(record.businessType),
      firstProduct.name || '',
      firstProduct.quantity ?? '',
      firstProduct.unit || '',
      firstProduct.price ?? '',
      record.debtAmount ?? 0,
      record.currentDebt ?? 0
    ]
  })
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
    .join('\n')
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${displayTargetName.value}-对账单.csv`
  anchor.click()
  URL.revokeObjectURL(url)
}

const sendStatement = () => {
  window.alert('对账单已生成，可先导出后发送给客户')
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await request({
      url: `/customers/${props.targetId}/debt-details`,
      method: 'GET',
      params: {
        expandProducts: true
      }
    })
    customerInfo.value = response || {}
    summary.value = response?.summary || {
      initialDebt: response?.initialDebt || 0,
      receivableIncrease: 0,
      debtRecovered: 0,
      discountAmount: 0,
      storedBalance: response?.storedBalance || 0,
      receivable: response?.totalReceivable || 0
    }
    records.value = Array.isArray(response?.records) ? response.records : []
    currentPage.value = 1
    Object.keys(expandedRows).forEach((key) => delete expandedRows[key])
  } catch (error) {
    records.value = []
    customerInfo.value = {}
    window.alert(error?.response?.data?.error || '加载客户对账单失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.debt-details-page {
  --page-bg: #f4f7f8;
  --panel-bg: #fff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  --radius: 8px;
  min-height: calc(100vh - 60px);
  padding: 24px;
  background: var(--page-bg);
  color: var(--text);
  font-size: 14px;
}

* {
  box-sizing: border-box;
}

button,
input,
select {
  font: inherit;
}

.summary-card {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 24px;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
}

.target-label {
  font-size: 13px;
  color: var(--text-muted);
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 4px;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.close-button:hover {
  background: #f8fafc;
  border-color: var(--border-strong);
  color: var(--text);
}

.close-button svg {
  width: 16px;
  height: 16px;
}

.summary-stats {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  min-width: 140px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
}

.stat-operator {
  font-size: 18px;
  font-weight: 500;
  color: #94a3b8;
  flex-shrink: 0;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.content-section {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.search-form {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  flex: 1;
  flex-wrap: wrap;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 160px;
}

.field-group span {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-group input,
.field-group select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text);
  outline: none;
  transition: all 0.15s;
}

.field-group input:focus,
.field-group select:focus {
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

.search-actions {
  display: flex;
  gap: 8px;
}

.button {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.button svg {
  width: 16px;
  height: 16px;
  stroke-width: 2;
  fill: none;
  stroke: currentColor;
}

.button-secondary {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  color: var(--text);
}

.button-secondary:hover {
  background: #f8fafc;
  border-color: var(--border-strong);
}

.button-primary {
  background: var(--accent, #0f9f78);
  color: #fff;
}

.button-primary:hover {
  opacity: 0.9;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.icon-button svg {
  width: 18px;
  height: 18px;
  stroke-width: 2;
  fill: none;
  stroke: currentColor;
}

.icon-button:hover:not(:disabled) {
  background: #f8fafc;
  border-color: var(--border-strong);
  color: var(--text);
}

.icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-button svg.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: fixed;
}

.records-table thead {
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
}

.records-table th {
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

.records-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.records-table tbody tr:hover {
  background: #f8fafc;
}

.records-table td {
  padding: 14px 16px;
  color: var(--text);
}

.index-column,
.index-cell {
  width: 70px;
  text-align: center;
}

.date-column,
.date-cell {
  width: 130px;
}

.doc-number-column,
.doc-number-cell {
  width: 190px;
}

.type-column,
.type-cell {
  width: 110px;
}

.product-column,
.product-cell {
  width: 220px;
}

.quantity-column,
.quantity-cell {
  width: 80px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.unit-column,
.unit-cell {
  width: 60px;
  text-align: center;
}

.price-column,
.price-cell {
  width: 100px;
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.money-column,
.money-cell {
  width: 130px;
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.current-debt-cell {
  padding-right: 24px !important;
}

.product-cell {
  position: relative;
}

.product-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.product-text {
  display: inline-flex;
  align-items: center;
}

.expand-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  transition: transform 0.2s;
  flex-shrink: 0;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.main-row.has-products {
  cursor: pointer;
}

.main-row.expanded {
  background: #f8fafc;
}

.expanded-product-row {
  background: #f8fafc;
}

.expanded-product-row .expanded-meta-cell {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 400;
}

.expanded-product-row:hover {
  background: #f1f5f9 !important;
}

.more-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 6px;
  background: #e2e8f0;
  color: var(--text-secondary);
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

.empty-text {
  color: var(--text-muted);
}

.type-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.type-order {
  background: #e9f8f3;
  color: #0f9f78;
}

.type-purchase {
  background: #eff6ff;
  color: #3b82f6;
}

.type-return {
  background: #fef3f2;
  color: #ef4444;
}

.type-payment {
  background: #f4f3ff;
  color: #8b5cf6;
}

.type-discount {
  background: #fff4ed;
  color: #f97316;
}

.type-initial {
  background: #fff9e6;
  color: #d97706;
  border: 1px solid #f59e0b;
  font-weight: 600;
}

.type-balance {
  background: #e0f2fe;
  color: #0891b2;
  border: 1px solid #06b6d4;
  font-weight: 600;
}

.increase-amount {
  color: #0f9f78;
  font-weight: 500;
}

.decrease-amount {
  color: #ef4444;
  font-weight: 500;
}

.current-debt-cell strong {
  font-weight: 600;
  color: var(--text);
}

.skeleton-row td {
  padding: 14px 16px;
}

.skeleton-row span {
  display: block;
  height: 16px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  to {
    background-position: -200% 0;
  }
}

.empty-cell {
  text-align: center;
  padding: 60px 20px !important;
  color: var(--text-muted);
}

.empty-mark {
  margin: 0 auto 16px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-mark svg {
  width: 32px;
  height: 32px;
  stroke-width: 2;
  fill: none;
  stroke: var(--border-strong);
}

.empty-cell strong {
  display: block;
  margin-bottom: 6px;
  font-size: 15px;
  color: var(--text-secondary);
}

.empty-cell span {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-secondary);
}

.table-footer strong {
  color: var(--text);
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination select {
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text);
  cursor: pointer;
}

.pagination button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.pagination button svg {
  width: 16px;
  height: 16px;
  stroke-width: 2;
  fill: none;
  stroke: currentColor;
}

.pagination button:hover:not(:disabled) {
  background: #f8fafc;
  border-color: var(--border-strong);
  color: var(--text);
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-number {
  min-width: 80px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
</style>
