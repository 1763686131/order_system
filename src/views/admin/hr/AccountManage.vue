<template>
  <div class="page-root employee-account-page">
    <nav class="workspace-nav" aria-label="员工管理导航">
      <button
        class="workspace-tab"
        :class="{ active: !selectedEmployee }"
        type="button"
        @click="goToList"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6.5h16"></path>
          <path d="M4 12h16"></path>
          <path d="M4 17.5h16"></path>
        </svg>
        员工列表
      </button>
      <button
        v-if="selectedEmployee"
        class="workspace-tab employee-workspace-tab"
        :class="{ active: Boolean(selectedEmployee) }"
        type="button"
        @click="activeDetailTab = 'profile'"
      >
        <span class="tab-avatar" :style="avatarStyle(selectedEmployee)">{{ selectedEmployee.displayName.slice(0, 1) }}</span>
        {{ selectedEmployee.displayName }}
        <span class="tab-close" title="返回员工列表" @click.stop="goToList">×</span>
      </button>
    </nav>

    <template v-if="!selectedEmployee">
      <section class="records-panel">
        <div class="records-toolbar">
          <div class="records-heading">
            <h2>员工列表</h2>
            <span class="record-count">共 {{ filteredEmployees.length }} 条记录</span>
          </div>
          <div class="employee-toolbar">
            <div class="toolbar-filters">
              <label class="toolbar-search">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="11" cy="11" r="6.5"></circle>
                  <path d="m16 16 4.5 4.5"></path>
                </svg>
                <input v-model.trim="filters.keyword" type="search" placeholder="搜索姓名 / 工号 / 账号" />
              </label>
              <select v-model="filters.department" title="按部门筛选">
                <option value="">全部部门</option>
                <option v-for="department in departments" :key="department" :value="department">
                  {{ department }}
                </option>
              </select>
              <select v-model="filters.employmentStatus" title="按在职状态筛选">
                <option value="">全部在职状态</option>
                <option value="active">在职</option>
                <option value="probation">试用期</option>
                <option value="leave">休假</option>
                <option value="resigned">离职</option>
              </select>
              <select v-model="filters.accountStatus" title="按账号状态筛选">
                <option value="">全部账号状态</option>
                <option value="active">正常</option>
                <option value="pending">待开通</option>
                <option value="disabled">已停用</option>
              </select>
              <button class="toolbar-reset" type="button" @click="resetFilters">重置</button>
            </div>
            <div class="toolbar-actions">
              <button class="icon-button toolbar-refresh" type="button" title="刷新列表" @click="refreshList">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 11a8.1 8.1 0 0 0-14.8-3.8L3 10"></path>
                  <path d="M3 4v6h6"></path>
                  <path d="M4 13a8.1 8.1 0 0 0 14.8 3.8L21 14"></path>
                  <path d="M21 20v-6h-6"></path>
                </svg>
              </button>
              <button class="button button-secondary" type="button" @click="exportPreview">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 3v12"></path>
                  <path d="m7 10 5 5 5-5"></path>
                  <path d="M5 21h14"></path>
                </svg>
                导出
              </button>
              <button class="button button-primary" type="button" @click="openCreate">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 5v14"></path>
                  <path d="M5 12h14"></path>
                </svg>
                新增员工
              </button>
            </div>
          </div>
        </div>

      <div class="table-scroll">
        <table class="employee-table">
          <thead>
            <tr>
              <th class="col-employee">员工信息</th>
              <th class="col-account">登录账号</th>
              <th class="col-job">部门 / 职位</th>
              <th class="col-phone">联系电话</th>
              <th class="col-employment">在职状态</th>
              <th class="col-role">角色组</th>
              <th class="col-date">入职日期</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="employee in filteredEmployees"
              :key="employee.id"
              class="record-row"
              :class="{ 'row-resigned': employee.employmentStatus === 'resigned' }"
              tabindex="0"
              @click="openEmployee(employee)"
              @keydown.enter="openEmployee(employee)"
            >
              <td>
                <div class="employee-cell">
                  <span class="avatar" :style="avatarStyle(employee)">{{ employee.displayName.slice(0, 1) }}</span>
                  <div class="employee-copy">
                    <strong>{{ employee.displayName }}</strong>
                    <span>{{ employee.employeeNo }} · {{ employee.employmentType }}</span>
                  </div>
                </div>
              </td>
              <td>
                <div class="account-cell">
                  <strong>{{ employee.username || '未开通' }}</strong>
                  <span :class="['status-badge', accountStatusClass(employee.accountStatus)]">
                    <i></i>{{ accountStatusLabel(employee.accountStatus) }}
                  </span>
                </div>
              </td>
              <td>
                <div class="job-cell">
                  <strong>{{ employee.department }}</strong>
                  <span>{{ employee.position }}</span>
                </div>
              </td>
              <td class="tabular">{{ employee.phone }}</td>
              <td>
                <span :class="['status-badge', employmentStatusClass(employee.employmentStatus)]">
                  <i></i>{{ employmentStatusLabel(employee.employmentStatus) }}
                </span>
              </td>
              <td>
                <div class="role-list">
                  <span
                    v-for="role in employee.roleIds.slice(0, 2)"
                    :key="role"
                    :class="['role-tag', roleTone(role)]"
                  >
                    {{ roleName(role) }}
                  </span>
                  <span v-if="employee.roleIds.length > 2" class="role-more">
                    +{{ employee.roleIds.length - 2 }}
                  </span>
                  <span v-if="employee.roleIds.length === 0" class="empty-inline">未绑定</span>
                </div>
              </td>
              <td class="tabular">{{ employee.hireDate || '-' }}</td>
              <td>
                <div class="row-actions" @click.stop>
                  <button class="text-button" type="button" @click="openEmployee(employee)">查看</button>
                  <button class="text-button" type="button" @click="openEdit(employee)">编辑</button>
                  <button class="text-button" type="button" @click="toggleAccount(employee)">
                    {{ employee.accountStatus === 'disabled' ? '启用账号' : '停用账号' }}
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredEmployees.length === 0">
              <td colspan="8">
                <div class="empty-state">
                  <span class="empty-icon">—</span>
                  <strong>没有匹配的员工</strong>
                  <span>调整筛选条件后再试</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-footer">
        <span>当前为前端占位数据，后续接入员工档案与账号接口。</span>
        <span class="footer-summary">显示 {{ filteredEmployees.length }} / {{ employees.length }}</span>
      </div>
      </section>
    </template>

    <template v-else>
      <section class="employee-context">
        <div class="context-identity">
          <span class="context-avatar" :style="avatarStyle(selectedEmployee)">
            {{ selectedEmployee.displayName.slice(0, 1) }}
          </span>
          <div>
            <div class="context-title">
              <h2>{{ selectedEmployee.displayName }}</h2>
              <span :class="['status-badge', employmentStatusClass(selectedEmployee.employmentStatus)]">
                <i></i>{{ employmentStatusLabel(selectedEmployee.employmentStatus) }}
              </span>
            </div>
            <p>{{ selectedEmployee.employeeNo }} · {{ selectedEmployee.department }} · {{ selectedEmployee.position }}</p>
          </div>
        </div>
        <div class="context-actions">
          <button class="button button-secondary" type="button" @click="openEdit(selectedEmployee)">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m4 16-.8 4.8L8 20l10.8-10.8a2.1 2.1 0 0 0-3-3L4 16Z"></path>
              <path d="m14.5 7.5 2 2"></path>
            </svg>
            编辑档案
          </button>
          <button class="button button-ghost" type="button" @click="goToList">返回列表</button>
        </div>
      </section>

      <nav class="detail-tabs" aria-label="员工详情导航">
        <button
          class="detail-tab"
          :class="{ active: activeDetailTab === 'profile' }"
          type="button"
          @click="activeDetailTab = 'profile'"
        >
          员工信息
        </button>
        <button
          class="detail-tab"
          :class="{ active: activeDetailTab === 'permissions' }"
          type="button"
          @click="activeDetailTab = 'permissions'"
        >
          权限控制
          <span class="detail-tab-count">{{ selectedPermissionCount }}</span>
        </button>
      </nav>

      <section v-if="activeDetailTab === 'profile'" class="detail-content profile-content">
        <div class="detail-column">
          <article class="detail-card identity-card">
            <div class="detail-card-heading">
              <div>
                <h3>个人信息</h3>
                <span>花名册主档信息</span>
              </div>
              <span class="card-index">01</span>
            </div>
            <div class="identity-overview">
              <span class="profile-avatar" :style="avatarStyle(selectedEmployee)">
                {{ selectedEmployee.displayName.slice(0, 1) }}
              </span>
              <div>
                <strong>{{ selectedEmployee.displayName }}</strong>
                <span>{{ selectedEmployee.employeeNo }}</span>
              </div>
            </div>
            <dl class="info-grid">
              <div>
                <dt>身份证号</dt>
                <dd>{{ selectedEmployee.idCard || '未填写' }}</dd>
              </div>
              <div>
                <dt>用工类型</dt>
                <dd>{{ selectedEmployee.employmentType || '未填写' }}</dd>
              </div>
              <div>
                <dt>入职日期</dt>
                <dd class="tabular">{{ selectedEmployee.hireDate || '未填写' }}</dd>
              </div>
              <div>
                <dt>当前状态</dt>
                <dd>{{ employmentStatusLabel(selectedEmployee.employmentStatus) }}</dd>
              </div>
            </dl>
          </article>

          <article class="detail-card">
            <div class="detail-card-heading">
              <div>
                <h3>工作信息</h3>
                <span>组织归属与岗位</span>
              </div>
              <span class="card-index">02</span>
            </div>
            <dl class="info-grid">
              <div>
                <dt>所属部门</dt>
                <dd>{{ selectedEmployee.department || '未填写' }}</dd>
              </div>
              <div>
                <dt>职位</dt>
                <dd>{{ selectedEmployee.position || '未填写' }}</dd>
              </div>
              <div>
                <dt>可访问门店</dt>
                <dd>{{ selectedEmployee.storeIds.length ? scopeNames(selectedEmployee.storeIds, stores) : '未分配' }}</dd>
              </div>
              <div>
                <dt>可操作仓库</dt>
                <dd>{{ selectedEmployee.warehouseIds.length ? scopeNames(selectedEmployee.warehouseIds, warehouses) : '未分配' }}</dd>
              </div>
            </dl>
          </article>
        </div>

        <div class="detail-column">
          <article class="detail-card">
            <div class="detail-card-heading">
              <div>
                <h3>联系方式</h3>
                <span>后续人事行政资料</span>
              </div>
              <span class="card-index">03</span>
            </div>
            <dl class="info-grid single-column">
              <div>
                <dt>联系电话</dt>
                <dd class="tabular">{{ selectedEmployee.phone || '未填写' }}</dd>
              </div>
              <div>
                <dt>家庭住址</dt>
                <dd>{{ selectedEmployee.currentAddress || '未填写' }}</dd>
              </div>
              <div>
                <dt>紧急联系人</dt>
                <dd>{{ selectedEmployee.emergencyContact || '未填写' }}</dd>
              </div>
              <div>
                <dt>紧急联系电话</dt>
                <dd class="tabular">{{ selectedEmployee.emergencyPhone || '未填写' }}</dd>
              </div>
            </dl>
          </article>

          <article class="detail-card account-summary-card">
            <div class="detail-card-heading">
              <div>
                <h3>登录账号</h3>
                <span>账号状态和角色组概览</span>
              </div>
              <span class="card-index">04</span>
            </div>
            <div class="account-summary">
              <div>
                <span class="summary-label">账号</span>
                <strong>{{ selectedEmployee.username || '暂未开通' }}</strong>
              </div>
              <span :class="['status-badge', accountStatusClass(selectedEmployee.accountStatus)]">
                <i></i>{{ accountStatusLabel(selectedEmployee.accountStatus) }}
              </span>
            </div>
            <div class="assigned-role-list">
              <span class="summary-label">已绑定角色组</span>
              <div class="role-list">
                <span
                  v-for="roleId in selectedEmployee.roleIds"
                  :key="roleId"
                  :class="['role-tag', roleTone(roleId)]"
                >
                  {{ roleName(roleId) }}
                </span>
                <span v-if="selectedEmployee.roleIds.length === 0" class="empty-inline">暂未绑定角色组</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="detail-content permission-content">
        <article class="permission-summary-card">
          <div>
            <span class="summary-label">当前权限来源</span>
            <strong>{{ selectedEmployee.roleIds.length }} 个角色组</strong>
            <p>权限由角色组汇总，员工档案只保存绑定关系。</p>
          </div>
          <button class="button button-secondary" type="button" @click="openEdit(selectedEmployee)">
            调整角色组
          </button>
        </article>

        <div class="permission-layout">
          <div class="permission-main">
            <div class="content-heading">
              <div>
                <h3>权限矩阵</h3>
                <span>点击权限项可预览当前员工获得的业务动作</span>
              </div>
              <span class="permission-total">{{ selectedPermissionCount }} 项已生效</span>
            </div>
            <div class="employee-permission-grid">
              <article v-for="module in selectedPermissionModules" :key="module.id" class="employee-permission-module">
                <div class="module-heading">
                  <span :class="['module-dot', module.tone]"></span>
                  <div>
                    <strong>{{ module.name }}</strong>
                    <small>{{ module.description }}</small>
                  </div>
                </div>
                <div class="employee-permission-list">
                  <span
                    v-for="permission in module.permissions"
                    :key="permission.id"
                    :class="['employee-permission-chip', { active: permission.enabled }]"
                  >
                    <span>{{ permission.enabled ? '✓' : '—' }}</span>
                    {{ permission.name }}
                  </span>
                </div>
              </article>
            </div>
          </div>

          <aside class="permission-side">
            <article class="detail-card">
              <div class="detail-card-heading">
                <div>
                  <h3>角色组来源</h3>
                  <span>员工绑定关系</span>
                </div>
              </div>
              <div class="source-role-list">
                <div v-for="roleId in selectedEmployee.roleIds" :key="roleId" class="source-role-item">
                  <span :class="['role-dot', roleTone(roleId)]"></span>
                  <div>
                    <strong>{{ roleName(roleId) }}</strong>
                    <span>{{ roleDescription(roleId) }}</span>
                  </div>
                </div>
                <div v-if="selectedEmployee.roleIds.length === 0" class="side-empty">暂未绑定角色组</div>
              </div>
            </article>

            <article class="detail-card">
              <div class="detail-card-heading">
                <div>
                  <h3>数据范围</h3>
                  <span>门店、仓库和本人数据</span>
                </div>
              </div>
              <div class="scope-summary">
                <div>
                  <span>门店范围</span>
                  <strong>{{ selectedEmployee.storeIds.length ? scopeNames(selectedEmployee.storeIds, stores) : '未分配' }}</strong>
                </div>
                <div>
                  <span>仓库范围</span>
                  <strong>{{ selectedEmployee.warehouseIds.length ? scopeNames(selectedEmployee.warehouseIds, warehouses) : '未分配' }}</strong>
                </div>
              </div>
            </article>
          </aside>
        </div>
      </section>
    </template>

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
        <aside class="edit-drawer" role="dialog" aria-modal="true" aria-labelledby="employee-drawer-title">
          <div class="drawer-header">
            <div>
              <span class="drawer-eyebrow">{{ editingEmployee ? '编辑档案' : '新建档案' }}</span>
              <h2 id="employee-drawer-title">{{ editingEmployee ? draft.displayName : '新增员工' }}</h2>
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
                <h3>基本信息</h3>
                <span>花名册主档</span>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>姓名 <em>*</em></span>
                  <input v-model.trim="draft.displayName" type="text" placeholder="请输入员工姓名" />
                </label>
                <label class="field">
                  <span>工号</span>
                  <input v-model.trim="draft.employeeNo" type="text" placeholder="例如 E-0008" />
                </label>
                <label class="field">
                  <span>身份证号</span>
                  <input v-model.trim="draft.idCard" type="text" placeholder="建议后端加密存储" />
                </label>
                <label class="field">
                  <span>用工类型</span>
                  <select v-model="draft.employmentType">
                    <option value="正式">正式</option>
                    <option value="试用">试用</option>
                    <option value="兼职">兼职</option>
                    <option value="外包">外包</option>
                  </select>
                </label>
                <label class="field">
                  <span>在职状态</span>
                  <select v-model="draft.employmentStatus">
                    <option value="active">在职</option>
                    <option value="probation">试用期</option>
                    <option value="leave">休假</option>
                    <option value="resigned">离职</option>
                  </select>
                </label>
                <label class="field">
                  <span>入职日期</span>
                  <input v-model="draft.hireDate" type="date" />
                </label>
              </div>
            </section>

            <section class="form-section">
              <div class="section-heading">
                <h3>工作信息</h3>
                <span>用于组织和后续人事接口</span>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>部门</span>
                  <select v-model="draft.department">
                    <option v-for="department in departments" :key="department" :value="department">
                      {{ department }}
                    </option>
                  </select>
                </label>
                <label class="field">
                  <span>职位</span>
                  <input v-model.trim="draft.position" type="text" placeholder="请输入职位" />
                </label>
                <label class="field field-wide">
                  <span>家庭住址</span>
                  <input v-model.trim="draft.currentAddress" type="text" placeholder="请输入现居住地址" />
                </label>
              </div>
            </section>

            <section class="form-section">
              <div class="section-heading">
                <h3>账号绑定</h3>
                <span>账号和员工档案分开存储</span>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>登录账号</span>
                  <input v-model.trim="draft.username" type="text" placeholder="未填写则暂不开通" />
                </label>
                <label class="field">
                  <span>账号状态</span>
                  <select v-model="draft.accountStatus">
                    <option value="active">正常</option>
                    <option value="pending">待开通</option>
                    <option value="disabled">已停用</option>
                  </select>
                </label>
                <label class="field">
                  <span>紧急联系人</span>
                  <input v-model.trim="draft.emergencyContact" type="text" placeholder="姓名 / 称谓" />
                </label>
                <label class="field">
                  <span>紧急联系电话</span>
                  <input v-model.trim="draft.emergencyPhone" type="text" placeholder="联系电话" />
                </label>
              </div>
            </section>

            <section class="form-section">
              <div class="section-heading">
                <h3>角色组绑定</h3>
                <span>员工加入角色组后获得对应权限</span>
              </div>
              <div class="check-grid">
                <label v-for="role in roleGroups" :key="role.id" class="check-item">
                  <input v-model="draft.roleIds" type="checkbox" :value="role.id" />
                  <span class="check-mark"></span>
                  <span>
                    <strong>{{ role.name }}</strong>
                    <small>{{ role.description }}</small>
                  </span>
                </label>
              </div>
            </section>

            <section class="form-section">
              <div class="section-heading">
                <h3>数据范围</h3>
                <span>先用门店 / 仓库占位，后端接入后按 ID 保存</span>
              </div>
              <div class="scope-block">
                <span class="scope-label">可访问门店</span>
                <div class="scope-list">
                  <label v-for="store in stores" :key="store.id" class="scope-item">
                    <input v-model="draft.storeIds" type="checkbox" :value="store.id" />
                    <span>{{ store.name }}</span>
                  </label>
                </div>
              </div>
              <div class="scope-block">
                <span class="scope-label">可操作仓库</span>
                <div class="scope-list">
                  <label v-for="warehouse in warehouses" :key="warehouse.id" class="scope-item">
                    <input v-model="draft.warehouseIds" type="checkbox" :value="warehouse.id" />
                    <span>{{ warehouse.name }}</span>
                  </label>
                </div>
              </div>
            </section>
          </div>

          <div class="drawer-footer">
            <button class="button button-secondary" type="button" @click="closeDrawer">取消</button>
            <button class="button button-primary" type="button" @click="saveEmployee">
              {{ editingEmployee ? '保存修改' : '创建员工' }}
            </button>
          </div>
        </aside>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const departments = ['仓储部', '财务部', '销售部', '人事行政', '运营部']

