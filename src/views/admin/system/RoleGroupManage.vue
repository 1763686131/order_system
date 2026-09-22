<template>
  <div class="page-root role-group-page">
    <nav class="role-tabs" aria-label="角色组导航">
      <div class="role-tab-scroll">
        <button
          v-for="group in roleGroups"
          :key="group.id"
          class="role-tab"
          :class="{ active: group.id === selectedGroupId }"
          type="button"
          @click="selectGroup(group.id)"
        >
          <span :class="['role-tab-icon', group.tone]">{{ group.name.slice(0, 1) }}</span>
          <span>{{ group.name }}</span>
          <i :class="['role-tab-status', group.status === 'enabled' ? 'enabled' : 'disabled']"></i>
        </button>
      </div>
      <button class="button button-primary add-role-button" type="button" @click="openCreate">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 5v14"></path>
          <path d="M5 12h14"></path>
          </svg>
        新增角色组
      </button>
    </nav>

    <div v-if="selectedGroup" class="role-context">
      <div class="role-context-main">
        <span :class="['role-context-icon', selectedGroup.tone]">{{ selectedGroup.name.slice(0, 1) }}</span>
        <div>
          <div class="role-context-title">
            <strong>{{ selectedGroup.name }}</strong>
            <span :class="['status-badge', selectedGroup.status === 'enabled' ? 'status-success' : 'status-disabled']">
              <i></i>{{ selectedGroup.status === 'enabled' ? '已启用' : '已停用' }}
            </span>
          </div>
          <span class="role-context-meta">{{ selectedGroup.code }} · {{ selectedGroup.description }}</span>
          <div class="role-policy-summary">
            <span :class="{ active: selectedGroup.canAccessAdmin }">
              {{ selectedGroup.canAccessAdmin ? '后台可访问' : '仅触屏端' }}
            </span>
            <span :class="{ active: selectedGroup.longSession }">
              {{ selectedGroup.longSession ? '长期会话 365 天' : '标准会话 7 天' }}
            </span>
          </div>
        </div>
      </div>
      <div class="role-context-actions">
        <button
          v-if="!selectedGroup.isSystem"
          class="button button-secondary"
          type="button"
          @click="toggleSelectedGroup"
        >
          {{ selectedGroup.status === 'enabled' ? '停用' : '启用' }}
        </button>
        <button
          v-if="!selectedGroup.isSystem"
          class="button button-ghost"
          type="button"
          @click="openEdit(selectedGroup)"
        >
          编辑信息
        </button>
        <span v-else class="system-role-hint">系统内置角色组</span>
      </div>
    </div>

    <section v-if="selectedGroup" class="permission-member-layout">
      <section class="permission-panel">
        <div class="box-header">
          <div class="box-title">
            <h2>权限组</h2>
            <span>{{ selectedGroup.permissions.length }} / {{ permissionTotal }} 项</span>
          </div>
          <span class="permission-panel-hint">点击分类配置权限</span>
        </div>

        <div class="permission-category-grid">
          <button
            v-for="module in permissionModules"
            :key="module.id"
            class="permission-category"
            :class="{
              empty: moduleSelectedCount(module) === 0,
              complete: moduleSelectedCount(module) === module.permissions.length
            }"
            type="button"
            @click="openPermissionModule(module)"
          >
            <span class="permission-category-main">
              <span :class="['module-dot', module.tone]"></span>
              <strong>{{ module.name }}</strong>
            </span>
            <span class="permission-category-count">
              <b>{{ moduleSelectedCount(module) }}</b>
              <i>/</i>
              {{ module.permissions.length }}
            </span>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m9 6 6 6-6 6"></path>
            </svg>
          </button>
        </div>

        <section class="scope-panel">
          <div class="scope-panel-heading">
            <div>
              <h3>数据可见范围</h3>
              <p>角色组成员将继承已启用的门店和仓库范围</p>
            </div>
            <span>
              {{ selectedGroup.storeIds.length + selectedGroup.warehouseIds.length }} 项已配置
            </span>
          </div>
          <div class="scope-config-grid">
            <div class="scope-config-block">
              <div class="scope-config-title">
                <strong>门店范围</strong>
                <span>点击标签切换</span>
              </div>
              <div class="scope-chip-list">
                <button
                  v-for="store in stores"
                  :key="store.id"
                  class="scope-chip"
                  :class="{ active: selectedGroup.storeIds.includes(store.id) }"
                  type="button"
                  :disabled="selectedGroup.fullAccess"
                  @click="toggleGroupScope('store', store.id)"
                >
                  <i></i>{{ store.name }}
                </button>
              </div>
            </div>
            <div class="scope-config-block">
              <div class="scope-config-title">
                <strong>仓库范围</strong>
                <span>点击标签切换</span>
              </div>
              <div class="scope-chip-list">
                <button
                  v-for="warehouse in warehouses"
                  :key="warehouse.id"
                  class="scope-chip"
                  :class="{ active: selectedGroup.warehouseIds.includes(warehouse.id) }"
                  type="button"
                  :disabled="selectedGroup.fullAccess"
                  @click="toggleGroupScope('warehouse', warehouse.id)"
                >
                  <i></i>{{ warehouse.name }}
                </button>
              </div>
            </div>
          </div>
        </section>
      </section>

      <aside class="members-panel">
        <div class="box-header">
          <div class="box-title">
            <h2>组内成员</h2>
            <span>{{ selectedGroup.memberIds.length }} 人</span>
          </div>
          <div class="box-actions">
            <div
              class="member-search"
              @focusin="memberSearchOpen = true"
              @focusout="queueCloseMemberSearch"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4 4"></path>
              </svg>
              <input
                v-model="memberSearchQuery"
                type="search"
                placeholder="搜索员工"
                aria-label="搜索可添加员工"
                @input="memberToAddId = null; memberSearchOpen = true"
              />
              <div v-if="memberSearchOpen" class="member-search-dropdown">
                <button
                  v-for="member in memberSearchResults"
                  :key="member.id"
                  type="button"
                  @mousedown.prevent
                  @click="selectMemberToAdd(member)"
                >
                  <span class="avatar small" :style="avatarStyle(member)">{{ member.name.slice(0, 1) }}</span>
                  <span>
                    <strong>{{ member.name }}</strong>
                    <small>{{ member.employeeNo }} · {{ member.department }}</small>
                  </span>
                </button>
                <span v-if="memberSearchResults.length === 0" class="member-search-empty">
                  未找到可添加员工
                </span>
              </div>
            </div>
            <button
              class="button button-secondary compact-button"
              type="button"
              :disabled="!memberToAddId"
              @click="addSelectedMember"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14"></path>
                <path d="M5 12h14"></path>
              </svg>
              添加成员
            </button>
            <button
              class="button button-danger compact-button"
              type="button"
              :disabled="selectedMemberIds.length === 0"
              @click="deleteSelectedMembers"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 7h14"></path>
                <path d="M10 11v6"></path>
                <path d="M14 11v6"></path>
                <path d="m9 7 .8-2h4.4l.8 2"></path>
                <path d="m7 7 .7 13h8.6L17 7"></path>
              </svg>
              删除成员
            </button>
          </div>
        </div>

        <div class="member-list">
          <label
            v-for="member in selectedMembers"
            :key="member.id"
            class="member-row"
            :class="{ selected: selectedMemberIds.includes(member.id) }"
          >
            <input v-model="selectedMemberIds" type="checkbox" :value="member.id" />
            <span class="avatar" :style="avatarStyle(member)">{{ member.name.slice(0, 1) }}</span>
            <span class="member-copy">
              <strong>{{ member.name }}</strong>
              <small>{{ member.employeeNo }} · {{ member.department }}</small>
            </span>
            <span :class="['member-account-status', member.accountStatus]">
              {{ memberAccountStatusLabel(member.accountStatus) }}
            </span>
          </label>
          <div v-if="selectedMembers.length === 0" class="member-empty">
            <strong>暂无成员</strong>
            <span>使用上方“添加成员”加入员工</span>
          </div>
        </div>
      </aside>
    </section>

    <transition name="notice">
      <div v-if="notice" class="page-notice notice-success" role="status">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="m8 12 2.5 2.5L16 9"></path>
        </svg>
        <span>{{ notice }}</span>
      </div>
    </transition>

    <Teleport to="body">
      <div
        v-if="permissionModalVisible && activePermissionModule"
        class="modal-layer permission-modal-layer"
        @click.self="closePermissionModal"
      >
        <section
          class="permission-config-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="permission-modal-title"
        >
          <div class="modal-header permission-modal-header">
            <div class="permission-modal-title">
              <span :class="['permission-modal-icon', activePermissionModule.tone]">
                {{ activePermissionModule.name.slice(0, 1) }}
              </span>
              <div>
                <span class="drawer-eyebrow">权限分类</span>
                <h2 id="permission-modal-title">{{ activePermissionModule.name }}</h2>
                <p>{{ activePermissionModule.description }}</p>
              </div>
            </div>
            <button
              class="icon-button"
              type="button"
              title="关闭"
              :disabled="saving"
              @click="closePermissionModal"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </div>

          <div class="permission-modal-toolbar">
            <label class="permission-modal-search">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4 4"></path>
              </svg>
              <input
                v-model="permissionSearchQuery"
                type="search"
                placeholder="搜索权限名称"
                aria-label="搜索当前分类权限"
              />
            </label>
            <div v-if="!permissionModalReadonly" class="permission-modal-actions">
              <button
                type="button"
                :disabled="permissionModalSelectedCount === activePermissionModule.permissions.length"
                @click="selectAllModulePermissions"
              >
                全选
              </button>
              <button
                type="button"
                :disabled="permissionModalSelectedCount === 0"
                @click="clearModulePermissions"
              >
                清空
              </button>
            </div>
          </div>

          <div class="permission-modal-body">
            <div class="permission-modal-grid">
              <div
                v-for="permission in filteredModulePermissions"
                :key="permission.id"
                class="permission-row"
                :class="{
                  active: permissionModalDraft.includes(permission.id),
                  addable: !permissionModalDraft.includes(permission.id),
                  'config-mode': !permissionModalReadonly,
                  readonly: permissionModalReadonly
                }"
                :aria-label="`${permission.name}，权限编码 ${permission.id}`"
                :tabindex="permissionModalReadonly ? -1 : 0"
                @click="togglePermissionDraft(permission)"
                @keydown.enter.self.prevent="togglePermissionDraft(permission)"
                @keydown.space.self.prevent="togglePermissionDraft(permission)"
              >
                <span class="permission-row-copy">
                  <strong>{{ permission.name }}</strong>
                </span>
                <span class="permission-code-tooltip" role="tooltip">
                  {{ permission.id }}
                </span>
                <button
                  v-if="!permissionModalReadonly && !permissionModalDraft.includes(permission.id)"
                  class="permission-add"
                  type="button"
                  :aria-label="`添加${permission.name}`"
                  @click.stop="togglePermissionDraft(permission)"
                >
                  <span>+</span><em>添加</em>
                </button>
                <button
                  v-if="!permissionModalReadonly && permissionModalDraft.includes(permission.id)"
                  class="permission-remove"
                  type="button"
                  :aria-label="`移除${permission.name}`"
                  @click.stop="togglePermissionDraft(permission)"
                >
                  ×
                </button>
              </div>
            </div>
            <div v-if="filteredModulePermissions.length === 0" class="permission-modal-empty">
              没有找到匹配的权限
            </div>
          </div>

          <div class="modal-footer permission-modal-footer">
            <span>
              已选择
              <strong>{{ permissionModalSelectedCount }}</strong>
              / {{ activePermissionModule.permissions.length }} 项
            </span>
            <div>
              <button
                v-if="permissionModalReadonly"
                class="button button-secondary"
                type="button"
                @click="closePermissionModal"
              >
                关闭
              </button>
              <template v-else>
                <button
                  class="button button-secondary"
                  type="button"
                  :disabled="saving"
                  @click="closePermissionModal"
                >
                  取消
                </button>
                <button
                  class="button button-primary"
                  type="button"
                  :disabled="saving || !permissionModalChanged"
                  @click="savePermissionModule"
                >
                  {{ saving ? '保存中...' : '保存配置' }}
                </button>
              </template>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="drawerVisible" class="modal-layer" @click.self="closeDrawer">
        <aside class="edit-modal" role="dialog" aria-modal="true" aria-labelledby="role-modal-title">
          <div class="modal-header">
            <div>
              <span class="drawer-eyebrow">{{ editingGroup ? '编辑角色组' : '新建角色组' }}</span>
              <h2 id="role-modal-title">{{ editingGroup ? '编辑角色组信息' : '新建角色组' }}</h2>
            </div>
            <button class="icon-button" type="button" title="关闭" @click="closeDrawer">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <section class="form-section modal-form-section">
              <div class="section-heading">
                <h3>角色组信息</h3>
                <span>维护角色组的基本信息</span>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>角色组名称 <em>*</em></span>
                  <input v-model.trim="draft.name" type="text" placeholder="例如 财务人员" />
                </label>
                <label class="field">
                  <span>权限编码</span>
                  <input
                    v-model.trim="draft.code"
                    type="text"
                    :disabled="editingGroup"
                    placeholder="例如 finance_staff"
                  />
                </label>
                <label class="field">
                  <span>状态</span>
                  <select v-model="draft.status">
                    <option value="enabled">启用</option>
                    <option value="disabled">停用</option>
                  </select>
                </label>
                <label class="field">
                  <span>颜色主题</span>
                  <select v-model="draft.tone">
                    <option value="green">绿色</option>
                    <option value="blue">蓝色</option>
                    <option value="orange">橙色</option>
                    <option value="red">红色</option>
                    <option value="purple">紫色</option>
                  </select>
                </label>
                <label class="field field-wide">
                  <span>职责说明</span>
                  <textarea v-model.trim="draft.description" rows="3" placeholder="简述该角色组负责的业务范围"></textarea>
                </label>
              </div>
            </section>

            <section class="form-section modal-form-section access-policy-section">
              <div class="section-heading">
                <h3>访问与会话</h3>
                <span>后台入口与登录时长分别控制</span>
              </div>
              <div class="access-policy-grid">
                <label
                  class="policy-toggle-card"
                  :class="{ active: draft.canAccessAdmin }"
                >
                  <span class="policy-toggle-copy">
                    <strong>允许访问后台</strong>
                    <small>可进入后台管理页面，但不会获得超级管理员身份</small>
                  </span>
                  <span class="policy-switch">
                    <input v-model="draft.canAccessAdmin" type="checkbox" />
                    <i></i>
                  </span>
                </label>
                <label
                  class="policy-toggle-card"
                  :class="{ active: draft.longSession }"
                >
                  <span class="policy-toggle-copy">
                    <strong>长期登录会话</strong>
                    <small>开启后 365 天滑动续期，关闭后为 7 天</small>
                  </span>
                  <span class="policy-switch">
                    <input v-model="draft.longSession" type="checkbox" />
                    <i></i>
                  </span>
                </label>
              </div>
            </section>
          </div>

          <div class="modal-footer">
            <button class="button button-secondary" type="button" @click="closeDrawer">取消</button>
            <button class="button button-primary" type="button" @click="saveGroup">
              {{ editingGroup ? '保存修改' : '创建角色组' }}
            </button>
          </div>
        </aside>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import request from '@/api/request'

