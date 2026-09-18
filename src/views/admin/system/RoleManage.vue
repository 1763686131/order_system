<template>
  <div class="access-page">
    <Transition name="notice">
      <div
        v-if="notice.visible"
        :class="['page-notice', `notice-${notice.type}`]"
        role="status"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path v-if="notice.type === 'success'" d="m8 12 2.7 2.7L16.5 9" />
          <path v-else d="M12 8v5M12 17h.01" />
        </svg>
        {{ notice.message }}
      </div>
    </Transition>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="view-tabs" role="tablist" aria-label="权限管理视图">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            :class="['view-tab', { active: activeTab === tab.value }]"
            @click="activeTab = tab.value"
          >
            {{ tab.label }}
            <span class="count-badge">{{ tab.count }}</span>
          </button>
        </div>
        <div class="toolbar-actions">
          <button class="button button-secondary icon-button" title="刷新" @click="loadAll">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5" />
              <path d="M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5" />
            </svg>
          </button>
          <button
            class="button button-primary"
            type="button"
            @click="activeTab === 'accounts' ? openAccountModal() : openRoleModal()"
          >
            <span aria-hidden="true">+</span>
            {{ activeTab === 'accounts' ? '新增账号' : '新增权限组' }}
          </button>
        </div>
      </header>

      <template v-if="activeTab === 'accounts'">
        <div class="sub-toolbar">
          <div class="search-input">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.6-3.6" />
            </svg>
            <input v-model.trim="accountKeyword" placeholder="搜索账号或姓名" />
          </div>
          <span class="toolbar-note">账号不直接保存权限，只通过权限组获得权限。</span>
        </div>

        <div class="table-scroll">
          <table class="records-table">
            <thead>
              <tr>
                <th>账号信息</th>
                <th>权限组</th>
                <th>账号状态</th>
                <th>最近登录</th>
                <th>创建时间</th>
                <th class="operation-column">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="6" class="state-cell">正在加载账号...</td>
              </tr>
              <tr v-else-if="filteredAccounts.length === 0">
                <td colspan="6" class="state-cell">没有符合条件的账号。</td>
              </tr>
              <tr v-for="account in filteredAccounts" v-else :key="account.id">
                <td>
                  <div class="account-cell">
                    <span class="avatar">{{ accountInitial(account) }}</span>
                    <div class="cell-stack">
                      <strong>{{ account.displayName }}</strong>
                      <span>{{ account.username }}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="tag-row">
                    <span
                      v-for="role in account.roles"
                      :key="role.id"
                      class="role-tag"
                    >
                      {{ role.name }}
                    </span>
                    <span v-if="account.roles.length === 0" class="muted-text">未分组</span>
                  </div>
                </td>
                <td>
                  <span :class="['status-tag', account.status === 'active' ? 'success' : 'disabled']">
                    {{ account.status === 'active' ? '启用' : '停用' }}
                  </span>
                </td>
                <td class="date-cell">{{ formatDate(account.lastLoginAt) }}</td>
                <td class="date-cell">{{ formatDate(account.createdAt) }}</td>
                <td class="operation-column">
                  <button class="text-button" type="button" @click="openAccountModal(account)">
                    编辑
                  </button>
                  <button class="text-button" type="button" @click="openPasswordModal(account)">
                    重置密码
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else class="role-workspace">
        <aside class="role-list" aria-label="权限组列表">
          <button
            v-for="role in roles"
            :key="role.id"
            type="button"
            :class="['role-list-item', { active: selectedRoleId === role.id }]"
            @click="selectRole(role.id)"
          >
            <span class="role-list-mark">{{ role.name.slice(0, 1) }}</span>
            <span class="role-list-copy">
              <strong>{{ role.name }}</strong>
              <small>{{ role.memberCount }} 个账号</small>
            </span>
            <span :class="['status-dot', { disabled: role.status !== 'active' }]"></span>
          </button>
        </aside>

        <section v-if="selectedRole" class="role-detail">
          <header class="role-header">
            <div>
              <div class="role-title-row">
                <h2>{{ selectedRole.name }}</h2>
                <span v-if="selectedRole.isSystem" class="system-tag">系统内置</span>
                <span :class="['status-tag', selectedRole.status === 'active' ? 'success' : 'disabled']">
                  {{ selectedRole.status === 'active' ? '启用' : '停用' }}
                </span>
              </div>
              <p>{{ selectedRole.description || '暂无说明' }}</p>
              <div class="role-meta">
                <span>编码：{{ selectedRole.code }}</span>
                <span>数据范围：{{ dataScopeName(selectedRole.dataScope) }}</span>
                <span>成员：{{ selectedRole.memberCount }}</span>
              </div>
            </div>
            <div class="toolbar-actions">
              <button
                class="button button-secondary"
                type="button"
                :disabled="selectedRole.isSystem"
                @click="openRoleModal(selectedRole)"
              >
                编辑信息
              </button>
              <button
                v-if="!selectedRole.fullAccess && !permissionEditing"
                class="button button-primary"
                type="button"
                @click="startPermissionEditing"
              >
                配置权限
              </button>
              <template v-else-if="permissionEditing">
                <button class="button button-secondary" type="button" @click="cancelPermissionEditing">
                  取消
                </button>
                <button class="button button-primary" type="button" :disabled="saving" @click="savePermissions">
                  {{ saving ? '保存中...' : '保存权限' }}
                </button>
              </template>
            </div>
          </header>

          <div v-if="selectedRole.fullAccess" class="full-access-state">
            <span class="full-access-icon">全</span>
            <div>
              <strong>拥有系统全部权限</strong>
              <p>超级管理员组自动覆盖后台与触屏端全部操作。</p>
            </div>
          </div>

          <div v-else class="permission-area">
            <section
              v-for="module in visiblePermissionModules"
              :key="module.code"
              class="permission-module"
            >
              <header>
                <div>
                  <h3>{{ module.name }}</h3>
                  <p>{{ module.description }}</p>
                </div>
                <span>{{ selectedCount(module) }} / {{ module.permissions.length }}</span>
              </header>
              <div class="permission-grid">
                <button
                  v-for="permission in visiblePermissions(module)"
                  :key="permission.code"
                  type="button"
                  :class="[
                    'permission-chip',
                    { selected: permissionDraft.includes(permission.code), editable: permissionEditing }
                  ]"
                  :disabled="!permissionEditing"
                  @click="togglePermission(permission.code)"
                >
                  <span class="permission-name">{{ permission.name }}</span>
                  <span class="permission-code">{{ permission.code }}</span>
                </button>
              </div>
            </section>
            <div v-if="visiblePermissionModules.length === 0" class="empty-permissions">
              当前权限组还没有权限，点击“配置权限”开始添加。
            </div>
          </div>
        </section>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="accountModal.visible" class="modal-layer" @click.self="closeAccountModal">
        <section class="form-modal" role="dialog" aria-modal="true" aria-labelledby="account-modal-title">
          <header class="modal-header">
            <div>
              <span class="modal-kicker">账号信息</span>
              <h2 id="account-modal-title">
                {{ accountModal.mode === 'create' ? '新增账号' : '编辑账号' }}
              </h2>
            </div>
            <button class="modal-close" type="button" title="关闭" @click="closeAccountModal">×</button>
          </header>
          <form class="modal-body form-grid" @submit.prevent="saveAccount">
            <label class="field">
              <span>登录账号</span>
              <input
                v-model.trim="accountForm.username"
                :disabled="accountModal.mode === 'edit'"
                autocomplete="off"
                placeholder="不含空格"
              />
            </label>
            <label class="field">
              <span>显示姓名</span>
              <input v-model.trim="accountForm.displayName" placeholder="用于系统显示" />
            </label>
            <label v-if="accountModal.mode === 'create'" class="field">
              <span>初始密码</span>
              <input
                v-model="accountForm.password"
                type="password"
                autocomplete="new-password"
                placeholder="至少 8 位"
              />
            </label>
            <label class="field">
              <span>账号状态</span>
              <select v-model="accountForm.status">
                <option value="active">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <label class="field field-span">
              <span>头像地址</span>
              <input v-model.trim="accountForm.avatarUrl" placeholder="可填写本地或上传后的图片地址" />
            </label>
            <fieldset class="role-options field-span">
              <legend>所属权限组</legend>
              <label v-for="role in activeRoles" :key="role.id" class="role-option">
                <input v-model="accountForm.roleIds" type="checkbox" :value="role.id" />
                <span>
                  <strong>{{ role.name }}</strong>
                  <small>{{ role.description || role.code }}</small>
                </span>
              </label>
            </fieldset>
          </form>
          <footer class="modal-footer">
            <button class="button button-secondary" type="button" @click="closeAccountModal">取消</button>
            <button class="button button-primary" type="button" :disabled="saving" @click="saveAccount">
              {{ saving ? '保存中...' : '保存账号' }}
            </button>
          </footer>
        </section>
      </div>

      <div v-if="roleModal.visible" class="modal-layer" @click.self="closeRoleModal">
        <section class="form-modal compact-modal" role="dialog" aria-modal="true" aria-labelledby="role-modal-title">
          <header class="modal-header">
            <div>
              <span class="modal-kicker">权限组信息</span>
              <h2 id="role-modal-title">
                {{ roleModal.mode === 'create' ? '新增权限组' : '编辑权限组' }}
              </h2>
            </div>
            <button class="modal-close" type="button" title="关闭" @click="closeRoleModal">×</button>
          </header>
          <div class="modal-body form-grid">
            <label class="field">
              <span>权限组名称</span>
              <input v-model.trim="roleForm.name" placeholder="例如：触屏录入员" />
            </label>
            <label class="field">
              <span>权限组编码</span>
              <input
                v-model.trim="roleForm.code"
                :disabled="roleModal.mode === 'edit'"
                placeholder="例如：touch_operator"
              />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="roleForm.status">
                <option value="active">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <label class="field">
              <span>数据可见范围</span>
              <select v-model="roleForm.dataScope">
                <option value="all">全部数据</option>
                <option value="store">所属门店</option>
                <option value="self">本人数据</option>
              </select>
            </label>
            <label class="field field-span">
              <span>权限组说明</span>
              <textarea v-model.trim="roleForm.description" rows="4" placeholder="说明该组适用的岗位或工作范围"></textarea>
            </label>
          </div>
          <footer class="modal-footer">
            <button class="button button-secondary" type="button" @click="closeRoleModal">取消</button>
            <button class="button button-primary" type="button" :disabled="saving" @click="saveRole">
              {{ saving ? '保存中...' : '保存信息' }}
            </button>
          </footer>
        </section>
      </div>

      <div v-if="passwordModal.visible" class="modal-layer" @click.self="closePasswordModal">
        <section class="form-modal password-modal" role="dialog" aria-modal="true" aria-labelledby="password-modal-title">
          <header class="modal-header">
            <div>
              <span class="modal-kicker">账号安全</span>
              <h2 id="password-modal-title">重置 {{ passwordModal.account?.displayName }} 的密码</h2>
            </div>
            <button class="modal-close" type="button" title="关闭" @click="closePasswordModal">×</button>
          </header>
          <div class="modal-body">
            <label class="field">
              <span>新密码</span>
              <input v-model="newPassword" type="password" autocomplete="new-password" placeholder="至少 8 位" />
            </label>
            <p class="password-note">保存后该账号的现有登录状态会失效，下次登录需使用新密码。</p>
          </div>
          <footer class="modal-footer">
            <button class="button button-secondary" type="button" @click="closePasswordModal">取消</button>
            <button class="button button-primary" type="button" :disabled="saving" @click="resetPassword">
              确认重置
            </button>
          </footer>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const activeTab = ref('accounts')
