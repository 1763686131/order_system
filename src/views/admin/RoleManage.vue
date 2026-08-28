<template>
  <div class="role-manage-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <button class="btn-add" @click="openCreateModal">+ 新增角色</button>
    </div>

    <!-- 角色列表表格 -->
    <div class="table-container">
      <table class="role-table">
        <thead>
          <tr>
            <th>角色名称</th>
            <th>角色ID</th>
            <th>权限</th>
            <th>备注</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.username">
            <td>{{ role.name }}</td>
            <td>{{ role.username }}</td>
            <td>
              <span class="status-badge" :class="getRoleClass(role.role)">
                {{ getRoleName(role.role) }}
              </span>
            </td>
            <td>{{ role.description || '-' }}</td>
            <td>{{ formatDate(role.createdAt) }}</td>
            <td>
              <div class="action-buttons">
                <button class="btn-link btn-modify" @click="openEditModal(role)">修改</button>
                <button class="btn-link btn-detail" @click="openPermissionDrawer(role)">详情</button>
                <button
                  class="btn-link btn-delete"
                  @click="deleteRole(role)"
                  :disabled="!canDelete(role)"
                  :style="{ opacity: !canDelete(role) ? 0.5 : 1, cursor: !canDelete(role) ? 'not-allowed' : 'pointer' }"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination">
        <span class="total-info">共 {{ totalRoles }} 条记录</span>
        <div class="page-controls">
          <span class="page-size">{{ pageSize }}/页</span>
          <div class="page-buttons">
            <button @click="goToPage(1)" :disabled="currentPage === 1">首页</button>
            <button @click="goToPage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
            <button
              v-for="page in visiblePages"
              :key="page"
              :class="{ active: currentPage === page }"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
            <button @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages">下一页</button>
            <button @click="goToPage(totalPages)" :disabled="currentPage === totalPages">末页</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 权限配置抽屉 -->
    <div v-if="showPermissionDrawer" class="drawer-overlay" @click.self="closePermissionDrawer">
      <div class="drawer-container">
        <div class="drawer-header">
          <h3>修改</h3>
          <button class="btn-close" @click="closePermissionDrawer">×</button>
        </div>

        <div class="drawer-body">
          <!-- 角色基本信息 -->
          <div class="form-section">
            <div class="form-item-inline">
              <label><span class="required">*</span> 角色名称</label>
              <input v-model="currentRole.name" placeholder="请输入" />
            </div>

            <div class="form-item-inline">
              <label>角色ID</label>
              <input v-model="currentRole.username" placeholder="请输入" :disabled="isEditMode" />
            </div>

            <div class="form-item-inline">
              <label><span class="required">*</span> 权限</label>
              <select v-model="currentRole.role" :disabled="isEditMode && currentRole.role === 'super_admin'">
                <option value="employee">普通员工</option>
                <option value="operator">操作员</option>
                <option value="admin">管理员</option>
                <option value="super_admin" v-if="userStore.user?.role === 'super_admin'">超级管理员</option>
              </select>
            </div>

            <div class="form-item-inline">
              <label>创建时间</label>
              <input
                v-model="currentRole.createdAt"
                :placeholder="isEditMode ? '请输入创建时间' : '自动生成当前时间'"
                :disabled="!isEditMode"
              />
            </div>

            <div class="form-item-full">
              <label>备注</label>
              <input v-model="currentRole.description" placeholder="请输入" />
            </div>
          </div>

          <!-- 权限配置树 -->
          <div class="permission-section">
            <h4>授权</h4>
            <div class="permission-tree">
              <div v-for="module in permissionModules" :key="module.id" class="permission-module">
                <div class="module-header">
                  <label>
                    <input
                      type="checkbox"
                      :checked="isModuleChecked(module)"
                      @change="toggleModule(module, $event)"
                    />
                    <span class="module-icon" v-html="module.icon"></span>
                    {{ module.label }}
                  </label>
                </div>

                <div class="module-children">
                  <div v-for="item in module.children" :key="item.id" class="permission-item">
                    <label>
                      <input
                        type="checkbox"
                        :value="item.id"
                        v-model="currentRole.permissions"
                      />
                      <span class="item-icon" v-html="item.icon"></span>
                      {{ item.label }}
                    </label>

                    <!-- 子权限 -->
                    <div v-if="item.children" class="permission-actions">
                      <label v-for="action in item.children" :key="action.id">
                        <input
                          type="checkbox"
                          :value="action.id"
                          v-model="currentRole.permissions"
                        />
                        {{ action.label }}
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="drawer-footer">
          <button class="btn-cancel" @click="closePermissionDrawer">取消</button>
          <button class="btn-confirm" @click="saveRole">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