const permissionModules = ref([])
const stores = ref([])
const warehouses = ref([])
const memberCatalog = ref([])
const roleGroups = ref([])
const allPermissionIds = computed(() =>
  permissionModules.value.flatMap(module => module.permissions.map(permission => permission.id))
)

const selectedGroupId = ref(null)
const permissionModalVisible = ref(false)
const activePermissionModuleId = ref(null)
const permissionSearchQuery = ref('')
const permissionModalDraft = ref([])
const permissionModalSnapshot = ref([])
const selectedMemberIds = ref([])
const memberSearchQuery = ref('')
const memberSearchOpen = ref(false)
const memberToAddId = ref(null)
const drawerVisible = ref(false)
const editingGroup = ref(false)
const draft = ref(createEmptyGroup())
const notice = ref('')
const saving = ref(false)
let noticeTimer

const selectedGroup = computed(() => roleGroups.value.find(group => group.id === selectedGroupId.value))
const selectedMembers = computed(() => {
  if (!selectedGroup.value) return []
  return memberCatalog.value.filter(member => selectedGroup.value.memberIds.includes(member.id))
})
const activePermissionModule = computed(() =>
  permissionModules.value.find(module => module.id === activePermissionModuleId.value) || null
)
const permissionModalReadonly = computed(() => Boolean(selectedGroup.value?.fullAccess))
const filteredModulePermissions = computed(() => {
  const permissions = activePermissionModule.value?.permissions || []
  const keyword = permissionSearchQuery.value.trim().toLowerCase()
  if (!keyword) return permissions
  return permissions.filter(permission =>
    [permission.name, permission.id].join(' ').toLowerCase().includes(keyword)
  )
})
const permissionModalSelectedCount = computed(() => permissionModalDraft.value.length)
const permissionModalChanged = computed(() => {
  const original = [...permissionModalSnapshot.value].sort()
  const current = [...permissionModalDraft.value].sort()
  return JSON.stringify(original) !== JSON.stringify(current)
})
const availableMembers = computed(() => {
  if (!selectedGroup.value) return []
  return memberCatalog.value.filter(member => !selectedGroup.value.memberIds.includes(member.id))
})
const memberSearchResults = computed(() => {
  const keyword = memberSearchQuery.value.trim().toLowerCase()
  if (!keyword) return availableMembers.value
  return availableMembers.value.filter(member =>
    [member.name, member.employeeNo, member.department]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  )
})
const permissionTotal = computed(() => allPermissionIds.value.length)