const roleGroups = [
  { id: 'system_admin', name: '系统管理员', tone: 'red', description: '系统基础资料和账号权限' },
  { id: 'finance', name: '财务人员', tone: 'blue', description: '应收、收款和财务对账' },
  { id: 'warehouse', name: '仓库操作员', tone: 'orange', description: '入库、出库和库存日常操作' },
  { id: 'touch_staff', name: '触屏员工', tone: 'green', description: '前端触屏端和授权仓库草稿' },
  { id: 'sales', name: '销售人员', tone: 'purple', description: '客户和销售订单日常录入' }
]

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

const rolePermissionMap = {
  system_admin: permissionModules.flatMap(module => module.permissions.map(permission => permission.id)),
  finance: [
    'finance.receivable.view',
    'finance.payment.create',
    'finance.reconciliation.view',
    'sales.customer.view'
  ],
  warehouse: ['inventory.view', 'inventory.inbound.create', 'inventory.outbound.create'],
  touch_staff: ['front.access', 'front.material_outbound.create', 'front.material_outbound.view'],
  sales: ['sales.customer.view', 'sales.order.create', 'sales.order.edit']
}

const stores = [
  { id: 1, name: '一号门店' },
  { id: 2, name: '二号门店' },
  { id: 3, name: '直营网点' }
]