const loading = ref(false)
const saving = ref(false)
const accounts = ref([])
const roles = ref([])
const permissionModules = ref([])
const accountKeyword = ref('')
const selectedRoleId = ref(null)
const permissionEditing = ref(false)
const permissionDraft = ref([])
let noticeTimer = null

const notice = reactive({ visible: false, type: 'success', message: '' })
const accountModal = reactive({ visible: false, mode: 'create', accountId: null })
const roleModal = reactive({ visible: false, mode: 'create', roleId: null })
const passwordModal = reactive({ visible: false, account: null })
const newPassword = ref('')

const accountForm = reactive({
  username: '',
  displayName: '',
  password: '',
  avatarUrl: '',
  status: 'active',
  roleIds: []
})

const roleForm = reactive({
  code: '',
  name: '',
  description: '',
  status: 'active',
  dataScope: 'all'
})

const tabs = computed(() => [
  { value: 'accounts', label: '账号管理', count: accounts.value.length },
  { value: 'roles', label: '权限组', count: roles.value.length }
])

const filteredAccounts = computed(() => {
  const keyword = accountKeyword.value.toLowerCase()
  if (!keyword) return accounts.value
  return accounts.value.filter(account => (
    account.username.toLowerCase().includes(keyword)
    || account.displayName.toLowerCase().includes(keyword)
  ))
})