function toneForRole(role, index) {
  if (role.fullAccess) return 'red'
  return ['green', 'blue', 'orange', 'purple'][index % 4]
}

function mapRole(role, index = 0) {
  return {
    ...role,
    canAccessAdmin: Boolean(role.canAccessAdmin || role.fullAccess),
    longSession: Boolean(role.longSession),
    tone: toneForRole(role, index),
    status: role.status === 'active' ? 'enabled' : 'disabled',
    permissions: role.fullAccess ? [...allPermissionIds.value] : [...(role.permissionCodes || [])],
    memberIds: [...(role.memberIds || [])],
    storeIds: role.fullAccess ? stores.value.map(store => store.id) : [...(role.storeIds || [])],
    warehouseIds: role.fullAccess
      ? warehouses.value.map(warehouse => warehouse.id)
      : [...(role.warehouseIds || [])]
  }
}

function mapEmployee(employee) {
  return {
    ...employee,
    name: employee.displayName,
    avatarColor: employee.avatarColor || '#e9f8f3'
  }
}

async function loadAll() {
  try {
    const [permissionResponse, roleResponse, employeeResponse, storeResponse, warehouseResponse] =
      await Promise.all([
        request.get('/admin/permissions'),
        request.get('/admin/roles'),
        request.get('/admin/employees'),
        request.get('/stores'),
        request.get('/warehouses')
      ])

    stores.value = Array.isArray(storeResponse) ? storeResponse : []
    warehouses.value = Array.isArray(warehouseResponse) ? warehouseResponse : []
    permissionModules.value = (permissionResponse.modules || []).map((module, index) => ({
      ...module,
      id: module.code,
      tone: ['green', 'blue', 'orange', 'purple'][index % 4],
      permissions: (module.permissions || []).map(permission => ({
        ...permission,
        id: permission.code
      }))
    }))
    memberCatalog.value = (employeeResponse.employees || []).map(mapEmployee)
    roleGroups.value = (roleResponse.roles || []).map(mapRole)

    if (!roleGroups.value.some(group => group.id === selectedGroupId.value)) {
      selectedGroupId.value = roleGroups.value[0]?.id || null
    }
  } catch (error) {
    showNotice(error?.response?.data?.message || '角色组数据加载失败')
  }
}

function createEmptyGroup() {
  return {
    id: null,
    code: '',
    name: '',
    description: '',
    tone: 'green',
    status: 'enabled',
    memberIds: [],
    permissions: [],
    storeIds: [],
    warehouseIds: [],
    dataScope: 'custom',
    canAccessAdmin: false,
    longSession: true,
    createdAt: '',
    updatedAt: ''
  }
}

function openCreate() {
  editingGroup.value = false
  draft.value = createEmptyGroup()
  drawerVisible.value = true
}

function selectGroup(groupId) {
  closePermissionModal()
  selectedGroupId.value = groupId
  selectedMemberIds.value = []
  resetMemberSearch()
}

function openEdit(group) {
  editingGroup.value = true
  draft.value = {
    ...group,
    memberIds: [...group.memberIds],
    permissions: [...group.permissions],
    storeIds: [...(group.storeIds || [])],
    warehouseIds: [...(group.warehouseIds || [])]
  }
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
}

function rolePayload(group) {
  return {
    code: group.code,
    name: group.name,
    description: group.description,
    status: group.status === 'enabled' ? 'active' : 'disabled',
    canAccessAdmin: Boolean(group.canAccessAdmin),
    longSession: Boolean(group.longSession),
    dataScope: group.dataScope || 'custom',
    permissionCodes: [...group.permissions],
    storeIds: [...group.storeIds],
    warehouseIds: [...group.warehouseIds]
  }
}