// 注入 Admin 组件提供的方法
const setHeaderActions = inject('setHeaderActions', null)

// 角色管理页面不需要顶部按钮，清空
onMounted(async () => {
  if (setHeaderActions) {
    setHeaderActions(null)
  }
  await loadRoles()
})

// 角色列表数据
const roles = ref([])

// 加载角色列表
const loadRoles = async () => {
  try {
    const response = await request({ url: '/users', method: 'GET' })
    roles.value = response || []
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalRoles = computed(() => roles.value.length)

const totalPages = computed(() => Math.ceil(totalRoles.value / pageSize.value))

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 权限配置
const showPermissionDrawer = ref(false)
const currentRole = ref({
  username: '',
  name: '',
  role: 'employee',
  description: '',
  createdAt: '',
  permissions: []
})
const isEditMode = ref(false)

// 权限模块配置（映射自用户管理的权限配置）
const permissionModules = ref([
  {
    id: 'pending_order',
    label: '未完成订单 (车间看板)',
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="15" x2="15" y2="15"/></svg>',
    children: [
      { id: 'pending.add', label: '显示：发布新订单 (悬浮球)' },
      { id: 'pending.view_detail', label: '显示：卡片翻转与详情页面' },
      { id: 'pending.complete', label: '操作：确定完成业务' },
      { id: 'pending.edit', label: '操作：修改订单信息' },
      { id: 'pending.copy', label: '显示：复制物流信息' },
      { id: 'pending.delete', label: '操作：物理删除订单' }
    ]
  },
  {
    id: 'completed_order',
    label: '已完成订单 (核对发货)',
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    children: [
      { id: 'completed.ship', label: '操作：发货并出库' },
      { id: 'completed.uncomplete', label: '操作：撤销回未完成' },
      { id: 'completed.copy', label: '显示：复制物流信息' },
      { id: 'completed.delete', label: '操作：物理删除订单' }
    ]
  },
  {
    id: 'shipped',
    label: '已出库订单栏目',
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    children: [
      { id: 'shipped.audit', label: '发货方式标签（出库审核与撤销）' },
      { id: 'shipped.view_receipt', label: '回单标签（查看与下载凭证）' },
      { id: 'shipped.upload_receipt', label: '单号标签（上传与管理回单图片）' },
      { id: 'shipped.delete_receipt', label: '弹窗操作：允许删除回单图片' }
    ]
  },
  {
    id: 'material',
    label: '原材料数据模块',
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    children: [
      { id: 'material.add', label: '录入原材料数据' },
      { id: 'material.edit', label: '行内就地修改数据' },
      { id: 'material.delete', label: '物理删除流水记录' }
    ]
  },
  {
    id: 'system',
    label: '系统管理模块',
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"/></svg>',
    children: [
      { id: 'system.user_manage', label: '账户与权限控制台' }
    ]
  }
])

// 打开创建模态框
const openCreateModal = () => {
  isEditMode.value = false
  currentRole.value = {
    username: '',
    name: '',
    role: 'employee',
    description: '',
    createdAt: '',
    permissions: []
  }
  showPermissionDrawer.value = true
}

// 打开编辑模态框
const openEditModal = (role) => {
  isEditMode.value = true
  currentRole.value = {
    ...role,
    permissions: role.permissions || []
  }
  showPermissionDrawer.value = true
}

// 打开权限抽屉
const openPermissionDrawer = (role) => {
  isEditMode.value = true
  currentRole.value = {
    ...role,
    permissions: role.permissions || []
  }
  showPermissionDrawer.value = true
}

// 关闭抽屉
const closePermissionDrawer = () => {
  showPermissionDrawer.value = false
}

// 检查模块是否全选
const isModuleChecked = (module) => {
  if (!module.children || module.children.length === 0) {
    return currentRole.value.permissions.includes(module.id)
  }

  const allIds = module.children.map(item => item.id)
  return allIds.every(id => currentRole.value.permissions.includes(id))
}

// 切换模块
const toggleModule = (module, event) => {
  const checked = event.target.checked

  if (!module.children || module.children.length === 0) {
    if (checked) {
      if (!currentRole.value.permissions.includes(module.id)) {
        currentRole.value.permissions.push(module.id)
      }
    } else {
      const index = currentRole.value.permissions.indexOf(module.id)
      if (index > -1) {
        currentRole.value.permissions.splice(index, 1)
      }
    }
    return
  }

  const allIds = module.children.map(item => item.id)

  if (checked) {
    allIds.forEach(id => {
      if (!currentRole.value.permissions.includes(id)) {
        currentRole.value.permissions.push(id)
      }
    })
  } else {
    allIds.forEach(id => {
      const index = currentRole.value.permissions.indexOf(id)
      if (index > -1) {
        currentRole.value.permissions.splice(index, 1)
      }
    })
  }
}

// 保存角色
const saveRole = async () => {
  if (!isEditMode.value) {
    // 新建角色（使用用户管理的新增员工接口）
    const username = currentRole.value.username.trim()
    const name = currentRole.value.name.trim()
    if (!username || !name) {
      return alert('角色ID和角色名称不能为空！')
    }

    const payload = {
      username: username,
      name: name,
      password: '123456', // 默认密码
      role: currentRole.value.role || 'employee',
      permissions: currentRole.value.permissions
    }

    try {
      const res = await request({ url: '/users', method: 'POST', data: payload })
      if (res) {
        alert('角色创建成功')
        await loadRoles()
        closePermissionDrawer()
      }
    } catch (error) {
      alert('角色已存在或无权限！')
    }
  } else {
    // 编辑现有角色（使用用户管理的更新权限接口）
    const payload = {
      name: currentRole.value.name.trim(),
      permissions: currentRole.value.permissions,
      role: currentRole.value.role || 'employee'
    }

    try {
      const res = await request({
        url: `/users/${currentRole.value.username}/permissions`,
        method: 'PUT',
        data: payload
      })
      if (res) {
        alert('角色更新成功')
        await loadRoles()
        closePermissionDrawer()
      }
    } catch (error) {
      alert('更新失败，权限不足')
    }
  }
}

// 判断是否可以删除
const canDelete = (role) => {
  // 不能删除自己
  if (role.username === userStore.username) {
    return false
  }

  // 超管可以删除除了自己以外的所有人
  if (userStore.role === 'super_admin') {
    return true
  }

  // 管理员不能删除同级管理员和超管
  if (userStore.role === 'admin') {
    return role.role !== 'admin' && role.role !== 'super_admin'
  }

  // 其他角色不能删除
  return false
}

// 删除角色
const deleteRole = async (role) => {
  if (!canDelete(role)) {
    const currentUser = userStore.user
    if (role.username === currentUser?.username) {
      alert('不能删除自己的账号！')
    } else if (currentUser?.role === 'admin') {
      alert('管理员只能删除普通员工和操作员！')
    } else {
      alert('权限不足，无法删除此角色！')
    }
    return
  }

  if (!confirm(`确定要删除角色 ${role.name} 吗？`)) {
    return
  }

  try {
    await request({ url: `/users/${role.username}`, method: 'DELETE' })
    alert('角色已删除')
    await loadRoles()
  } catch (error) {
    alert('删除失败')
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  return dateStr || '-'
}

// 获取角色名称
const getRoleName = (role) => {
  const roleMap = {
    super_admin: '超管',
    admin: '管理',
    operator: '操作',
    employee: '员工'
  }
  return roleMap[role] || '未知'
}

// 获取角色样式类名
const getRoleClass = (role) => {
  const classMap = {
    super_admin: 'role-super-admin',
    admin: 'role-admin',
    operator: 'role-operator',
    employee: 'role-employee'
  }
  return classMap[role] || 'role-default'
}
</script>

<style scoped>
.role-manage-page {
  width: 100%;
  height: 100%;
  background: #1a1d24;
  color: #fff;
  padding: 20px;
}

/* 顶部操作栏 */
.page-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.btn-add {
  background: #1890ff;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.btn-add:hover {
  background: #40a9ff;
}

/* 表格容器 */
.table-container {
  background: #23262e;
  border-radius: 4px;
  overflow: hidden;
}

/* 表格样式 */
.role-table {
  width: 100%;
  border-collapse: collapse;
}

.role-table thead {
  background: #2a2d35;
}

.role-table th {
  padding: 16px;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #a0a4aa;
  border-bottom: 1px solid #3a3d45;
}

.role-table td {
  padding: 16px;
  font-size: 14px;
  color: #d0d3d9;
  border-bottom: 1px solid #3a3d45;
}

.role-table tbody tr:hover {
  background: #2a2d35;
}

/* 状态标签 */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-super-admin {
  background: rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
}

.role-admin {
  background: rgba(250, 173, 20, 0.2);
  color: #faad14;
}

.role-operator {
  background: rgba(24, 144, 255, 0.2);
  color: #1890ff;
}

.role-employee {
  background: rgba(82, 196, 26, 0.2);
  color: #52c41a;
}

.role-default {
  background: rgba(160, 164, 170, 0.2);
  color: #a0a4aa;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-link {
  background: none;
  border: none;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.3s;
}

.btn-modify {
  color: #1890ff;
}

.btn-modify:hover {
  color: #40a9ff;
}

.btn-detail {
  color: #52c41a;
}

.btn-detail:hover {
  color: #73d13d;
}

.btn-delete {
  color: #ff4d4f;
}

.btn-delete:hover {
  color: #ff7875;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-top: 1px solid #3a3d45;
}

.total-info {
  font-size: 14px;
  color: #a0a4aa;
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-size {
  font-size: 14px;
  color: #a0a4aa;
}

.page-buttons {
  display: flex;
  gap: 8px;
}

.page-buttons button {
  background: #2a2d35;
  color: #d0d3d9;
  border: 1px solid #3a3d45;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.page-buttons button:hover:not(:disabled) {
  background: #3a3d45;
  border-color: #1890ff;
  color: #1890ff;
}

.page-buttons button.active {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.page-buttons button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 抽屉遮罩 */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

/* 抽屉容器 */
.drawer-container {
  width: 600px;
  height: 100%;
  background: #23262e;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.3);
}

/* 抽屉头部 */
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #3a3d45;
}

.drawer-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.btn-close {
  background: none;
  border: none;
  color: #a0a4aa;
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.btn-close:hover {
  color: #fff;
}

/* 抽屉主体 */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 表单区域 */
.form-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.form-item-inline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item-full {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-section label {
  font-size: 14px;
  color: #a0a4aa;
  font-weight: 500;
}

.required {
  color: #ff4d4f;
  margin-right: 4px;
}

.form-section input {
  background: #1a1d24;
  border: 1px solid #3a3d45;
  color: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.form-section input:focus {
  border-color: #1890ff;
}

.form-section input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 状态切换 */
.status-toggle {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  flex: 1;
  background: #1a1d24;
  border: 1px solid #3a3d45;
  color: #a0a4aa;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.toggle-btn.active {
  background: rgba(24, 144, 255, 0.2);
  border-color: #1890ff;
  color: #1890ff;
}

/* 日期范围 */
.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
  grid-column: 1 / -1;
}

.date-range input {
  flex: 1;
}

.date-range span {
  color: #a0a4aa;
}

/* 权限配置区域 */
.permission-section {
  margin-top: 24px;
}

.permission-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

/* 权限树 */
.permission-tree {
  background: #1a1d24;
  border: 1px solid #3a3d45;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.permission-module {
  margin-bottom: 20px;
}

.permission-module:last-child {
  margin-bottom: 0;
}

.module-header label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
}

.module-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.module-children {
  margin-left: 24px;
  margin-top: 12px;
}

.permission-item {
  margin-bottom: 16px;
}

.permission-item > label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #d0d3d9;
  cursor: pointer;
  margin-bottom: 8px;
}

.item-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.permission-actions {
  margin-left: 32px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.permission-actions label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #a0a4aa;
  cursor: pointer;
}

/* 自定义复选框 */
input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 抽屉底部 */
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #3a3d45;
}

.btn-cancel {
  background: #2a2d35;
  color: #d0d3d9;
  border: 1px solid #3a3d45;
  padding: 8px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #3a3d45;
}

.btn-confirm {
  background: #1890ff;
  color: #fff;
  border: none;
  padding: 8px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn-confirm:hover {
  background: #40a9ff;
}

/* 滚动条样式 */
.drawer-body::-webkit-scrollbar,
.permission-tree::-webkit-scrollbar {
  width: 6px;
}

.drawer-body::-webkit-scrollbar-track,
.permission-tree::-webkit-scrollbar-track {
  background: #1a1d24;
}

.drawer-body::-webkit-scrollbar-thumb,
.permission-tree::-webkit-scrollbar-thumb {
  background: #3a3d45;
  border-radius: 3px;
}

.drawer-body::-webkit-scrollbar-thumb:hover,
.permission-tree::-webkit-scrollbar-thumb:hover {
  background: #4a4d55;
}
</style>