const warehouses = [
  { id: 1, name: '成品仓' },
  { id: 2, name: '原材料仓' },
  { id: 3, name: '周转仓' }
]

const employees = ref([
  {
    id: 1001,
    employeeNo: 'E-0001',
    displayName: '张三',
    avatarColor: '#d8f4ea',
    username: 'zhangsan',
    accountStatus: 'active',
    department: '仓储部',
    position: '仓库操作员',
    phone: '138****1024',
    idCard: '110101********1234',
    currentAddress: '北京市朝阳区示例街道 18 号',
    emergencyContact: '李女士',
    emergencyPhone: '139****2088',
    employmentStatus: 'active',
    employmentType: '正式',
    hireDate: '2024-03-01',
    roleIds: ['warehouse', 'touch_staff'],
    storeIds: [1],
    warehouseIds: [1, 2]
  },
  {
    id: 1002,
    employeeNo: 'E-0002',
    displayName: '李四',
    avatarColor: '#e2edff',
    username: 'lisi',
    accountStatus: 'active',
    department: '财务部',
    position: '财务专员',
    phone: '139****3412',
    idCard: '110102********5678',
    currentAddress: '北京市海淀区示例路 6 号',
    emergencyContact: '王先生',
    emergencyPhone: '137****9088',
    employmentStatus: 'active',
    employmentType: '正式',
    hireDate: '2023-08-15',
    roleIds: ['finance'],
    storeIds: [1, 2, 3],
    warehouseIds: []
  },
  {
    id: 1003,
    employeeNo: 'E-0003',
    displayName: '王五',
    avatarColor: '#fff0d7',
    username: 'wangwu',
    accountStatus: 'pending',
    department: '销售部',
    position: '销售顾问',
    phone: '137****7765',
    idCard: '110105********9012',
    currentAddress: '北京市东城区示例胡同 9 号',
    emergencyContact: '赵女士',
    emergencyPhone: '136****3310',
    employmentStatus: 'probation',
    employmentType: '试用',
    hireDate: '2026-08-20',
    roleIds: ['sales'],
    storeIds: [2],
    warehouseIds: []
  },
  {
    id: 1004,
    employeeNo: 'E-0004',
    displayName: '赵六',
    avatarColor: '#eee4ff',
    username: '',
    accountStatus: 'disabled',
    department: '人事行政',
    position: '行政专员',
    phone: '136****5521',
    idCard: '110106********3456',
    currentAddress: '北京市西城区示例小区 2 号',
    emergencyContact: '陈先生',
    emergencyPhone: '135****6622',
    employmentStatus: 'leave',
    employmentType: '正式',
    hireDate: '2022-11-03',
    roleIds: [],
    storeIds: [],
    warehouseIds: []
  }
])

