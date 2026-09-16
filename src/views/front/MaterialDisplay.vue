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
          <div class="card-main">
            <div class="material-name">
              <span>{{ record.primaryItem?.productCode || '原材料' }}</span>
              <strong>{{ record.primaryItem?.productName || '-' }}</strong>
              <small>{{ record.primaryItem?.specification || record.warehouseName || '-' }}</small>
            </div>

            <div class="quantity-block used">
              <span>出库数量</span>
              <strong>
                {{ formatNumber(record.totalQuantity) }}
                <small>{{ record.primaryItem?.unit || '' }}</small>
              </strong>
            </div>

            <div class="quantity-block produced">
              <span>成品数量</span>
              <strong>{{ formatNumber(record.producedQuantity) }} <small>kg</small></strong>
            </div>

            <div class="record-note">
              <span>备注</span>
              <strong>{{ record.remark || '无' }}</strong>
            </div>
          </div>

          <footer>
            <div>
              <span>{{ record.documentNo }}</span>
              <small>{{ formatTime(record.createdAt) }} · {{ record.createdBy || '员工' }}</small>
            </div>
            <span :class="['status-badge', `status-${record.status}`]">
              {{ statusLabel(record.status) }}
            </span>
          </footer>
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
const filterStartDate = ref('')
const filterEndDate = ref('')

const emptyMessage = computed(() => (
  filterStartDate.value && filterEndDate.value
    ? `${filterStartDate.value} 至 ${filterEndDate.value} 暂无原材料出库记录`
    : '最近 30 天暂无原材料出库记录'
))

const materialGroups = computed(() => {
  const groups = new Map()
  records.value.forEach(record => {
    const date = String(record.documentDate || record.createdAt || '').slice(0, 10) || '未记录日期'
    if (!groups.has(date)) groups.set(date, [])
    groups.get(date).push(record)
  })
  return [...groups.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([date, items]) => ({
      date,
      records: items.sort((left, right) => String(right.createdAt).localeCompare(String(left.createdAt)))
    }))
})

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const formatTime = value => {
  const text = String(value || '')
  return text.length >= 16 ? text.slice(11, 16) : text || '-'
}

const statusLabel = status => ({
  draft: '待管理员审核',
  reviewed: '已审核扣库',
  cancelled: '已作废'
}[status] || status)

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

const fetchRecords = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const range = filterStartDate.value && filterEndDate.value
      ? { start: filterStartDate.value, end: filterEndDate.value }
      : defaultDateRange()
    const response = await request({
      url: '/material-outbounds',
      method: 'GET',
      params: {
        startDate: range.start,
        endDate: range.end,
        limit: 300
      }
    })
    records.value = Array.isArray(response) ? response : []
  } catch (error) {
    loadError.value = error?.response?.data?.message || '原材料出库记录加载失败。'
    records.value = []
  } finally {
    loading.value = false
  }
}

const handleDateFilter = event => {
  filterStartDate.value = event.detail?.startDate || ''
  filterEndDate.value = event.detail?.endDate || ''
  fetchRecords()
}

const handleRefresh = () => fetchRecords()

onMounted(() => {
  fetchRecords()
  window.addEventListener('filter-material-date', handleDateFilter)
  window.addEventListener('refresh-materials', handleRefresh)
  window.addEventListener('refresh-material-outbounds', handleRefresh)
})

onBeforeUnmount(() => {
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.material-card {
  overflow: hidden;
  background: #fff;
  border: 1px solid #dfe7ef;
  border-radius: 18px;
  box-shadow: 0 5px 18px rgba(15, 23, 42, 0.04);
}

.card-main {
  display: grid;
  grid-template-columns: minmax(150px, 1.2fr) repeat(2, minmax(115px, 0.75fr)) minmax(120px, 0.8fr);
  gap: 0;
  padding: 22px 24px;
}

.card-main > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 0 18px;
  border-right: 1px solid #edf1f5;
}

.card-main > div:first-child {
  padding-left: 0;
}

.card-main > div:last-child {
  padding-right: 0;
  border-right: 0;
}

.material-name span,
.quantity-block span,
.record-note span {
  color: #526074;
  font-size: 16px;
  font-weight: 750;
  line-height: 1.35;
}

.quantity-block span {
  color: #344054;
  font-size: 17px;
  font-weight: 800;
}

.material-name strong {
  overflow: hidden;
  color: #172033;
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-name small {
  overflow: hidden;
  color: #64748b;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quantity-block strong {
  color: #e5487b;
  font-size: 22px;
}

.quantity-block.produced strong {
  color: #16a36a;
}

.quantity-block strong small {
  font-size: 12px;
}

.record-note strong {
  overflow: hidden;
  color: #344054;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-card footer {
  display: flex;
  min-height: 54px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 24px;
  background: #f8fafc;
  border-top: 1px solid #edf1f5;
}

.material-card footer > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.material-card footer > div span {
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.material-card footer small {
  color: #94a3b8;
  font-size: 11px;
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

@media (max-width: 1200px) {
  .timeline-items {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .card-main {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px 0;
  }

  .card-main > div:nth-child(2) {
    border-right: 0;
  }
}
</style>
