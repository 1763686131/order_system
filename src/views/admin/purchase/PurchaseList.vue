<template>
  <div class="purchase-list" :class="{ inbound: isInbound }">
    <section class="table-card">
      <div class="table-toolbar">
        <h2>{{ isInbound ? '采购入库' : '采购订单' }}</h2>
        <form class="filters" role="search" :aria-label="isInbound ? '入库单筛选' : '采购订单筛选'" @submit.prevent="applyFilters">
          <template v-if="isInbound">
            <label class="filter-field">
              <span>开始日期</span>
              <input v-model="dateRange.start" type="date" />
            </label>
            <label class="filter-field">
              <span>结束日期</span>
              <input v-model="dateRange.end" type="date" />
            </label>
          </template>
          <label v-else class="filter-field">
            <span>订单状态</span>
            <select v-model="statusFilter">
              <option value="">全部状态</option>
              <option value="pending">待确认</option>
              <option value="confirmed">已确认</option>
              <option value="partial">部分入库</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </label>
          <label class="filter-field search-field">
            <span>{{ isInbound ? '入库单信息' : '采购订单信息' }}</span>
            <input
              v-model.trim="searchQuery"
              type="search"
              :placeholder="isInbound ? '搜索入库单号、采购单号' : '搜索采购单号、供应商'"
            />
          </label>
          <div class="filter-actions">
            <button class="btn btn-primary" type="submit">
              <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></svg>
              查询
            </button>
            <button class="btn btn-ghost" type="button" @click="resetFilters">
              <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><path d="M4 12a8 8 0 1 0 2.3-5.7" /><path d="M4 4v5h5" /></svg>
              重置
            </button>
          </div>
        </form>
        <div class="toolbar-actions">
          <span class="result-count">共 {{ filteredRecords.length }} 条</span>
          <button class="btn btn-primary" type="button" @click="createRecord">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17"><path d="M12 5v14M5 12h14" /></svg>
            {{ isInbound ? '新增入库单' : '新增采购订单' }}
          </button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr v-if="isInbound">
              <th>入库单号</th>
              <th>采购单号</th>
              <th>供应商</th>
              <th>入库日期</th>
              <th>入库仓库</th>
              <th>操作人</th>
              <th class="actions">操作</th>
            </tr>
            <tr v-else>
              <th>采购单号</th>
              <th>供应商</th>
              <th>采购日期</th>
              <th>总金额</th>
              <th>状态</th>
              <th class="actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredRecords.length === 0">
              <td :colspan="isInbound ? 7 : 6" class="empty-state">
                {{ records.length ? (isInbound ? '暂无匹配的入库记录' : '暂无匹配的采购订单') : (isInbound ? '暂无入库记录' : '暂无采购订单') }}
              </td>
            </tr>
            <tr v-for="record in filteredRecords" :key="record.id">
              <template v-if="isInbound">
                <td class="record-no">{{ record.inboundNo }}</td>
                <td>{{ record.purchaseOrderNo }}</td>
                <td>{{ record.supplierName }}</td>
                <td>{{ formatDate(record.inboundDate) }}</td>
                <td>{{ record.warehouseName }}</td>
                <td>{{ record.operator }}</td>
              </template>
              <template v-else>
                <td class="record-no">{{ record.orderNo }}</td>
                <td>{{ record.supplierName }}</td>
                <td>{{ formatDate(record.purchaseDate) }}</td>
                <td class="amount">¥{{ Number(record.totalAmount).toFixed(2) }}</td>
                <td><span class="status-badge" :class="record.status">{{ statusLabel(record.status) }}</span></td>
              </template>
              <td class="actions">
                <button class="row-action" type="button" :title="isInbound ? '查看入库单' : '查看采购订单'" :aria-label="isInbound ? '查看入库单' : '查看采购订单'" @click="viewRecord(record.id)">
                  <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></svg>
                </button>
                <button v-if="isInbound" class="row-action" type="button" title="打印入库单" aria-label="打印入库单" @click="printRecord(record.id)">
                  <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><path d="M6 9V3h12v6M6 17H4V9h16v8h-2M6 14h12v7H6z" /></svg>
                </button>
                <button v-else class="row-action" type="button" title="编辑采购订单" aria-label="编辑采购订单" @click="editRecord(record.id)">
                  <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16"><path d="m4 16-.8 4.8L8 20l11.5-11.5a2.8 2.8 0 0 0-4-4Z" /><path d="m13.5 6.5 4 4" /></svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  mode: {
    type: String,
    required: true,
    validator: value => ['orders', 'inbound'].includes(value)
  }
})

const router = useRouter()
const isInbound = computed(() => props.mode === 'inbound')
const orders = ref([])
const inbounds = ref([])
const records = computed(() => isInbound.value ? inbounds.value : orders.value)
const searchQuery = ref('')
const statusFilter = ref('')
const dateRange = ref({ start: '', end: '' })
const appliedFilters = ref({ search: '', status: '', start: '', end: '' })

const filteredRecords = computed(() => {
  const { search, status, start, end } = appliedFilters.value
  const keyword = search.toLowerCase()
  return records.value.filter(record => {
    if (isInbound.value) {
      const matchesSearch = !keyword || [record.inboundNo, record.purchaseOrderNo]
        .some(value => String(value ?? '').toLowerCase().includes(keyword))
      const recordDate = new Date(record.inboundDate)
      return matchesSearch
        && (!start || recordDate >= new Date(start))
        && (!end || recordDate <= new Date(end + 'T23:59:59.999'))
    }
    const matchesSearch = !keyword || [record.orderNo, record.supplierName]
      .some(value => String(value ?? '').toLowerCase().includes(keyword))
    return matchesSearch && (!status || record.status === status)
  })
})

