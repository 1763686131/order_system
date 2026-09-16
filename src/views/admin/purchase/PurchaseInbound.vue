<template>
  <div class="purchase-inbound">
    <div class="page-header">
      <h2>采购入库</h2>
      <button class="btn-primary" @click="createInbound">
        <span class="icon">+</span>
        新增入库单
      </button>
    </div>

    <div class="filters">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索入库单号、采购单号..."
        class="search-input"
      />
      <input
        v-model="dateRange.start"
        type="date"
        class="filter-input"
      />
      <span class="date-separator">至</span>
      <input
        v-model="dateRange.end"
        type="date"
        class="filter-input"
      />
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>入库单号</th>
            <th>采购单号</th>
            <th>供应商</th>
            <th>入库日期</th>
            <th>入库仓库</th>
            <th>操作人</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredRecords.length === 0">
            <td colspan="7" class="empty-state">暂无入库记录</td>
          </tr>
          <tr v-for="record in filteredRecords" :key="record.id">
            <td class="inbound-no">{{ record.inboundNo }}</td>
            <td>{{ record.purchaseOrderNo }}</td>
            <td>{{ record.supplierName }}</td>
            <td>{{ formatDate(record.inboundDate) }}</td>
            <td>{{ record.warehouseName }}</td>
            <td>{{ record.operator }}</td>
            <td class="actions">
              <button @click="viewRecord(record.id)" class="btn-text">查看</button>
              <button @click="printRecord(record.id)" class="btn-text">打印</button>
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
const dateRange = ref({
  start: '',
  end: ''
})
const records = ref([])

const filteredRecords = computed(() => {
  return records.value.filter(record => {
    const matchesSearch = !searchQuery.value ||
      record.inboundNo.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      record.purchaseOrderNo.toLowerCase().includes(searchQuery.value.toLowerCase())

    const recordDate = new Date(record.inboundDate)
    const matchesDateStart = !dateRange.value.start || recordDate >= new Date(dateRange.value.start)
    const matchesDateEnd = !dateRange.value.end || recordDate <= new Date(dateRange.value.end)

    return matchesSearch && matchesDateStart && matchesDateEnd
  })
})

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const createInbound = () => {
  router.push('/admin/purchase/inbound/create')
}

const viewRecord = (id) => {
  router.push(`/admin/purchase/inbound/${id}`)
}

const printRecord = (id) => {
  console.log('打印入库单:', id)
}
</script>

<style scoped>
.purchase-inbound {
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
  align-items: center;
}

.search-input,
.filter-input {
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

.filter-input {
  width: 160px;
}

.date-separator {
  color: #64748b;
  font-size: 14px;
}

.search-input:focus,
.filter-input:focus {
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

.inbound-no {
  font-weight: 600;
  color: #0f172a;
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
