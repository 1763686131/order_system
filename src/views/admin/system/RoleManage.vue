<template>
  <div class="role-manage-page">
    <section class="page-intro" aria-labelledby="role-page-title">
      <div>
        <span class="eyebrow">系统权限</span>
        <h1 id="role-page-title">角色管理</h1>
        <p>统一维护账号角色、权限范围与可执行操作。</p>
      </div>
      <button class="button button-primary" type="button" @click="openCreateModal">
        <span aria-hidden="true">+</span>
        新增角色
      </button>
    </section>

    <section class="records-panel" aria-labelledby="role-list-title">
      <header class="records-toolbar">
        <div class="toolbar-title">
          <div>
            <span class="section-kicker">权限目录</span>
            <h2 id="role-list-title">角色列表</h2>
          </div>
          <span class="count-badge">{{ totalRoles }}</span>
        </div>
        <span class="toolbar-hint">点击修改可调整角色信息和授权范围</span>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th>角色</th>
              <th>角色 ID</th>
              <th>权限级别</th>
              <th>授权数量</th>
              <th>创建时间</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" class="state-row">
              <td colspan="6">
                <span class="loading-dot" aria-hidden="true"></span>
                正在加载角色列表…
              </td>
            </tr>
            <tr v-else-if="paginatedRoles.length === 0" class="state-row">
              <td colspan="6">
                <span class="empty-mark" aria-hidden="true">⌁</span>
                <strong>暂无角色数据</strong>
                <span>可以点击右上角“新增角色”创建第一个角色。</span>
              </td>
            </tr>
            <tr v-for="role in paginatedRoles" v-else :key="role.username">
              <td>
                <strong class="role-name">{{ role.name || role.username }}</strong>
                <span class="role-secondary">{{ role.description || '未填写备注' }}</span>
              </td>
              <td class="mono-value">{{ role.username }}</td>
              <td>
                <span class="status-badge" :class="getRoleClass(role.role)">
                  <span class="status-dot" aria-hidden="true"></span>
                  {{ getRoleName(role.role) }}
                </span>
              </td>
              <td class="number-value">{{ getPermissionCount(role) }}</td>
              <td class="date-value">{{ formatDate(role.createdAt || role.created_at) }}</td>
              <td class="operation-column">
                <div class="row-actions">
                  <button class="action-button action-edit" type="button" @click="openEditModal(role)">
                    修改
                  </button>
                  <button
                    class="action-button action-delete"
                    type="button"
                    :disabled="!canDelete(role)"
                    :title="canDelete(role) ? '删除角色' : getDeleteDisabledReason(role)"
                    @click="deleteRole(role)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span class="table-summary">共 <strong>{{ totalRoles }}</strong> 条角色记录</span>
        <div class="pagination">
          <label class="page-size-control">
            <span>每页</span>
            <select v-model.number="pageSize" aria-label="每页条数">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
            <span>条</span>
          </label>
          <button class="page-button" type="button" :disabled="currentPage === 1" @click="goToPage(1)">首页</button>
          <button class="page-button" type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">上一页</button>
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-button page-number"
            :class="{ active: currentPage === page }"
            type="button"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button class="page-button" type="button" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">下一页</button>
          <button class="page-button" type="button" :disabled="currentPage === totalPages" @click="goToPage(totalPages)">末页</button>
        </div>
      </footer>
    </section>

    <Transition name="notice">
      <div
        v-if="notice.visible"
        class="page-notice"
        :class="notice.type"
        :role="notice.type === 'error' || notice.type === 'warning' ? 'alert' : 'status'"
        :aria-live="notice.type === 'error' || notice.type === 'warning' ? 'assertive' : 'polite'"
      >
        <span class="page-notice-icon" aria-hidden="true">{{ noticeIcon }}</span>
        <span class="page-notice-text">{{ notice.message }}</span>
        <button class="page-notice-close" type="button" aria-label="关闭通知" @click="hideNotice">×</button>
      </div>
    </Transition>

    <div v-if="showPermissionDrawer" class="drawer-overlay" @click.self="closePermissionDrawer">
      <aside class="drawer-container" role="dialog" aria-modal="true" aria-labelledby="role-drawer-title">
        <header class="drawer-header">
          <div>
            <span class="section-kicker">{{ isEditMode ? '编辑角色' : '新建角色' }}</span>
            <h2 id="role-drawer-title">{{ isEditMode ? '角色权限配置' : '创建角色' }}</h2>
          </div>
          <button class="icon-button" type="button" aria-label="关闭角色配置" @click="closePermissionDrawer">×</button>
        </header>

        <div class="drawer-body">
          <section class="form-card">
            <div class="form-card-header">
              <div>
                <h3>基本信息</h3>
                <p>角色名称和登录凭据用于识别账号。</p>
              </div>
            </div>
            <div class="form-grid">
              <label class="form-field">
                <span>角色名称 <b>*</b></span>
                <input v-model="currentRole.name" type="text" placeholder="例如：仓库主管" />
              </label>
              <label class="form-field">
                <span>角色 ID <b>*</b></span>
                <input v-model="currentRole.username" type="text" placeholder="用于登录和接口识别" :disabled="isEditMode" />
              </label>
              <label class="form-field">
                <span>权限级别 <b>*</b></span>
                <select v-model="currentRole.role" :disabled="isEditMode && currentRole.role === 'super_admin'">
                  <option value="employee">普通员工</option>
                  <option value="operator">操作员</option>
                  <option value="admin">管理员</option>
                  <option v-if="userStore.user?.role === 'super_admin'" value="super_admin">超级管理员</option>
                </select>
              </label>
              <label class="form-field">
                <span>密码 <b v-if="!isEditMode">*</b></span>
                <input v-model="currentRole.password" type="password" :placeholder="isEditMode ? '留空表示不修改' : '请输入登录密码'" />
              </label>
              <label class="form-field">
                <span>创建时间</span>
                <input v-model="currentRole.createdAt" type="text" :disabled="!isEditMode" :placeholder="isEditMode ? '创建时间' : '保存后自动生成'" />
              </label>
              <label class="form-field form-field-wide">
                <span>备注</span>
                <input v-model="currentRole.description" type="text" placeholder="补充角色职责或适用范围" />
              </label>
            </div>
          </section>

          <section class="form-card permission-card">
            <div class="form-card-header">
              <div>
                <h3>授权范围</h3>
                <p>按模块选择页面访问、业务操作和回单权限。</p>
              </div>
              <span class="permission-total">{{ currentRole.permissions.length }} 项</span>
            </div>
            <div class="permission-tree">
              <article
                v-for="module in permissionModules"
                :key="module.id"
                class="permission-module"
              >
                <label class="module-header" :class="{ 'is-partial': isModulePartiallyChecked(module) }">
                  <input
                    type="checkbox"
                    :checked="isModuleChecked(module)"
                    :indeterminate="isModulePartiallyChecked(module)"
                    @change="toggleModule(module, $event)"
                  />
                  <span class="module-icon" v-html="module.icon"></span>
                  <span>{{ module.label }}</span>
                </label>
                <div class="module-children">
                  <div v-for="item in module.children" :key="item.id" class="permission-group">
                    <label class="permission-item">
                      <input type="checkbox" :value="item.id" v-model="currentRole.permissions" />
                      <span>{{ item.label }}</span>
                    </label>
                    <div v-if="item.children" class="permission-actions">
                      <label v-for="action in item.children" :key="action.id" class="permission-item">
                        <input type="checkbox" :value="action.id" v-model="currentRole.permissions" />
                        <span>{{ action.label }}</span>
                      </label>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>

        <footer class="drawer-footer">
          <button class="button button-secondary" type="button" @click="closePermissionDrawer">取消</button>
          <button class="button button-primary" type="button" :disabled="saving" @click="saveRole">
            {{ saving ? '保存中…' : '保存角色' }}
          </button>
        </footer>
      </aside>
    </div>

    <div v-if="confirmDialog.visible" class="custom-modal-overlay" @click.self="closeConfirmDialog">
      <section class="custom-modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">
        <div class="confirm-icon" aria-hidden="true">!</div>
        <h2 id="confirm-title">{{ confirmDialog.title }}</h2>
        <p>{{ confirmDialog.message }}</p>
        <div class="confirm-actions">
          <button class="button button-secondary" type="button" @click="closeConfirmDialog">取消</button>
          <button class="button button-danger" type="button" @click="confirmAction">{{ confirmDialog.confirmText }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, inject } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