const applyFilters = () => {
  appliedFilters.value = { search: searchQuery.value, status: statusFilter.value, ...dateRange.value }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  dateRange.value = { start: '', end: '' }
  applyFilters()
}

watch(() => props.mode, resetFilters)

const formatDate = date => new Date(date).toLocaleDateString('zh-CN')

const statusLabel = status => ({
  pending: '待确认',
  confirmed: '已确认',
  partial: '部分入库',
  completed: '已完成',
  cancelled: '已取消'
})[status] || status

const createRecord = () => router.push(`/admin/purchase/${isInbound.value ? 'inbound' : 'orders'}/create`)
const viewRecord = id => router.push(`/admin/purchase/${isInbound.value ? 'inbound' : 'orders'}/${id}`)
const editRecord = id => router.push(`/admin/purchase/orders/edit/${id}`)

const printRecord = id => {
  console.log('打印入库单:', id)
}
</script>

<style scoped>
.purchase-list,
.purchase-list * {
  box-sizing: border-box;
}

.purchase-list {
  min-height: 100%;
  color: #17212b;
  background: #f5f7f8;
}

.table-card {
  width: 100%;
  overflow: hidden;
  border: 1px solid #e5e9ed;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 5px 18px rgba(23, 33, 43, .04);
}

.table-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid #e5e9ed;
}

.table-toolbar h2 {
  flex: 0 0 auto;
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  white-space: nowrap;
}

.filters {
  display: grid;
  grid-template-columns: minmax(130px, 150px) minmax(180px, 1fr) auto;
  align-items: end;
  flex: 1 1 520px;
  gap: 10px;
  max-width: 670px;
  min-width: 0;
  margin: 0;
}

.inbound .filters {
  grid-template-columns: minmax(130px, 150px) minmax(130px, 150px) minmax(190px, 1fr) auto;
  flex-basis: 740px;
  max-width: 850px;
}

.filter-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  color: #566371;
  font-size: 12px;
  font-weight: 600;
}

.filter-field input,
.filter-field select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 1px solid #d8dfe4;
  border-radius: 5px;
  outline: none;
  color: #17212b;
  background: #fff;
  font: inherit;
  font-weight: 400;
}

.filter-field input::placeholder {
  color: #a5afb7;
}

.filter-field input:focus,
.filter-field select:focus {
  border-color: #47b79d;
  box-shadow: 0 0 0 3px rgba(21, 154, 124, .12);
}

.filter-actions,
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.toolbar-actions {
  margin-left: auto;
}

.result-count {
  padding: 6px 11px;
  border-radius: 999px;
  color: #08755e;
  background: #e8f6f1;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.btn {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
}

.btn-primary {
  border-color: #159a7c;
  color: #fff;
  background: #159a7c;
}

.btn-primary:hover {
  border-color: #08755e;
  background: #08755e;
}

.btn-ghost {
  border-color: #d8dfe4;
  color: #4d5b67;
  background: #fff;
}

.btn-ghost:hover {
  border-color: #9db4ad;
  color: #08755e;
  background: #f5fbf9;
}

svg {
  flex: none;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  min-width: 780px;
  border-collapse: collapse;
  font-size: 13px;
}

.inbound .data-table {
  min-width: 900px;
}

.data-table th,
.data-table td {
  padding: 13px 15px;
  border-bottom: 1px solid #edf0f2;
  text-align: left;
  white-space: nowrap;
}

.data-table th {
  color: #7a8791;
  background: #fbfcfc;
  font-size: 11px;
  font-weight: 700;
}

.data-table tbody tr:hover {
  background: #fbfdfd;
}

.data-table tbody tr:last-child td {
  border-bottom: 0;
}

.data-table .empty-state {
  height: 220px;
  color: #76838d;
  text-align: center;
}

.record-no {
  color: #08755e;
  font-weight: 700;
}

.amount {
  font-variant-numeric: tabular-nums;
  font-weight: 650;
}

.data-table .actions {
  text-align: right;
}

.row-action {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  color: #65727e;
  background: transparent;
}

.row-action + .row-action {
  margin-left: 4px;
}

.row-action:hover {
  color: #08755e;
  background: #f1faf7;
}

.status-badge {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
}

.status-badge.pending { color: #955e0e; background: #fff1d8; }
.status-badge.confirmed { color: #28608a; background: #e7f2fa; }
.status-badge.partial { color: #755382; background: #f3ebf6; }
.status-badge.completed { color: #08755e; background: #e5f5ef; }
.status-badge.cancelled { color: #66737d; background: #f0f2f4; }

@media (max-width: 1240px) {
  .inbound .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    flex-basis: 100%;
    max-width: none;
    order: 2;
  }

  .inbound .toolbar-actions {
    order: 1;
  }
}

@media (max-width: 1100px) {
  .purchase-list:not(.inbound) .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    flex-basis: 100%;
    max-width: none;
    order: 2;
  }

  .purchase-list:not(.inbound) .toolbar-actions {
    order: 1;
  }
}

@media (max-width: 700px) {
  .table-toolbar {
    padding: 12px;
  }

  .filters,
  .inbound .filters {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    justify-content: flex-end;
  }
}
</style>
