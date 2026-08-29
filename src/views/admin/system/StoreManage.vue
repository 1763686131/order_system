<template>
  <div class="store-management-page">
    <!-- 操作栏 -->
    <div class="action-bar">
      <button class="btn-new" @click="handleNew">
        <span class="icon">+</span> 新增门店
      </button>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="store-table">
        <thead>
          <tr>
            <th class="col-id">ID</th>
            <th class="col-code">门店编码</th>
            <th class="col-name">门店名称</th>
            <th class="col-status">状态</th>
            <th class="col-color">背景颜色</th>
            <th class="col-text-color">字体颜色</th>
            <th class="col-create-time">创建时间</th>
            <th class="col-remark">备注</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="store in stores" :key="store.id" :class="{ 'row-disabled': store.status === 'inactive' }">
            <td class="col-id">{{ store.id }}</td>
            <td class="col-code">{{ store.code }}</td>
            <td class="col-name">{{ store.name }}</td>
            <td class="col-status">
              <span :class="['status-badge', store.status === 'active' ? 'status-active' : 'status-inactive']">
                {{ store.status === 'active' ? '启用' : '停用' }}
              </span>
            </td>
            <td class="col-color">
              <div style="display: flex; align-items: center; gap: 8px;">
                <div
                  style="width: 40px; height: 24px; border: 1px solid #d9d9d9; border-radius: 4px;"
                  :style="{ backgroundColor: store.color || '#f5f5f5' }"
                ></div>
                <span style="font-size: 12px; color: #666;">{{ store.color || '#f5f5f5' }}</span>
              </div>
            </td>
            <td class="col-text-color">
              <div style="display: flex; align-items: center; gap: 8px;">
                <div
                  style="width: 60px; height: 24px; border: 1px solid #d9d9d9; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold;"
                  :style="{ backgroundColor: store.color || '#f5f5f5', color: store.textColor || '#333333' }"
                >
                  示例
                </div>
                <span style="font-size: 12px; color: #666;">{{ store.textColor || '#333333' }}</span>
              </div>
            </td>
            <td class="col-create-time">{{ store.created_at || '-' }}</td>
            <td class="col-remark">{{ store.remark || '-' }}</td>
            <td class="col-actions">
              <button class="btn-action btn-edit" @click="handleEdit(store)">编辑</button>
              <button
                class="btn-action"
                :class="store.status === 'active' ? 'btn-disable' : 'btn-enable'"
                @click="handleToggleStatus(store)"
              >
                {{ store.status === 'active' ? '停用' : '启用' }}
              </button>
              <button class="btn-action btn-delete" @click="handleDelete(store)">删除</button>
            </td>
          </tr>

          <tr v-if="stores.length === 0">
            <td colspan="7" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">🏪</span>
                <p>暂无门店数据</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 提示信息 -->
    <div class="info-box">
      <div class="info-title">💡 温馨提示</div>
      <ul class="info-list">
        <li>门店ID用于关联订单、商品等数据，创建后不可修改</li>
        <li>停用门店后，相关数据仍然保留，但无法创建新的关联数据</li>
        <li>删除门店前请确保没有关联的订单数据，否则可能导致数据异常</li>
      </ul>
    </div>

    <!-- 门店表单弹窗 -->
    <StoreFormModal ref="storeFormModal" @save="handleSave" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StoreFormModal from '@/components/admin/StoreFormModal.vue'
import request from '@/api/request'

const stores = ref([])
const storeFormModal = ref(null)

// 加载门店列表
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      stores.value = response
    }
  } catch (error) {
    console.error('加载门店列表失败:', error)
  }
}

// 新增门店
const handleNew = () => {
  if (storeFormModal.value) {
    storeFormModal.value.open()
  }
}

// 编辑门店
const handleEdit = (store) => {
  if (storeFormModal.value) {
    storeFormModal.value.open(store)
  }
}

