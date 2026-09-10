<template>
  <div class="receivables-page">
    <section class="search-panel" aria-label="应收欠款筛选">
      <form class="search-grid" @submit.prevent="handleFilter">
        <label class="field-group">
          <span>客户搜索</span>
          <span class="input-with-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            <input
              v-model.trim="filters.keyword"
              type="search"
              placeholder="客户ID、客户名称或联系人"
            />
          </span>
        </label>

        <label class="field-group">
          <span>联系电话</span>
          <input
            v-model.trim="filters.phone"
            type="search"
            placeholder="请输入联系电话"
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
            查询
          </button>
        </div>
      </form>
    </section>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="status-filter-slider" role="tablist" aria-label="欠款状态筛选">
          <button
            :class="['slider-tab', { active: filters.debtStatus === '' }]"
            type="button"
            role="tab"
            :aria-selected="filters.debtStatus === ''"
            @click="setDebtStatus('')"
          >
            全部
            <span class="count-badge">{{ receivables.length }}</span>
          </button>
          <button
            :class="['slider-tab', { active: filters.debtStatus === 'outstanding' }]"
            type="button"
            role="tab"
            :aria-selected="filters.debtStatus === 'outstanding'"
            @click="setDebtStatus('outstanding')"
          >
            有欠款
            <span class="count-badge">{{ outstandingCount }}</span>
          </button>
          <button
            :class="['slider-tab', { active: filters.debtStatus === 'settled' }]"
            type="button"
            role="tab"
            :aria-selected="filters.debtStatus === 'settled'"
            @click="setDebtStatus('settled')"
          >
            无欠款
            <span class="count-badge">{{ settledCount }}</span>
          </button>
        </div>

        <div class="toolbar-actions">
          <span class="receivable-total">
            当前应收合计
            <strong>{{ formatMoney(filteredReceivablesTotal) }}</strong>
          </span>
          <button
            class="icon-button"
            type="button"
            title="刷新应收列表"
            :disabled="loading"
            @click="loadReceivables"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="customer-column">客户ID</th>
              <th>客户联系人</th>
              <th class="phone-column">电话</th>
              <th class="money-column">期初欠款</th>
              <th class="money-column">增加的应收欠款</th>
              <th class="money-column">收回欠款</th>
              <th class="money-column">优惠</th>
              <th class="money-column">应收欠款</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 9" :key="cell"><span></span></td>
              </tr>
            </template>

            <tr v-else-if="pagedReceivables.length === 0">
              <td colspan="9" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>没有符合条件的应收记录</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>

            <template v-else>
              <tr v-for="item in pagedReceivables" :key="item.customerId">
                <td class="customer-cell">
                  <strong>#{{ item.customerId }}</strong>
                  <span :title="item.customerName">{{ item.customerName || '-' }}</span>
                </td>
                <td>{{ item.contactPerson || '-' }}</td>
                <td class="phone-cell">{{ item.phone || '-' }}</td>
                <td class="money-cell">{{ formatMoney(item.initialDebt) }}</td>
                <td class="money-cell increase-amount">
                  {{ formatMoney(item.receivableIncrease) }}
                </td>
                <td class="money-cell recovered-amount">
                  {{ formatMoney(item.debtRecovered) }}
                </td>
                <td class="money-cell discount-amount">
                  {{ formatMoney(item.discountAmount) }}
                </td>
                <td class="money-cell receivable-amount">
                  <strong>{{ formatMoney(item.receivable) }}</strong>
                  <span>净额 {{ formatSignedMoney(item.netAccountBalance) }}</span>
                </td>
                <td class="operation-column">
                  <div class="row-actions">
                    <button
                      class="action-button"
                      type="button"
                      @click="showPendingFeature('欠款详情', item)"
                    >
                      欠款详情
                    </button>
                    <button
                      class="action-button action-button-primary"
                      type="button"
                      @click="showPendingFeature('收款', item)"
                    >
                      收款
                    </button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
          <tfoot v-if="!loading && filteredReceivables.length > 0">
            <tr>
              <td colspan="3" class="total-label">合计</td>
              <td class="money-cell">{{ formatMoney(totals.initialDebt) }}</td>
              <td class="money-cell">{{ formatMoney(totals.receivableIncrease) }}</td>
              <td class="money-cell recovered-amount">{{ formatMoney(totals.debtRecovered) }}</td>
              <td class="money-cell discount-amount">{{ formatMoney(totals.discountAmount) }}</td>
              <td class="money-cell receivable-amount">{{ formatMoney(totals.receivable) }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredReceivables.length }}</strong> 条客户应收记录
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import request from '@/api/request'