const activeRoles = computed(() => roles.value.filter(role => role.status === 'active'))
const selectedRole = computed(() => (
  roles.value.find(role => role.id === selectedRoleId.value) || null
))

const visiblePermissionModules = computed(() => {
  if (permissionEditing.value) return permissionModules.value
  return permissionModules.value.filter(module => (
    module.permissions.some(permission => (
      permissionDraft.value.includes(permission.code)
    ))
  ))
})

const showNotice = (message, type = 'success') => {
  clearTimeout(noticeTimer)
  notice.message = message
  notice.type = type
  notice.visible = true
  noticeTimer = setTimeout(() => {
    notice.visible = false
  }, type === 'error' ? 5000 : 3000)
}

const loadAll = async () => {
  loading.value = true
  try {
    const [userResponse, roleResponse, permissionResponse] = await Promise.all([
      request.get('/admin/users'),
      request.get('/admin/roles'),
      request.get('/admin/permissions')
    ])
    accounts.value = userResponse.users || []
    roles.value = roleResponse.roles || []
    permissionModules.value = permissionResponse.modules || []
    if (!roles.value.some(role => role.id === selectedRoleId.value)) {
      selectedRoleId.value = roles.value[0]?.id || null
    }
    syncPermissionDraft()
  } catch (error) {
    showNotice(error?.response?.data?.message || '权限数据加载失败', 'error')
  } finally {
    loading.value = false
  }
}

