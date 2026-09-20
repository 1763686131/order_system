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
                <input v-model.trim="filters.keyword" type="search" placeholder="搜索姓名 / 工号 / 账号 / 手机号" />
              </label>
              <select v-model="filters.department" title="按部门筛选">
                <option value="">全部部门</option>
                <option v-for="department in departments" :key="department.id" :value="department.id">
                  {{ department.name }}
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
              <th class="col-status">状态</th>
              <th class="col-role">权限组</th>
              <th class="col-device">设备信息</th>
              <th class="col-time">入职 / 最近活跃</th>
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
                  <strong>{{ employee.username || '—' }}</strong>
                  <span :class="['mini-badge', accountStatusClass(employee.accountStatus)]">
                    <i></i>{{ accountStatusLabel(employee.accountStatus) }}
                  </span>
                </div>
              </td>
              <td>
                <div class="job-cell">
                  <strong>{{ employee.department }}</strong>
                  <span>{{ employee.position || '暂无职位' }}</span>
                </div>
              </td>
              <td class="tabular cell-muted">{{ employee.phone || '—' }}</td>
              <td>
                <span :class="['mini-badge', employmentStatusClass(employee.employmentStatus)]">
                  <i></i>{{ employmentStatusLabel(employee.employmentStatus) }}
                </span>
              </td>
              <td>
                <div class="role-list">
                  <span
                    v-for="role in employee.roleIds.slice(0, 2)"
                    :key="role"
                    :class="['role-tag', 'role-' + roleTone(role)]"
                  >
                    {{ roleName(role) }}
                  </span>
                  <span v-if="employee.roleIds.length > 2" class="role-more">
                    +{{ employee.roleIds.length - 2 }}
                  </span>
                  <span v-if="employee.roleIds.length === 0" class="empty-inline">—</span>
                </div>
              </td>
              <td>
                <div v-if="employee.lastActiveDevice" class="device-cell">
                  <strong :title="employee.lastActiveDevice.deviceName || '未命名设备'">
                    {{ employee.lastActiveDevice.deviceName || '未命名设备' }}
                  </strong>
                  <span :title="deviceDescription(employee.lastActiveDevice)">
                    {{ deviceDescription(employee.lastActiveDevice) }}
                  </span>
                </div>
                <span v-else class="empty-inline">—</span>
              </td>
              <td>
                <div class="time-cell">
                  <span class="time-primary tabular">入职: {{ employee.hireDate || '—' }}</span>
                  <span class="time-secondary tabular">活跃: {{ formatDateTime(employee.lastActiveAt) }}</span>
                </div>
              </td>
              <td>
                <div class="row-actions" @click.stop>
                  <button class="action-link" type="button" @click="openEmployee(employee)">查看</button>
                  <button class="action-link" type="button" @click="openEdit(employee)">编辑</button>
                  <div class="action-dropdown">
                    <button class="action-more" type="button" title="更多操作">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <circle cx="12" cy="12" r="1"></circle>
                        <circle cx="12" cy="5" r="1"></circle>
                        <circle cx="12" cy="19" r="1"></circle>
                      </svg>
                    </button>
                    <div class="action-menu">
                      <button type="button" @click="openPasswordEditor(employee)">修改密码</button>
                      <button
                        type="button"
                        class="action-danger"
                        @click="confirmToggleAccount(employee)"
                      >
                        {{ employee.accountStatus === 'disabled' ? '启用账号' : '停用账号' }}
                      </button>
                      <button
                        v-if="employee.username"
                        type="button"
                        class="action-danger"
                        @click="confirmUnbindAccount(employee)"
                      >
                        解绑账号
                      </button>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="filteredEmployees.length === 0">
              <td colspan="9">
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
        <div class="footer-left">
          <button class="footer-info-trigger" type="button" title="查看说明">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
          </button>
          <span class="footer-hint">员工档案是人员主体，登录账号按需开通，角色组请在角色组管理中统一分配。</span>
        </div>
        <div class="footer-pagination">
          <span class="pagination-info">显示 {{ filteredEmployees.length }} / {{ employees.length }}</span>
          <select v-model="pageSize" class="page-size-select">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="50">50 条/页</option>
            <option :value="100">100 条/页</option>
          </select>
          <div class="pagination-controls">
            <button class="pagination-btn" type="button" title="上一页" disabled>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m15 18-6-6 6-6"></path>
              </svg>
            </button>
            <span class="pagination-current">1</span>
            <button class="pagination-btn" type="button" title="下一页" disabled>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m9 18 6-6-6-6"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
      </section>
    </template>

    <template v-else>
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
        <div class="detail-tab-actions">
          <button class="button button-ghost" type="button" @click="goToList">返回列表</button>
          <button class="button button-secondary" type="button" @click="openEdit(selectedEmployee)">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m4 16-.8 4.8L8 20l10.8-10.8a2.1 2.1 0 0 0-3-3L4 16Z"></path>
              <path d="m14.5 7.5 2 2"></path>
            </svg>
            编辑档案
          </button>
        </div>
      </nav>

      <section v-if="activeDetailTab === 'profile'" class="detail-content profile-content">
        <div class="detail-column">
          <article class="detail-card identity-card">
            <span class="card-index identity-card-index">01</span>
            <div class="identity-card-layout">
              <div class="identity-card-profile">
                <span class="identity-card-avatar" :style="avatarStyle(selectedEmployee)">
                  {{ selectedEmployee.displayName.slice(0, 1) }}
                </span>
              </div>
              <dl class="info-grid identity-info-grid">
                <div>
                  <dt>姓名</dt>
                  <dd class="dd-primary">{{ selectedEmployee.displayName }}</dd>
                </div>
                <div>
                  <dt>工号</dt>
                  <dd class="dd-primary tabular">{{ selectedEmployee.employeeNo || '—' }}</dd>
                </div>
                <div>
                  <dt>部门</dt>
                  <dd class="dd-primary">{{ selectedEmployee.department || '—' }}</dd>
                </div>
                <div>
                  <dt>职位</dt>
                  <dd class="dd-primary">{{ selectedEmployee.position || '—' }}</dd>
                </div>
                <div>
                  <dt>入职日期</dt>
                  <dd class="dd-primary tabular">{{ selectedEmployee.hireDate || '—' }}</dd>
                </div>
                <div>
                  <dt>当前状态</dt>
                  <dd>
                    <span :class="['mini-badge', employmentStatusClass(selectedEmployee.employmentStatus)]">
                      <i></i>{{ employmentStatusLabel(selectedEmployee.employmentStatus) }}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>
          </article>

          <article class="detail-card">
            <div class="detail-card-heading">
              <div class="heading-with-icon">
                <svg viewBox="0 0 24 24" aria-hidden="true" class="heading-icon">
                  <rect x="2" y="7" width="20" height="14" rx="2"></rect>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
                <div>
                  <h3>工作信息</h3>
                  <span>组织归属与岗位</span>
                </div>
              </div>
              <span class="card-index">02</span>
            </div>
            <dl class="info-grid">
              <div>
                <dt>所属部门</dt>
                <dd class="dd-primary">{{ selectedEmployee.department || '—' }}</dd>
              </div>
              <div>
                <dt>职位</dt>
                <dd class="dd-primary">{{ selectedEmployee.position || '—' }}</dd>
              </div>
              <div class="scope-field">
                <dt>可访问门店</dt>
                <dd>
                  <div v-if="selectedEmployeeScope.storeIds.length" class="capsule-list">
                    <span
                      v-for="storeId in selectedEmployeeScope.storeIds"
                      :key="storeId"
                      class="capsule-tag capsule-green"
                    >
                      {{ scopeOptionName(storeId, stores) || storeId }}
                    </span>
                  </div>
                  <span v-else class="dd-empty">—</span>
                </dd>
              </div>
              <div class="scope-field">
                <dt>可操作仓库</dt>
                <dd>
                  <div v-if="selectedEmployeeScope.warehouseIds.length" class="capsule-list">
                    <span
                      v-for="warehouseId in selectedEmployeeScope.warehouseIds"
                      :key="warehouseId"
                      class="capsule-tag capsule-blue"
                    >
                      {{ scopeOptionName(warehouseId, warehouses) || warehouseId }}
                    </span>
                  </div>
                  <span v-else class="dd-empty">—</span>
                </dd>
              </div>
            </dl>
          </article>
        </div>

        <div class="detail-column">
          <article class="detail-card">
            <div class="detail-card-heading">
              <div class="heading-with-icon">
                <svg viewBox="0 0 24 24" aria-hidden="true" class="heading-icon">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                </svg>
                <div>
                  <h3>联系方式</h3>
                  <span>后续人事行政资料</span>
                </div>
              </div>
              <span class="card-index">03</span>
            </div>
            <dl class="info-grid single-column">
              <div>
                <dt>联系电话</dt>
                <dd class="dd-primary tabular">{{ selectedEmployee.phone || '—' }}</dd>
              </div>
              <div>
                <dt>家庭住址</dt>
                <dd class="dd-primary">{{ selectedEmployee.currentAddress || '—' }}</dd>
              </div>
              <div>
                <dt>紧急联系人</dt>
                <dd class="dd-primary">{{ selectedEmployee.emergencyContact || '—' }}</dd>
              </div>
              <div>
                <dt>紧急联系电话</dt>
                <dd class="dd-primary tabular">{{ selectedEmployee.emergencyPhone || '—' }}</dd>
              </div>
            </dl>
          </article>

          <article class="detail-card account-summary-card">
            <div class="detail-card-heading">
              <div class="heading-with-icon">
                <svg viewBox="0 0 24 24" aria-hidden="true" class="heading-icon">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <div>
                  <h3>登录账号</h3>
                  <span>账号状态和权限组概览</span>
                </div>
              </div>
              <span class="card-index">04</span>
            </div>
            <div class="account-summary-row">
              <div>
                <span class="summary-label">账号</span>
                <strong class="account-username">{{ selectedEmployee.username || '暂未开通' }}</strong>
              </div>
              <span :class="['mini-badge', accountStatusClass(selectedEmployee.accountStatus)]">
                <i></i>{{ accountStatusLabel(selectedEmployee.accountStatus) }}
              </span>
            </div>
            <div v-if="selectedEmployee.username" class="account-security-grid">
              <div class="account-security-item">
                <span class="summary-label">登录密码</span>
                <div class="stored-password">
                  <strong>
                    {{ detailPasswordVisible ? '已加密，无法查看原密码' : '••••••••' }}
                  </strong>
                  <button
                    class="password-toggle"
                    type="button"
                    :title="detailPasswordVisible ? '隐藏密码说明' : '查看密码'"
                    :aria-label="detailPasswordVisible ? '隐藏密码说明' : '查看密码'"
                    @click="toggleStoredPasswordVisibility"
                  >
                    <svg v-if="detailPasswordVisible" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="2.5"></circle>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                      <path d="m3 3 18 18"></path>
                      <path d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6 0 9.5 6 9.5 6a16.7 16.7 0 0 1-2.2 2.9"></path>
                      <path d="M6.6 6.6C4 8.3 2.5 12 2.5 12s3.5 6 9.5 6c1.4 0 2.7-.3 3.8-.7"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="account-security-item">
                <span class="summary-label">最近活跃时间</span>
                <strong class="tabular">{{ formatDateTime(selectedEmployee.lastActiveAt) }}</strong>
              </div>
              <button class="button-link password-edit-button" type="button" @click="openPasswordEditor">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
                修改密码
              </button>
            </div>
            <div class="assigned-role-section">
              <span class="summary-label">已绑定权限组</span>
              <div v-if="selectedEmployee.roleIds.length" class="capsule-list">
                <span
                  v-for="roleId in selectedEmployee.roleIds"
                  :key="roleId"
                  :class="['capsule-tag', 'capsule-' + roleTone(roleId)]"
                >
                  {{ roleName(roleId) }}
                </span>
              </div>
              <span v-else class="dd-empty">暂未绑定权限组</span>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="detail-content permission-content">
        <article class="permission-summary-card">
          <div>
            <span class="summary-label">当前权限来源</span>
            <strong>{{ selectedEmployee.roleIds.length }} 个权限组</strong>
            <p>权限和数据范围由权限组统一维护，员工档案只保存绑定关系。</p>
          </div>
          <span class="summary-hint">请前往角色组管理维护绑定关系</span>
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
                  <h3>权限组来源</h3>
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
                <div v-if="selectedEmployee.roleIds.length === 0" class="side-empty">暂未绑定权限组</div>
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
                  <strong>{{ selectedEmployeeScope.storeIds.length ? scopeNames(selectedEmployeeScope.storeIds, stores) : '未分配' }}</strong>
                </div>
                <div>
                  <span>仓库范围</span>
                  <strong>{{ selectedEmployeeScope.warehouseIds.length ? scopeNames(selectedEmployeeScope.warehouseIds, warehouses) : '未分配' }}</strong>
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
            <div class="drawer-header-main">
              <button
                class="avatar-upload"
                type="button"
                title="选择并裁剪头像"
                :style="avatarStyle(draft)"
                @click="avatarInput?.click()"
              >
                <span>{{ draft.displayName?.slice(0, 1) || '人' }}</span>
                <i aria-hidden="true">+</i>
              </button>
              <input
                ref="avatarInput"
                class="avatar-upload-input"
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                @change="handleAvatarUpload"
              />
              <div>
                <span class="drawer-eyebrow">{{ editingEmployee ? '编辑档案' : '新建档案' }}</span>
                <h2 id="employee-drawer-title">{{ editingEmployee ? draft.displayName : '新增员工' }}</h2>
                <button
                  v-if="draft.avatarPreviewUrl || (!draft.avatarRemovalRequested && draft.avatarUrl)"
                  class="avatar-remove-button"
                  type="button"
                  @click="removeAvatar"
                >
                  移除头像
                </button>
              </div>
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
                  <span>手机号</span>
                  <input
                    v-model.trim="draft.phone"
                    type="tel"
                    inputmode="tel"
                    maxlength="30"
                    placeholder="请输入员工手机号"
                  />
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
                <div class="field">
                  <span>部门</span>
                  <div class="department-multi-select" :class="{ open: departmentSelectorOpen }">
                    <button
                      class="department-multi-trigger"
                      type="button"
                      :aria-expanded="departmentSelectorOpen"
                      @click="departmentSelectorOpen = !departmentSelectorOpen"
                    >
                      <span>{{ departmentSelectionLabel }}</span>
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="m7 10 5 5 5-5"></path>
                      </svg>
                    </button>
                    <div v-if="departmentSelectorOpen" class="department-multi-menu">
                      <label
                        v-for="department in departments"
                        :key="department.id"
                        class="department-multi-option"
                        :class="{ selected: draft.departmentIds.includes(department.id) }"
                      >
                        <input
                          type="checkbox"
                          :checked="draft.departmentIds.includes(department.id)"
                          :disabled="department.status !== 'active' && !draft.departmentIds.includes(department.id)"
                          @change="toggleDraftDepartment(department.id)"
                        />
                        <span>{{ department.name }}</span>
                        <small v-if="department.status !== 'active'">已停用</small>
                      </label>
                      <span v-if="departments.length === 0" class="department-multi-empty">
                        暂无部门配置
                      </span>
                    </div>
                  </div>
                  <small class="field-hint">可同时选择多个部门，第一项作为主部门</small>
                </div>
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
                <span>登录账号依附当前员工档案</span>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>登录账号</span>
                  <input
                    v-model.trim="draft.username"
                    type="text"
                    :disabled="editingEmployee && draft.passwordSet"
                    placeholder="未填写则暂不开通"
                  />
                </label>
                <label class="field">
                  <span>登录密码 <em v-if="!editingEmployee && draft.username">*</em></span>
                  <div class="password-input-wrap">
                    <input
                      ref="passwordInput"
                      v-model.trim="draft.password"
                      :type="passwordVisible ? 'text' : 'password'"
                      :placeholder="editingEmployee ? '留空保持原密码' : '请输入登录密码'"
                      autocomplete="new-password"
                    />
                    <button
                      class="password-toggle"
                      type="button"
                      :title="passwordVisible ? '隐藏密码' : '显示密码'"
                      :aria-label="passwordVisible ? '隐藏密码' : '显示密码'"
                      @click="passwordVisible = !passwordVisible"
                    >
                      <svg v-if="passwordVisible" viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                        <circle cx="12" cy="12" r="2.5"></circle>
                      </svg>
                      <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                        <path d="m3 3 18 18"></path>
                        <path d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6 0 9.5 6 9.5 6a16.7 16.7 0 0 1-2.2 2.9"></path>
                        <path d="M6.6 6.6C4 8.3 2.5 12 2.5 12s3.5 6 9.5 6c1.4 0 2.7-.3 3.8-.7"></path>
                      </svg>
                    </button>
                  </div>
                </label>
                <label class="field">
                  <span>确认密码 <em v-if="draft.password">*</em></span>
                  <div class="password-input-wrap">
                    <input
                      v-model.trim="draft.passwordConfirm"
                      :type="passwordConfirmVisible ? 'text' : 'password'"
                      placeholder="请再次输入登录密码"
                      autocomplete="new-password"
                    />
                    <button
                      class="password-toggle"
                      type="button"
                      :title="passwordConfirmVisible ? '隐藏确认密码' : '显示确认密码'"
                      :aria-label="passwordConfirmVisible ? '隐藏确认密码' : '显示确认密码'"
                      @click="passwordConfirmVisible = !passwordConfirmVisible"
                    >
                      <svg v-if="passwordConfirmVisible" viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                        <circle cx="12" cy="12" r="2.5"></circle>
                      </svg>
                      <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                        <path d="m3 3 18 18"></path>
                        <path d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6 0 9.5 6 9.5 6s-1.5 2.6-3.8 4.3"></path>
                        <path d="M6.6 6.6C4 8.3 2.5 12 2.5 12s3.5 6 9.5 6c1.4 0 2.7-.3 3.8-.7"></path>
                      </svg>
                    </button>
                  </div>
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

    <AvatarCropper
      :visible="avatarCropVisible"
      :file="avatarCropFile"
      @cancel="closeAvatarCropper"
      @confirm="applyCroppedAvatar"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import AvatarCropper from '@/components/admin/AvatarCropper.vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { mergeRolePermissions, mergeRoleScopes } from '@/utils/accessControl'