// 注入 Admin 组件提供的方法
const setHeaderActions = inject('setHeaderActions', null)

// 角色列表数据
const roles = ref([])
const loading = ref(false)
const saving = ref(false)

const notice = ref({
  visible: false,
  type: 'success',
  message: ''
})
let noticeTimer = null

const noticeIcon = computed(() => {
  const icons = {
    success: '✓',
    info: 'i',
    warning: '!',
    error: '×'
  }
  return icons[notice.value.type] || icons.info
})

const showNotice = (message, type = 'success', duration) => {
  if (noticeTimer) {
    clearTimeout(noticeTimer)
  }

  notice.value = {
    visible: true,
    type,
    message
  }

  const timeout = duration ?? (type === 'error' || type === 'warning' ? 5000 : 3000)
  if (timeout > 0) {
    noticeTimer = setTimeout(() => {
      notice.value.visible = false
      noticeTimer = null
    }, timeout)
  }
}

const hideNotice = () => {
  if (noticeTimer) {
    clearTimeout(noticeTimer)
    noticeTimer = null
  }
  notice.value.visible = false
}

// 加载角色列表
const loadRoles = async () => {
  loading.value = true
  try {
    const response = await request({ url: '/users', method: 'GET' })
    roles.value = Array.isArray(response) ? response : (response?.data || [])
  } catch (error) {
    console.error('获取角色列表失败:', error)
    showNotice('角色列表加载失败，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalRoles = computed(() => roles.value.length)

const totalPages = computed(() => Math.max(1, Math.ceil(totalRoles.value / pageSize.value)))

const paginatedRoles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return roles.value.slice(start, start + pageSize.value)
})

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

watch([totalPages, pageSize], () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

// 角色管理页面使用页面自身的工具栏
onMounted(async () => {
  if (setHeaderActions) {
    setHeaderActions(null)
  }
  await loadRoles()
})

onUnmounted(() => {
  if (noticeTimer) {
    clearTimeout(noticeTimer)
  }
})

// 权限配置
const showPermissionDrawer = ref(false)
const currentRole = ref({
  username: '',
  name: '',
  role: 'employee',
  password: '',
  description: '',
  createdAt: '',
  permissions: []
})
const isEditMode = ref(false)
const confirmDialog = ref({
  visible: false,
  title: '',
  message: '',
  confirmText: '确认',
  onConfirm: null
})

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
    password: '',
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
    password: '', // 编辑时密码为空，表示不修改
    permissions: Array.isArray(role.permissions) ? [...role.permissions] : []
  }
  showPermissionDrawer.value = true
}

