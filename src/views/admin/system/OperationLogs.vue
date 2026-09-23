<template>
  <div class="operation-logs-page">
    <header class="page-heading">
      <div>
        <h1>操作日志</h1>
        <p>账号安全、权限配置与业务操作记录</p>
      </div>
      <div class="heading-actions">
        <button
          v-if="canClear"
          class="button button-danger"
          type="button"
          :disabled="loading || clearing"
          @click="clearLogs"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7h16M10 11v6m4-6v6M6 7l1 14h10l1-14M9 7V4h6v3" />
          </svg>
          {{ clearing ? '清空中...' : '清空日志' }}
        </button>
        <button
          class="button button-secondary"
          type="button"
          :disabled="loading"
          title="刷新"
          aria-label="刷新"
          @click="loadLogs"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 7v5h-5M4 17v-5h5" />
            <path d="M5.6 9a7 7 0 0 1 11.8-2L20 12M4 12l2.6 5a7 7 0 0 0 11.8-2" />
          </svg>
        </button>
      </div>
    </header>

    <section class="filter-bar" aria-label="日志筛选">
      <label class="filter-field date-field">
        <span>开始日期</span>
        <input v-model="filters.startDate" type="date" @change="search" />
      </label>
      <label class="filter-field date-field">
        <span>结束日期</span>
        <input v-model="filters.endDate" type="date" @change="search" />
      </label>
      <label class="filter-field">
        <span>操作人</span>
        <input
          v-model.trim="filters.actor"
          type="search"
          placeholder="姓名或账号"
          @keyup.enter="search"
        />
      </label>
      <label class="filter-field">
        <span>业务模块</span>
        <select v-model="filters.module" @change="search">
          <option value="">全部模块</option>
          <option v-for="module in modules" :key="module.code" :value="module.code">
            {{ module.name }}
          </option>
        </select>
      </label>
      <label class="filter-field">
        <span>操作类型</span>
        <select v-model="filters.action" @change="search">
          <option value="">全部操作</option>
          <option v-for="action in actions" :key="action.code" :value="action.code">
            {{ action.name }}
          </option>
        </select>
      </label>
      <label class="filter-field">
        <span>操作结果</span>
        <select v-model="filters.outcome" @change="search">
          <option value="">全部结果</option>
          <option value="success">成功</option>
          <option value="failure">失败</option>
        </select>
      </label>
      <label class="filter-field keyword-field">
        <span>关键字</span>
        <input
          v-model.trim="filters.keyword"
          type="search"
          placeholder="目标编号、路径或 IP"
          @keyup.enter="search"
        />
      </label>
      <div class="filter-actions">
        <button class="button button-primary" type="button" @click="search">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="10.8" cy="10.8" r="6.8" />
            <path d="m16 16 4.5 4.5" />
          </svg>
          查询
        </button>
        <button class="button button-quiet" type="button" @click="resetFilters">
          重置
        </button>
      </div>
    </section>

    <section class="table-panel">
      <div class="table-summary">
        <span>共 <strong>{{ total }}</strong> 条记录</span>
        <span v-if="errorMessage" class="inline-error" role="alert">{{ errorMessage }}</span>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>操作人</th>
              <th>来源</th>
              <th>业务模块</th>
              <th>操作</th>
              <th>操作对象</th>
              <th>结果</th>
              <th>IP 地址</th>
              <th class="detail-column">详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="9" class="state-cell">正在加载操作日志...</td>
            </tr>
            <tr v-else-if="logs.length === 0">
              <td colspan="9" class="state-cell">没有符合条件的操作记录</td>
            </tr>
            <template v-else>
              <tr v-for="log in logs" :key="log.id">
                <td class="time-cell">{{ formatDateTime(log.occurredAt) }}</td>
                <td>
                  <strong>{{ log.actorDisplayName || '未登录用户' }}</strong>
                  <small v-if="log.actorUsername">{{ log.actorUsername }}</small>
                </td>
                <td>
                  <span :class="['source-label', `source-${log.sourceSurface}`]">
                    {{ sourceName(log.sourceSurface) }}
                  </span>
                </td>
                <td>{{ log.moduleName }}</td>
                <td>{{ log.actionName }}</td>
                <td class="target-cell">
                  <span>{{ log.targetLabel || log.targetType || '-' }}</span>
                  <small v-if="log.targetId">#{{ log.targetId }}</small>
                </td>
                <td>
                  <span :class="['result-label', log.succeeded ? 'is-success' : 'is-failure']">
                    <i></i>{{ log.succeeded ? '成功' : `失败 · ${log.statusCode || '-'}` }}
                  </span>
                </td>
                <td class="mono-cell">{{ log.ipAddress || '-' }}</td>
                <td>
                  <button
                    class="icon-button"
                    type="button"
                    title="查看详情"
                    :aria-label="`查看 ${log.actorDisplayName || '用户'} 的操作详情`"
                    @click="selectedLog = log"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <circle cx="12" cy="12" r="9" />
                      <path d="M12 11v5m0-8h.01" />
                    </svg>
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <footer class="pagination">
        <label>
          每页
          <select v-model.number="pageSize" @change="search">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          条
        </label>
        <span>{{ page }} / {{ totalPages }} 页</span>
        <div class="page-buttons">
          <button
            type="button"
            title="上一页"
            aria-label="上一页"
            :disabled="page <= 1 || loading"
            @click="changePage(page - 1)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
          </button>
          <button
            type="button"
            title="下一页"
            aria-label="下一页"
            :disabled="page >= totalPages || loading"
            @click="changePage(page + 1)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
          </button>
        </div>
      </footer>
    </section>

    <Teleport to="body">
      <div v-if="selectedLog" class="detail-overlay" @click.self="selectedLog = null">
        <section
          class="detail-drawer"
          role="dialog"
          aria-modal="true"
          aria-labelledby="operation-log-detail-title"
          @keydown.esc="selectedLog = null"
        >
          <header class="drawer-header">
            <div>
              <span class="drawer-eyebrow">操作记录 #{{ selectedLog.id }}</span>
              <h2 id="operation-log-detail-title">
                {{ selectedLog.moduleName }} · {{ selectedLog.actionName }}
              </h2>
            </div>
            <button
              class="icon-button close-button"
              type="button"
              title="关闭"
              aria-label="关闭详情"
              @click="selectedLog = null"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
            </button>
          </header>
          <div class="drawer-body">
            <dl class="detail-grid">
              <div><dt>操作时间</dt><dd>{{ formatDateTime(selectedLog.occurredAt) }}</dd></div>
              <div><dt>操作人</dt><dd>{{ selectedLog.actorDisplayName || '未登录用户' }} <small>{{ selectedLog.actorUsername }}</small></dd></div>
              <div><dt>角色组</dt><dd>{{ selectedLog.actorRoleNames.join('、') || '-' }}</dd></div>
              <div><dt>来源</dt><dd>{{ sourceName(selectedLog.sourceSurface) }}</dd></div>
              <div><dt>请求</dt><dd><code>{{ selectedLog.requestMethod }} {{ selectedLog.requestPath }}</code></dd></div>
              <div><dt>目标</dt><dd>{{ selectedLog.targetType || '-' }} {{ selectedLog.targetId ? `#${selectedLog.targetId}` : '' }}</dd></div>
              <div><dt>结果</dt><dd>{{ selectedLog.succeeded ? '成功' : `失败（HTTP ${selectedLog.statusCode || '-'}）` }}</dd></div>
              <div><dt>IP 地址</dt><dd>{{ selectedLog.ipAddress || '-' }}</dd></div>
              <div class="detail-wide"><dt>请求字段</dt><dd>{{ selectedLog.details.fields?.join('、') || '无' }}</dd></div>
              <div class="detail-wide"><dt>筛选字段</dt><dd>{{ selectedLog.details.filters?.join('、') || '无' }}</dd></div>
              <div class="detail-wide"><dt>User-Agent</dt><dd class="breakable">{{ selectedLog.userAgent || '-' }}</dd></div>
              <div class="detail-wide"><dt>请求 ID</dt><dd><code>{{ selectedLog.requestId || '-' }}</code></dd></div>
            </dl>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { ADMIN_OPERATION_LOG_PERMISSIONS } from '@/utils/accessControl'

