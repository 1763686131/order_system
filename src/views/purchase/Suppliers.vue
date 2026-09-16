<template>
  <div class="suppliers">
    <div class="page-header">
      <h2>供应商管理</h2>
      <button class="btn-primary" @click="createSupplier">
        <span class="icon">+</span>
        新增供应商
      </button>
    </div>

    <div class="filters">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索供应商名称、联系人..."
        class="search-input"
      />
      <select v-model="statusFilter" class="filter-select">
        <option value="">全部状态</option>
        <option value="active">合作中</option>
        <option value="inactive">已停用</option>
      </select>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>供应商名称</th>
            <th>联系人</th>
            <th>联系电话</th>
            <th>地址</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredSuppliers.length === 0">
            <td colspan="6" class="empty-state">暂无供应商</td>
          </tr>
          <tr v-for="supplier in filteredSuppliers" :key="supplier.id">
            <td class="supplier-name">{{ supplier.name }}</td>
            <td>{{ supplier.contactPerson }}</td>
            <td>{{ supplier.contactPhone }}</td>
            <td>{{ supplier.address }}</td>
            <td>
              <span :class="['status-badge', supplier.status]">
                {{ supplier.status === 'active' ? '合作中' : '已停用' }}
              </span>
            </td>
            <td class="actions">
              <button @click="viewSupplier(supplier.id)" class="btn-text">查看</button>
              <button @click="editSupplier(supplier.id)" class="btn-text">编辑</button>
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
const statusFilter = ref('')
const suppliers = ref([])

const filteredSuppliers = computed(() => {
  return suppliers.value.filter(supplier => {
    const matchesSearch = !searchQuery.value ||
      supplier.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      supplier.contactPerson.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesStatus = !statusFilter.value || supplier.status === statusFilter.value

    return matchesSearch && matchesStatus
  })
})

const createSupplier = () => {
  router.push('/admin/purchase/suppliers/create')
}

const viewSupplier = (id) => {
  router.push(`/admin/purchase/suppliers/${id}`)
}

const editSupplier = (id) => {
  router.push(`/admin/purchase/suppliers/edit/${id}`)
}
</script>

<style scoped>
.suppliers {
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
}

.search-input,
.filter-select {
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

.search-input:focus,
.filter-select:focus {
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

.supplier-name {
  font-weight: 600;
  color: #0f172a;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #f3f4f6;
  color: #6b7280;
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
