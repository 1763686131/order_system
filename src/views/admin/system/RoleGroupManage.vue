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
        </div>
      </div>
      <div class="role-context-actions">
        <button class="button button-secondary" type="button" @click="toggleSelectedGroup">
          {{ selectedGroup.status === 'enabled' ? '停用' : '启用' }}
        </button>
        <button class="button button-ghost" type="button" @click="openEdit(selectedGroup)">编辑信息</button>
      </div>
    </div>

    <section v-if="selectedGroup" class="permission-member-layout">
      <section class="permission-panel">
        <div class="box-header">
          <div class="box-title">
            <h2>权限组</h2>
            <span>{{ selectedGroup.permissions.length }} / {{ permissionTotal }} 项</span>
          </div>
          <div class="box-actions">
            <button
              class="button button-secondary compact-button"
              :class="{ 'mode-active': permissionAddMode }"
              type="button"
              @click="togglePermissionAddMode"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14"></path>
                <path d="M5 12h14"></path>
              </svg>
              {{ permissionAddMode ? '完成添加' : '添加权限' }}
            </button>
            <button
              class="button button-danger compact-button"
              :class="{ 'mode-active': permissionDeleteMode }"
              type="button"
              :disabled="selectedGroup.permissions.length === 0"
              @click="togglePermissionDeleteMode"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 7h14"></path>
                <path d="M10 11v6"></path>
                <path d="M14 11v6"></path>
                <path d="m9 7 .8-2h4.4l.8 2"></path>
                <path d="m7 7 .7 13h8.6L17 7"></path>
              </svg>
              {{ permissionDeleteMode ? '完成删除' : '删除权限' }}
            </button>
          </div>
        </div>

        <div class="permission-module-list">
          <article v-for="module in displayedPermissionModules" :key="module.id" class="permission-module-box">
            <div class="module-heading">
              <span :class="['module-dot', module.tone]"></span>
              <div>
                <strong>{{ module.name }}</strong>
                <small>{{ module.description }}</small>
              </div>
            </div>
            <div class="permission-row-list">
              <div
                v-for="permission in module.permissions"
                :key="permission.id"
                class="permission-row"
                :class="{
                  active: selectedGroup.permissions.includes(permission.id),
                  addable: !selectedGroup.permissions.includes(permission.id),
                  'add-mode': permissionAddMode,
                  'delete-mode': permissionDeleteMode
                }"
                @click="handlePermissionRowClick(permission.id)"
              >
                <span class="permission-row-copy">
                  <strong>{{ permission.name }}</strong>
                  <small>{{ permission.id }}</small>
                </span>
                <div v-if="permissionDeleteMode && selectedGroup.permissions.includes(permission.id)" class="permission-remove-wrap">
                  <button
                    class="permission-remove"
                    type="button"
                    :aria-label="`删除${permission.name}`"
                    @click.stop="openPermissionDeleteConfirm(permission.id)"
                  >
                    ×
                  </button>
                  <div
                    v-if="permissionDeleteTarget === permission.id"
                    class="permission-confirm-popover"
                    @click.stop
                  >
                    <strong>确定删除吗？</strong>
                    <div>
                      <button type="button" @click="confirmPermissionDelete">删除</button>
                      <button type="button" @click="cancelPermissionDelete">取消</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </div>
        <div v-if="displayedPermissionModules.length === 0" class="permission-empty">
          <strong>暂未配置权限</strong>
          <span>点击“添加权限”查看全部权限</span>
        </div>
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
            <span :class="['member-account-status', member.accountStatus === 'active' ? 'active' : 'pending']">
              {{ member.accountStatus === 'active' ? '正常' : '待完善' }}
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
                  <input v-model.trim="draft.code" type="text" placeholder="例如 finance_staff" />
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
import { computed, ref } from 'vue'

