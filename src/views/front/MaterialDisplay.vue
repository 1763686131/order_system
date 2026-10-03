<template>
  <div class="material-outbound-display">
    <div v-if="loading" class="display-state">正在加载原材料出库记录...</div>
    <div v-else-if="loadError" class="display-state error">
      <span>{{ loadError }}</span>
      <button type="button" @click="fetchRecords">重新加载</button>
    </div>
    <div v-else-if="materialGroups.length === 0" class="display-state">
      {{ emptyMessage }}
    </div>

    <section v-for="group in materialGroups" v-else :key="group.date" class="timeline-group">
      <div class="timeline-date">{{ group.date }}</div>
      <div class="timeline-items">
        <article v-for="record in group.records" :key="record.id" class="material-card">
          <div class="card-header">
            <span class="card-document-no" :title="record.documentNo || '-'">
              {{ record.documentNo || '-' }}
            </span>
            <span
              v-if="record.stockCalculation"
              class="stock-calculation"
              :title="record.stockCalculation"
            >
              {{ record.stockCalculation }}
            </span>
          </div>
          <span
            :class="['status-ribbon', `status-ribbon-${statusClass(record.status)}`]"
            :aria-label="statusLabel(record.status)"
          >
            {{ statusLabel(record.status) }}
          </span>

          <div class="card-main">
            <div class="material-name">
              <span class="column-label">{{ record.primaryItem?.productCode || '原材料' }}</span>
              <strong>{{ record.primaryItem?.productName || '-' }}</strong>
            </div>

            <div class="quantity-block used">
              <span class="column-label">出库数量</span>
              <strong>
                {{ formatNumber(record.totalQuantity) }}
                <small>{{ record.primaryItem?.unit || '' }}</small>
              </strong>
            </div>

            <div class="finished-name">
              <span class="column-label">成品名称</span>
              <strong>{{ record.remark || '-' }}</strong>
            </div>

            <div class="quantity-block produced">
              <span class="column-label">成品数量</span>
              <strong>{{ formatNumber(record.producedQuantity) }} <small>kg</small></strong>
            </div>

            <div class="record-creator">
              <span class="column-label">制单人</span>
              <div class="creator-value">
                <strong>{{ record.createdBy || '员工' }}</strong>
                <small>{{ formatTime(record.createdAt) }}</small>
              </div>
            </div>

            <div class="quantity-block stock-balance">
              <span class="column-label">{{ stockLabel(record.status) }}</span>
              <strong>
                {{ record.remainingStockKnown ? formatNumber(record.remainingStock) : '-' }}
                <small v-if="record.primaryItem?.unit">{{ record.primaryItem.unit }}</small>
              </strong>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const loadError = ref('')
const records = ref([])
const stockBalances = ref([])
const stockBalancesLoaded = ref(false)
const filterStartDate = ref('')
const filterEndDate = ref('')
let materialEventSource = null
let fallbackPollingInterval = null
let isFetching = false
let refreshQueued = false

const emptyMessage = computed(() => (
  filterStartDate.value && filterEndDate.value
    ? `${filterStartDate.value} 至 ${filterEndDate.value} 暂无原材料出库记录`
    : '最近 30 天暂无原材料出库记录'
))