const syncPermissionDraft = () => {
  permissionDraft.value = [...(selectedRole.value?.permissionCodes || [])]
}

const selectRole = (roleId) => {
  selectedRoleId.value = roleId
  permissionEditing.value = false
  syncPermissionDraft()
}

const visiblePermissions = (module) => {
  if (permissionEditing.value) return module.permissions
  return module.permissions.filter(permission => (
    permissionDraft.value.includes(permission.code)
  ))
}

const selectedCount = (module) => (
  module.permissions.filter(permission => (
    permissionDraft.value.includes(permission.code)
  )).length
)

const startPermissionEditing = () => {
  syncPermissionDraft()
  permissionEditing.value = true
}

const cancelPermissionEditing = () => {
  permissionEditing.value = false
  syncPermissionDraft()
}

const togglePermission = (permissionCode) => {
  if (!permissionEditing.value) return
  const index = permissionDraft.value.indexOf(permissionCode)
  if (index >= 0) permissionDraft.value.splice(index, 1)
  else permissionDraft.value.push(permissionCode)
}

const savePermissions = async () => {
  if (!selectedRole.value) return
  saving.value = true
  try {
    await request.put(`/admin/roles/${selectedRole.value.id}`, {
      name: selectedRole.value.name,
      description: selectedRole.value.description,
      status: selectedRole.value.status,
      dataScope: selectedRole.value.dataScope,
      permissionCodes: permissionDraft.value
    })
    await loadAll()
    permissionEditing.value = false
    showNotice('权限配置已保存')
  } catch (error) {
    showNotice(error?.response?.data?.message || '权限保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const resetAccountForm = () => {
  Object.assign(accountForm, {
    username: '',
    displayName: '',
    password: '',
    avatarUrl: '',
    status: 'active',
    roleIds: []
  })
}

const openAccountModal = (account = null) => {
  resetAccountForm()
  accountModal.mode = account ? 'edit' : 'create'
  accountModal.accountId = account?.id || null
  if (account) {
    Object.assign(accountForm, {
      username: account.username,
      displayName: account.displayName,
      avatarUrl: account.avatarUrl || '',
      status: account.status,
      roleIds: account.roleIds || []
    })
  }
  accountModal.visible = true
}

const closeAccountModal = () => {
  accountModal.visible = false
}

const saveAccount = async () => {
  if (!accountForm.username || !accountForm.displayName) {
    showNotice('请填写登录账号和显示姓名', 'error')
    return
  }
  if (accountModal.mode === 'create' && accountForm.password.length < 8) {
    showNotice('初始密码至少需要 8 位', 'error')
    return
  }

  saving.value = true
  try {
    const payload = {
      username: accountForm.username,
      displayName: accountForm.displayName,
      password: accountForm.password,
      avatarUrl: accountForm.avatarUrl,
      status: accountForm.status,
      roleIds: accountForm.roleIds
    }
    const response = accountModal.mode === 'create'
      ? await request.post('/admin/users', payload)
      : await request.put(`/admin/users/${accountModal.accountId}`, payload)
    closeAccountModal()
    await loadAll()
    if (accountModal.accountId === userStore.id && response.user) {
      userStore.setUser(response.user)
    }
    showNotice(response.message || '账号已保存')
  } catch (error) {
    showNotice(error?.response?.data?.message || '账号保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const openPasswordModal = (account) => {
  passwordModal.account = account
  newPassword.value = ''
  passwordModal.visible = true
}

const closePasswordModal = () => {
  passwordModal.visible = false
  passwordModal.account = null
}

const resetPassword = async () => {
  if (newPassword.value.length < 8) {
    showNotice('新密码至少需要 8 位', 'error')
    return
  }
  saving.value = true
  try {
    const response = await request.put(
      `/admin/users/${passwordModal.account.id}/password`,
      { password: newPassword.value }
    )
    closePasswordModal()
    showNotice(response.message || '密码已重置')
  } catch (error) {
    showNotice(error?.response?.data?.message || '密码重置失败', 'error')
  } finally {
    saving.value = false
  }
}

const resetRoleForm = () => {
  Object.assign(roleForm, {
    code: '',
    name: '',
    description: '',
    status: 'active',
    dataScope: 'all'
  })
}

const openRoleModal = (role = null) => {
  resetRoleForm()
  roleModal.mode = role ? 'edit' : 'create'
  roleModal.roleId = role?.id || null
  if (role) {
    Object.assign(roleForm, {
      code: role.code,
      name: role.name,
      description: role.description,
      status: role.status,
      dataScope: role.dataScope
    })
  }
  roleModal.visible = true
}

const closeRoleModal = () => {
  roleModal.visible = false
}

const saveRole = async () => {
  if (!roleForm.name || !roleForm.code) {
    showNotice('请填写权限组名称和编码', 'error')
    return
  }
  saving.value = true
  try {
    const currentRole = roles.value.find(role => role.id === roleModal.roleId)
    const payload = {
      ...roleForm,
      permissionCodes: currentRole?.permissionCodes || []
    }
    const response = roleModal.mode === 'create'
      ? await request.post('/admin/roles', payload)
      : await request.put(`/admin/roles/${roleModal.roleId}`, payload)
    closeRoleModal()
    await loadAll()
    if (response.role?.id) selectedRoleId.value = response.role.id
    syncPermissionDraft()
    showNotice(response.message || '权限组已保存')
  } catch (error) {
    showNotice(error?.response?.data?.message || '权限组保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const accountInitial = (account) => (
  (account.displayName || account.username || '?').slice(0, 1)
)

const formatDate = (value) => {
  if (!value) return '从未登录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const dataScopeName = (value) => ({
  all: '全部数据',
  store: '所属门店',
  self: '本人数据'
}[value] || '全部数据')

onMounted(loadAll)
</script>

<style scoped>
.access-page,
.modal-layer {
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
}

.access-page {
  min-height: 100%;
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

.records-panel {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--panel-bg);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.records-toolbar,
.sub-toolbar,
.role-header,
.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.records-toolbar {
  min-height: 62px;
  gap: 20px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.view-tabs {
  display: inline-flex;
  gap: 6px;
  padding: 4px;
  border-radius: 8px;
  background: #f1f5f9;
}

.view-tab {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  border: 0;
  border-radius: 6px;
  color: var(--text-secondary);
  background: transparent;
  font-weight: 700;
  cursor: pointer;
}

.view-tab.active {
  color: #fff;
  background: var(--accent);
}

.count-badge {
  display: inline-grid;
  min-width: 20px;
  height: 20px;
  place-items: center;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  font-size: 11px;
}

.view-tab.active .count-badge {
  background: rgba(255, 255, 255, 0.2);
}

.toolbar-actions,
.tag-row,
.role-title-row,
.role-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
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
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.button-primary {
  color: #fff;
  border-color: var(--accent, #0f9f78);
  background: var(--accent, #0f9f78);
}

.button-primary:hover:not(:disabled) {
  border-color: var(--accent-dark, #08745a);
  background: var(--accent-dark, #08745a);
}

.button-secondary {
  color: var(--text-secondary, #596579);
  border-color: var(--border-strong, #cbd5e1);
  background: var(--panel-bg, #fff);
}

.button-secondary:hover:not(:disabled) {
  color: var(--accent-dark, #08745a);
  border-color: var(--accent-border, #a9e5d2);
  background: var(--accent-soft, #e9f8f3);
}

.icon-button {
  width: 38px;
  padding: 0;
}

.icon-button svg,
.search-input svg,
.page-notice svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.sub-toolbar {
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.search-input {
  position: relative;
  width: min(320px, 100%);
}

.search-input svg {
  position: absolute;
  top: 10px;
  left: 11px;
  color: var(--text-muted);
}

.search-input input {
  width: 100%;
  height: 38px;
  padding: 0 11px 0 36px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  outline: none;
}

.search-input input:focus,
.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.11);
}

.toolbar-note,
.muted-text {
  color: var(--text-muted);
  font-size: 12px;
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
  table-layout: fixed;
}

.records-table th {
  height: 44px;
  padding: 0 14px;
  color: var(--text-secondary);
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  text-align: left;
}

.records-table td {
  height: 58px;
  padding: 9px 14px;
  border-bottom: 1px solid #edf1f5;
  overflow: hidden;
  text-overflow: ellipsis;
}

.records-table th:nth-child(1) { width: 220px; }
.records-table th:nth-child(2) { width: 260px; }
.records-table th:nth-child(3) { width: 110px; }
.records-table th:nth-child(4),
.records-table th:nth-child(5) { width: 150px; }
.records-table th:nth-child(6) { width: 150px; }

.account-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar,
.role-list-mark {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  font-weight: 750;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
}

.cell-stack {
  display: grid;
  min-width: 0;
  gap: 3px;
}

.cell-stack strong,
.cell-stack span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-stack span,
.date-cell {
  color: var(--text-muted);
  font-size: 12px;
}

.date-cell {
  font-variant-numeric: tabular-nums;
}

.role-tag,
.status-tag,
.system-tag {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
}

.role-tag,
.system-tag {
  color: #16647a;
  background: #e7f5f8;
}

.status-tag.success {
  color: #13734f;
  background: #eaf8f1;
}

.status-tag.disabled {
  color: #6b7280;
  background: #f1f2f4;
}

.operation-column {
  text-align: center;
}

.text-button {
  padding: 5px 7px;
  border: 0;
  color: var(--accent-dark);
  background: transparent;
  font-weight: 650;
  cursor: pointer;
}

.text-button:hover {
  text-decoration: underline;
}

.state-cell {
  height: 220px !important;
  color: var(--text-muted);
  text-align: center;
}

.role-workspace {
  display: grid;
  min-height: 620px;
  grid-template-columns: 240px minmax(0, 1fr);
}

.role-list {
  padding: 10px;
  border-right: 1px solid var(--border);
  background: #f8fafc;
}

.role-list-item {
  display: grid;
  width: 100%;
  grid-template-columns: 34px minmax(0, 1fr) 8px;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.role-list-item:hover {
  background: #fff;
}

.role-list-item.active {
  border-color: var(--accent-border);
  background: #fff;
  box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
}

.role-list-mark {
  width: 34px;
  height: 34px;
  border-radius: 6px;
}

.role-list-copy {
  display: grid;
  min-width: 0;
  gap: 3px;
}

.role-list-copy strong,
.role-list-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-list-copy small {
  color: var(--text-muted);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
}

.status-dot.disabled {
  background: #a8b0bd;
}

.role-detail {
  min-width: 0;
}

.role-header {
  gap: 20px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
}

.role-header h2 {
  margin: 0;
  font-size: 18px;
}

.role-header p,
.permission-module p,
.full-access-state p {
  margin: 5px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.role-meta {
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 12px;
}

.permission-area {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.permission-module {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: #f8fafc;
}

.permission-module > header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.permission-module h3 {
  margin: 0;
  font-size: 14px;
}

.permission-module > header > span {
  color: var(--text-muted);
  font-size: 12px;
}

.permission-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 7px;
}

.permission-chip {
  display: grid;
  min-width: 0;
  min-height: 48px;
  align-content: center;
  gap: 3px;
  padding: 7px 9px;
  border: 1px solid var(--accent-border);
  border-radius: 5px;
  color: var(--text);
  background: var(--accent-soft);
  text-align: left;
}

.permission-chip.editable:not(.selected) {
  border-style: dashed;
  border-color: var(--border-strong);
  background: #fff;
  cursor: pointer;
}

.permission-chip.editable.selected {
  cursor: pointer;
}

.permission-name {
  font-size: 13px;
  font-weight: 700;
}

.permission-code {
  overflow: hidden;
  color: var(--text-muted);
  font-family: Consolas, monospace;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-permissions,
.full-access-state {
  margin: 16px;
  padding: 28px;
  border: 1px dashed var(--border-strong);
  border-radius: 7px;
  color: var(--text-muted);
  text-align: center;
}

.full-access-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: left;
}

.full-access-icon {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 6px;
  color: #fff;
  background: var(--accent);
  font-weight: 800;
}

.modal-layer {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.form-modal {
  width: min(720px, calc(100vw - 48px));
  max-height: calc(100vh - 48px);
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--panel-bg);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.2);
}

.compact-modal {
  width: min(640px, calc(100vw - 48px));
}

.password-modal {
  width: min(440px, calc(100vw - 48px));
}

.modal-header {
  min-height: 72px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border);
}

.modal-kicker {
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
}

.modal-header h2 {
  margin: 3px 0 0;
  font-size: 18px;
}

.modal-close {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-secondary);
  background: #fff;
  font-size: 22px;
  cursor: pointer;
}

.modal-body {
  max-height: calc(100vh - 190px);
  overflow-y: auto;
  padding: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 7px;
}

.field > span,
.role-options legend {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  min-height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  color: var(--text);
  background: #fff;
  box-sizing: border-box;
  font: inherit;
  outline: none;
}

.field textarea {
  padding-top: 9px;
  resize: vertical;
}

.field input:disabled {
  color: var(--text-muted);
  background: #f3f5f7;
}

.field-span {
  grid-column: 1 / -1;
}

.role-options {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.role-options legend {
  padding: 0 5px;
}

.role-option {
  display: flex;
  min-width: 0;
  gap: 8px;
  align-items: start;
  padding: 9px;
  border: 1px solid var(--border);
  border-radius: 5px;
  cursor: pointer;
}

.role-option input {
  margin-top: 2px;
  accent-color: var(--accent);
}

.role-option span {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.role-option strong,
.role-option small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-option small {
  color: var(--text-muted);
}

.modal-footer {
  min-height: 64px;
  gap: 10px;
  padding: 0 20px;
  border-top: 1px solid var(--border);
}

.password-note {
  margin: 10px 0 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 12000;
  display: flex;
  align-items: center;
  gap: 9px;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  color: #172033;
  background: #fff;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  font-size: 13px;
  font-weight: 600;
}

.notice-success svg { color: #0f9f78; }
.notice-error svg { color: #dc3545; }

.notice-enter-active,
.notice-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.notice-enter-from,
.notice-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (max-width: 1000px) {
  .role-workspace {
    grid-template-columns: 200px minmax(0, 1fr);
  }

  .permission-grid {
    grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
  }
}

@media (max-width: 780px) {
  .records-toolbar,
  .sub-toolbar,
  .role-header {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    justify-content: flex-end;
  }

  .view-tabs,
  .search-input {
    width: 100%;
  }

  .view-tab {
    flex: 1;
  }

  .role-workspace {
    grid-template-columns: 1fr;
  }

  .role-list {
    display: flex;
    overflow-x: auto;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .role-list-item {
    min-width: 190px;
  }

  .form-grid,
  .role-options {
    grid-template-columns: 1fr;
  }

  .modal-layer {
    padding: 0;
  }

  .form-modal,
  .compact-modal,
  .password-modal {
    width: 100vw;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>