const permissionModules = [
  {
    id: 'front',
    name: '前端触屏端',
    description: '触屏端入口和作业操作',
    tone: 'green',
    permissions: [
      { id: 'front.access', name: '访问触屏端' },
      { id: 'front.material_outbound.create', name: '录入原材料出库' },
      { id: 'front.material_outbound.view', name: '查看本人出库记录' }
    ]
  },
  {
    id: 'sales',
    name: '销售业务',
    description: '客户、订单和物流信息',
    tone: 'blue',
    permissions: [
      { id: 'sales.customer.view', name: '查看客户' },
      { id: 'sales.order.create', name: '新增销售订单' },
      { id: 'sales.order.edit', name: '修改销售订单' },
      { id: 'sales.order.audit', name: '审核销售订单' }
    ]
  },
  {
    id: 'inventory',
    name: '库存管理',
    description: '入库、出库和库存流水',
    tone: 'orange',
    permissions: [
      { id: 'inventory.view', name: '查看库存' },
      { id: 'inventory.inbound.create', name: '录入入库单' },
      { id: 'inventory.outbound.create', name: '录入出库单' },
      { id: 'inventory.audit', name: '审核库存单据' }
    ]
  },
  {
    id: 'finance',
    name: '财务管理',
    description: '应收、收款和对账',
    tone: 'purple',
    permissions: [
      { id: 'finance.receivable.view', name: '查看应收欠款' },
      { id: 'finance.payment.create', name: '录入收款单' },
      { id: 'finance.payment.audit', name: '审核收款单' },
      { id: 'finance.reconciliation.view', name: '查看对账记录' }
    ]
  },
  {
    id: 'system',
    name: '系统管理',
    description: '账号、角色和基础配置',
    tone: 'red',
    permissions: [
      { id: 'system.account.manage', name: '管理员工账号' },
      { id: 'system.role.manage', name: '管理角色组' },
      { id: 'system.store.manage', name: '管理门店' },
      { id: 'system.settings.manage', name: '管理系统设置' }
    ]
  }
]

const allPermissionIds = permissionModules.flatMap(module => module.permissions.map(permission => permission.id))

const memberCatalog = [
  { id: 1001, name: '张三', employeeNo: 'E-0001', department: '仓储部', accountStatus: 'active', avatarColor: '#d8f4ea' },
  { id: 1002, name: '李四', employeeNo: 'E-0002', department: '财务部', accountStatus: 'active', avatarColor: '#e2edff' },
  { id: 1003, name: '王五', employeeNo: 'E-0003', department: '销售部', accountStatus: 'pending', avatarColor: '#fff0d7' },
  { id: 1004, name: '赵六', employeeNo: 'E-0004', department: '人事行政', accountStatus: 'disabled', avatarColor: '#eee4ff' }
]

const roleGroups = ref([
  {
    id: 'system_admin',
    code: 'system_admin',
    name: '系统管理员',
    description: '负责系统基础资料、账号权限和运行配置维护。',
    tone: 'red',
    status: 'enabled',
    memberIds: [1004],
    permissions: allPermissionIds,
    createdAt: '2026-09-01',
    updatedAt: '2026-09-17'
  },
  {
    id: 'finance',
    code: 'finance_staff',
    name: '财务人员',
    description: '负责应收、收款、银行账户和物流对账业务。',
    tone: 'purple',
    status: 'enabled',
    memberIds: [1002],
    permissions: [
      'finance.receivable.view',
      'finance.payment.create',
      'finance.reconciliation.view',
      'sales.customer.view'
    ],
    createdAt: '2026-09-02',
    updatedAt: '2026-09-16'
  },
  {
    id: 'warehouse',
    code: 'warehouse_operator',
    name: '仓库操作员',
    description: '负责授权仓库内的库存查看、入库和出库录入。',
    tone: 'orange',
    status: 'enabled',
    memberIds: [1001],
    permissions: ['inventory.view', 'inventory.inbound.create', 'inventory.outbound.create'],
    createdAt: '2026-09-03',
    updatedAt: '2026-09-15'
  },
  {
    id: 'touch_staff',
    code: 'touch_staff',
    name: '触屏员工',
    description: '仅开放前端触屏端作业，不接触财务和系统管理数据。',
    tone: 'green',
    status: 'enabled',
    memberIds: [1001, 1003],
    permissions: ['front.access', 'front.material_outbound.create', 'front.material_outbound.view'],
    createdAt: '2026-09-04',
    updatedAt: '2026-09-17'
  },
  {
    id: 'sales',
    code: 'sales_staff',
    name: '销售人员',
    description: '负责客户维护、销售订单录入和订单跟进。',
    tone: 'blue',
    status: 'disabled',
    memberIds: [1003],
    permissions: ['sales.customer.view', 'sales.order.create', 'sales.order.edit'],
    createdAt: '2026-09-05',
    updatedAt: '2026-09-12'
  }
])

const selectedGroupId = ref('system_admin')
const permissionAddMode = ref(false)
const permissionDeleteMode = ref(false)
const permissionDeleteTarget = ref(null)
const selectedMemberIds = ref([])
const memberSearchQuery = ref('')
const memberSearchOpen = ref(false)
const memberToAddId = ref(null)
const drawerVisible = ref(false)
const editingGroup = ref(false)
const draft = ref(createEmptyGroup())
const notice = ref('')
let noticeTimer

