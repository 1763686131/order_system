<template>
  <div class="debt-details-page">
    <!-- 顶部汇总卡片 -->
    <div class="summary-card" :class="`summary-card-${type}`">
      <div class="summary-header">
        <div class="summary-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="5" width="20" height="14" rx="2"></rect>
            <path d="M2 10h20"></path>
          </svg>
          <h2>{{ summaryTitle }}</h2>
        </div>
        <div class="target-info">
          <span class="target-label">{{ targetLabel }}</span>
          <strong class="target-name">{{ targetName }}</strong>
        </div>
        <button type="button" class="close-button" @click="goBack" title="返回上一级">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      <div class="summary-amount">
        <span class="amount-label">合计</span>
        <strong class="amount-value">{{ formatMoney(totalAmount) }}</strong>
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
              <option value="PURCHASE">采购订单</option>
              <option value="RETURN">退货单</option>
              <option value="PAYMENT">收付款</option>
              <option value="DISCOUNT">优惠调整</option>
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
              <th class="date-column">业务日期</th>
              <th class="doc-number-column">单据编号</th>
              <th class="type-column">业务类型</th>
              <th class="product-column">商品详情</th>
              <th class="price-column">单价</th>
              <th class="money-column">原单欠款</th>
              <th class="money-column">{{ type === 'receivable' ? '应收欠款' : '应付欠款' }}</th>
              <th class="money-column">当前欠款</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 8" :key="cell"><span></span></td>
              </tr>
            </template>

            <tr v-else-if="pagedRecords.length === 0">
              <td colspan="8" class="empty-cell">
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
              <template v-for="item in pagedRecords" :key="item.id">
                <!-- 主行 -->
                <tr
                  class="main-row"
                  :class="{ 'has-products': item.products && item.products.length > 1, 'expanded': expandedRows[item.id] }"
                >
                  <td class="date-cell">
                    <div class="cell-with-icon">
                      <svg
                        v-if="item.products && item.products.length > 1"
                        class="expand-icon"
                        :class="{ rotated: expandedRows[item.id] }"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        @click.stop="toggleRow(item.id)"
                      >
                        <path d="m9 18 6-6-6-6"></path>
                      </svg>
                      <span>{{ formatDate(item.businessDate) }}</span>
                    </div>
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
                    <span v-if="item.products && item.products.length > 0">
                      {{ item.products[0].name }}
                      <span v-if="item.products.length > 1" class="more-badge">+{{ item.products.length - 1 }}</span>
                    </span>
                    <span v-else class="empty-text">-</span>
                  </td>
                  <td class="price-cell">
                    <span v-if="item.products && item.products.length > 0">
                      {{ formatMoney(item.products[0].price) }}
                    </span>
                    <span v-else class="empty-text">-</span>
                  </td>
                  <td class="money-cell">{{ formatMoney(item.originalDebt) }}</td>
                  <td class="money-cell" :class="item.debtAmount > 0 ? 'increase-amount' : 'decrease-amount'">
                    {{ formatMoney(item.debtAmount) }}
                  </td>
                  <td class="money-cell current-debt-cell">
                    <strong>{{ formatMoney(item.currentDebt) }}</strong>
                  </td>
                </tr>

                <!-- 展开的商品行 -->
                <template v-if="expandedRows[item.id] && item.products && item.products.length > 1">
                  <tr
                    v-for="(product, index) in item.products.slice(1)"
                    :key="`${item.id}-product-${index + 1}`"
                    class="expanded-product-row"
                  >
                    <td colspan="3"></td>
                    <td class="product-cell">{{ product.name }}</td>
                    <td class="price-cell">{{ formatMoney(product.price) }}</td>
                    <td colspan="3"></td>
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

const router = useRouter()

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
const sortOrder = ref('asc')
const expandedRows = reactive({})

const filters = reactive({
  businessType: '',
  startDate: '',
  endDate: ''
})

const summaryTitle = computed(() => {
  return props.type === 'receivable' ? '应收欠款合计' : '应付欠款合计'
})

const targetLabel = computed(() => {
  return props.type === 'receivable' ? '客户' : '供应商'
})