const filters = ref({
  keyword: '',
  department: '',
  employmentStatus: '',
  accountStatus: ''
})

const selectedEmployeeId = ref(null)
const activeDetailTab = ref('profile')
const drawerVisible = ref(false)
const editingEmployee = ref(false)
const draft = ref(createEmptyEmployee())
const notice = ref('')
let noticeTimer

const selectedEmployee = computed(() => {
  return employees.value.find(employee => employee.id === selectedEmployeeId.value) || null
})

const selectedPermissionModules = computed(() => {
  if (!selectedEmployee.value) return []
  const enabledPermissions = new Set(
    selectedEmployee.value.roleIds.flatMap(roleId => rolePermissionMap[roleId] || [])
  )
  return permissionModules.map(module => ({
    ...module,
    permissions: module.permissions.map(permission => ({
      ...permission,
      enabled: enabledPermissions.has(permission.id)
    }))
  }))
})

const selectedPermissionCount = computed(() => {
  return selectedPermissionModules.value.reduce(
    (total, module) => total + module.permissions.filter(permission => permission.enabled).length,
    0
  )
})

const filteredEmployees = computed(() => {
  const keyword = filters.value.keyword.toLowerCase()
  return employees.value.filter(employee => {
    const matchesKeyword =
      !keyword ||
      [employee.displayName, employee.employeeNo, employee.username, employee.phone, employee.department]
        .join(' ')
        .toLowerCase()
        .includes(keyword)
    const matchesDepartment = !filters.value.department || employee.department === filters.value.department
    const matchesEmployment =
      !filters.value.employmentStatus || employee.employmentStatus === filters.value.employmentStatus
    const matchesAccount = !filters.value.accountStatus || employee.accountStatus === filters.value.accountStatus
    return matchesKeyword && matchesDepartment && matchesEmployment && matchesAccount
  })
})