function replaceRole(role) {
  const index = roleGroups.value.findIndex(group => group.id === role.id)
  const mapped = mapRole(role, index < 0 ? roleGroups.value.length : index)
  if (index < 0) roleGroups.value.push(mapped)
  else roleGroups.value[index] = mapped
  return mapped
}

async function persistRole(group, successMessage) {
  try {
    saving.value = true
    const response = await request.put(`/admin/roles/${group.id}`, rolePayload(group))
    replaceRole(response.role)
    showNotice(successMessage || response.message || '角色组已更新')
    return true
  } catch (error) {
    showNotice(error?.response?.data?.message || '角色组保存失败')
    await loadAll()
    return false
  } finally {
    saving.value = false
  }
}

async function saveGroup() {
  if (!draft.value.name) {
    showNotice('请先填写角色组名称')
    return
  }

  const normalizedCode = draft.value.code
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
  const payload = rolePayload({
    ...draft.value,
    code: normalizedCode || `role_${Date.now().toString(36)}`
  })

  try {
    saving.value = true
    const response = editingGroup.value
      ? await request.put(`/admin/roles/${draft.value.id}`, payload)
      : await request.post('/admin/roles', payload)
    const savedRole = replaceRole(response.role)
    selectedGroupId.value = savedRole.id
    showNotice(response.message || (editingGroup.value ? '角色组已更新' : '角色组已创建'))
    closeDrawer()
  } catch (error) {
    showNotice(error?.response?.data?.message || '角色组保存失败')
  } finally {
    saving.value = false
  }
}

function moduleSelectedCount(module) {
  if (!selectedGroup.value) return 0
  return module.permissions.filter(permission =>
    selectedGroup.value.permissions.includes(permission.id)
  ).length
}

function openPermissionModule(module) {
  if (!selectedGroup.value) return
  const selectedIds = module.permissions
    .filter(permission => selectedGroup.value.permissions.includes(permission.id))
    .map(permission => permission.id)
  activePermissionModuleId.value = module.id
  permissionSearchQuery.value = ''
  permissionModalDraft.value = [...selectedIds]
  permissionModalSnapshot.value = [...selectedIds]
  permissionModalVisible.value = true
}

function closePermissionModal() {
  if (saving.value) return
  permissionModalVisible.value = false
  activePermissionModuleId.value = null
  permissionSearchQuery.value = ''
  permissionModalDraft.value = []
  permissionModalSnapshot.value = []
}

function togglePermissionDraft(permission) {
  if (permissionModalReadonly.value) return
  const permissionIds = [...permissionModalDraft.value]
  const index = permissionIds.indexOf(permission.id)
  if (index === -1) permissionIds.push(permission.id)
  else permissionIds.splice(index, 1)
  permissionModalDraft.value = permissionIds
}

function selectAllModulePermissions() {
  if (!activePermissionModule.value || permissionModalReadonly.value) return
  permissionModalDraft.value = activePermissionModule.value.permissions.map(
    permission => permission.id
  )
}

function clearModulePermissions() {
  if (permissionModalReadonly.value) return
  permissionModalDraft.value = []
}

async function savePermissionModule() {
  if (
    !selectedGroup.value ||
    !activePermissionModule.value ||
    permissionModalReadonly.value ||
    !permissionModalChanged.value
  ) {
    return
  }

  const moduleIds = new Set(
    activePermissionModule.value.permissions.map(permission => permission.id)
  )
  const permissionsOutsideModule = selectedGroup.value.permissions.filter(
    permissionId => !moduleIds.has(permissionId)
  )
  const roleToSave = {
    ...selectedGroup.value,
    permissions: [...permissionsOutsideModule, ...permissionModalDraft.value]
  }
  const moduleName = activePermissionModule.value.name

  if (await persistRole(roleToSave, `${moduleName}权限已保存`)) {
    closePermissionModal()
  }
}

async function toggleGroupScope(scopeType, scopeId) {
  if (!selectedGroup.value || selectedGroup.value.fullAccess) return
  const key = scopeType === 'store' ? 'storeIds' : 'warehouseIds'
  const ids = [...(selectedGroup.value[key] || [])]
  const index = ids.indexOf(scopeId)

  if (index === -1) {
    ids.push(scopeId)
  } else {
    ids.splice(index, 1)
  }
  selectedGroup.value[key] = ids
  await persistRole(
    selectedGroup.value,
    `${scopeType === 'store' ? '门店' : '仓库'}范围已更新`
  )
}

function queueCloseMemberSearch() {
  window.setTimeout(() => {
    memberSearchOpen.value = false
  }, 120)
}

function selectMemberToAdd(member) {
  memberToAddId.value = member.id
  memberSearchQuery.value = `${member.name} · ${member.employeeNo}`
  memberSearchOpen.value = false
}

async function persistMembers(employeeIds, successMessage) {
  if (!selectedGroup.value) return false
  try {
    saving.value = true
    const response = await request.put(
      `/admin/roles/${selectedGroup.value.id}/members`,
      { employeeIds }
    )
    replaceRole(response.role)
    showNotice(response.message || successMessage)
    return true
  } catch (error) {
    showNotice(error?.response?.data?.message || '角色组成员保存失败')
    await loadAll()
    return false
  } finally {
    saving.value = false
  }
}

async function addSelectedMember() {
  if (!selectedGroup.value || !memberToAddId.value) return
  const employeeIds = [...selectedGroup.value.memberIds, memberToAddId.value]
  if (await persistMembers(employeeIds, '成员添加成功')) resetMemberSearch()
}

function resetMemberSearch() {
  memberSearchQuery.value = ''
  memberSearchOpen.value = false
  memberToAddId.value = null
}

async function deleteSelectedMembers() {
  if (!selectedGroup.value || selectedMemberIds.value.length === 0) return
  const employeeIds = selectedGroup.value.memberIds.filter(
    memberId => !selectedMemberIds.value.includes(memberId)
  )
  if (await persistMembers(employeeIds, '已删除选中的成员')) {
    selectedMemberIds.value = []
  }
}