const filteredRecords = computed(() => {
  let result = [...records.value]

  if (filters.businessType) {
    result = result.filter(r => r.businessType === filters.businessType)
  }

  if (filters.startDate) {
    result = result.filter(r => r.businessDate >= filters.startDate)
  }

  if (filters.endDate) {
    result = result.filter(r => r.businessDate <= filters.endDate)
  }

  result.sort((a, b) => {
    const dateA = new Date(a.businessDate)
    const dateB = new Date(b.businessDate)
    return sortOrder.value === 'asc' ? dateA - dateB : dateB - dateA
  })

  let cumulativeDebt = 0
  result.forEach(record => {
    cumulativeDebt += record.debtAmount
    record.currentDebt = cumulativeDebt
  })

  return result
})

const totalAmount = computed(() => {
  return filteredRecords.value.reduce((sum, r) => sum + r.debtAmount, 0)
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value))
})

const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

const formatMoney = (value) => {
  if (value == null) return '¥0.00'
  const num = Number(value)
  return `¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr
}

const formatBusinessType = (type) => {
  const typeMap = {
    ORDER: '销售订单',
    PURCHASE: '采购订单',
    RETURN: '退货单',
    PAYMENT: '收付款',
    DISCOUNT: '优惠调整'
  }
  return typeMap[type] || type
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

const goBack = () => {
  router.back()
}

const exportTable = () => {
  window.alert('导出功能开发中')
}

const sendStatement = () => {
  window.alert('发送对账单功能开发中')
}

const loadData = async () => {
  loading.value = true

  await new Promise(resolve => setTimeout(resolve, 800))

  records.value = [
    {
      id: 1,
      businessDate: '2026-09-01',
      docNumber: 'SO202609010001',
      businessType: 'ORDER',
      originalDebt: 0,
      debtAmount: 5000,
      products: [
        { name: '商品A', price: 120.50 },
        { name: '商品B', price: 85.00 }
      ]
    },
    {
      id: 2,
      businessDate: '2026-09-02',
      docNumber: 'SO202609020001',
      businessType: 'ORDER',
      originalDebt: 5000,
      debtAmount: 1000,
      products: [
        { name: '商品C', price: 200.00 }
      ]
    },
    {
      id: 3,
      businessDate: '2026-09-03',
      docNumber: 'PM202609030001',
      businessType: 'PAYMENT',
      originalDebt: 6000,
      debtAmount: -2000,
      products: []
    },
    {
      id: 4,
      businessDate: '2026-09-05',
      docNumber: 'SO202609050001',
      businessType: 'ORDER',
      originalDebt: 4000,
      debtAmount: 3500,
      products: [
        { name: '商品D', price: 150.00 },
        { name: '商品E', price: 90.00 },
        { name: '商品F', price: 110.00 }
      ]
    },
    {
      id: 5,
      businessDate: '2026-09-08',
      docNumber: 'DIS202609080001',
      businessType: 'DISCOUNT',
      originalDebt: 7500,
      debtAmount: -500,
      products: []
    }
  ]

  loading.value = false
}

onMounted(() => {
  loadData()
})
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

.summary-card-receivable {
  --accent: #0f9f78;
  --accent-soft: #e9f8f3;
}

.summary-card-payable {
  --accent: #f97316;
  --accent-soft: #fff4ed;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-title svg {
  width: 24px;
  height: 24px;
  color: var(--accent);
}

.summary-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}

.target-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.target-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.target-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent);
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

.summary-amount {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 16px 20px;
  background: var(--accent-soft);
  border-radius: 6px;
}

.amount-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.amount-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
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
}

.records-table thead {
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
}

.records-table th {
  padding: 12px 16px;
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

.date-column,
.date-cell {
  width: 120px;
}

.doc-number-column,
.doc-number-cell {
  width: 180px;
}

.type-column,
.type-cell {
  width: 120px;
}

.product-column,
.product-cell {
  width: 200px;
}

.price-column,
.price-cell {
  width: 120px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.money-column,
.money-cell {
  width: 140px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.cell-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-icon {
  width: 16px;
  height: 16px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.expand-icon.rotated {
  transform: rotate(90deg);
}

.expand-icon:hover {
  color: var(--text);
}

.main-row.has-products {
  cursor: default;
}

.main-row.expanded {
  background: #f8fafc;
}

.expanded-product-row {
  background: #f8fafc;
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