const selectedGroup = computed(() => roleGroups.value.find(group => group.id === selectedGroupId.value))
const selectedMembers = computed(() => {
  if (!selectedGroup.value) return []
  return memberCatalog.filter(member => selectedGroup.value.memberIds.includes(member.id))
})
const displayedPermissionModules = computed(() => {
  const permissionIds = selectedGroup.value?.permissions || []
  return permissionModules
    .map(module => ({
      ...module,
      permissions: module.permissions.filter(permission =>
        permissionAddMode.value || permissionIds.includes(permission.id)
      )
    }))
    .filter(module => module.permissions.length > 0)
})
const availableMembers = computed(() => {
  if (!selectedGroup.value) return []
  return memberCatalog.filter(member => !selectedGroup.value.memberIds.includes(member.id))
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
const enabledGroupCount = computed(() => roleGroups.value.filter(group => group.status === 'enabled').length)
const memberLinkCount = computed(() => roleGroups.value.reduce((total, group) => total + group.memberIds.length, 0))
const permissionTotal = allPermissionIds.length

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
    createdAt: '2026-09-17',
    updatedAt: '2026-09-17'
  }
}

function openCreate() {
  editingGroup.value = false
  draft.value = createEmptyGroup()
  drawerVisible.value = true
}

function selectGroup(groupId) {
  selectedGroupId.value = groupId
  permissionAddMode.value = false
  permissionDeleteMode.value = false
  permissionDeleteTarget.value = null
  selectedMemberIds.value = []
  resetMemberSearch()
}

function openEdit(group) {
  editingGroup.value = true
  draft.value = {
    ...group,
    memberIds: [...group.memberIds],
    permissions: [...group.permissions]
  }
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
}

function saveGroup() {
  if (!draft.value.name) {
    showNotice('请先填写角色组名称')
    return
  }

  const payload = {
    ...draft.value,
    code: draft.value.code || draft.value.name.toLowerCase().replace(/\s+/g, '_'),
    memberIds: [...draft.value.memberIds],
    permissions: [...draft.value.permissions],
    updatedAt: '2026-09-17'
  }

  if (editingGroup.value) {
    const index = roleGroups.value.findIndex(group => group.id === payload.id)
    if (index !== -1) roleGroups.value[index] = payload
    showNotice('角色组已更新')
  } else {
    payload.id = `role_${Date.now()}`
    roleGroups.value.push(payload)
    selectedGroupId.value = payload.id
    showNotice('角色组已创建')
  }
  closeDrawer()
}

function togglePermissionAddMode() {
  permissionAddMode.value = !permissionAddMode.value
  permissionDeleteMode.value = false
  permissionDeleteTarget.value = null
  if (permissionAddMode.value) showNotice('点击虚线权限即可添加')
}

function togglePermissionDeleteMode() {
  permissionDeleteMode.value = !permissionDeleteMode.value
  permissionAddMode.value = false
  permissionDeleteTarget.value = null
}

function handlePermissionRowClick(permissionId) {
  if (!permissionAddMode.value || permissionDeleteMode.value) return
  togglePermission(permissionId)
}

function togglePermission(permissionId) {
  if (!selectedGroup.value || permissionDeleteMode.value || !permissionAddMode.value) return
  if (selectedGroup.value.permissions.includes(permissionId)) return
  selectedGroup.value.permissions.push(permissionId)
  selectedGroup.value.updatedAt = '2026-09-17'
  showNotice('权限添加成功')
}

function openPermissionDeleteConfirm(permissionId) {
  permissionDeleteTarget.value = permissionDeleteTarget.value === permissionId ? null : permissionId
}

function confirmPermissionDelete() {
  if (!selectedGroup.value || !permissionDeleteTarget.value) return
  selectedGroup.value.permissions = selectedGroup.value.permissions.filter(
    permissionId => permissionId !== permissionDeleteTarget.value
  )
  selectedGroup.value.updatedAt = '2026-09-17'
  permissionDeleteTarget.value = null
  showNotice('权限已删除')
}