async function toggleSelectedGroup() {
  if (!selectedGroup.value || selectedGroup.value.isSystem) return
  selectedGroup.value.status = selectedGroup.value.status === 'enabled' ? 'disabled' : 'enabled'
  await persistRole(
    selectedGroup.value,
    selectedGroup.value.status === 'enabled' ? '角色组已启用' : '角色组已停用'
  )
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

function avatarStyle(member) {
  const style = {
    backgroundColor: member.avatarColor || '#e5e7eb',
    color: '#275a4d'
  }
  if (member.avatarUrl) {
    style.backgroundImage = `url("${member.avatarUrl}")`
    style.backgroundPosition = 'center'
    style.backgroundRepeat = 'no-repeat'
    style.backgroundSize = 'cover'
    style.color = 'transparent'
  }
  return style
}

function memberAccountStatusLabel(status) {
  return {
    active: '正常',
    disabled: '已停用',
    pending: '待开通'
  }[status] || '待开通'
}

onMounted(loadAll)
</script>

<style scoped>
.page-root {
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
  min-height: 100%;
  padding: 0;
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
  box-sizing: border-box;
}

.page-header,
.title-row,
.header-actions,
  .detail-header,
  .detail-title,
  .detail-actions,
  .panel-header,
  .member-info,
  .section-heading,
  .drawer-header,
  .drawer-footer,
  .modal-header,
  .modal-footer {
  display: flex;
  align-items: center;
}

.page-header {
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.breadcrumb,
.drawer-eyebrow {
  margin-bottom: 7px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.title-row {
  gap: 10px;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  font-size: 20px;
  line-height: 1.35;
}

.page-header p {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.demo-tag,
.mini-status,
.code-label,
.status-badge,
.section-count {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}

.demo-tag {
  height: 24px;
  padding: 0 9px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.header-actions,
.detail-actions {
  gap: 8px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 5px;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.button svg,
.page-notice svg,
.icon-button svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.button-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.18);
}

.button-secondary {
  color: var(--text-secondary);
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button:disabled,
.scope-chip:disabled {
  opacity: 0.52;
  cursor: not-allowed;
}

.system-role-hint {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 650;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.metric-card,
.group-panel,
.detail-panel {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
}

.metric-card {
  min-height: 94px;
  padding: 15px 16px;
  box-sizing: border-box;
}

.metric-label,
.metric-note {
  display: block;
}

.metric-label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.metric-card strong {
  display: block;
  margin: 7px 0 3px;
  font-size: 25px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.metric-note {
  color: var(--text-muted);
  font-size: 12px;
}

.success-text {
  color: #13734f;
}

.role-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 0.78fr) minmax(560px, 1.7fr);
  gap: 14px;
}

.group-panel,
.detail-panel {
  min-width: 0;
  overflow: hidden;
}

.panel-header,
.detail-header {
  justify-content: space-between;
  gap: 16px;
  min-height: 70px;
  padding: 13px 16px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.panel-header h2 {
  font-size: 15px;
}

.panel-header span {
  display: block;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  flex: 0 0 36px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.group-list {
  padding: 8px;
}

.group-item {
  display: flex;
  width: 100%;
  min-height: 84px;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 10px;
  color: var(--text);
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.group-item:hover {
  background: #f8fafc;
  border-color: var(--border);
}

.group-item.selected {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.group-icon {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 14px;
  font-weight: 750;
}

.group-icon.large {
  width: 42px;
  height: 42px;
  flex-basis: 42px;
  font-size: 17px;
}

.group-icon.green,
.module-dot.green {
  color: #13734f;
  background: #eaf8f1;
}

.group-icon.blue,
.module-dot.blue {
  color: #16647a;
  background: #e7f5f8;
}

.group-icon.orange,
.module-dot.orange {
  color: #a4510b;
  background: #fff3df;
}

.group-icon.red,
.module-dot.red {
  color: #b4232f;
  background: #fcebed;
}

.group-icon.purple,
.module-dot.purple {
  color: #6651a8;
  background: #f1edff;
}

.group-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.group-copy strong {
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-copy small {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-meta {
  display: flex !important;
  align-items: center;
  gap: 6px;
  margin-top: 2px !important;
  color: var(--text-secondary) !important;
  font-size: 11px !important;
}

.group-meta i {
  width: 3px;
  height: 3px;
  background: var(--border-strong);
  border-radius: 50%;
}

.mini-status {
  min-height: 23px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
}

.mini-status.enabled {
  color: #13734f;
  background: #eaf8f1;
}

.mini-status.disabled {
  color: #7b8492;
  background: #f1f2f4;
}

.detail-header {
  align-items: flex-start;
}

.detail-title {
  min-width: 0;
  align-items: flex-start;
  gap: 11px;
}

.detail-title h2 {
  font-size: 18px;
}

.detail-title p {
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-title .title-row {
  align-items: center;
}

.status-badge {
  min-height: 25px;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
  box-sizing: border-box;
}

.status-badge i {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-success {
  color: #13734f;
  background: #eaf8f1;
}

.status-disabled {
  color: #7b8492;
  background: #f1f2f4;
}

.code-label {
  margin-top: 8px;
  padding: 3px 7px;
  color: var(--text-muted);
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}

.detail-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-bottom: 1px solid var(--border);
}

.detail-summary div {
  min-height: 72px;
  padding: 13px 15px;
  border-right: 1px solid var(--border);
  box-sizing: border-box;
}

.detail-summary div:last-child {
  border-right: 0;
}

.detail-summary span,
.detail-summary strong {
  display: block;
}

.detail-summary span {
  color: var(--text-muted);
  font-size: 11px;
}

.detail-summary strong {
  margin-top: 7px;
  color: var(--text);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}

.detail-section {
  padding: 18px 16px 0;
}

.detail-section + .detail-section {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}

.section-heading {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 13px;
}

.section-heading h3 {
  font-size: 14px;
}

.section-heading span {
  display: block;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.section-count {
  margin-top: 0 !important;
  color: var(--accent-dark) !important;
  font-size: 12px !important;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.permission-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.permission-module {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.module-heading {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.module-dot {
  display: inline-flex;
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  margin-top: 4px;
  border-radius: 50%;
}

.module-heading strong,
.module-heading small {
  display: block;
}

.module-heading strong {
  font-size: 12px;
}

.module-heading small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
}

.permission-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-chip {
  display: inline-flex;
  min-height: 29px;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}

.permission-chip:hover {
  color: var(--accent-dark);
  border-color: var(--accent-border);
}

.permission-chip.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
  font-weight: 650;
}

.permission-check {
  display: inline-flex;
  width: 14px;
  height: 14px;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 3px;
  font-size: 10px;
  font-weight: 800;
}

.permission-chip.active .permission-check {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.member-table {
  border-top: 1px solid var(--border);
}

.member-row {
  display: flex;
  min-height: 59px;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #edf1f5;
}

.member-info {
  min-width: 0;
  flex: 1;
  gap: 9px;
}

.member-info > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.member-info strong,
.member-info span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-info strong {
  font-size: 13px;
}

.member-info div span {
  color: var(--text-muted);
  font-size: 11px;
}

.avatar {
  display: inline-flex;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 750;
}

.avatar.small {
  width: 30px;
  height: 30px;
  flex-basis: 30px;
  font-size: 12px;
}

.member-account-status {
  min-width: 70px;
  color: var(--text-muted);
  font-size: 11px;
}

.member-account-status.active {
  color: #13734f;
}

.member-account-status.pending {
  color: #a4510b;
}

.member-account-status.disabled {
  color: #7b8492;
}

.text-button {
  padding: 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
}

.text-button:hover {
  color: var(--accent);
  text-decoration: underline;
}

.danger-text {
  color: #b4232f;
}

.member-empty {
  display: flex;
  min-height: 120px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

.member-empty strong {
  color: var(--text-secondary);
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 3000;
  display: flex;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 10px 16px;
  color: var(--text);
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  box-sizing: border-box;
  font-size: 13px;
  font-weight: 600;
}

.page-notice svg {
  flex: 0 0 19px;
  width: 19px;
  height: 19px;
  color: var(--accent);
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

.modal-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --panel-bg: #fff;
  --border: #dfe5ec;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  box-sizing: border-box;
}

.edit-modal {
  display: flex;
  width: min(620px, calc(100vw - 48px));
  max-height: min(720px, calc(100vh - 48px));
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.2);
  overflow: hidden;
}

.permission-config-modal {
  display: flex;
  width: min(860px, calc(100vw - 48px));
  max-height: min(720px, calc(100vh - 48px));
  flex-direction: column;
  color: var(--text);
  background: var(--panel-bg, #fff);
  border: 1px solid var(--border, #dfe5ec);
  border-radius: 7px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.permission-modal-header {
  min-height: 90px;
}

.permission-modal-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.permission-modal-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  font-size: 15px;
}

.permission-modal-title > div {
  min-width: 0;
}

.permission-modal-title .drawer-eyebrow {
  display: block;
  margin-bottom: 4px;
}

.permission-modal-title h2 {
  line-height: 1.3;
}

.permission-modal-title p {
  margin-top: 4px;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.permission-modal-toolbar {
  display: flex;
  min-height: 59px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.permission-modal-search {
  display: flex;
  width: min(320px, 100%);
  height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.permission-modal-search:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.permission-modal-search svg {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.permission-modal-search input {
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 0;
  color: var(--text);
  background: transparent;
  border: 0;
  outline: 0;
  font: inherit;
  font-size: 12px;
}

.permission-modal-search input::placeholder {
  color: var(--text-muted);
}

.permission-modal-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 14px;
}

.permission-modal-actions button {
  padding: 3px 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.permission-modal-actions button:hover:not(:disabled) {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.permission-modal-actions button:disabled {
  color: var(--text-muted);
  cursor: not-allowed;
  opacity: 0.45;
}

.permission-modal-body {
  min-height: 220px;
  flex: 1;
  padding: 34px 20px 20px;
  overflow-y: auto;
  background: #f4f7f9;
}

.permission-modal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  align-items: stretch;
  gap: 8px;
}

.permission-modal-grid .permission-row {
  width: 100%;
  min-width: 0;
  min-height: 42px;
}

.permission-modal-empty {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 12px;
}

.permission-modal-footer {
  justify-content: space-between;
}

.permission-modal-footer > span {
  color: var(--text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.permission-modal-footer > span strong {
  color: var(--accent-dark);
  font-size: 13px;
}

.permission-modal-footer > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-header {
  min-height: 78px;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.modal-header h2 {
  font-size: 18px;
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f4f7f9;
}

.modal-form-section {
  margin: 0;
  padding: 15px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
}

.form-section.modal-form-section + .form-section.modal-form-section {
  margin-top: 12px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.access-policy-section .section-heading {
  align-items: flex-start;
}

.access-policy-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.policy-toggle-card {
  display: flex;
  min-height: 76px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.policy-toggle-card:hover,
.policy-toggle-card.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.policy-toggle-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.policy-toggle-copy strong {
  color: var(--text);
  font-size: 13px;
}

.policy-toggle-copy small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.policy-switch {
  position: relative;
  display: inline-flex;
  width: 38px;
  height: 22px;
  flex: 0 0 38px;
}

.policy-switch input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.policy-switch i {
  position: relative;
  width: 38px;
  height: 22px;
  background: var(--border-strong);
  border-radius: 999px;
  transition: background 0.18s ease;
}

.policy-switch i::after {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.2);
  content: '';
  transition: transform 0.18s ease;
}

.policy-switch input:checked + i {
  background: var(--accent);
}

.policy-switch input:checked + i::after {
  transform: translateX(16px);
}

.policy-switch input:focus-visible + i {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.form-section + .form-section {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid var(--border);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.field > span {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
}

.field em {
  color: #dc3545;
  font-style: normal;
}

input,
select,
textarea {
  width: 100%;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  font: inherit;
  font-size: 13px;
  box-sizing: border-box;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

input,
select {
  height: 38px;
}

textarea {
  min-height: 80px;
  padding-top: 10px;
  padding-bottom: 10px;
  resize: vertical;
}

input::placeholder,
textarea::placeholder {
  color: #a3adbb;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.field-wide {
  grid-column: 1 / -1;
}

.drawer-permissions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.drawer-module {
  display: grid;
  gap: 7px;
}

.drawer-module-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 2px;
  font-size: 12px;
}

.drawer-module-title .module-dot {
  width: 7px;
  height: 7px;
  flex-basis: 7px;
  margin-top: 0;
}

.check-item,
.member-check-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 9px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
  cursor: pointer;
  box-sizing: border-box;
}

.check-item:has(input:checked),
.member-check-item:has(input:checked) {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.check-item input,
.member-check-item input {
  width: 16px;
  height: 16px;
  margin: 1px 0 0;
  accent-color: var(--accent);
}

.check-item strong,
.check-item small,
.member-check-item strong,
.member-check-item small {
  display: block;
}

.check-item strong,
.member-check-item strong {
  font-size: 12px;
}

.check-item small,
.member-check-item small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
}

.member-check-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.member-check-item {
  align-items: center;
}

.modal-footer {
  justify-content: flex-end;
  gap: 8px;
  min-height: 68px;
  padding: 13px 20px;
  background: #fff;
  border-top: 1px solid var(--border);
}

.role-tabs {
  display: flex;
  min-height: 52px;
  align-items: stretch;
  gap: 10px;
  padding-right: 8px;
  background: #e8eef1;
  border: 1px solid var(--border);
  border-bottom: 0;
  border-radius: 7px 7px 0 0;
  box-shadow: none;
  box-sizing: border-box;
}

.role-tab-scroll {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  align-items: flex-end;
  gap: 3px;
  padding-left: 8px;
  overflow-x: auto;
}

.role-tab {
  position: relative;
  z-index: 1;
  display: inline-flex;
  min-width: 136px;
  height: 41px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 9px 9px 0 0;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  box-sizing: border-box;
  transition: color 0.18s ease, background 0.18s ease;
}

.role-tab:hover {
  color: var(--accent-dark);
  background: rgba(255, 255, 255, 0.62);
}

.role-tab.active {
  z-index: 2;
  color: var(--accent-dark);
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(203, 213, 225, 0.72);
}

.role-tab.active::before,
.role-tab.active::after {
  position: absolute;
  bottom: 0;
  width: 10px;
  height: 10px;
  content: '';
  pointer-events: none;
}

.role-tab.active::before {
  left: -10px;
  background: radial-gradient(circle at 0 0, transparent 9px, #fff 10px);
}

.role-tab.active::after {
  right: -10px;
  background: radial-gradient(circle at 100% 0, transparent 9px, #fff 10px);
}

.role-tab-icon,
.role-context-icon,
.permission-modal-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #13734f;
  background: #eaf8f1;
  border-radius: 6px;
  font-weight: 750;
}

.role-tab-icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  font-size: 11px;
}

.role-tab-icon.green,
.role-context-icon.green,
.permission-modal-icon.green {
  color: #13734f;
  background: #eaf8f1;
}

.role-tab-icon.blue,
.role-context-icon.blue,
.permission-modal-icon.blue {
  color: #16647a;
  background: #e7f5f8;
}

.role-tab-icon.orange,
.role-context-icon.orange,
.permission-modal-icon.orange {
  color: #a4510b;
  background: #fff3df;
}

.role-tab-icon.red,
.role-context-icon.red,
.permission-modal-icon.red {
  color: #b4232f;
  background: #fcebed;
}

.role-tab-icon.purple,
.role-context-icon.purple,
.permission-modal-icon.purple {
  color: #6651a8;
  background: #f1edff;
}

.role-tab-status {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  margin-left: 1px;
  border-radius: 50%;
}

.role-tab-status.enabled {
  background: var(--accent);
}

.role-tab-status.disabled {
  background: #aab4c1;
}

.add-role-button {
  align-self: center;
  margin-left: auto;
  flex: 0 0 auto;
}

.role-context {
  display: flex;
  min-height: 67px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 0;
  padding: 11px 15px;
  background: #fff;
  border: 1px solid var(--border);
  border-top: 0;
  border-radius: 0;
  box-shadow: none;
  box-sizing: border-box;
}

.role-context-main,
.role-context-title {
  display: flex;
  align-items: center;
}

.role-context-main {
  min-width: 0;
  gap: 10px;
}

.role-context-icon {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  font-size: 14px;
}

.role-context-title {
  gap: 8px;
}

.role-context-title strong {
  font-size: 14px;
}

.role-context-meta {
  display: block;
  max-width: 680px;
  margin-top: 4px;
  overflow: hidden;
  color: var(--text-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-context-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.permission-member-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.85fr);
  gap: 14px;
  margin-top: 0;
  align-items: start;
}

.permission-panel,
.members-panel {
  min-width: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-top: 0;
  border-radius: 0 0 7px 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
  box-sizing: border-box;
}

.permission-panel {
  overflow: visible;
}

.members-panel {
  overflow: visible;
}

.box-header {
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.box-title {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 8px;
}

.box-title h2 {
  font-size: 15px;
}

.box-title span {
  color: var(--text-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.permission-panel-hint {
  color: var(--text-muted);
  font-size: 11px;
}

.box-actions {
  display: flex;
  min-width: 0;
  align-items: center;
  flex: 0 0 auto;
  gap: 7px;
}

.compact-button {
  height: 34px;
  padding: 0 10px;
  font-size: 12px;
}

.compact-button svg {
  width: 15px;
  height: 15px;
}

.button-danger {
  color: #b4232f;
  background: #fff;
  border-color: #e7b3b9;
}

.button-danger:hover:not(:disabled) {
  color: #fff;
  background: #c73543;
  border-color: #c73543;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.member-search {
  position: relative;
  display: flex;
  width: 164px;
  height: 34px;
  align-items: center;
  gap: 6px;
  padding: 0 9px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
}

.member-search:focus-within {
  color: var(--accent-dark);
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.member-search > svg {
  width: 15px;
  height: 15px;
  flex: 0 0 15px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.member-search input {
  width: auto;
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0;
  color: var(--text);
  border: 0;
  box-shadow: none;
  font-size: 12px;
}

.member-search input:focus {
  border: 0;
  box-shadow: none;
}

.member-search-dropdown {
  position: absolute;
  top: calc(100% + 7px);
  right: 0;
  left: 0;
  z-index: 30;
  max-height: 240px;
  padding: 4px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.16);
}

.member-search-dropdown button {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 8px;
  padding: 7px;
  color: var(--text);
  text-align: left;
  background: #fff;
  border: 0;
  border-radius: 4px;
  font: inherit;
  cursor: pointer;
}

.member-search-dropdown button:hover {
  background: var(--accent-soft);
}

.member-search-dropdown button > span:last-child {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.member-search-dropdown strong,
.member-search-dropdown small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-policy-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.role-policy-summary span {
  display: inline-flex;
  min-height: 20px;
  align-items: center;
  padding: 2px 7px;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.role-policy-summary span.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.member-search-dropdown strong {
  font-size: 11px;
}

.member-search-dropdown small {
  color: var(--text-muted);
  font-size: 10px;
}

.member-search-empty {
  display: block;
  padding: 10px 7px;
  color: var(--text-muted);
  font-size: 11px;
  text-align: center;
}

.inline-picker {
  margin: 12px 14px 0;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--accent-border);
  border-radius: 6px;
}

.inline-picker-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.inline-picker-header strong {
  font-size: 12px;
}

.inline-picker-header span {
  color: var(--text-muted);
  font-size: 11px;
}

.picker-grid,
.member-picker-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.picker-option,
.picker-member-option {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  cursor: pointer;
  box-sizing: border-box;
}

.picker-option:has(input:checked),
.picker-member-option:has(input:checked) {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.picker-option input,
.picker-member-option input,
.permission-row input,
.member-row input {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  margin: 0;
  accent-color: var(--accent);
}

.picker-option strong,
.picker-option small,
.picker-member-option strong,
.picker-member-option small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-option strong,
.picker-member-option strong {
  font-size: 11px;
}

.picker-option small,
.picker-member-option small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
}

.inline-picker-actions {
  display: flex;
  justify-content: flex-end;
  gap: 7px;
  margin-top: 11px;
}

.picker-empty {
  padding: 10px;
  color: var(--text-muted);
  background: #fff;
  border: 1px dashed var(--border-strong);
  border-radius: 5px;
  font-size: 11px;
  text-align: center;
}

.permission-category-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 7px;
  padding: 10px;
}

.permission-category {
  display: grid;
  min-width: 0;
  min-height: 43px;
  grid-template-columns: minmax(0, 1fr) auto 14px;
  align-items: center;
  gap: 8px;
  padding: 7px 9px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.permission-category:hover,
.permission-category:focus-visible {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.07);
  outline: 0;
}

.permission-category.empty {
  background: #f8fafc;
  border-style: dashed;
}

.permission-category.complete {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.permission-category-main {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}

.permission-category-main strong {
  overflow: hidden;
  font-size: 12px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.permission-category-count {
  display: inline-flex;
  min-width: 42px;
  align-items: baseline;
  justify-content: flex-end;
  gap: 3px;
  color: var(--text-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.permission-category-count b {
  color: var(--accent-dark);
  font-size: 12px;
}

.permission-category-count i {
  color: var(--border-strong);
  font-style: normal;
}

.permission-category > svg {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  transition: color 0.18s ease, transform 0.18s ease;
}

.permission-category:hover > svg,
.permission-category:focus-visible > svg {
  color: var(--accent);
  transform: translateX(2px);
}

.scope-panel {
  margin: 0 10px 10px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.scope-panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 11px;
}

.scope-panel-heading h3 {
  font-size: 13px;
}

.scope-panel-heading p {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 11px;
}

.scope-panel-heading > span {
  flex: 0 0 auto;
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
}

.scope-config-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.scope-config-block {
  min-width: 0;
  padding: 10px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
}

.scope-config-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.scope-config-title strong {
  color: var(--text);
  font-size: 12px;
}

.scope-config-title span {
  color: var(--text-muted);
  font-size: 10px;
}

.scope-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.scope-chip {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  gap: 6px;
  padding: 0 9px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px dashed var(--border-strong);
  border-radius: 5px;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.scope-chip i {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  background: #cbd5e1;
  border-radius: 50%;
}

.scope-chip:hover {
  color: var(--accent-dark);
  border-color: var(--accent-border);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.07);
}

.scope-chip.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
  border-style: solid;
  font-weight: 650;
}

.scope-chip.active i {
  background: var(--accent);
}

.permission-row-list {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-row {
  position: relative;
  display: flex;
  width: 176px;
  min-width: 150px;
  min-height: 38px;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  background: #fff;
  border: 1px dashed var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.permission-row:hover,
.permission-row:focus-within {
  z-index: 10;
}

.permission-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.permission-row.config-mode.addable {
  padding-right: 61px;
  cursor: pointer;
}

.permission-row.config-mode.addable:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.09);
}

.permission-row.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  border-style: solid;
}

.permission-row.readonly {
  cursor: default;
}

.permission-row.config-mode.active {
  padding-right: 31px;
}

.permission-row-copy {
  display: block;
  min-width: 0;
}

.permission-row-copy strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.permission-row-copy strong {
  color: var(--text);
  font-size: 12px;
  line-height: 1.25;
}

.permission-code-tooltip {
  position: absolute;
  bottom: calc(100% + 7px);
  left: 7px;
  z-index: 30;
  max-width: 240px;
  padding: 5px 8px;
  overflow: hidden;
  color: #fff;
  background: #273244;
  border-radius: 4px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.18);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 10px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transform: translateY(3px);
  visibility: hidden;
  transition: opacity 0.16s ease, transform 0.16s ease, visibility 0.16s ease;
}

.permission-code-tooltip::after {
  position: absolute;
  top: 100%;
  left: 10px;
  width: 0;
  height: 0;
  border-top: 5px solid #273244;
  border-right: 5px solid transparent;
  border-left: 5px solid transparent;
  content: '';
}

.permission-row:hover .permission-code-tooltip,
.permission-row:focus-visible .permission-code-tooltip,
.permission-row:focus-within .permission-code-tooltip {
  opacity: 1;
  transform: translateY(0);
  visibility: visible;
}

.permission-add,
.permission-remove {
  position: absolute;
  top: 5px;
  right: 5px;
  display: inline-flex;
  width: 19px;
  height: 19px;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: #fff;
  border-radius: 50%;
  font: inherit;
  line-height: 1;
  cursor: pointer;
  transition: width 0.18s ease, color 0.18s ease, background 0.18s ease, border-color 0.18s ease, opacity 0.18s ease;
}

.permission-add {
  color: var(--accent-dark);
  border: 1px solid var(--accent-border);
  overflow: hidden;
  white-space: nowrap;
}

.permission-add span {
  flex: 0 0 auto;
  font-size: 14px;
  line-height: 1;
}

.permission-add em {
  width: 0;
  overflow: hidden;
  font-size: 10px;
  font-style: normal;
  font-weight: 700;
  opacity: 0;
  transition: width 0.18s ease, opacity 0.18s ease;
}

.permission-row.config-mode.addable:hover .permission-add,
.permission-add:focus-visible {
  width: 50px;
  gap: 2px;
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
  border-radius: 999px;
}

.permission-row.config-mode.addable:hover .permission-add em,
.permission-add:focus-visible em {
  width: 22px;
  opacity: 1;
}

.permission-remove {
  color: #b4232f;
  border: 1px solid #e7b3b9;
  font-size: 15px;
  opacity: 0;
  pointer-events: none;
}

.permission-row.config-mode.active:hover .permission-remove,
.permission-remove:focus-visible {
  opacity: 1;
  pointer-events: auto;
}

.permission-remove:hover {
  color: #fff;
  background: #c73543;
  border-color: #c73543;
}

@media (hover: none) {
  .permission-row.config-mode.active .permission-remove {
    opacity: 1;
    pointer-events: auto;
  }

  .permission-add {
    width: 50px;
    gap: 2px;
    color: #fff;
    background: var(--accent);
    border-color: var(--accent);
    border-radius: 999px;
  }

  .permission-add em {
    width: 22px;
    opacity: 1;
  }
}

.member-list {
  display: grid;
  gap: 7px;
  padding: 10px;
}

.member-row {
  display: flex;
  min-height: 62px;
  align-items: center;
  gap: 9px;
  padding: 9px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
}

.member-row:hover,
.member-row.selected {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.member-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.member-copy strong,
.member-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-copy strong {
  color: var(--text);
  font-size: 13px;
}

.member-copy small {
  color: var(--text-muted);
  font-size: 11px;
}

.member-row .member-account-status {
  min-width: 42px;
  text-align: right;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (max-width: 1180px) {
  .role-workspace {
    grid-template-columns: 1fr;
  }

  .permission-member-layout {
    grid-template-columns: 1fr;
  }

  .group-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .permission-category-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .page-root {
    padding: 0;
  }

  .role-tabs {
    min-height: 48px;
    padding-right: 6px;
  }

  .role-tab-scroll {
    padding-left: 5px;
  }

  .role-tab {
    min-width: 122px;
    height: 38px;
    padding: 0 9px;
  }

  .add-role-button {
    padding: 0 9px;
    font-size: 12px;
  }

  .role-context {
    align-items: flex-start;
    flex-direction: column;
  }

  .role-context-actions {
    width: 100%;
  }

  .role-context-actions .button {
    flex: 1;
  }

  .box-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .box-actions {
    width: 100%;
  }

  .box-actions .button,
  .box-actions .member-search {
    flex: 1;
  }

  .member-search {
    width: auto;
  }

  .permission-row-list {
    gap: 6px;
  }

  .permission-row {
    width: calc(50% - 3px);
    min-width: 0;
  }

  .picker-grid,
  .member-picker-list {
    grid-template-columns: 1fr;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .button {
    flex: 1;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .group-list,
  .permission-grid,
  .drawer-permissions,
  .member-check-list,
  .scope-config-grid {
    grid-template-columns: 1fr;
  }

  .detail-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .detail-actions {
    width: 100%;
  }

  .detail-actions .button {
    flex: 1;
  }

  .detail-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-summary div:nth-child(2) {
    border-right: 0;
  }

  .detail-summary div:nth-child(-n + 2) {
    border-bottom: 1px solid var(--border);
  }

  .detail-section {
    padding-right: 14px;
    padding-left: 14px;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .section-count {
    margin-top: 0 !important;
  }

  .member-account-status {
    display: none;
  }

  .modal-layer {
    align-items: flex-start;
    padding: 16px;
  }

  .edit-modal {
    width: calc(100vw - 32px);
    max-height: calc(100vh - 32px);
  }

  .permission-config-modal {
    width: calc(100vw - 32px);
    max-height: calc(100vh - 32px);
  }

  .permission-modal-toolbar {
    align-items: stretch;
    flex-direction: column;
    padding-right: 16px;
    padding-left: 16px;
  }

  .permission-modal-search {
    width: 100%;
  }

  .permission-modal-actions {
    justify-content: flex-end;
  }

  .permission-modal-body {
    padding-right: 16px;
    padding-left: 16px;
  }

  .permission-modal-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .permission-modal-footer > div {
    width: 100%;
    justify-content: flex-end;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-right: 16px;
    padding-left: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .access-policy-grid {
    grid-template-columns: 1fr;
  }

  .field-wide {
    grid-column: auto;
  }
}

@media (max-width: 520px) {
  .permission-category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .permission-modal-title p {
    white-space: normal;
  }

  .permission-modal-grid {
    grid-template-columns: 1fr;
  }

  .permission-row {
    width: 100%;
  }
}

@media (max-width: 360px) {
  .permission-category-grid {
    grid-template-columns: 1fr;
  }
}
</style>