const userStore = useUserStore()
const departments = ref([])

const roleGroups = ref([])
const permissionModules = ref([])

const stores = ref([])
const warehouses = ref([])

const employees = ref([])

const filters = ref({
  keyword: '',
  department: '',
  employmentStatus: '',
  accountStatus: ''
})

const pageSize = ref(20)

const selectedEmployeeId = ref(null)
const activeDetailTab = ref('profile')
const drawerVisible = ref(false)
const editingEmployee = ref(false)
const departmentSelectorOpen = ref(false)
const draft = ref(createEmptyEmployee())
const avatarInput = ref(null)
const pendingAvatarFile = ref(null)
const avatarCropVisible = ref(false)
const avatarCropFile = ref(null)
const passwordInput = ref(null)
const passwordVisible = ref(false)
const passwordConfirmVisible = ref(false)
const detailPasswordVisible = ref(false)
const notice = ref('')
let noticeTimer

async function loadEmployeeData() {
  try {
    const [
      employeeResponse,
      roleResponse,
      permissionResponse,
      departmentResponse,
      storeResponse,
      warehouseResponse
    ] = await Promise.all([
      request.get('/admin/employees'),
      request.get('/admin/roles'),
      request.get('/admin/permissions'),
      request.get('/admin/departments'),
      request.get('/stores'),
      request.get('/warehouses')
    ])
    employees.value = employeeResponse.employees || []
    departments.value = departmentResponse.departments || []
    stores.value = Array.isArray(storeResponse) ? storeResponse : []
    warehouses.value = Array.isArray(warehouseResponse) ? warehouseResponse : []
    roleGroups.value = (roleResponse.roles || []).map((role) => ({
      ...role
    }))
    permissionModules.value = (permissionResponse.modules || []).map((module, index) => ({
      ...module,
      id: module.code,
      tone: ['green', 'blue', 'orange', 'purple', 'red'][index % 5],
      permissions: module.permissions.map(permission => ({
        ...permission,
        id: permission.code
      }))
    }))
  } catch (error) {
    showNotice(error?.response?.data?.message || '员工数据加载失败')
  }
}