function cancelPermissionDelete() {
  permissionDeleteTarget.value = null
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

function addSelectedMember() {
  if (!selectedGroup.value || !memberToAddId.value) return
  selectedGroup.value.memberIds.push(memberToAddId.value)
  selectedGroup.value.updatedAt = '2026-09-17'
  resetMemberSearch()
  showNotice('成员添加成功')
}

function resetMemberSearch() {
  memberSearchQuery.value = ''
  memberSearchOpen.value = false
  memberToAddId.value = null
}

function deleteSelectedMembers() {
  if (!selectedGroup.value || selectedMemberIds.value.length === 0) return
  selectedGroup.value.memberIds = selectedGroup.value.memberIds.filter(
    memberId => !selectedMemberIds.value.includes(memberId)
  )
  selectedGroup.value.updatedAt = '2026-09-17'
  selectedMemberIds.value = []
  showNotice('已删除选中的成员')
}

function toggleSelectedGroup() {
  if (!selectedGroup.value) return
  selectedGroup.value.status = selectedGroup.value.status === 'enabled' ? 'disabled' : 'enabled'
  selectedGroup.value.updatedAt = '2026-09-17'
  showNotice(selectedGroup.value.status === 'enabled' ? '角色组已启用' : '角色组已停用')
}

function removeMember(memberId) {
  if (!selectedGroup.value) return
  const index = selectedGroup.value.memberIds.indexOf(memberId)
  if (index !== -1) selectedGroup.value.memberIds.splice(index, 1)
  selectedGroup.value.updatedAt = '2026-09-17'
  showNotice('员工已移出角色组')
}

function refreshGroups() {
  showNotice('演示数据已刷新')
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

function avatarStyle(member) {
  return {
    backgroundColor: member.avatarColor || '#e5e7eb',
    color: '#275a4d'
  }
}
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
.role-context-icon {
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
.role-context-icon.green {
  color: #13734f;
  background: #eaf8f1;
}

.role-tab-icon.blue,
.role-context-icon.blue {
  color: #16647a;
  background: #e7f5f8;
}

.role-tab-icon.orange,
.role-context-icon.orange {
  color: #a4510b;
  background: #fff3df;
}

.role-tab-icon.red,
.role-context-icon.red {
  color: #b4232f;
  background: #fcebed;
}

.role-tab-icon.purple,
.role-context-icon.purple {
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

.button.mode-active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-danger.mode-active {
  color: #b4232f;
  background: #fff1f2;
  border-color: #e7b3b9;
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

.permission-module-list {
  display: grid;
  gap: 8px;
  padding: 10px;
}

.permission-empty {
  display: flex;
  min-height: 150px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  color: var(--text-muted);
  text-align: center;
}

.permission-empty strong {
  color: var(--text-secondary);
  font-size: 13px;
}

.permission-empty span {
  font-size: 11px;
}

.permission-module-box {
  min-width: 0;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.permission-module-box .module-heading {
  margin-bottom: 9px;
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
  min-height: 42px;
  align-items: center;
  gap: 5px;
  padding: 6px 8px;
  background: #fff;
  border: 1px dashed var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.permission-row.add-mode.addable {
  cursor: pointer;
}

.permission-row.add-mode.addable:hover {
  background: #fbfffd;
  border-color: var(--accent-border);
  box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.08);
}

.permission-row.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  border-style: solid;
}

.permission-row-copy {
  display: block;
  min-width: 0;
}

.permission-row-copy strong,
.permission-row-copy small {
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

.permission-row-copy small {
  margin-top: 3px;
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 9px;
  line-height: 1.2;
}

.permission-remove-wrap {
  position: relative;
  flex: 0 0 auto;
}

.permission-remove {
  display: inline-flex;
  width: 19px;
  height: 19px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #b4232f;
  background: #fff;
  border: 1px solid #e7b3b9;
  border-radius: 50%;
  font: inherit;
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
}

.permission-remove:hover {
  color: #fff;
  background: #c73543;
  border-color: #c73543;
}

.permission-confirm-popover {
  position: absolute;
  right: -2px;
  bottom: calc(100% + 7px);
  z-index: 20;
  width: 142px;
  padding: 9px 10px;
  color: var(--text);
  background: #fff;
  border: 1px solid #e7b3b9;
  border-radius: 6px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.16);
  box-sizing: border-box;
}

.permission-confirm-popover::after {
  position: absolute;
  right: 7px;
  bottom: -5px;
  width: 8px;
  height: 8px;
  background: #fff;
  border-right: 1px solid #e7b3b9;
  border-bottom: 1px solid #e7b3b9;
  content: '';
  transform: rotate(45deg);
}

.permission-confirm-popover strong {
  display: block;
  font-size: 11px;
  font-weight: 650;
}

.permission-confirm-popover > div {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
  margin-top: 8px;
}

.permission-confirm-popover button {
  padding: 3px 7px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  font: inherit;
  font-size: 10px;
  cursor: pointer;
}

.permission-confirm-popover button:first-child {
  color: #fff;
  background: #c73543;
  border-color: #c73543;
}

.permission-confirm-popover button:hover {
  filter: brightness(0.97);
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
  .member-check-list {
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

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-right: 16px;
    padding-left: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-wide {
    grid-column: auto;
  }
}

@media (max-width: 520px) {
  .permission-row {
    width: 100%;
  }
}
</style>