const activeEmployeeCount = computed(() => employees.value.filter(item => item.employmentStatus === 'active').length)
const enabledAccountCount = computed(() => employees.value.filter(item => item.accountStatus === 'active').length)
const pendingAccountCount = computed(() => employees.value.filter(item => item.accountStatus === 'pending').length)

function createEmptyEmployee() {
  return {
    id: null,
    employeeNo: '',
    displayName: '',
    avatarColor: '#e5e7eb',
    username: '',
    accountStatus: 'pending',
    department: departments[0],
    position: '',
    phone: '',
    idCard: '',
    currentAddress: '',
    emergencyContact: '',
    emergencyPhone: '',
    employmentStatus: 'active',
    employmentType: '正式',
    hireDate: '',
    roleIds: [],
    storeIds: [],
    warehouseIds: []
  }
}

function openCreate() {
  editingEmployee.value = false
  draft.value = createEmptyEmployee()
  drawerVisible.value = true
}

function openEmployee(employee) {
  selectedEmployeeId.value = employee.id
  activeDetailTab.value = 'profile'
}

function goToList() {
  selectedEmployeeId.value = null
  activeDetailTab.value = 'profile'
}

function openEdit(employee) {
  editingEmployee.value = true
  draft.value = {
    ...employee,
    roleIds: [...employee.roleIds],
    storeIds: [...employee.storeIds],
    warehouseIds: [...employee.warehouseIds]
  }
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
}

function saveEmployee() {
  if (!draft.value.displayName) {
    showNotice('请先填写员工姓名')
    return
  }

  const payload = {
    ...draft.value,
    employeeNo: draft.value.employeeNo || `E-${String(employees.value.length + 1).padStart(4, '0')}`,
    roleIds: [...draft.value.roleIds],
    storeIds: [...draft.value.storeIds],
    warehouseIds: [...draft.value.warehouseIds]
  }

  if (editingEmployee.value) {
    const index = employees.value.findIndex(item => item.id === payload.id)
    if (index !== -1) employees.value[index] = payload
    showNotice('员工档案已更新')
  } else {
    payload.id = Math.max(...employees.value.map(item => item.id), 1000) + 1
    employees.value.unshift(payload)
    showNotice('员工档案已创建')
  }
  closeDrawer()
}

function toggleAccount(employee) {
  employee.accountStatus = employee.accountStatus === 'disabled' ? 'active' : 'disabled'
  showNotice(employee.accountStatus === 'active' ? '账号已启用' : '账号已停用')
}