const selectedEmployee = computed(() => {
  return employees.value.find(employee => employee.id === selectedEmployeeId.value) || null
})

const selectedEmployeeRoles = computed(() => {
  const roleIds = new Set(selectedEmployee.value?.roleIds || [])
  return roleGroups.value.filter(role => roleIds.has(role.id))
})

const selectedEmployeeScope = computed(() => {
  return mergeRoleScopes(selectedEmployeeRoles.value, {
    storeIds: stores.value.map(store => store.id),
    warehouseIds: warehouses.value.map(warehouse => warehouse.id)
  })
})

const selectedPermissionModules = computed(() => {
  if (!selectedEmployee.value) return []
  const enabledPermissions = new Set(mergeRolePermissions(selectedEmployeeRoles.value))
  return permissionModules.value.map(module => ({
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
    const employeeDepartmentIds = employee.departmentIds || (employee.departmentId ? [employee.departmentId] : [])
    const matchesDepartment = !filters.value.department || employeeDepartmentIds.includes(Number(filters.value.department))
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
    avatarUrl: '',
    avatarPreviewUrl: '',
    avatarRemovalRequested: false,
    username: '',
    password: '',
    passwordConfirm: '',
    passwordSet: false,
    accountStatus: 'pending',
    departmentId: null,
    departmentIds: [],
    position: '',
    phone: '',
    idCard: '',
    currentAddress: '',
    emergencyContact: '',
    emergencyPhone: '',
    employmentStatus: 'active',
    employmentType: '正式',
    hireDate: '',
    roleIds: []
  }
}

function openCreate() {
  resetPendingAvatar()
  editingEmployee.value = false
  draft.value = createEmptyEmployee()
  const defaultDepartmentId = departments.value.find(item => item.status === 'active')?.id || null
  draft.value.departmentId = defaultDepartmentId
  draft.value.departmentIds = defaultDepartmentId ? [defaultDepartmentId] : []
  departmentSelectorOpen.value = false
  passwordVisible.value = false
  passwordConfirmVisible.value = false
  drawerVisible.value = true
}

function openEmployee(employee) {
  selectedEmployeeId.value = employee.id
  activeDetailTab.value = 'profile'
  detailPasswordVisible.value = false
}

function goToList() {
  selectedEmployeeId.value = null
  activeDetailTab.value = 'profile'
  detailPasswordVisible.value = false
}

function openEdit(employee) {
  resetPendingAvatar()
  editingEmployee.value = true
  draft.value = {
    ...employee,
    avatarPreviewUrl: '',
    avatarRemovalRequested: false,
    departmentIds: [...(employee.departmentIds || (employee.departmentId ? [employee.departmentId] : []))],
    roleIds: [...employee.roleIds],
    password: '',
    passwordConfirm: '',
    passwordSet: Boolean(employee.passwordSet || employee.username)
  }
  passwordVisible.value = false
  passwordConfirmVisible.value = false
  departmentSelectorOpen.value = false
  drawerVisible.value = true
}

function closeDrawer() {
  resetPendingAvatar()
  drawerVisible.value = false
  passwordVisible.value = false
  passwordConfirmVisible.value = false
  departmentSelectorOpen.value = false
}

const departmentSelectionLabel = computed(() => {
  const selectedIds = draft.value.departmentIds || []
  const selectedNames = departments.value
    .filter(department => selectedIds.includes(department.id))
    .map(department => department.name)
  return selectedNames.length ? selectedNames.join('、') : '未分配部门'
})

function toggleDraftDepartment(departmentId) {
  const selectedIds = [...(draft.value.departmentIds || [])]
  const index = selectedIds.indexOf(departmentId)
  if (index === -1) {
    selectedIds.push(departmentId)
  } else {
    selectedIds.splice(index, 1)
  }
  draft.value.departmentIds = selectedIds
  draft.value.departmentId = selectedIds[0] || null
}

function toggleStoredPasswordVisibility() {
  detailPasswordVisible.value = !detailPasswordVisible.value
  if (detailPasswordVisible.value) {
    showNotice('现有密码采用不可逆加密保存，无法查看原密码，可通过“修改密码”设置新密码')
  }
}

async function openPasswordEditor(employee = selectedEmployee.value) {
  if (!employee?.username) {
    showNotice('该员工尚未开通登录账号')
    return
  }
  selectedEmployeeId.value = employee.id
  openEdit(employee)
  await nextTick()
  passwordInput.value?.focus()
}

async function saveEmployee() {
  if (!draft.value.displayName) {
    showNotice('请先填写员工姓名')
    return
  }

  if (draft.value.username && !editingEmployee.value && !draft.value.password) {
    showNotice('开通登录账号需要设置密码')
    return
  }

  if (draft.value.password && draft.value.password !== draft.value.passwordConfirm) {
    showNotice('两次输入的密码不一致')
    return
  }

  try {
    const {
      avatarPreviewUrl,
      avatarRemovalRequested,
      passwordConfirm,
      ...employeePayload
    } = draft.value
    const payload = {
      ...employeePayload,
      roleIds: [...draft.value.roleIds]
    }
    const response = editingEmployee.value
      ? await request.put(`/admin/employees/${draft.value.id}`, payload)
      : await request.post('/admin/employees', payload)
    let savedEmployee = response.employee
    let avatarError = ''
    try {
      if (pendingAvatarFile.value) {
        const uploadData = new FormData()
        uploadData.append('avatar', pendingAvatarFile.value)
        const avatarResponse = await request({
          url: `/admin/employees/${savedEmployee.id}/avatar`,
          method: 'POST',
          data: uploadData,
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        savedEmployee = avatarResponse.employee
      } else if (avatarRemovalRequested && savedEmployee.avatarUrl) {
        const avatarResponse = await request.delete(`/admin/employees/${savedEmployee.id}/avatar`)
        savedEmployee = avatarResponse.employee
      }
    } catch (error) {
      avatarError = error?.response?.data?.message || '头像处理失败'
    }
    if (editingEmployee.value) {
      const index = employees.value.findIndex(item => item.id === savedEmployee.id)
      if (index !== -1) employees.value[index] = savedEmployee
    } else {
      employees.value.unshift(savedEmployee)
    }
    if (Number(savedEmployee.userId) === Number(userStore.id)) {
      userStore.name = savedEmployee.displayName
      userStore.avatarUrl = savedEmployee.avatarUrl || ''
      userStore.phone = savedEmployee.phone || ''
      userStore.position = savedEmployee.position || ''
    }
    showNotice(
      avatarError
        ? `员工档案已保存，但${avatarError}`
        : response.message || '员工档案已保存'
    )
    closeDrawer()
  } catch (error) {
    showNotice(error?.response?.data?.message || '员工档案保存失败')
  }
}

function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    showNotice('请选择图片格式的头像文件')
    return
  }
  if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)) {
    showNotice('头像仅支持 JPG、PNG、WebP 或 GIF 图片')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    showNotice('头像图片不能超过 5MB')
    return
  }

  avatarCropFile.value = file
  avatarCropVisible.value = true
}

function applyCroppedAvatar(file) {
  revokeAvatarPreview()
  pendingAvatarFile.value = file
  draft.value.avatarPreviewUrl = URL.createObjectURL(file)
  draft.value.avatarRemovalRequested = false
  closeAvatarCropper()
}

function closeAvatarCropper() {
  avatarCropVisible.value = false
  avatarCropFile.value = null
}

function removeAvatar() {
  const hasStoredAvatar = Boolean(draft.value.avatarUrl)
  revokeAvatarPreview()
  pendingAvatarFile.value = null
  draft.value.avatarRemovalRequested = hasStoredAvatar
}

function revokeAvatarPreview() {
  if (draft.value.avatarPreviewUrl) {
    URL.revokeObjectURL(draft.value.avatarPreviewUrl)
    draft.value.avatarPreviewUrl = ''
  }
}

function resetPendingAvatar() {
  closeAvatarCropper()
  revokeAvatarPreview()
  pendingAvatarFile.value = null
}

async function toggleAccount(employee) {
  if (!employee.username) {
    showNotice('该员工尚未开通登录账号')
    return
  }
  const nextStatus = employee.accountStatus === 'disabled' ? 'active' : 'disabled'
  try {
    const response = await request.put(`/admin/employees/${employee.id}`, {
      ...employee,
      accountStatus: nextStatus,
      password: ''
    })
    const index = employees.value.findIndex(item => item.id === employee.id)
    if (index !== -1) employees.value[index] = response.employee
    showNotice(nextStatus === 'active' ? '账号已启用' : '账号已停用')
  } catch (error) {
    showNotice(error?.response?.data?.message || '账号状态更新失败')
  }
}

function confirmToggleAccount(employee) {
  if (!employee.username) {
    showNotice('该员工尚未开通登录账号')
    return
  }
  const action = employee.accountStatus === 'disabled' ? '启用' : '停用'
  if (window.confirm(`确认${action}账号 "${employee.username}"？\n\n${action === '停用' ? '停用后该员工将无法登录系统。' : ''}`)) {
    toggleAccount(employee)
  }
}

async function unbindAccount(employee) {
  try {
    const response = await request.delete(`/admin/employees/${employee.id}/account`)
    const index = employees.value.findIndex(item => item.id === employee.id)
    if (index !== -1) employees.value[index] = response.employee
    if (selectedEmployeeId.value === employee.id) {
      detailPasswordVisible.value = false
    }
    showNotice(response.message || '账号已解绑')
  } catch (error) {
    showNotice(error?.response?.data?.message || '账号解绑失败')
  }
}

function confirmUnbindAccount(employee) {
  if (!employee.username) {
    showNotice('该员工尚未开通登录账号')
    return
  }
  const confirmed = window.confirm(
    `确认解绑账号 "${employee.username}"？\n\n解绑后将删除该账号及其登录会话，员工档案和权限组会保留，之后可以重新绑定。`
  )
  if (confirmed) {
    unbindAccount(employee)
  }
}

function resetFilters() {
  filters.value = {
    keyword: '',
    department: '',
    employmentStatus: '',
    accountStatus: ''
  }
}

async function refreshList() {
  await loadEmployeeData()
  showNotice('员工数据已刷新')
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
  return roleGroups.value.find(role => role.id === roleId)?.name || roleId
}

function roleTone(roleId) {
  return roleGroups.value.find(role => role.id === roleId)?.tone || 'neutral'
}

function roleDescription(roleId) {
  return roleGroups.value.find(role => role.id === roleId)?.description || '未配置角色说明'
}

function scopeOptionName(id, options) {
  return options.find(option => String(option.id) === String(id))?.name || ''
}

function scopeNames(ids, options) {
  return ids
    .map(id => scopeOptionName(id, options))
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
  // 根据员工姓名生成不同的头像颜色
  const colors = [
    { bg: '#d1f4e8', color: '#0d7a5f' }, // 绿色
    { bg: '#d4f0f7', color: '#0e5a6d' }, // 蓝色
    { bg: '#ece5fb', color: '#5a4691' }, // 紫色
    { bg: '#fde8cf', color: '#8b4508' }, // 橙色
    { bg: '#fde1e4', color: '#991f29' }  // 红色
  ]

  // 简单的哈希函数，基于员工姓名或工号
  const hashString = employee.displayName + (employee.employeeNo || '')
  let hash = 0
  for (let i = 0; i < hashString.length; i++) {
    hash = hashString.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colorIndex = Math.abs(hash) % colors.length
  const selectedColor = colors[colorIndex]

  const style = {
    backgroundColor: employee.avatarColor || selectedColor.bg,
    color: employee.avatarColor ? '#275a4d' : selectedColor.color
  }
  const avatarUrl = employee.avatarPreviewUrl
    || (employee.avatarRemovalRequested ? '' : employee.avatarUrl)
  if (avatarUrl) {
    style.backgroundImage = `url("${avatarUrl}")`
    style.backgroundPosition = 'center'
    style.backgroundRepeat = 'no-repeat'
    style.backgroundSize = 'cover'
    style.color = 'transparent'
  }
  return style
}

function formatDateTime(value) {
  if (!value) return '-'
  const normalized = String(value).replace(' ', 'T')
  const dateValue = /(Z|[+-]\d{2}:\d{2})$/.test(normalized)
    ? normalized
    : `${normalized}Z`
  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date)
}

function deviceDescription(device) {
  const terminal = device?.sessionKind === 'touch' ? '触屏端' : '后台管理'
  return [
    terminal,
    device?.operatingSystem || '未知系统',
    device?.browser || '未知浏览器'
  ].join(' · ')
}

onMounted(loadEmployeeData)
onBeforeUnmount(resetPendingAvatar)
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
  background: var(--accent, #0f9f78);
  border-color: var(--accent, #0f9f78);
}

.button-primary:hover:not(:disabled) {
  background: var(--accent-dark, #08745a);
  border-color: var(--accent-dark, #08745a);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb, 15, 159, 120), 0.18);
}

.button-secondary,
.button-ghost {
  color: var(--text-secondary, #596579);
  background: var(--panel-bg, #fff);
  border-color: var(--border-strong, #cbd5e1);
}

.button-secondary:hover:not(:disabled),
.button-ghost:hover:not(:disabled) {
  color: var(--accent-dark, #08745a);
  background: var(--accent-soft, #e9f8f3);
  border-color: var(--accent-border, #a9e5d2);
}

.button:disabled {
  color: #8a96a8;
  background: #f1f5f9;
  border-color: #dfe5ec;
  box-shadow: none;
  cursor: not-allowed;
  opacity: 1;
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
  color: var(--text, #172033);
  background: #fff;
  border: 1px solid var(--border-strong, #cbd5e1);
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
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb, 15, 159, 120), 0.12);
}

.department-multi-select {
  position: relative;
}

.department-multi-trigger {
  display: flex;
  width: 100%;
  min-height: 38px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 11px;
  color: var(--text, #172033);
  text-align: left;
  background: #fff;
  border: 1px solid var(--border-strong, #cbd5e1);
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}

.department-multi-trigger:hover,
.department-multi-select.open .department-multi-trigger {
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb, 15, 159, 120), 0.12);
}

.department-multi-trigger > span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.department-multi-trigger svg {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  transition: transform 0.18s ease;
}

.department-multi-select.open .department-multi-trigger svg {
  transform: rotate(180deg);
}

.department-multi-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  left: 0;
  z-index: 30;
  max-height: 220px;
  padding: 6px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--border-strong, #cbd5e1);
  border-radius: 6px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.16);
}

.department-multi-option {
  display: flex;
  min-height: 36px;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  color: var(--text, #172033);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.department-multi-option:hover,
.department-multi-option.selected {
  background: var(--accent-soft, #e9f8f3);
}

.department-multi-option input {
  width: 15px;
  height: 15px;
  flex: 0 0 15px;
  accent-color: var(--accent, #0f9f78);
}

.department-multi-option > span {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.department-multi-option small {
  color: var(--text-muted, #8a96a8);
  font-size: 11px;
}

.department-multi-empty {
  display: block;
  padding: 10px 8px;
  color: var(--text-muted, #8a96a8);
  font-size: 12px;
  text-align: center;
}

.field-hint {
  margin-top: 5px;
  color: var(--text-muted, #8a96a8);
  font-size: 11px;
  line-height: 1.4;
}

input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: var(--accent, #0f9f78);
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
  min-height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.workspace-nav + .records-panel {
  margin-top: 0;
  border-top: 0;
  border-radius: 0 0 7px 7px;
}

.workspace-nav + .detail-tabs {
  margin-top: 0;
  border-top: 0;
  border-radius: 0;
}

.detail-tabs + .detail-content {
  margin-top: 0;
}

.detail-tabs + .profile-content > .detail-column > .detail-card:first-child,
.detail-tabs + .permission-content > .permission-summary-card {
  border-top: 0;
  border-radius: 0 0 7px 7px;
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
  flex: 1;
}

.employee-table {
  width: 100%;
  min-width: 1470px;
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
  width: 200px;
}

.col-account {
  width: 155px;
}

.col-job {
  width: 165px;
}

.col-phone {
  width: 120px;
}

.col-status {
  width: 100px;
}

.col-role {
  width: 200px;
}

.col-device {
  width: 190px;
}

.col-time {
  width: 160px;
}

.col-actions {
  width: 180px;
  text-align: center !important;
}

.cell-muted {
  color: #64748b;
  font-size: 13px !important;
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
.job-cell,
.device-cell,
.time-cell {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.account-cell {
  align-items: flex-start;
}

.employee-copy strong,
.account-cell strong,
.job-cell strong,
.device-cell strong {
  overflow: hidden;
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.employee-copy span,
.job-cell span,
.device-cell span {
  overflow: hidden;
  color: #94a3b8;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-cell .mini-badge {
  width: fit-content;
}

.time-cell {
  gap: 3px;
}

.time-primary {
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
}

.time-secondary {
  color: #94a3b8;
  font-size: 11px;
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

.role-tag.role-green {
  color: #0d7a5f;
  background: #d1f4e8;
}

.role-tag.role-blue {
  color: #0e5a6d;
  background: #d4f0f7;
}

.role-tag.role-orange {
  color: #8b4508;
  background: #fde8cf;
}

.role-tag.role-red {
  color: #991f29;
  background: #fde1e4;
}

.role-tag.role-purple {
  color: #5a4691;
  background: #ece5fb;
}

.role-tag.role-neutral,
.role-more {
  color: var(--text-secondary);
  background: #f1f5f9;
}

.empty-inline {
  color: #cbd5e1;
  font-size: 12px;
  font-style: italic;
}

.tabular {
  font-variant-numeric: tabular-nums;
}

.row-actions {
  justify-content: center;
  gap: 10px;
  position: relative;
}

.action-link {
  padding: 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
  transition: color 0.15s ease;
}

.action-link:hover {
  color: var(--accent);
  text-decoration: underline;
}

.action-dropdown {
  position: relative;
  display: inline-flex;
}

.action-more {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-more:hover {
  color: var(--accent-dark);
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.action-more svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
  stroke: none;
}

.action-dropdown:hover .action-menu {
  display: block;
}

.action-dropdown:focus-within .action-menu {
  display: block;
}

.action-menu {
  position: absolute;
  top: calc(100% - 2px);
  right: 0;
  z-index: 100;
  display: none;
  min-width: 130px;
  margin-top: 0;
  padding: 6px 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
}

.action-menu::before {
  position: absolute;
  top: -7px;
  right: 0;
  left: 0;
  height: 7px;
  content: '';
}

.action-menu button {
  display: block;
  width: 100%;
  padding: 8px 14px;
  color: var(--text);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.action-menu button:hover {
  background: #f8fafc;
}

.action-menu button.action-danger {
  color: #dc2626;
}

.action-menu button.action-danger:hover {
  background: #fef2f2;
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
  min-height: 54px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.footer-info-trigger {
  display: inline-flex;
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #94a3b8;
  background: transparent;
  border: 0;
  border-radius: 50%;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.footer-info-trigger:hover {
  color: var(--accent-dark);
  background: #f1f5f9;
}

.footer-info-trigger svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.footer-hint {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.5;
}

.footer-pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
}

.pagination-info {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.page-size-select {
  width: 100px;
  height: 32px;
  padding: 0 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.page-size-select:hover {
  border-color: var(--accent);
}

.page-size-select:focus {
  border-color: var(--accent);
  outline: none;
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-btn {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.pagination-btn:not(:disabled):hover {
  color: var(--accent-dark);
  background: #f8fafc;
  border-color: var(--accent);
}

.pagination-btn:disabled {
  color: #cbd5e1;
  background: #f8fafc;
  cursor: not-allowed;
}

.pagination-btn svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
}

.pagination-current {
  min-width: 32px;
  padding: 0 8px;
  color: var(--text);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  text-align: center;
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
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.35);
  color: var(--text, #172033);
  font-size: 14px;
}

.edit-drawer {
  display: flex;
  width: min(640px, 100vw);
  height: 100%;
  flex-direction: column;
  background: var(--panel-bg, #fff);
  box-shadow: -12px 0 32px rgba(15, 23, 42, 0.16);
}

.drawer-header {
  min-height: 78px;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border, #dfe5ec);
  box-sizing: border-box;
}

.drawer-header-main {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.avatar-upload {
  position: relative;
  display: inline-flex;
  width: 52px;
  height: 52px;
  flex: 0 0 52px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #275a4d;
  background-color: #e5e7eb;
  border: 1px solid var(--accent-border, #a9e5d2);
  border-radius: 50%;
  font: inherit;
  font-size: 18px;
  font-weight: 750;
  cursor: pointer;
  overflow: hidden;
}

.avatar-upload:hover {
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb, 15, 159, 120), 0.12);
}

.avatar-upload > i {
  position: absolute;
  right: -1px;
  bottom: -1px;
  display: inline-flex;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--accent, #0f9f78);
  border: 2px solid #fff;
  border-radius: 50%;
  font-size: 16px;
  font-style: normal;
  line-height: 1;
}

.avatar-upload-input {
  display: none;
}

.avatar-remove-button {
  display: block;
  margin-top: 4px;
  padding: 0;
  color: var(--text-muted, #8a96a8);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}

.avatar-remove-button:hover {
  color: #b4232f;
}

.summary-hint {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
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
  color: var(--text-secondary, #596579);
  background: var(--panel-bg, #fff);
  border: 1px solid var(--border-strong, #cbd5e1);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover {
  color: var(--accent-dark, #08745a);
  background: var(--accent-soft, #e9f8f3);
  border-color: var(--accent-border, #a9e5d2);
}

.drawer-body {
  flex: 1;
  padding: 20px 22px;
  color: var(--text, #172033);
  overflow-y: auto;
}

.form-section + .form-section {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid var(--border, #dfe5ec);
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

.drawer-footer {
  justify-content: flex-end;
  gap: 8px;
  padding: 13px 22px;
  border-top: 1px solid var(--border, #dfe5ec);
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
  border-bottom: 0;
  border-radius: 7px 7px 0 0;
  box-shadow: none;
  box-sizing: border-box;
}

.workspace-tab {
  position: relative;
  z-index: 1;
  display: inline-flex;
  min-width: 124px;
  height: 38px;
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

.workspace-tab:hover {
  color: var(--accent-dark);
  background: rgba(255, 255, 255, 0.62);
}

.workspace-tab.active {
  z-index: 2;
  color: var(--accent-dark);
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(203, 213, 225, 0.72);
}

.workspace-tab.active::before,
.workspace-tab.active::after {
  position: absolute;
  bottom: 0;
  width: 10px;
  height: 10px;
  content: '';
  pointer-events: none;
}

.workspace-tab.active::before {
  left: -10px;
  background: radial-gradient(circle at 0 0, transparent 9px, #fff 10px);
}

.workspace-tab.active::after {
  right: -10px;
  background: radial-gradient(circle at 100% 0, transparent 9px, #fff 10px);
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

.identity-card-avatar {
  display: inline-flex;
  width: 176px;
  height: 176px;
  flex: 0 0 176px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 4px solid #fff;
  box-shadow: 0 0 0 1px #dbe5e9, 0 5px 12px rgba(15, 23, 42, 0.08);
  font-size: 52px;
  font-weight: 750;
}

.identity-card {
  position: relative;
}

.identity-card-index {
  position: absolute;
  top: 18px;
  right: 20px;
}

.identity-card-layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 20px;
  align-items: stretch;
}

.identity-card-profile {
  display: flex;
  min-height: 190px;
  align-items: center;
  justify-content: center;
  padding-right: 20px;
  border-right: 1px solid #eef2f6;
}

.identity-info-grid {
  align-content: center;
  gap: 26px 24px;
}

.identity-card .identity-info-grid dt {
  font-size: 18px;
  line-height: 1.4;
}

.identity-card .identity-info-grid dd {
  margin-top: 8px;
  font-size: 18px;
  line-height: 1.4;
}

.identity-card .identity-info-grid > div:last-child dt {
  font-size: 18px;
  line-height: 1.4;
}

.identity-card .identity-info-grid > div:last-child dd {
  margin-top: 8px;
  font-size: 18px;
  line-height: 1.4;
}

.identity-card .identity-info-grid > div:last-child .mini-badge {
  min-height: 32px;
  gap: 8px;
  padding: 5px 14px;
  font-size: 18px;
}

.identity-card .identity-info-grid > div:last-child .mini-badge i {
  width: 8px;
  height: 8px;
  flex-basis: 8px;
}

.detail-tab-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 0 0 auto;
  gap: 8px;
  margin-left: auto;
}

.detail-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 10px;
  padding: 0 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02);
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
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02);
  box-sizing: border-box;
}

.detail-card {
  padding: 18px 20px;
}

.detail-card-heading,
.content-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.detail-card-heading {
  margin-bottom: 15px;
}

.heading-with-icon {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.heading-icon {
  width: 18px;
  height: 18px;
  margin-top: 1px;
  flex: 0 0 18px;
  fill: none;
  stroke: var(--accent);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.detail-card-heading h3,
.content-heading h3 {
  font-size: 14px;
  font-weight: 650;
  color: var(--text);
}

.detail-card-heading span:not(.card-index),
.content-heading > div > span {
  display: block;
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 400;
}

.card-index {
  color: #cbd5e1;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 20px;
  margin: 0;
}

.info-grid.single-column {
  grid-template-columns: 1fr;
  gap: 16px;
  margin-top: 0;
}

.info-grid div {
  min-width: 0;
}

.info-grid .scope-field {
  grid-column: 1 / -1;
}

.info-grid dt,
.info-grid dd {
  margin: 0;
}

.info-grid dt {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}

.info-grid dd {
  margin-top: 6px;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-grid dd.dd-primary {
  color: #1e293b;
  font-weight: 500;
}

.info-grid dd.dd-empty {
  color: #cbd5e1;
  font-style: italic;
}

.capsule-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.capsule-tag {
  display: inline-flex;
  min-height: 26px;
  align-items: center;
  padding: 4px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  box-sizing: border-box;
}

.capsule-tag.capsule-green {
  color: #0d7a5f;
  background: #d1f4e8;
  border: 1px solid #9de5cc;
}

.capsule-tag.capsule-blue {
  color: #0e5a6d;
  background: #d4f0f7;
  border: 1px solid #a1dce9;
}

.capsule-tag.capsule-orange {
  color: #8b4508;
  background: #fde8cf;
  border: 1px solid #f6c896;
}

.capsule-tag.capsule-purple {
  color: #5a4691;
  background: #ece5fb;
  border: 1px solid #d0c2f3;
}

.capsule-tag.capsule-red {
  color: #991f29;
  background: #fde1e4;
  border: 1px solid #f6b6bd;
}

.capsule-tag.capsule-neutral {
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
}

.mini-badge {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  box-sizing: border-box;
}

.mini-badge i {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  background: currentColor;
}

.mini-badge.status-success {
  color: #0d7a5f;
  background: #d1f4e8;
}

.mini-badge.status-warning {
  color: #8b4508;
  background: #fde8cf;
}

.mini-badge.status-info {
  color: #0e5a6d;
  background: #d4f0f7;
}

.mini-badge.status-disabled {
  color: #64748b;
  background: #f1f5f9;
}

.account-summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.account-username {
  display: block;
  margin-top: 6px;
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.account-security-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 1fr) auto;
  align-items: end;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.account-security-item {
  min-width: 0;
}

.account-security-item > strong {
  display: block;
  margin-top: 6px;
  overflow: hidden;
  color: #1e293b;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stored-password {
  display: flex;
  min-width: 0;
  height: 34px;
  align-items: center;
  gap: 6px;
}

.stored-password strong {
  overflow: hidden;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.button-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.15s ease;
}

.button-link:hover {
  color: var(--accent);
}

.button-link svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.password-edit-button {
  align-self: center;
}

.summary-label {
  display: block;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}

.assigned-role-section {
  margin-top: 16px;
}

.assigned-role-section .capsule-list {
  margin-top: 10px;
}

.assigned-role-section .dd-empty {
  display: block;
  margin-top: 10px;
  color: #cbd5e1;
  font-size: 13px;
  font-style: italic;
}

.password-input-wrap {
  position: relative;
  min-width: 0;
}

.password-input-wrap input {
  width: 100%;
  padding-right: 40px;
  box-sizing: border-box;
}

.password-toggle {
  display: inline-flex;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #94a3b8;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.password-input-wrap .password-toggle {
  position: absolute;
  top: 3px;
  right: 3px;
}

.password-toggle:hover {
  color: var(--accent-dark, #08745a);
  background: #e9f8f3;
}

.password-toggle svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.permission-summary-card {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
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
  padding: 18px 20px;
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
  align-items: start;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.employee-permission-module {
  align-self: start;
  min-width: 0;
  padding: 13px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
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
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 6px;
}

.employee-permission-chip {
  display: flex;
  flex: 0 1 auto;
  min-height: 29px;
  align-items: center;
  gap: 7px;
  max-width: 100%;
  padding: 4px 8px;
  color: var(--text-muted);
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 11px;
  line-height: 1.3;
  white-space: nowrap;
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
  padding: 11px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
}

.scope-summary span,
.scope-summary strong {
  display: block;
}

.scope-summary span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
}

.scope-summary strong {
  margin-top: 6px;
  color: #1e293b;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.5;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
.record-row:focus-visible {
  outline: 2px solid var(--accent, #0f9f78);
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

  .table-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }

  .footer-left {
    width: 100%;
  }

  .footer-pagination {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 780px) {
  .page-root {
    padding: 0;
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
    margin-right: 0;
    margin-left: 0;
  }

  .workspace-tab {
    min-width: 116px;
  }

  .detail-tab-actions {
    gap: 6px;
  }

  .detail-tab-actions .button {
    padding-right: 10px;
    padding-left: 10px;
  }

  .detail-tabs {
    margin-top: 8px;
  }

  .detail-tab {
    flex: 1;
    justify-content: center;
  }

  .account-security-grid {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .password-edit-button {
    justify-self: start;
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

  .identity-card-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .identity-card-profile {
    min-height: 160px;
    padding-right: 0;
    padding-bottom: 16px;
    border-right: 0;
    border-bottom: 1px solid #eef2f6;
  }

  .identity-card-avatar {
    width: 136px;
    height: 136px;
    flex-basis: 136px;
    font-size: 40px;
  }

  .identity-info-grid {
    gap: 18px 16px;
  }

  .identity-card .identity-info-grid dt {
    font-size: 18px;
  }

  .identity-card .identity-info-grid dd {
    font-size: 18px;
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

  .footer-left {
    width: 100%;
  }

  .footer-hint {
    font-size: 11px;
  }

  .footer-pagination {
    width: 100%;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .pagination-info {
    flex: 1 1 100%;
    margin-bottom: 8px;
  }

  .form-grid {
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