// 打开权限抽屉
const openPermissionDrawer = (role) => {
  isEditMode.value = true
  currentRole.value = {
    ...role,
    permissions: Array.isArray(role.permissions) ? [...role.permissions] : []
  }
  showPermissionDrawer.value = true
}

// 关闭抽屉
const closePermissionDrawer = () => {
  showPermissionDrawer.value = false
}

const closeConfirmDialog = () => {
  confirmDialog.value.visible = false
  confirmDialog.value.onConfirm = null
}

const confirmAction = async () => {
  const action = confirmDialog.value.onConfirm
  closeConfirmDialog()
  if (action) {
    await action()
  }
}

const getModulePermissionIds = (module) => {
  const ids = []
  if (!module.children || module.children.length === 0) {
    ids.push(module.id)
    return ids
  }

  module.children.forEach(item => {
    ids.push(item.id)
    if (Array.isArray(item.children)) {
      ids.push(...item.children.map(action => action.id))
    }
  })

  return ids
}

// 检查模块是否全选
const isModuleChecked = (module) => {
  const allIds = getModulePermissionIds(module)
  return allIds.length > 0 && allIds.every(id => currentRole.value.permissions.includes(id))
}

const isModulePartiallyChecked = (module) => {
  const allIds = getModulePermissionIds(module)
  const selectedCount = allIds.filter(id => currentRole.value.permissions.includes(id)).length
  return selectedCount > 0 && selectedCount < allIds.length
}