function resetFilters() {
  filters.value = {
    keyword: '',
    department: '',
    employmentStatus: '',
    accountStatus: ''
  }
}

function refreshList() {
  showNotice('演示数据已刷新')
}

function exportPreview() {
  showNotice('导出功能将在后端接口接入后启用')
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 3000)
}

function roleName(roleId) {
  return roleGroups.find(role => role.id === roleId)?.name || roleId
}

function roleTone(roleId) {
  return roleGroups.find(role => role.id === roleId)?.tone || 'neutral'
}

function roleDescription(roleId) {
  return roleGroups.find(role => role.id === roleId)?.description || '未配置角色说明'
}

function scopeNames(ids, options) {
  return ids
    .map(id => options.find(option => option.id === id)?.name)
    .filter(Boolean)
    .join('、')
}

function accountStatusLabel(status) {
  return {
    active: '正常',
    pending: '待开通',
    disabled: '已停用'
  }[status] || status
}

function accountStatusClass(status) {
  return {
    active: 'status-success',
    pending: 'status-warning',
    disabled: 'status-disabled'
  }[status] || 'status-disabled'
}

function employmentStatusLabel(status) {
  return {
    active: '在职',
    probation: '试用期',
    leave: '休假',
    resigned: '离职'
  }[status] || status
}

function employmentStatusClass(status) {
  return {
    active: 'status-success',
    probation: 'status-warning',
    leave: 'status-info',
    resigned: 'status-disabled'
  }[status] || 'status-disabled'
}

