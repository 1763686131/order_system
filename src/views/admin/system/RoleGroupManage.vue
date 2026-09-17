<template>
  <div class="page-root role-group-page">
    <header class="page-header">
      <div>
        <div class="breadcrumb">系统设置 / 权限管理</div>
        <div class="title-row">
          <h1>角色组管理</h1>
          <span class="demo-tag">本地演示数据</span>
        </div>
        <p>按岗位维护权限模板，员工只需加入角色组即可获得对应权限。</p>
      </div>
      <div class="header-actions">
        <button class="button button-secondary" type="button" title="刷新角色组" @click="refreshGroups">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 11a8.1 8.1 0 0 0-14.8-3.8L3 10"></path>
            <path d="M3 4v6h6"></path>
            <path d="M4 13a8.1 8.1 0 0 0 14.8 3.8L21 14"></path>
            <path d="M21 20v-6h-6"></path>
          </svg>
          刷新
        </button>
        <button class="button button-primary" type="button" @click="openCreate">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 5v14"></path>
            <path d="M5 12h14"></path>
          </svg>
          新建角色组
        </button>
      </div>
    </header>

    <section class="metric-grid" aria-label="角色组概况">
      <article class="metric-card">
        <span class="metric-label">角色组总数</span>
        <strong>{{ roleGroups.length }}</strong>
        <span class="metric-note">按岗位职责拆分</span>
      </article>
      <article class="metric-card">
        <span class="metric-label">已启用</span>
        <strong>{{ enabledGroupCount }}</strong>
        <span class="metric-note success-text">可绑定员工账号</span>
      </article>
      <article class="metric-card">
        <span class="metric-label">角色成员关系</span>
        <strong>{{ memberLinkCount }}</strong>
        <span class="metric-note">员工可加入多个角色组</span>
      </article>
      <article class="metric-card">
        <span class="metric-label">权限目录</span>
        <strong>{{ permissionTotal }}</strong>
        <span class="metric-note">按业务模块统一编码</span>
      </article>
    </section>

    <section class="role-workspace">
      <div class="group-panel">
        <div class="panel-header">
          <div>
            <h2>角色组列表</h2>
            <span>{{ roleGroups.length }} 个角色组</span>
          </div>
          <button class="icon-button" type="button" title="新建角色组" @click="openCreate">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
          </button>
        </div>

        <div class="group-list">
          <button
            v-for="group in roleGroups"
            :key="group.id"
            type="button"
            class="group-item"
            :class="{ selected: group.id === selectedGroupId }"
            @click="selectedGroupId = group.id"
          >
            <span :class="['group-icon', group.tone]">{{ group.name.slice(0, 1) }}</span>
            <span class="group-copy">
              <strong>{{ group.name }}</strong>
              <small>{{ group.description }}</small>
              <span class="group-meta">
                {{ group.memberIds.length }} 名成员
                <i></i>
                {{ group.permissions.length }} 项权限
              </span>
            </span>
            <span :class="['mini-status', group.status === 'enabled' ? 'enabled' : 'disabled']">
              {{ group.status === 'enabled' ? '启用' : '停用' }}
            </span>
          </button>
        </div>
      </div>

      <div v-if="selectedGroup" class="detail-panel">
        <div class="detail-header">
          <div class="detail-title">
            <span :class="['group-icon large', selectedGroup.tone]">{{ selectedGroup.name.slice(0, 1) }}</span>
            <div>
              <div class="title-row">
                <h2>{{ selectedGroup.name }}</h2>
                <span :class="['status-badge', selectedGroup.status === 'enabled' ? 'status-success' : 'status-disabled']">
                  <i></i>{{ selectedGroup.status === 'enabled' ? '已启用' : '已停用' }}
                </span>
              </div>
              <p>{{ selectedGroup.description }}</p>
              <span class="code-label">{{ selectedGroup.code }}</span>
            </div>
          </div>
          <div class="detail-actions">
            <button class="button button-secondary" type="button" @click="toggleSelectedGroup">
              {{ selectedGroup.status === 'enabled' ? '停用角色组' : '启用角色组' }}
            </button>
            <button class="button button-primary" type="button" @click="openEdit(selectedGroup)">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m4 16-.8 4.8L8 20l10.8-10.8a2.1 2.1 0 0 0-3-3L4 16Z"></path>
                <path d="m14.5 7.5 2 2"></path>
              </svg>
              编辑角色组
            </button>
          </div>
        </div>

        <div class="detail-summary">
          <div>
            <span>成员数量</span>
            <strong>{{ selectedGroup.memberIds.length }}</strong>
          </div>
          <div>
            <span>权限数量</span>
            <strong>{{ selectedGroup.permissions.length }}</strong>
          </div>
          <div>
            <span>创建时间</span>
            <strong>{{ selectedGroup.createdAt }}</strong>
          </div>
          <div>
            <span>最近调整</span>
            <strong>{{ selectedGroup.updatedAt }}</strong>
          </div>
        </div>

        <section class="detail-section">
          <div class="section-heading">
            <div>
              <h3>权限目录</h3>
              <span>权限编码后续由前后端共用</span>
            </div>
            <span class="section-count">{{ selectedGroup.permissions.length }} / {{ permissionTotal }}</span>
          </div>
          <div class="permission-grid">
            <article v-for="module in permissionModules" :key="module.id" class="permission-module">
              <div class="module-heading">
                <span :class="['module-dot', module.tone]"></span>
                <div>
                  <strong>{{ module.name }}</strong>
                  <small>{{ module.description }}</small>
                </div>
              </div>
              <div class="permission-list">
                <button
                  v-for="permission in module.permissions"
                  :key="permission.id"
                  type="button"
                  class="permission-chip"
                  :class="{ active: selectedGroup.permissions.includes(permission.id) }"
                  @click="togglePermission(selectedGroup, permission.id)"
                >
                  <span class="permission-check">{{ selectedGroup.permissions.includes(permission.id) ? '✓' : '' }}</span>
                  <span>{{ permission.name }}</span>
                </button>
              </div>
            </article>
          </div>
        </section>

        <section class="detail-section members-section">
          <div class="section-heading">
            <div>
              <h3>角色组成员</h3>
              <span>姓名、头像、工号从员工花名册关联读取</span>
            </div>
            <button class="text-button" type="button" @click="openEdit(selectedGroup)">管理成员</button>
          </div>
          <div class="member-table">
            <div v-for="member in selectedMembers" :key="member.id" class="member-row">
              <div class="member-info">
                <span class="avatar" :style="avatarStyle(member)">{{ member.name.slice(0, 1) }}</span>
                <div>
                  <strong>{{ member.name }}</strong>
                  <span>{{ member.employeeNo }} · {{ member.department }}</span>
                </div>
              </div>
              <span :class="['member-account-status', member.accountStatus === 'active' ? 'active' : 'pending']">
                {{ member.accountStatus === 'active' ? '账号正常' : '待完善账号' }}
              </span>
              <button class="text-button danger-text" type="button" @click="removeMember(member.id)">移出</button>
            </div>
            <div v-if="selectedMembers.length === 0" class="member-empty">
              <strong>暂无成员</strong>
              <span>编辑角色组后即可添加员工</span>
            </div>
          </div>
        </section>
      </div>
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
      <div v-if="drawerVisible" class="drawer-layer" @click.self="closeDrawer">
        <aside class="edit-drawer" role="dialog" aria-modal="true" aria-labelledby="role-drawer-title">
          <div class="drawer-header">
            <div>
              <span class="drawer-eyebrow">{{ editingGroup ? '编辑角色组' : '新建角色组' }}</span>
              <h2 id="role-drawer-title">{{ editingGroup ? draft.name : '新建角色组' }}</h2>
            </div>
            <button class="icon-button" type="button" title="关闭" @click="closeDrawer">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </div>

          <div class="drawer-body">
            <section class="form-section">
              <div class="section-heading">
                <h3>角色组信息</h3>
                <span>岗位职责模板</span>
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

            <section class="form-section">
              <div class="section-heading">
                <h3>权限配置</h3>
                <span>点击勾选业务动作</span>
              </div>
              <div class="drawer-permissions">
                <div v-for="module in permissionModules" :key="module.id" class="drawer-module">
                  <div class="drawer-module-title">
                    <span :class="['module-dot', module.tone]"></span>
                    <strong>{{ module.name }}</strong>
                  </div>
                  <label v-for="permission in module.permissions" :key="permission.id" class="check-item compact">
                    <input v-model="draft.permissions" type="checkbox" :value="permission.id" />
                    <span class="check-mark"></span>
                    <span>
                      <strong>{{ permission.name }}</strong>
                      <small>{{ permission.id }}</small>
                    </span>
                  </label>
                </div>
              </div>
            </section>

            <section class="form-section">
              <div class="section-heading">
                <h3>绑定员工</h3>
                <span>同一员工可以加入多个角色组</span>
              </div>
              <div class="member-check-list">
                <label v-for="member in memberCatalog" :key="member.id" class="member-check-item">
                  <input v-model="draft.memberIds" type="checkbox" :value="member.id" />
                  <span class="avatar small" :style="avatarStyle(member)">{{ member.name.slice(0, 1) }}</span>
                  <span>
                    <strong>{{ member.name }}</strong>
                    <small>{{ member.employeeNo }} · {{ member.department }}</small>
                  </span>
                </label>
              </div>
            </section>
          </div>

          <div class="drawer-footer">
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

function togglePermission(group, permissionId) {
  const index = group.permissions.indexOf(permissionId)
  if (index === -1) {
    group.permissions.push(permissionId)
  } else {
    group.permissions.splice(index, 1)
  }
  group.updatedAt = '2026-09-17'
  showNotice('权限配置已更新')
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
  padding: 20px;
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
.drawer-footer {
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

.drawer-layer {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.35);
}

.edit-drawer {
  display: flex;
  width: min(680px, 100vw);
  height: 100%;
  flex-direction: column;
  background: #fff;
  box-shadow: -12px 0 32px rgba(15, 23, 42, 0.16);
}

.drawer-header {
  min-height: 78px;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.drawer-header h2 {
  font-size: 18px;
}

.drawer-body {
  flex: 1;
  padding: 20px 22px;
  overflow-y: auto;
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

.drawer-footer {
  justify-content: flex-end;
  gap: 8px;
  padding: 13px 22px;
  border-top: 1px solid var(--border);
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

  .group-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .page-root {
    padding: 14px;
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

  .drawer-header,
  .drawer-body,
  .drawer-footer {
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
</style>