// 切换模块
const toggleModule = (module, event) => {
  const checked = event.target.checked
  const allIds = getModulePermissionIds(module)

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

const getPermissionCount = (role) => {
  return Array.isArray(role.permissions) ? role.permissions.length : 0
}

// 保存角色
const saveRole = async () => {
  const username = currentRole.value.username.trim()
  const name = currentRole.value.name.trim()
  const password = currentRole.value.password.trim()

  if (!username || !name) {
    showNotice('角色 ID 和角色名称不能为空', 'warning')
    return
  }

  if (!isEditMode.value) {
    if (!password) {
      showNotice('新建角色时必须设置登录密码', 'warning')
      return
    }

    const payload = {
      username: username,
      name: name,
      password: password,
      role: currentRole.value.role || 'employee',
      permissions: currentRole.value.permissions
    }

    saving.value = true
    try {
      const res = await request({ url: '/users', method: 'POST', data: payload })
      if (res) {
        await loadRoles()
        closePermissionDrawer()
        showNotice('角色创建成功', 'success')
      }
    } catch (error) {
      showNotice('角色创建失败，可能已存在或当前账号无权限', 'error')
    } finally {
      saving.value = false
    }
  } else {
    const payload = {
      name,
      permissions: currentRole.value.permissions,
      role: currentRole.value.role || 'employee',
      createdAt: currentRole.value.createdAt
    }

    saving.value = true
    try {
      const res = await request({
        url: `/users/${username}/permissions`,
        method: 'PUT',
        data: payload
      })

      if (password) {
        await request({
          url: `/users/${username}/password`,
          method: 'PUT',
          data: { password }
        })
      }

      if (res) {
        await loadRoles()
        closePermissionDrawer()
        showNotice('角色更新成功', 'success')
      }
    } catch (error) {
      showNotice('角色更新失败，请检查权限或稍后重试', 'error')
    } finally {
      saving.value = false
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

const getDeleteDisabledReason = (role) => {
  if (role.username === userStore.username) {
    return '不能删除当前登录账号'
  }
  if (userStore.role === 'admin') {
    return '管理员只能删除普通员工和操作员'
  }
  return '当前账号没有删除权限'
}

// 删除角色
const deleteRole = async (role) => {
  if (!canDelete(role)) {
    showNotice(getDeleteDisabledReason(role), 'warning')
    return
  }

  confirmDialog.value = {
    visible: true,
    title: '确认删除角色？',
    message: `删除“${role.name || role.username}”后，该账号将无法继续登录，且此操作不可恢复。`,
    confirmText: '确认删除',
    onConfirm: async () => {
      try {
        await request({ url: `/users/${role.username}`, method: 'DELETE' })
        await loadRoles()
        showNotice('角色已删除', 'success')
      } catch (error) {
        showNotice('删除失败，请稍后重试', 'error')
      }
    }
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

<style scoped>
.role-manage-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  box-sizing: border-box;
  width: 100%;
  min-height: 100%;
  padding: 24px;
  color: var(--text);
  background: var(--page-bg);
}

.role-manage-page *,
.role-manage-page *::before,
.role-manage-page *::after {
  box-sizing: border-box;
}

.page-intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.eyebrow,
.section-kicker {
  display: block;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-intro h1 {
  margin: 4px 0 5px;
  color: var(--text);
  font-size: 22px;
  font-weight: 750;
  line-height: 1.25;
}

.page-intro p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.button {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease,
    color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.button-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.22);
}

.button-secondary {
  color: var(--text-secondary);
  background: var(--panel-bg);
  border-color: var(--border-strong);
}

.button-secondary:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-danger {
  color: #fff;
  background: #d14352;
  border-color: #d14352;
}

.button-danger:hover:not(:disabled) {
  background: #b4232f;
  border-color: #b4232f;
  box-shadow: 0 4px 12px rgba(209, 67, 82, 0.22);
}

.records-panel {
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.records-toolbar {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 11px;
}

.toolbar-title h2 {
  margin: 3px 0 0;
  color: var(--text);
  font-size: 16px;
  font-weight: 700;
}

.count-badge,
.permission-total {
  display: inline-flex;
  min-width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  padding: 0 7px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
}

.toolbar-hint {
  color: var(--text-muted);
  font-size: 12px;
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 880px;
  table-layout: fixed;
  border-collapse: collapse;
}

.records-table th,
.records-table td {
  border-bottom: 1px solid #edf1f5;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: var(--text-secondary);
  background: #f8fafc;
  font-size: 12px;
  font-weight: 700;
  text-align: left;
}

.records-table th:nth-child(1) {
  width: 21%;
}

.records-table th:nth-child(2) {
  width: 18%;
}

.records-table th:nth-child(3) {
  width: 16%;
}

.records-table th:nth-child(4) {
  width: 14%;
}

.records-table th:nth-child(5) {
  width: 16%;
}

.records-table th:nth-child(6) {
  width: 15%;
}

.records-table td {
  height: 64px;
  padding: 9px 12px;
  color: var(--text-secondary);
  font-size: 13px;
  vertical-align: middle;
}

.records-table tbody tr:not(.state-row):hover {
  background: rgba(var(--accent-rgb), 0.045);
}

.role-name,
.role-secondary {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-name {
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
}

.role-secondary {
  max-width: 220px;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 11px;
}

.mono-value,
.number-value {
  font-variant-numeric: tabular-nums;
}

.mono-value {
  color: var(--text-secondary);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
}

.number-value {
  color: var(--text);
  font-weight: 700;
}

.date-value {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.status-badge {
  display: inline-flex;
  min-height: 25px;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
}

.status-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  background: currentColor;
  border-radius: 50%;
}

.role-super-admin {
  color: #b4232f;
  background: #fff1f2;
}

.role-admin {
  color: #8a4b0b;
  background: #fff3df;
}

.role-operator {
  color: #16647a;
  background: #e7f5f8;
}

.role-employee,
.role-default {
  color: #13734f;
  background: #eaf8f1;
}

.operation-column {
  text-align: center !important;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.action-button {
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.action-edit {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.action-edit:hover {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.action-delete {
  color: #b4232f;
  background: #fff;
  border-color: #f0a5ad;
}

.action-delete:hover:not(:disabled) {
  color: #fff;
  background: #d14352;
  border-color: #d14352;
}

.action-delete:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.state-row td {
  height: 220px;
  color: var(--text-muted);
  text-align: center;
}

.state-row strong,
.state-row span {
  display: block;
}

.state-row strong {
  margin-top: 10px;
  color: var(--text);
  font-size: 14px;
}

.state-row span:last-child {
  margin-top: 5px;
  font-size: 12px;
}

.empty-mark {
  display: inline-flex !important;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  color: var(--text-muted);
  background: #f1f4f7;
  border-radius: 50%;
  font-size: 24px;
}

.loading-dot {
  display: inline-block !important;
  width: 10px;
  height: 10px;
  margin: 0 auto 9px;
  background: var(--accent);
  border-radius: 50%;
  animation: role-pulse 1s ease-in-out infinite;
}

.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
}

.table-summary {
  color: var(--text-secondary);
  font-size: 12px;
}

.table-summary strong {
  color: var(--text);
  font-weight: 750;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-control {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-secondary);
  font-size: 12px;
}

.page-size-control select {
  width: 58px;
  height: 32px;
  padding: 0 7px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
}

.page-button {
  display: inline-flex;
  min-width: 31px;
  height: 31px;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
}

.page-button:hover:not(:disabled),
.page-button.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.page-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.drawer-overlay,
.custom-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: stretch;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.drawer-container {
  display: flex;
  width: min(680px, 100vw);
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  background: var(--page-bg);
  box-shadow: -20px 0 50px rgba(15, 23, 42, 0.18);
}

.drawer-header {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.drawer-header h2 {
  margin: 3px 0 0;
  color: var(--text);
  font-size: 18px;
}

.icon-button,
.page-notice-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.icon-button {
  width: 34px;
  height: 34px;
  color: var(--text-secondary);
  background: transparent;
  font-size: 22px;
}

.icon-button:hover {
  color: var(--text);
  background: #f1f5f9;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

.form-card {
  margin-bottom: 12px;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
}

.form-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 15px;
  padding-bottom: 11px;
  border-bottom: 1px solid #edf1f5;
}

.form-card-header h3 {
  margin: 0;
  color: var(--text);
  font-size: 14px;
}

.form-card-header p {
  margin: 3px 0 0;
  color: var(--text-muted);
  font-size: 11px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
}

.form-field-wide {
  grid-column: 1 / -1;
}

.form-field b {
  color: #d14352;
}

.form-field input,
.form-field select {
  width: 100%;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  font: inherit;
  font-weight: 400;
}

.form-field input:focus,
.form-field select:focus,
.page-size-control select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.form-field input:disabled,
.form-field select:disabled {
  color: var(--text-muted);
  background: #f8fafc;
  cursor: not-allowed;
}

.permission-card {
  margin-bottom: 0;
}

.permission-tree {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.permission-module {
  min-width: 0;
  padding: 12px;
  background: #fafcfd;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.module-header,
.permission-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--text);
  cursor: pointer;
  line-height: 1.45;
}

.module-header {
  align-items: center;
  font-size: 13px;
  font-weight: 700;
}

.module-header.is-partial {
  color: var(--accent-dark);
}

.module-icon {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  color: var(--accent-dark);
}

.module-icon :deep(svg) {
  width: 16px;
  height: 16px;
}

.module-children {
  display: grid;
  gap: 8px;
  margin: 11px 0 0 26px;
  padding-top: 10px;
  border-top: 1px solid #edf1f5;
}

.permission-group {
  display: grid;
  gap: 7px;
}

.permission-actions {
  display: grid;
  gap: 7px;
  margin-left: 24px;
  padding-left: 10px;
  border-left: 1px solid var(--border);
}

.permission-item {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 400;
}

.permission-item:hover {
  color: var(--accent-dark);
}

.module-header input,
.permission-item input {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  margin: 1px 0 0;
  accent-color: var(--accent);
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid var(--border);
}

.custom-modal-overlay {
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.custom-modal {
  width: min(400px, 100%);
  padding: 24px;
  text-align: center;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.2);
}

.confirm-icon {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #c98216;
  border-radius: 50%;
  font-size: 24px;
  font-weight: 800;
}

.custom-modal h2 {
  margin: 14px 0 7px;
  color: var(--text);
  font-size: 18px;
}

.custom-modal p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
}

.page-notice {
  position: fixed;
  top: 20px;
  left: 50%;
  z-index: 100001;
  display: flex;
  width: max-content;
  min-width: 280px;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
}

.page-notice-icon {
  display: inline-flex;
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 800;
}

.page-notice-text {
  min-width: 0;
  flex: 1;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.5;
}

.page-notice-close {
  width: 28px;
  height: 28px;
  color: currentColor;
  background: transparent;
  font-size: 18px;
}

.page-notice-close:hover {
  background: rgba(15, 23, 42, 0.07);
}

.page-notice.success {
  color: #166b50;
  background: #eaf8f1;
  border-color: var(--accent-border);
}

.page-notice.success .page-notice-icon {
  color: #fff;
  background: var(--accent);
}

.page-notice.warning {
  color: #8a4b0b;
  background: #fff3df;
  border-color: #f3c887;
}

.page-notice.warning .page-notice-icon {
  color: #fff;
  background: #c98216;
}

.page-notice.error {
  color: #a12635;
  background: #fff1f2;
  border-color: #f0a5ad;
}

.page-notice.error .page-notice-icon {
  color: #fff;
  background: #d14352;
}

.notice-enter-active,
.notice-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.notice-enter-from,
.notice-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

.role-manage-page button:focus-visible,
.role-manage-page input:focus-visible,
.role-manage-page select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@keyframes role-pulse {
  0%,
  100% {
    opacity: 0.35;
    transform: scale(0.85);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1280px) {
  .role-manage-page {
    padding: 18px;
  }

  .toolbar-hint {
    display: none;
  }
}

@media (max-width: 780px) {
  .role-manage-page {
    padding: 12px;
  }

  .page-intro {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-intro .button {
    width: 100%;
  }

  .records-toolbar,
  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .pagination {
    width: 100%;
    flex-wrap: wrap;
  }

  .permission-tree,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-field-wide {
    grid-column: auto;
  }

  .drawer-header,
  .drawer-footer {
    padding-right: 14px;
    padding-left: 14px;
  }

  .drawer-body {
    padding: 10px;
  }

  .page-notice {
    top: 12px;
    min-width: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .notice-enter-active,
  .notice-leave-active,
  .loading-dot {
    animation: none;
    transition: none;
  }
}
</style>