// 切换状态
const handleToggleStatus = async (store) => {
  const newStatus = store.status === 'active' ? 'inactive' : 'active'
  const action = newStatus === 'active' ? '启用' : '停用'

  if (!confirm(`确定要${action}门店"${store.name}"吗？`)) {
    return
  }

  try {
    const response = await request({
      url: `/stores/${store.id}`,
      method: 'PUT',
      data: {
        ...store,
        status: newStatus
      }
    })

    if (response && response.success) {
      alert(`${action}成功`)
      loadStores()
    }
  } catch (error) {
    console.error('更新门店状态失败:', error)
    alert(`${action}失败`)
  }
}

// 删除门店
const handleDelete = async (store) => {
  if (!confirm(`确定要删除门店"${store.name}"吗？\n\n删除前请确保该门店没有关联的订单数据！`)) {
    return
  }

  try {
    const response = await request({
      url: `/stores/${store.id}`,
      method: 'DELETE'
    })

    if (response && response.success) {
      alert('删除成功')
      loadStores()
    }
  } catch (error) {
    console.error('删除门店失败:', error)
    alert('删除失败：' + (error.message || '未知错误'))
  }
}

// 保存门店
const handleSave = async (storeData) => {
  try {
    const isEdit = !!storeData.id
    const response = await request({
      url: isEdit ? `/stores/${storeData.id}` : '/stores',
      method: isEdit ? 'PUT' : 'POST',
      data: storeData
    })

    if (response && response.success) {
      alert(isEdit ? '更新成功' : '创建成功')
      loadStores()
    }
  } catch (error) {
    console.error('保存门店失败:', error)
    alert('保存失败：' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  loadStores()
})
</script>

<style scoped>
.store-management-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 操作栏 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.btn-new {
  padding: 10px 24px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-new:hover {
  background: #059669;
}

.icon {
  font-size: 18px;
  font-weight: bold;
}

/* 表格 */
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
  margin-bottom: 24px;
}

.store-table {
  width: 100%;
  border-collapse: collapse;
}

.store-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.store-table td {
  padding: 14px 16px;
  font-size: 13px;
  color: #1f2937;
  border-bottom: 1px solid #e5e7eb;
}

.store-table tbody tr:hover {
  background: #f9fafb;
}

.store-table tbody tr.row-disabled {
  opacity: 0.6;
  background: #f3f4f6;
}

/* 列宽 */
.col-id {
  width: 80px;
  text-align: center;
}

.col-code {
  width: 150px;
}

.col-name {
  width: 200px;
}

.col-status {
  width: 100px;
  text-align: center;
}

.col-create-time {
  width: 180px;
}

.col-remark {
  min-width: 200px;
}

.col-actions {
  width: 200px;
}

/* 状态标签 */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background: #d1fae5;
  color: #065f46;
}

.status-inactive {
  background: #fee2e2;
  color: #991b1b;
}

/* 操作按钮 */
.btn-action {
  padding: 4px 12px;
  margin-right: 6px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.btn-action.btn-edit {
  color: #3b82f6;
  border-color: #3b82f6;
}

.btn-action.btn-edit:hover {
  background: #3b82f6;
  color: white;
}

.btn-action.btn-disable {
  color: #f59e0b;
  border-color: #f59e0b;
}

.btn-action.btn-disable:hover {
  background: #f59e0b;
  color: white;
}

.btn-action.btn-enable {
  color: #10b981;
  border-color: #10b981;
}

.btn-action.btn-enable:hover {
  background: #10b981;
  color: white;
}

.btn-action.btn-delete {
  color: #ef4444;
  border-color: #ef4444;
}

.btn-action.btn-delete:hover {
  background: #ef4444;
  color: white;
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

/* 提示信息 */
.info-box {
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 16px 20px;
}

.info-title {
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 8px;
}

.info-list {
  margin: 0;
  padding-left: 20px;
  color: #78350f;
  font-size: 13px;
  line-height: 1.8;
}

.info-list li {
  margin-bottom: 4px;
}
</style>
