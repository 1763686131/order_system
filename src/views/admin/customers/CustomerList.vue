<template>
  <div class="customer-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-group store-slider">
        <label>门店分类</label>
        <div class="store-tabs">
          <div
            :class="['store-tab', { active: filters.storeId === null }]"
            @click="filters.storeId = null"
          >
            全部
          </div>
          <div
            v-for="store in allStores"
            :key="store.id"
            :class="['store-tab', { active: filters.storeId === store.id }]"
            @click="filters.storeId = store.id"
          >
            {{ store.name }}
          </div>
        </div>
      </div>

      <div class="search-group">
        <label>客户名称</label>
        <input
          v-model="filters.customerName"
          type="text"
          placeholder="请输入客户名称"
          class="search-input"
        />
      </div>

      <div class="search-group">
        <label>联系电话</label>
        <input
          v-model="filters.phone"
          type="text"
          placeholder="请输入联系电话"
          class="search-input"
        />
      </div>

      <div class="search-group">
        <label>客户状态</label>
        <select v-model="filters.status" class="search-select">
          <option value="">全部</option>
          <option value="active">活跃</option>
          <option value="inactive">不活跃</option>
        </select>
      </div>

      <button class="btn-search" @click="handleSearch">
        <span class="icon">🔍</span> 搜索
      </button>

      <button class="btn-reset" @click="handleReset">
        <span class="icon">↻</span> 重置
      </button>

      <button class="btn-add" @click="handleAdd">
        <span class="icon">➕</span> 新增客户
      </button>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>客户编号</th>
            <th>客户名称</th>
            <th>所属门店</th>
            <th>联系人</th>
            <th>联系电话</th>
            <th>储值余额</th>
            <th>应收欠款</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="loading-cell">
              <div class="loading-spinner"></div>
              <span>加载中...</span>
            </td>
          </tr>
          <tr v-else-if="customers.length === 0">
            <td colspan="10" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="customer in customers" :key="customer.id">
            <td>{{ customer.customerCode }}</td>
            <td>{{ customer.customerName }}</td>
            <td>{{ customer.storeName }}</td>
            <td>{{ customer.contactPerson }}</td>
            <td>{{ customer.phone }}</td>
            <td class="amount balance">¥{{ formatAmount(customer.balance) }}</td>
            <td class="amount">
              <span :class="{ 'debt-amount': customer.receivable > 0 }">
                ¥{{ formatAmount(customer.receivable) }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', customer.status]">
                {{ customer.status === 'active' ? '活跃' : '不活跃' }}
              </span>
            </td>
            <td>{{ formatDate(customer.createdAt) }}</td>
            <td class="actions">
              <button class="btn-action btn-view" @click="handleView(customer)" title="查看详情">
                👁️
              </button>
              <button class="btn-action btn-edit" @click="handleEdit(customer)" title="编辑">
                ✏️
              </button>
              <button class="btn-action btn-delete" @click="handleDelete(customer)" title="删除">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <div class="pagination-info">
        共 {{ total }} 条记录，每页 {{ pageSize }} 条
      </div>
      <div class="pagination-controls">
        <button
          class="btn-page"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button
          class="btn-page"
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 客户详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>客户详情</h3>
          <button class="btn-close" @click="closeDetailModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>客户编号</label>
                <span>{{ selectedCustomer?.customerCode }}</span>
              </div>
              <div class="detail-item">
                <label>客户名称</label>
                <span>{{ selectedCustomer?.customerName }}</span>
              </div>
              <div class="detail-item">
                <label>所属门店</label>
                <span>{{ selectedCustomer?.storeName }}</span>
              </div>
              <div class="detail-item">
                <label>联系人</label>
                <span>{{ selectedCustomer?.contactPerson }}</span>
              </div>
              <div class="detail-item">
                <label>联系电话</label>
                <span>{{ selectedCustomer?.phone }}</span>
              </div>
              <div class="detail-item">
                <label>联系地址</label>
                <span>{{ selectedCustomer?.address }}</span>
              </div>
            </div>
          </div>
          <div class="detail-section">
            <h4>财务信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>储值余额</label>
                <span class="amount balance">¥{{ formatAmount(selectedCustomer?.balance) }}</span>
              </div>
              <div class="detail-item">
                <label>应收欠款</label>
                <span class="amount" :class="{ 'debt-amount': selectedCustomer?.receivable > 0 }">
                  ¥{{ formatAmount(selectedCustomer?.receivable) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑/新增弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditMode ? '编辑客户' : '新增客户' }}</h3>
          <button class="btn-close" @click="closeEditModal">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleSubmit">
            <!-- 第一排：客户名称 + 编号 -->
            <div class="form-row">
              <div class="form-group">
                <label>客户名称 <span class="required">*</span></label>
                <input
                  v-model="formData.customerName"
                  type="text"
                  placeholder="请输入客户名称"
                  required
                />
              </div>
              <div class="form-group">
                <label>客户编号 <span class="required">*</span></label>
                <input
                  v-model="formData.customerCode"
                  type="text"
                  placeholder="请输入客户编号"
                  required
                />
              </div>
            </div>

            <!-- 第二排：联系人 + 联系电话 -->
            <div class="form-row">
              <div class="form-group">
                <label>联系人</label>
                <input
                  v-model="formData.contactPerson"
                  type="text"
                  placeholder="请输入联系人"
                />
              </div>
              <div class="form-group">
                <label>联系电话</label>
                <input
                  v-model="formData.phone"
                  type="tel"
                  placeholder="请输入联系电话"
                />
              </div>
            </div>

            <!-- 第三排：联系地址（独占一排） -->
            <div class="form-row">
              <div class="form-group form-group-full">
                <label>联系地址</label>
                <textarea
                  v-model="formData.address"
                  placeholder="请输入联系地址"
                  rows="2"
                ></textarea>
              </div>
            </div>

            <!-- 第四排：储值余额 + 期初欠款 -->
            <div class="form-row">
              <div class="form-group">
                <label>储值余额</label>
                <input
                  v-model.number="formData.balance"
                  type="number"
                  step="0.01"
                  placeholder="请输入储值余额"
                />
              </div>
              <div class="form-group">
                <label>期初欠款</label>
                <input
                  v-model.number="formData.initialDebt"
                  type="number"
                  step="0.01"
                  placeholder="请输入期初欠款"
                />
              </div>
            </div>

            <!-- 财务信息标题 -->
            <div class="form-section-title">财务信息</div>

            <!-- 第五排：开户行 + 银行账号 -->
            <div class="form-row">
              <div class="form-group">
                <label>开户行</label>
                <input
                  v-model="formData.bankName"
                  type="text"
                  placeholder="请输入开户行"
                />
              </div>
              <div class="form-group">
                <label>银行账号</label>
                <input
                  v-model="formData.bankAccount"
                  type="text"
                  placeholder="请输入银行账号"
                />
              </div>
            </div>

            <!-- 第六排：行号 + 税号 -->
            <div class="form-row">
              <div class="form-group">
                <label>行号</label>
                <input
                  v-model="formData.bankCode"
                  type="text"
                  placeholder="请输入行号"
                />
              </div>
              <div class="form-group">
                <label>税号</label>
                <input
                  v-model="formData.taxNumber"
                  type="text"
                  placeholder="请输入税号"
                />
              </div>
            </div>

            <!-- 最后一排：备注（独占一排） -->
            <div class="form-row">
              <div class="form-group form-group-full">
                <label>备注</label>
                <textarea
                  v-model="formData.remark"
                  placeholder="请输入备注信息"
                  rows="3"
                ></textarea>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" class="btn-cancel" @click="closeEditModal">取消</button>
              <button type="submit" class="btn-submit">{{ isEditMode ? '保存' : '创建' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const customers = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = ref({
  customerName: '',
  phone: '',
  storeId: null,
  status: ''
})

const allStores = ref([])

const showDetailModal = ref(false)
const showEditModal = ref(false)
const isEditMode = ref(false)
const selectedCustomer = ref(null)

const formData = ref({
  customerName: '',
  customerCode: '',
  storeId: '',
  contactPerson: '',
  phone: '',
  address: '',
  balance: 0,
  initialDebt: 0,
  bankName: '',
  bankAccount: '',
  bankCode: '',
  taxNumber: '',
  remark: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 加载门店数据
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allStores.value = response
    }
  } catch (error) {
    console.error('加载门店失败:', error)
  }
}

// 加载客户列表
const loadCustomers = async () => {
  loading.value = true
  try {
    const params = {
      customerName: filters.value.customerName,
      phone: filters.value.phone,
      storeId: filters.value.storeId,
      status: filters.value.status
    }

    const response = await request({
      url: '/customers',
      method: 'GET',
      params
    })

    if (response && Array.isArray(response)) {
      // 关联门店名称
      customers.value = response.map(customer => {
        const store = allStores.value.find(s => s.id === customer.storeId)
        return {
          ...customer,
          storeName: store ? store.name : '未知门店'
        }
      })
      total.value = customers.value.length
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadCustomers()
}

// 重置
const handleReset = () => {
  filters.value = {
    customerName: '',
    phone: '',
    storeId: null,
    status: ''
  }
  currentPage.value = 1
  loadCustomers()
}

// 新增
const handleAdd = () => {
  isEditMode.value = false
  formData.value = {
    customerName: '',
    customerCode: '',
    storeId: '',
    contactPerson: '',
    phone: '',
    address: '',
    balance: 0,
    initialDebt: 0,
    bankName: '',
    bankAccount: '',
    bankCode: '',
    taxNumber: '',
    remark: ''
  }
  showEditModal.value = true
}

// 查看详情
const handleView = (customer) => {
  selectedCustomer.value = customer
  showDetailModal.value = true
}

// 编辑
const handleEdit = (customer) => {
  isEditMode.value = true
  selectedCustomer.value = customer
  formData.value = {
    customerName: customer.customerName,
    customerCode: customer.customerCode,
    storeId: customer.storeId,
    contactPerson: customer.contactPerson,
    phone: customer.phone,
    address: customer.address,
    balance: customer.balance,
    initialDebt: customer.receivable,
    bankName: customer.bankName || '',
    bankAccount: customer.bankAccount || '',
    bankCode: customer.bankCode || '',
    taxNumber: customer.taxNumber || '',
    remark: customer.remark || ''
  }
  showEditModal.value = true
}

// 删除
const handleDelete = async (customer) => {
  if (confirm(`确定要删除客户"${customer.customerName}"吗？`)) {
    try {
      await request({
        url: `/customers/${customer.id}`,
        method: 'DELETE'
      })
      alert('删除成功')
      loadCustomers()
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    if (isEditMode.value) {
      // 更新客户
      await request({
        url: `/customers/${selectedCustomer.value.id}`,
        method: 'PUT',
        data: formData.value
      })
      alert('保存成功')
    } else {
      // 创建客户
      await request({
        url: '/customers',
        method: 'POST',
        data: formData.value
      })
      alert('创建成功')
    }
    closeEditModal()
    loadCustomers()
  } catch (error) {
    console.error('保存失败:', error)
    alert(error.response?.data?.error || '保存失败')
  }
}

// 关闭详情弹窗
const closeDetailModal = () => {
  showDetailModal.value = false
  selectedCustomer.value = null
}

// 关闭编辑弹窗
const closeEditModal = () => {
  showEditModal.value = false
  isEditMode.value = false
  selectedCustomer.value = null
}

// 分页
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadCustomers()
}

// 格式化金额
const formatAmount = (amount) => {
  return amount ? amount.toFixed(2) : '0.00'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 获取客户类型标签
const getCustomerTypeLabel = (type) => {
  const labels = {
    retail: '零售客户',
    wholesale: '批发客户',
    vip: 'VIP客户'
  }
  return labels[type] || type
}

onMounted(async () => {
  await loadStores()
  await loadCustomers()
})
</script>

<style scoped>
.customer-list-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.search-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-group label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.store-slider {
  flex: 1;
  min-width: 0;
  max-width: 600px;
}

.store-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
}

.store-tabs::-webkit-scrollbar {
  height: 4px;
}

.store-tabs::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.store-tab {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  flex-shrink: 0;
}

.store-tab:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.store-tab.active {
  background: #34d399;
  color: #fff;
  border-color: #34d399;
}

.search-input,
.search-select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  min-width: 180px;
}

.search-input:focus,
.search-select:focus {
  border-color: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
}

.btn-search,
.btn-reset,
.btn-add {
  height: 36px;
  padding: 0 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-search {
  background: #34d399;
  color: #fff;
}

.btn-search:hover {
  background: #10b981;
}

.btn-reset {
  background: #f3f4f6;
  color: #374151;
}

.btn-reset:hover {
  background: #e5e7eb;
}

.btn-add {
  background: #3b82f6;
  color: #fff;
  margin-left: auto;
}

.btn-add:hover {
  background: #2563eb;
}

/* 表格 */
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table thead {
  background: #f9fafb;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  color: #6b7280;
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px !important;
  color: #9ca3af;
}

.loading-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #34d399;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.amount {
  font-weight: 600;
  color: #059669;
}

.amount.balance {
  color: #0891b2;
}

.debt-amount {
  color: #ef4444 !important;
}

.type-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-retail {
  background: #dbeafe;
  color: #1e40af;
}

.type-wholesale {
  background: #fef3c7;
  color: #92400e;
}

.type-vip {
  background: #fce7f3;
  color: #9f1239;
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
  gap: 8px;
}

.btn-action {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-view {
  background: #dbeafe;
}

.btn-view:hover {
  background: #bfdbfe;
}

.btn-edit {
  background: #fef3c7;
}

.btn-edit:hover {
  background: #fde68a;
}

.btn-delete {
  background: #fee2e2;
}

.btn-delete:hover {
  background: #fecaca;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
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

.btn-page {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-page:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #34d399;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #374151;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.modal-large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  color: #6b7280;
  transition: all 0.3s;
}

.btn-close:hover {
  background: #e5e7eb;
  color: #111827;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  padding-bottom: 100px;
}

/* 详情页 */
.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #111827;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 13px;
  color: #6b7280;
}

.detail-item span {
  font-size: 14px;
  color: #111827;
}

/* 表单 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.form-section-title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin: 24px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group-full {
  grid-column: 1 / -1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.required {
  color: #ef4444;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  margin: 0;
  z-index: 10;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.btn-cancel,
.btn-submit {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-submit {
  background: #34d399;
  color: #fff;
}

.btn-submit:hover {
  background: #10b981;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .modal-large {
    max-width: 95%;
  }
}
</style>