const receivables = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const filters = reactive({
  keyword: '',
  phone: '',
  debtStatus: ''
})

const matchesSearch = item => {
  const keyword = filters.keyword.toLowerCase()
  const searchText = [
    item.customerId,
    item.customerCode,
    item.customerName,
    item.contactPerson
  ].join(' ').toLowerCase()

  return (!keyword || searchText.includes(keyword)) &&
    (!filters.phone || String(item.phone || '').includes(filters.phone))
}

const filteredReceivables = computed(() => receivables.value.filter(item => {
  if (!matchesSearch(item)) return false
  if (filters.debtStatus === 'outstanding') return Number(item.receivable) > 0
  if (filters.debtStatus === 'settled') return Number(item.receivable) <= 0
  return true
}))

const outstandingCount = computed(() =>
  receivables.value.filter(item => Number(item.receivable) > 0).length
)

const settledCount = computed(() =>
  receivables.value.filter(item => Number(item.receivable) <= 0).length
)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredReceivables.value.length / pageSize.value))
)

const pagedReceivables = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredReceivables.value.slice(start, start + pageSize.value)
})

const totals = computed(() => filteredReceivables.value.reduce((result, item) => {
  result.initialDebt += Number(item.initialDebt) || 0
  result.receivableIncrease += Number(item.receivableIncrease) || 0
  result.debtRecovered += Number(item.debtRecovered) || 0
  result.discountAmount += Number(item.discountAmount) || 0
  result.receivable += Number(item.receivable) || 0
  return result
}, {
  initialDebt: 0,
  receivableIncrease: 0,
  debtRecovered: 0,
  discountAmount: 0,
  receivable: 0
}))

const filteredReceivablesTotal = computed(() => totals.value.receivable)