const toFiniteNumber = value => {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

const normalizedStatus = status => (status === 'posted' ? 'reviewed' : status)

const statusClass = status => normalizedStatus(status) || 'draft'

const stockLabel = status => (
  statusClass(status) === 'draft' ? '预计剩余库存' : '剩余库存'
)

const statusLabel = status => ({
  draft: '未审核',
  reviewed: '已审核',
  posted: '已审核',
  cancelled: '已作废'
}[normalizedStatus(status)] || '未审核')

const recordSortValue = record => (
  `${record.documentDate || ''} ${record.createdAt || ''} ${String(record.id || '').padStart(12, '0')}`
)

const inventoryKey = (productId, warehouseId, storeId) => (
  [productId, warehouseId, storeId].map(value => String(value ?? '')).join(':')
)

const stockBalanceMap = computed(() => {
  const balances = new Map()
  stockBalances.value.forEach(balance => {
    if (balance.productType && balance.productType !== 'raw-material') return

    const key = inventoryKey(balance.productId, balance.warehouseId, balance.storeId)
    balances.set(key, (balances.get(key) || 0) + toFiniteNumber(balance.quantity))
  })
  return balances
})

const materialRecordsWithStock = computed(() => {
  const runningDrafts = new Map()

  return [...records.value]
    .sort((left, right) => recordSortValue(right).localeCompare(recordSortValue(left)))
    .map(record => {
      const item = record.primaryItem
      const productId = item?.productId
      const key = inventoryKey(productId, record.warehouseId, record.storeId)
      const hasProduct = productId !== null && productId !== undefined && productId !== ''
      const hasStock = stockBalancesLoaded.value && hasProduct

      if (!hasStock) {
        return {
          ...record,
          remainingStock: null,
          remainingStockKnown: false
        }
      }

      const baseStock = stockBalanceMap.value.get(key) || 0
      let currentStock = baseStock
      const quantity = toFiniteNumber(item?.quantity ?? record.totalQuantity)
      const status = statusClass(record.status)
      let stockCalculation = `库存 ${formatNumber(currentStock)}`

      if (status === 'draft') {
        const deductions = runningDrafts.get(key) || []
        deductions.push(quantity)
        runningDrafts.set(key, deductions)
        currentStock = baseStock - deductions.reduce(
          (sum, value) => sum + value,
          0
        )
        stockCalculation = `${formatNumber(baseStock)}${deductions
          .map(value => ` - ${formatNumber(value)}`)
          .join('')} = ${formatNumber(currentStock)}`
      } else if (status === 'reviewed') {
        stockCalculation = `库存 ${formatNumber(currentStock)}（已含本单）`
      } else if (status === 'cancelled') {
        stockCalculation = `库存 ${formatNumber(currentStock)}（已作废）`
      }

      return {
        ...record,
        remainingStock: currentStock,
        remainingStockKnown: true,
        stockCalculation
      }
    })
})

const materialGroups = computed(() => {
  const groups = new Map()
  materialRecordsWithStock.value.forEach(record => {
    const date = String(record.documentDate || record.createdAt || '').slice(0, 10) || '未记录日期'
    if (!groups.has(date)) groups.set(date, [])
    groups.get(date).push(record)
  })
  return [...groups.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([date, items]) => ({
      date,
      records: items.sort((left, right) => recordSortValue(right).localeCompare(recordSortValue(left)))
    }))
})

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const formatTime = value => {
  const text = String(value || '')
  return text.length >= 16 ? text.slice(11, 16) : text || '-'
}

const defaultDateRange = () => {
  const end = new Date()
  const start = new Date(end.getFullYear(), end.getMonth(), end.getDate() - 29)
  const format = date => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
  return { start: format(start), end: format(end) }
}

const fetchRecords = async ({ silent = false } = {}) => {
  if (isFetching) {
    refreshQueued = true
    return
  }

  isFetching = true
  if (!silent) {
    loading.value = true
    loadError.value = ''
  }

  try {
    const range = filterStartDate.value && filterEndDate.value
      ? { start: filterStartDate.value, end: filterEndDate.value }
      : defaultDateRange()

    const [recordResult, stockResult] = await Promise.allSettled([
      request({
        url: '/material-outbounds',
        method: 'GET',
        params: {
          startDate: range.start,
          endDate: range.end,
          limit: 300
        }
      }),
      request({
        url: '/stock-balances',
        method: 'GET',
        params: { type: 'raw-material' }
      })
    ])

    if (stockResult.status === 'fulfilled') {
      stockBalances.value = Array.isArray(stockResult.value) ? stockResult.value : []
      stockBalancesLoaded.value = true
    } else {
      stockBalances.value = []
      stockBalancesLoaded.value = false
      console.warn('原材料库存加载失败，触屏端暂时无法计算剩余库存', stockResult.reason)
    }

    if (recordResult.status === 'rejected') {
      throw recordResult.reason
    }

    records.value = Array.isArray(recordResult.value) ? recordResult.value : []
    loadError.value = ''
  } catch (error) {
    if (!silent || records.value.length === 0) {
      loadError.value = error?.response?.data?.message || '原材料出库记录加载失败。'
      records.value = []
    }
  } finally {
    isFetching = false
    if (!silent) loading.value = false
    if (refreshQueued) {
      refreshQueued = false
      fetchRecords({ silent: true })
    }
  }
}

const handleDateFilter = event => {
  filterStartDate.value = event.detail?.startDate || ''
  filterEndDate.value = event.detail?.endDate || ''
  fetchRecords()
}

const handleRefresh = () => fetchRecords()

const refreshFromRealtimeEvent = () => {
  fetchRecords({ silent: true })
  window.dispatchEvent(new CustomEvent('refresh-material-stocks'))
}

const connectMaterialEvents = () => {
  if (typeof EventSource === 'undefined') {
    console.warn('当前浏览器不支持 SSE，原材料记录启用轮询降级方案')
    fallbackPollingInterval = window.setInterval(() => {
      fetchRecords({ silent: true })
    }, 3000)
    return
  }

  const eventSource = new EventSource('/api/material-outbounds/events')
  materialEventSource = eventSource
  let hasConnected = false

  eventSource.addEventListener('material-outbound-change', () => {
    refreshFromRealtimeEvent()
  })

  eventSource.onopen = () => {
    if (hasConnected) {
      refreshFromRealtimeEvent()
    }
    hasConnected = true
  }

  eventSource.onerror = () => {
    console.warn('原材料记录实时连接暂时断开，等待浏览器自动重连')
  }
}

onMounted(() => {
  fetchRecords()
  connectMaterialEvents()
  window.addEventListener('filter-material-date', handleDateFilter)
  window.addEventListener('refresh-materials', handleRefresh)
  window.addEventListener('refresh-material-outbounds', handleRefresh)
})

onBeforeUnmount(() => {
  materialEventSource?.close()
  if (fallbackPollingInterval) {
    window.clearInterval(fallbackPollingInterval)
  }
  window.removeEventListener('filter-material-date', handleDateFilter)
  window.removeEventListener('refresh-materials', handleRefresh)
  window.removeEventListener('refresh-material-outbounds', handleRefresh)
})

defineExpose({ refresh: fetchRecords })
</script>

<style scoped>
.material-outbound-display {
  width: 100%;
}

.display-state {
  display: flex;
  min-height: 260px;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: #64748b;
  font-size: 17px;
}

.display-state.error {
  flex-direction: column;
  color: #b42318;
}

.display-state button {
  height: 38px;
  padding: 0 16px;
  color: #fff;
  background: #2563eb;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
}

.timeline-group + .timeline-group {
  margin-top: 36px;
}

.timeline-date {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  color: #172033;
  font-size: 23px;
  font-weight: 850;
}

.timeline-date::before {
  width: 7px;
  height: 25px;
  content: '';
  background: #2563eb;
  border-radius: 999px;
}

.timeline-items {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
}

.material-card {
  position: relative;
  display: block;
  overflow: hidden;
  padding: 0 !important;
  background: #fff;
  border: 1px solid #dfe7ef;
  border-radius: 8px !important;
  box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
}

.card-header {
  position: absolute;
  top: 16px;
  left: 24px;
  right: 118px;
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 16px;
}

.card-document-no {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 42%;
  overflow: hidden;
  color: #2459a4;
  font-size: 14px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stock-calculation {
  min-width: 0;
  overflow: hidden;
  color: #08745a;
  font-size: 12px;
  font-weight: 750;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-ribbon {
  --ribbon-color: #f5c8cf;
  --ribbon-shadow: #c88a94;
  position: absolute;
  top: 11px;
  right: -39px;
  z-index: 2;
  width: 132px;
  padding: 7px 0 6px;
  color: #9e3850;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.2;
  text-align: center;
  letter-spacing: 1px;
  background: var(--ribbon-color);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.12);
  transform: rotate(45deg);
  transform-origin: center;
}

.status-ribbon::before,
.status-ribbon::after {
  position: absolute;
  bottom: -5px;
  width: 0;
  height: 0;
  content: '';
  border-top: 5px solid var(--ribbon-shadow);
}

.status-ribbon::before {
  left: 0;
  border-right: 5px solid transparent;
}

.status-ribbon::after {
  right: 0;
  border-left: 5px solid transparent;
}

.status-ribbon-reviewed {
  --ribbon-color: #16a36a;
  --ribbon-shadow: #0b714b;
  color: #fff;
}

.status-ribbon-cancelled {
  --ribbon-color: #d7dce3;
  --ribbon-shadow: #aab2bd;
  color: #475467;
}

.card-main {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.8fr) minmax(0, 1fr) minmax(0, 0.8fr) minmax(0, 0.9fr) minmax(0, 1fr);
  min-height: 160px;
  align-items: center;
  padding: 38px 24px;
}

.card-main > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  border-right: 1px solid #edf1f5;
}