const userStore = useUserStore()
const loading = ref(false)
const clearing = ref(false)
const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const selectedLog = ref(null)
const errorMessage = ref('')
const filters = reactive({
  startDate: '',
  endDate: '',
  actor: '',
  module: '',
  action: '',
  outcome: '',
  keyword: ''
})

const canClear = computed(() =>
  userStore.hasPerm(ADMIN_OPERATION_LOG_PERMISSIONS.CLEAR)
)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const modules = [
  { code: 'account_security', name: '账号安全' },
  { code: 'role_permissions', name: '角色权限' },
  { code: 'employees', name: '员工管理' },
  { code: 'departments', name: '部门管理' },
  { code: 'sales_orders', name: '销售订单' },
  { code: 'logistics', name: '物流管理' },
  { code: 'raw_materials', name: '原材料' },
  { code: 'inventory', name: '库存管理' },
  { code: 'payment_history', name: '收款历史' },
  { code: 'bank_accounts', name: '银行账户' },
  { code: 'print_templates', name: '打印模板' },
  { code: 'operation_logs', name: '操作日志' }
]
const actions = [
  { code: 'create', name: '新增' },
  { code: 'update', name: '修改' },
  { code: 'delete', name: '删除' },
  { code: 'login_success', name: '登录成功' },
  { code: 'login_failure', name: '登录失败' },
  { code: 'logout', name: '退出登录' },
  { code: 'password_change', name: '修改密码' },
  { code: 'password_reset', name: '重置密码' },
  { code: 'clear', name: '清空日志' }
]

function formatDateTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

function sourceName(value) {
  return ({ admin: '后台', touch: '触屏端', web: '网页', api: 'API' })[value] || 'API'
}

async function loadLogs() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request.get('/admin/operation-logs', {
      params: {
        ...filters,
        page: page.value,
        pageSize: pageSize.value
      }
    })
    logs.value = response.items || []
    total.value = Number(response.total || 0)
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '操作日志加载失败'
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  loadLogs()
}

function resetFilters() {
  Object.assign(filters, {
    startDate: '',
    endDate: '',
    actor: '',
    module: '',
    action: '',
    outcome: '',
    keyword: ''
  })
  search()
}

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return
  page.value = nextPage
  loadLogs()
}

async function clearLogs() {
  if (!window.confirm('确定清空所有操作日志吗？清空操作本身仍会保留一条记录。')) return
  clearing.value = true
  errorMessage.value = ''
  try {
    const response = await request.delete('/admin/operation-logs')
    total.value = 0
    page.value = 1
    await loadLogs()
    window.alert(response.message || '操作日志已清空')
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '清空操作日志失败'
  } finally {
    clearing.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.operation-logs-page {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --border: #dfe6ec;
  --text: #172033;
  --muted: #778397;
  min-width: 0;
  color: var(--text);
}

.page-heading,
.heading-actions,
.filter-actions,
.pagination,
.page-buttons,
.table-summary {
  display: flex;
  align-items: center;
}

.page-heading {
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 16px;
}

.page-heading h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.35;
  font-weight: 680;
}

.page-heading p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.heading-actions {
  gap: 8px;
}

.button {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
}

.button svg,
.icon-button svg,
.page-buttons svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.button:disabled,
.page-buttons button:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

.button-primary {
  color: #fff;
  background: var(--accent);
}

.button-primary:hover:not(:disabled) {
  background: var(--accent-dark);
}

.button-secondary {
  color: #344054;
  background: #fff;
  border-color: #cfd8e3;
}

.button-danger {
  color: #b4232f;
  background: #fff;
  border-color: #f0c8cc;
}

.button-danger:hover:not(:disabled) {
  background: #fff4f4;
}

.button-quiet {
  color: #526074;
  background: transparent;
  border-color: #d6dee7;
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(6, minmax(120px, 1fr));
  gap: 12px;
  align-items: end;
  padding: 14px;
  margin-bottom: 14px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.filter-field {
  display: grid;
  min-width: 0;
  gap: 6px;
}

.filter-field > span {
  color: #526074;
  font-size: 12px;
  font-weight: 600;
}

.filter-field input,
.filter-field select,
.pagination select {
  width: 100%;
  min-width: 0;
  height: 36px;
  padding: 0 9px;
  color: var(--text);
  background: #fff;
  border: 1px solid #d5dde7;
  border-radius: 4px;
  font: inherit;
  font-size: 13px;
}

.filter-field input:focus,
.filter-field select:focus,
.pagination select:focus {
  outline: 2px solid #a9e5d2;
  outline-offset: 1px;
  border-color: var(--accent);
}

.keyword-field {
  grid-column: span 2;
}

.filter-actions {
  grid-column: span 4;
  justify-content: flex-end;
  gap: 8px;
}

.table-panel {
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.table-summary {
  min-height: 44px;
  justify-content: space-between;
  padding: 0 14px;
  color: var(--muted);
  font-size: 12px;
  border-bottom: 1px solid #e8edf2;
}

.table-summary strong {
  color: var(--accent-dark);
  font-variant-numeric: tabular-nums;
}

.inline-error {
  color: #b4232f;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 1040px;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  height: 48px;
  padding: 0 12px;
  text-align: left;
  border-bottom: 1px solid #edf0f3;
  white-space: nowrap;
}

th {
  height: 40px;
  color: #667287;
  background: #f8fafb;
  font-size: 12px;
  font-weight: 650;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover:not(:has(.state-cell)) {
  background: #fbfdfd;
}

td strong,
td small {
  display: block;
}

td strong {
  font-weight: 600;
}

td small {
  margin-top: 3px;
  color: var(--muted);
  font-size: 11px;
}

.time-cell,
.mono-cell,
code {
  font-variant-numeric: tabular-nums;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
}

.target-cell {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-label,
.result-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.source-label {
  padding: 3px 7px;
  color: #475467;
  background: #f1f4f7;
  border-radius: 3px;
  font-size: 11px;
}

.source-admin {
  color: #08745a;
  background: #e9f8f3;
}

.source-touch {
  color: #975a16;
  background: #fff5e7;
}

.result-label {
  font-size: 12px;
}

.result-label i {
  width: 7px;
  height: 7px;
  background: currentColor;
  border-radius: 50%;
}

.is-success {
  color: #08745a;
}

.is-failure {
  color: #b4232f;
}

.icon-button,
.page-buttons button {
  display: inline-grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: #526074;
  background: #fff;
  border: 1px solid #d6dee7;
  border-radius: 4px;
  cursor: pointer;
}

.icon-button:hover,
.page-buttons button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: #a9e5d2;
}

.state-cell {
  height: 150px;
  color: var(--muted);
  text-align: center;
}

.pagination {
  min-height: 54px;
  justify-content: flex-end;
  gap: 16px;
  padding: 0 14px;
  color: #667287;
  font-size: 12px;
  border-top: 1px solid #e8edf2;
}

.pagination label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pagination select {
  width: 72px;
  height: 30px;
}

.page-buttons {
  gap: 6px;
}

.page-buttons button {
  width: 30px;
  height: 30px;
}

.detail-overlay {
  position: fixed;
  z-index: 3000;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgb(15 23 42 / 34%);
}

.detail-drawer {
  display: flex;
  width: min(560px, 100%);
  height: 100%;
  flex-direction: column;
  background: #fff;
  box-shadow: -12px 0 32px rgb(15 23 42 / 14%);
}

.drawer-header {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.drawer-eyebrow {
  color: var(--muted);
  font-size: 11px;
}

.drawer-header h2 {
  margin: 5px 0 0;
  font-size: 17px;
  line-height: 1.4;
}

.close-button {
  flex: 0 0 auto;
}

.drawer-body {
  overflow-y: auto;
  padding: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 18px;
  margin: 0;
}

.detail-grid > div {
  min-width: 0;
  padding: 13px 0;
  border-bottom: 1px solid #edf0f3;
}

.detail-grid dt {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
}

.detail-grid dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--text);
  font-size: 13px;
  line-height: 1.55;
}

.detail-grid dd small {
  display: block;
  color: var(--muted);
  font-size: 11px;
}

.detail-grid code {
  white-space: normal;
  overflow-wrap: anywhere;
}

.detail-wide {
  grid-column: 1 / -1;
}

.breakable {
  word-break: break-word;
}

@media (max-width: 1100px) {
  .filter-bar {
    grid-template-columns: repeat(3, minmax(120px, 1fr));
  }

  .keyword-field {
    grid-column: span 2;
  }

  .filter-actions {
    grid-column: span 1;
  }
}

@media (max-width: 680px) {
  .page-heading {
    align-items: flex-start;
  }

  .page-heading h1 {
    font-size: 18px;
  }

  .page-heading p {
    max-width: 34ch;
    line-height: 1.5;
  }

  .heading-actions {
    flex: 0 0 auto;
  }

  .button-danger {
    padding: 0 8px;
  }

  .filter-bar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    padding: 12px;
  }

  .date-field,
  .keyword-field {
    grid-column: span 1;
  }

  .filter-actions {
    grid-column: 1 / -1;
  }

  .pagination {
    justify-content: space-between;
    gap: 8px;
    padding: 0 10px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-wide {
    grid-column: auto;
  }
}
</style>