const formatMoney = value => {
  const amount = Number(value) || 0
  return `¥${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

const formatSignedMoney = value => {
  const amount = Number(value) || 0
  const sign = amount < 0 ? '-' : amount > 0 ? '+' : ''
  return `${sign}¥${Math.abs(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

const loadReceivables = async () => {
  loading.value = true
  try {
    const response = await request({
      url: '/customers/receivables',
      method: 'GET'
    })
    receivables.value = Array.isArray(response?.items) ? response.items : []
  } catch (error) {
    console.error('加载应收欠款失败:', error)
    receivables.value = []
    window.alert(error?.response?.data?.error || '加载应收欠款失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleReset = () => {
  filters.keyword = ''
  filters.phone = ''
  filters.debtStatus = ''
  currentPage.value = 1
}

const setDebtStatus = status => {
  filters.debtStatus = status
  currentPage.value = 1
}

const showPendingFeature = (action, item) => {
  window.alert(`${item.customerName || item.customerCode}的“${action}”功能入口已预留`)
}

watch(totalPages, pages => {
  if (currentPage.value > pages) currentPage.value = pages
})

onMounted(loadReceivables)
</script>

<style scoped>
.receivables-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #fff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  min-width: 0;
  min-height: calc(100vh - 100px);
  color: var(--text);
  background: var(--page-bg);
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

button:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.search-panel {
  padding: 18px 20px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(240px, 1.3fr) minmax(220px, 1fr) auto;
  gap: 14px;
  align-items: end;
}

.field-group {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.field-group > span:first-child {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-group input {
  width: 100%;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field-group input::placeholder {
  color: #a2adba;
}

.field-group input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.input-with-icon {
  position: relative;
  display: block;
}

.input-with-icon svg {
  position: absolute;
  top: 11px;
  left: 11px;
  z-index: 1;
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.input-with-icon input {
  padding-left: 35px;
}

.search-actions,
.toolbar-actions,
.row-actions,
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.button svg {
  width: 16px;
  height: 16px;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 2px 5px rgba(var(--accent-rgb), 0.18);
}

.button-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.button-secondary {
  color: #445066;
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.records-panel {
  margin-top: 14px;
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 3px 14px rgba(15, 23, 42, 0.045);
}

.records-toolbar {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.status-filter-slider {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.slider-tab {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 16px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease;
}

.slider-tab:hover {
  color: var(--accent-dark);
  background: rgba(var(--accent-rgb), 0.1);
}

.slider-tab.active {
  color: #fff;
  background: var(--accent);
  box-shadow: 0 2px 6px rgba(var(--accent-rgb), 0.3);
}

.count-badge {
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
}

.slider-tab.active .count-badge {
  background: rgba(255, 255, 255, 0.25);
}

.receivable-total {
  color: var(--text-secondary);
  font-size: 12px;
}

.receivable-total strong {
  margin-left: 5px;
  color: #dc3545;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.icon-button svg {
  width: 17px;
  height: 17px;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1180px;
  border-collapse: collapse;
  table-layout: fixed;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.records-table tbody tr:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.customer-column {
  width: 170px;
}

.phone-column {
  width: 130px;
}

.money-column,
.money-cell {
  width: 135px;
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.operation-column {
  width: 185px;
  text-align: center !important;
}

.customer-cell strong,
.customer-cell span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.customer-cell strong {
  color: var(--accent-dark);
  font-weight: 700;
}

.customer-cell span {
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 11px;
}

.phone-cell {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.increase-amount,
.receivable-amount {
  color: #dc3545 !important;
  font-weight: 700;
}

.receivable-amount strong,
.receivable-amount span {
  display: block;
}

.receivable-amount span {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 500;
}

.recovered-amount {
  color: #07805f !important;
  font-weight: 650;
}

.discount-amount {
  color: #a4510b !important;
  font-weight: 650;
}

.row-actions {
  justify-content: center;
}

.action-button {
  display: inline-flex;
  height: 30px;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  color: #445066;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.action-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.action-button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.action-button-primary:hover {
  color: #fff;
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.records-table tfoot {
  color: var(--text);
  background: #f8fafc;
  border-top: 2px solid var(--border);
  font-weight: 700;
}

.total-label {
  padding-left: 20px !important;
  text-align: left;
}

.empty-cell {
  height: 290px !important;
  color: var(--text-muted) !important;
  text-align: center;
}

.empty-cell strong,
.empty-cell span {
  display: block;
}

.empty-cell strong {
  margin-top: 11px;
  color: #4c586b;
  font-size: 14px;
}

.empty-cell span {
  margin-top: 5px;
  font-size: 12px;
}

.empty-mark {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  color: #aab4c0;
  background: #f1f4f7;
  border-radius: 50%;
}

.empty-mark svg {
  width: 24px;
  height: 24px;
}

.skeleton-row span {
  display: block;
  width: 78%;
  height: 10px;
  background: linear-gradient(90deg, #eef2f5 25%, #e2e8ee 50%, #eef2f5 75%);
  background-size: 200% 100%;
  border-radius: 3px;
  animation: shimmer 1.25s linear infinite;
}

@keyframes shimmer {
  to { background-position: -200% 0; }
}

.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 16px;
  color: var(--text-secondary);
  background: #fff;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.table-footer strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.pagination select {
  height: 32px;
  padding: 0 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
}

.pagination button {
  display: inline-flex;
  width: 31px;
  height: 31px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.pagination svg {
  width: 15px;
  height: 15px;
}

.page-number {
  min-width: 58px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
  }
}

@media (max-width: 780px) {
  .search-grid {
    grid-template-columns: 1fr;
  }

  .search-actions {
    grid-column: auto;
  }

  .records-toolbar,
  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: space-between;
  }

  .status-filter-slider {
    max-width: 100%;
    overflow-x: auto;
  }
}
</style>