.card-main > div:first-child {
  padding-left: 0;
}

.card-main > div:last-child {
  padding-right: 0;
  border-right: 0;
}

.card-main .column-label {
  color: #344054;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.35;
}

.material-name strong {
  color: #172033;
  font-size: 18px;
  overflow-wrap: anywhere;
}

.quantity-block strong {
  color: #e5487b;
  font-size: 22px;
  overflow-wrap: anywhere;
}

.quantity-block.produced strong {
  color: #16a36a;
}

.stock-balance strong {
  color: #08745a;
}

.quantity-block strong small {
  font-size: 12px;
}

.finished-name strong {
  color: #344054;
  font-size: 16px;
  overflow-wrap: anywhere;
}

.creator-value {
  display: flex;
  min-width: 0;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 3px 8px;
}

.creator-value strong {
  color: #172033;
  font-size: 15px;
  overflow-wrap: anywhere;
}

.creator-value small {
  color: #94a3b8;
  font-size: 12px;
}

.record-status .status-badge {
  align-self: flex-start;
}

.status-badge {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 750;
  white-space: nowrap;
}

.status-draft {
  color: #a4510b;
  background: #fff3df;
}

.status-reviewed {
  color: #08745a;
  background: #e9f8f3;
}

.status-cancelled {
  color: #b4232f;
  background: #f1f2f4;
}

@media (max-width: 980px) {
  .card-main {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    min-height: 0;
    gap: 22px 0;
    padding: 40px 24px;
  }

  .card-main > div:nth-child(even) {
    border-right: 0;
  }

  .card-main > div:nth-child(odd) {
    padding-left: 0;
  }

}

@media (max-width: 480px) {
  .card-header {
    top: 14px;
    left: 18px;
    right: 88px;
    gap: 8px;
  }

  .card-document-no {
    max-width: 42%;
    font-size: 12px;
  }

  .stock-calculation {
    font-size: 10px;
  }

  .card-main {
    padding: 40px 18px;
  }

  .card-main > div {
    padding-right: 10px;
  }

  .quantity-block strong {
    font-size: 19px;
  }

  .card-main .column-label {
    font-size: 15px;
  }

  .status-ribbon {
    top: 9px;
    right: -43px;
    width: 126px;
    font-size: 11px;
  }
}
</style>