function avatarStyle(employee) {
  return {
    backgroundColor: employee.avatarColor || '#e5e7eb',
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
.records-toolbar,
.title-row,
.header-actions,
.toolbar-actions,
.employee-cell,
.account-cell,
.row-actions,
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
.record-count,
.role-tag,
.role-more,
.status-badge {
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
.toolbar-actions {
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

.button-secondary,
.button-ghost {
  color: var(--text-secondary);
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover,
.button-ghost:hover {
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
.search-panel,
.records-panel {
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

.warning-text {
  color: #a4510b;
}

.search-panel {
  padding: 18px 20px;
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.4fr) repeat(3, minmax(150px, 1fr)) auto;
  gap: 14px;
  align-items: end;
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
select {
  width: 100%;
  height: 38px;
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

input::placeholder {
  color: #a3adbb;
}

input:focus,
select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.input-with-icon {
  position: relative;
}

.input-with-icon svg {
  position: absolute;
  top: 10px;
  left: 11px;
  width: 17px;
  height: 17px;
  fill: none;
  stroke: var(--text-muted);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  pointer-events: none;
}

.input-with-icon input {
  padding-left: 35px;
}

.reset-button {
  align-self: end;
}

.records-panel {
  margin-top: 14px;
  overflow: hidden;
}

.records-toolbar {
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  min-height: 62px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.records-heading {
  display: flex;
  min-width: 112px;
  flex-direction: column;
  gap: 4px;
}

.records-toolbar h2 {
  font-size: 15px;
}

.record-count {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.employee-toolbar {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex: 1;
}

.toolbar-filters {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}

.toolbar-search {
  position: relative;
  display: flex;
  width: 205px;
  height: 38px;
  align-items: center;
  flex: 0 1 205px;
}

.toolbar-search svg {
  position: absolute;
  left: 10px;
  width: 16px;
  height: 16px;
  fill: none;
  stroke: var(--text-muted);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  pointer-events: none;
}

.toolbar-search input {
  height: 38px;
  padding-left: 33px;
}

.toolbar-filters > select {
  width: 126px;
  flex: 0 1 126px;
  color: var(--text-secondary);
  font-size: 12px;
}

.toolbar-reset {
  height: 30px;
  padding: 0 5px;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
}

.toolbar-reset:hover {
  color: var(--accent);
  text-decoration: underline;
}

.toolbar-refresh {
  flex: 0 0 36px;
}

.table-scroll {
  overflow-x: auto;
}

.employee-table {
  width: 100%;
  min-width: 1260px;
  table-layout: fixed;
  border-collapse: collapse;
}

.employee-table th {
  height: 45px;
  padding: 0 12px;
  color: var(--text-secondary);
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
}

.employee-table td {
  height: 69px;
  padding: 9px 12px;
  border-bottom: 1px solid #edf1f5;
  font-size: 13px;
  vertical-align: middle;
  box-sizing: border-box;
}

.employee-table tbody tr:last-child td {
  border-bottom: 0;
}

.employee-table tbody tr.record-row {
  cursor: pointer;
  transition: background 0.18s ease;
}

.employee-table tbody tr.record-row:hover,
.employee-table tbody tr.record-row:focus-visible {
  background: rgba(var(--accent-rgb), 0.06);
  outline: none;
}

.row-resigned {
  opacity: 0.72;
}

.col-employee {
  width: 215px;
}

.col-account {
  width: 155px;
}

.col-job {
  width: 155px;
}

.col-phone {
  width: 125px;
}

.col-employment {
  width: 110px;
}

.col-role {
  width: 215px;
}

.col-date {
  width: 110px;
}

.col-actions {
  width: 170px;
  text-align: center !important;
}

.employee-cell {
  gap: 10px;
  min-width: 0;
}

.avatar {
  display: inline-flex;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 750;
}

.employee-copy,
.account-cell,
.job-cell {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.employee-copy strong,
.account-cell strong,
.job-cell strong {
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.employee-copy span,
.job-cell span {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-cell .status-badge {
  width: fit-content;
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

.status-warning {
  color: #a4510b;
  background: #fff3df;
}

.status-info {
  color: #16647a;
  background: #e7f5f8;
}

.status-disabled {
  color: #7b8492;
  background: #f1f2f4;
}

.role-list {
  display: flex;
  align-items: center;
  gap: 5px;
  overflow: hidden;
}

.role-tag,
.role-more {
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  box-sizing: border-box;
}

.role-tag {
  max-width: 108px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.role-tag.green {
  color: #13734f;
  background: #eaf8f1;
}

.role-tag.blue {
  color: #16647a;
  background: #e7f5f8;
}

.role-tag.orange {
  color: #a4510b;
  background: #fff3df;
}

.role-tag.red {
  color: #b4232f;
  background: #fcebed;
}

.role-tag.purple {
  color: #6651a8;
  background: #f1edff;
}

.role-tag.neutral,
.role-more {
  color: var(--text-secondary);
  background: #f1f5f9;
}

.empty-inline {
  color: var(--text-muted);
  font-size: 12px;
}

.tabular {
  font-variant-numeric: tabular-nums;
}

.row-actions {
  justify-content: center;
  gap: 10px;
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

.empty-state {
  display: flex;
  min-height: 180px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 7px;
  color: var(--text-muted);
}

.empty-state strong {
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-icon {
  color: var(--border-strong);
  font-size: 28px;
  line-height: 1;
}

.table-footer {
  display: flex;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.footer-summary {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
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
  width: min(640px, 100vw);
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

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
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

.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-heading h3 {
  font-size: 14px;
}

.section-heading span {
  color: var(--text-muted);
  font-size: 12px;
  text-align: right;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-wide {
  grid-column: 1 / -1;
}

.check-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.check-item {
  display: flex;
  min-height: 58px;
  align-items: flex-start;
  gap: 9px;
  padding: 11px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  box-sizing: border-box;
}

.check-item:has(input:checked) {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.check-item input,
.scope-item input {
  margin: 2px 0 0;
}

.check-item strong,
.check-item small {
  display: block;
}

.check-item strong {
  color: var(--text);
  font-size: 12px;
}

.check-item small {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.4;
}

.scope-block + .scope-block {
  margin-top: 14px;
}

.scope-label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
}

.scope-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scope-item {
  display: inline-flex;
  min-height: 34px;
  align-items: center;
  gap: 7px;
  padding: 0 10px;
  color: var(--text-secondary);
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
}

.scope-item:has(input:checked) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.drawer-footer {
  justify-content: flex-end;
  gap: 8px;
  padding: 13px 22px;
  border-top: 1px solid var(--border);
}

.workspace-nav {
  display: flex;
  min-height: 47px;
  align-items: flex-end;
  gap: 3px;
  padding: 0 8px;
  overflow-x: auto;
  background: #e8eef1;
  border: 1px solid var(--border);
  border-radius: 7px 7px 0 0;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
  box-sizing: border-box;
}

.workspace-tab {
  display: inline-flex;
  min-width: 124px;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-bottom: 0;
  border-radius: 6px 6px 0 0;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  box-sizing: border-box;
}

.workspace-tab:hover {
  color: var(--accent-dark);
  background: rgba(255, 255, 255, 0.62);
}

.workspace-tab.active {
  color: var(--accent-dark);
  background: #fff;
  border-color: var(--border);
  box-shadow: 0 -1px 0 #fff;
}

.workspace-tab svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.employee-workspace-tab {
  min-width: 150px;
  justify-content: flex-start;
}

.tab-avatar {
  display: inline-flex;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 750;
}

.tab-close {
  display: inline-flex;
  width: 19px;
  height: 19px;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  color: var(--text-muted);
  border-radius: 4px;
  font-size: 17px;
  font-weight: 400;
  line-height: 1;
}

.tab-close:hover {
  color: #b4232f;
  background: #fcebed;
}

.employee-context {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 14px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
  box-sizing: border-box;
}

.context-identity,
.context-title {
  display: flex;
  align-items: center;
}

.context-identity {
  min-width: 0;
  gap: 11px;
}

.context-avatar {
  display: inline-flex;
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 17px;
  font-weight: 750;
}

.context-identity > div {
  min-width: 0;
}

.context-title {
  gap: 9px;
}

.context-title h2 {
  overflow: hidden;
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-identity p {
  margin-top: 5px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.detail-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 10px;
  padding: 0 12px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
}

.detail-tab {
  position: relative;
  display: inline-flex;
  height: 47px;
  align-items: center;
  gap: 7px;
  padding: 0 15px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
}

.detail-tab::after {
  position: absolute;
  right: 10px;
  bottom: -1px;
  left: 10px;
  height: 2px;
  background: transparent;
  content: '';
}

.detail-tab:hover {
  color: var(--accent-dark);
}

.detail-tab.active {
  color: var(--accent-dark);
}

.detail-tab.active::after {
  background: var(--accent);
}

.detail-tab-count {
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 999px;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.detail-content {
  margin-top: 14px;
}

.profile-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
}

.detail-column {
  display: grid;
  align-content: start;
  gap: 14px;
  min-width: 0;
}

.detail-card,
.permission-summary-card,
.permission-main {
  min-width: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
  box-sizing: border-box;
}

.detail-card {
  padding: 16px;
}

.detail-card-heading,
.account-summary,
.assigned-role-list,
.content-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.detail-card-heading {
  margin-bottom: 15px;
}

.detail-card-heading h3,
.content-heading h3 {
  font-size: 14px;
}

.detail-card-heading span:not(.card-index),
.content-heading > div > span {
  display: block;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.card-index {
  color: var(--border-strong);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
}

.identity-overview {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border);
}

.profile-avatar {
  display: inline-flex;
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 750;
}

.identity-overview strong,
.identity-overview span {
  display: block;
}

.identity-overview strong {
  font-size: 15px;
}

.identity-overview span {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px 20px;
  margin: 17px 0 0;
}

.info-grid.single-column {
  grid-template-columns: 1fr;
  gap: 14px;
  margin-top: 0;
}

.info-grid div {
  min-width: 0;
}

.info-grid dt,
.info-grid dd {
  margin: 0;
}

.info-grid dt {
  color: var(--text-muted);
  font-size: 11px;
}

.info-grid dd {
  margin-top: 5px;
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-summary {
  align-items: center;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.summary-label {
  display: block;
  margin-bottom: 5px;
  color: var(--text-muted);
  font-size: 11px;
}

.account-summary strong {
  color: var(--text);
  font-size: 14px;
}

.assigned-role-list {
  display: block;
  margin-top: 14px;
}

.assigned-role-list .role-list {
  min-height: 25px;
  margin-top: 7px;
}

.permission-summary-card {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 15px 16px;
}

.permission-summary-card strong {
  display: block;
  font-size: 16px;
}

.permission-summary-card p {
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 12px;
}

.permission-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.72fr);
  gap: 14px;
  margin-top: 14px;
}

.permission-main {
  padding: 16px;
}

.content-heading {
  align-items: flex-end;
  margin-bottom: 14px;
}

.permission-total {
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.employee-permission-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.employee-permission-module {
  min-width: 0;
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

.module-dot.green {
  background: #0f9f78;
}

.module-dot.blue {
  background: #4796aa;
}

.module-dot.orange {
  background: #d58b2a;
}

.module-dot.purple {
  background: #806bc0;
}

.module-dot.red {
  background: #d25a64;
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

.employee-permission-list {
  display: grid;
  gap: 6px;
}

.employee-permission-chip {
  display: flex;
  min-height: 29px;
  align-items: center;
  gap: 7px;
  padding: 4px 8px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 11px;
  box-sizing: border-box;
}

.employee-permission-chip > span {
  display: inline-flex;
  width: 14px;
  height: 14px;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  background: #f1f5f9;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 800;
}

.employee-permission-chip.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
  font-weight: 650;
}

.employee-permission-chip.active > span {
  color: #fff;
  background: var(--accent);
}

.permission-side {
  display: grid;
  align-content: start;
  gap: 14px;
  min-width: 0;
}

.source-role-list {
  display: grid;
  gap: 10px;
}

.source-role-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  padding-bottom: 10px;
  border-bottom: 1px solid #edf1f5;
}

.source-role-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.role-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  margin-top: 4px;
  border-radius: 50%;
}

.role-dot.green {
  background: #0f9f78;
}

.role-dot.blue {
  background: #4796aa;
}

.role-dot.orange {
  background: #d58b2a;
}

.role-dot.purple {
  background: #806bc0;
}

.role-dot.red {
  background: #d25a64;
}

.source-role-item strong,
.source-role-item span {
  display: block;
}

.source-role-item strong {
  font-size: 12px;
}

.source-role-item div span {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.4;
}

.side-empty {
  min-height: 70px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 70px;
  text-align: center;
}

.scope-summary {
  display: grid;
  gap: 12px;
}

.scope-summary div {
  padding: 10px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
}

.scope-summary span,
.scope-summary strong {
  display: block;
}

.scope-summary span {
  color: var(--text-muted);
  font-size: 11px;
}

.scope-summary strong {
  margin-top: 5px;
  color: var(--text);
  font-size: 12px;
  line-height: 1.5;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
.record-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(4, minmax(150px, 1fr));
  }

  .search-grid .field:first-child {
    grid-column: span 2;
  }

  .reset-button {
    grid-column: span 2;
    justify-self: start;
  }

  .records-toolbar {
    align-items: flex-start;
  }

  .employee-toolbar {
    flex-wrap: wrap;
  }

  .toolbar-filters {
    flex: 1 1 100%;
    justify-content: flex-end;
  }

  .permission-layout {
    grid-template-columns: 1fr;
  }

  .permission-side {
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

  .workspace-nav {
    margin-right: -14px;
    margin-left: -14px;
    border-right: 0;
    border-left: 0;
    border-radius: 0;
  }

  .workspace-tab {
    min-width: 116px;
  }

  .employee-context {
    align-items: flex-start;
    flex-direction: column;
  }

  .context-actions {
    width: 100%;
  }

  .context-actions .button {
    flex: 1;
  }

  .detail-tabs {
    margin-top: 8px;
  }

  .detail-tab {
    flex: 1;
    justify-content: center;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-panel {
    padding: 14px;
  }

  .search-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .search-grid .field:first-child,
  .reset-button {
    grid-column: auto;
  }

  .reset-button {
    justify-self: stretch;
  }

  .records-toolbar {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .employee-toolbar {
    width: 100%;
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-filters {
    display: grid;
    width: 100%;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    justify-content: stretch;
  }

  .toolbar-search {
    width: auto;
    grid-column: 1 / -1;
    flex-basis: auto;
  }

  .toolbar-filters > select {
    width: auto;
    flex-basis: auto;
  }

  .toolbar-reset {
    justify-self: start;
  }

  .employee-toolbar .toolbar-actions {
    width: 100%;
  }

  .employee-toolbar .toolbar-actions .button {
    flex: 1;
  }

  .profile-content,
  .permission-side {
    grid-template-columns: 1fr;
  }

  .permission-summary-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .permission-summary-card .button {
    width: 100%;
  }

  .employee-permission-grid {
    grid-template-columns: 1fr;
  }

  .table-footer {
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    padding: 10px 14px;
  }

  .form-grid,
  .check-grid {
    grid-template-columns: 1fr;
  }

  .field-wide {
    grid-column: auto;
  }

  .drawer-header,
  .drawer-body,
  .drawer-footer {
    padding-right: 16px;
    padding-left: 16px;
  }
}
</style>
