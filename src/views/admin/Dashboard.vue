<template>
  <main class="dashboard-page">
    <header class="dashboard-header">
      <div>
        <h1>经营概览</h1>
        <p>{{ todayLabel }}<span v-if="refreshedAt"> · 更新于 {{ formatTime(refreshedAt) }}</span></p>
      </div>
      <button
        class="icon-button"
        type="button"
        title="刷新数据"
        aria-label="刷新数据"
        :disabled="loading"
        @click="loadDashboard"
      >
        <RefreshCw :size="17" :class="{ spinning: loading }" aria-hidden="true" />
      </button>
    </header>

    <div v-if="!canReadOrders" class="access-notice" role="status">
      当前账号没有订单读取权限，订单指标暂不可用。
    </div>

    <section class="summary-grid" aria-label="经营摘要" :aria-busy="loading">
      <article v-for="stat in summaryStats" :key="stat.label" class="summary-item">
        <span class="summary-icon" :class="`tone-${stat.tone}`">
          <component :is="stat.icon" :size="19" aria-hidden="true" />
        </span>
        <div class="summary-copy">
          <span class="summary-label">{{ stat.label }}</span>
          <strong class="summary-value">{{ stat.value }}</strong>
          <small>{{ stat.detail }}</small>
        </div>
      </article>
    </section>

    <div v-if="orderError" class="load-error" role="alert">
      <span>{{ orderError }}</span>
      <button type="button" :disabled="loading" @click="loadDashboard">重试</button>
    </div>
    <div v-if="inventoryError" class="load-error" role="alert">
      <span>{{ inventoryError }}</span>
      <button type="button" :disabled="loading" @click="loadDashboard">重试</button>
    </div>

    <section class="dashboard-columns">
      <section class="dashboard-panel trend-panel">
        <header class="panel-header">
          <div>
            <h2>订单趋势</h2>
            <p>{{ trendRangeLabel }}</p>
          </div>
          <div class="range-control" role="group" aria-label="趋势周期">
            <button
              v-for="option in rangeOptions"
              :key="option.value"
              type="button"
              :class="{ active: selectedRange === option.value }"
              :aria-pressed="selectedRange === option.value"
              @click="selectedRange = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </header>

        <div v-if="loading && orders === null" class="chart-message" role="status">正在加载订单数据…</div>
        <div v-else-if="!canReadOrders" class="chart-message">暂无可显示的数据</div>
        <div v-else-if="orderError" class="chart-message">订单数据加载失败</div>
        <div v-else class="chart-content">
          <svg
            class="trend-chart"
            viewBox="0 0 720 240"
            role="img"
            :aria-label="`${trendRangeLabel}订单数量趋势`"
          >
            <line v-for="line in gridLines" :key="line.y" x1="42" :y1="line.y" x2="704" :y2="line.y" />
            <text v-for="line in gridLines" :key="`label-${line.y}`" x="32" :y="line.y + 4" text-anchor="end">
              {{ line.value }}
            </text>
            <polyline v-if="chartPolyline" :points="chartPolyline" />
            <circle
              v-for="point in chartPoints"
              :key="point.key"
              :cx="point.x"
              :cy="point.y"
              r="3.5"
            >
              <title>{{ point.label }}：{{ formatCount(point.count) }} 单</title>
            </circle>
            <text
              v-for="tick in chartTicks"
              :key="tick.key"
              class="axis-label"
              :x="tick.x"
              y="228"
              text-anchor="middle"
            >
              {{ tick.label }}
            </text>
          </svg>
          <div v-if="rangeOrderCount === 0" class="empty-range">所选周期暂无订单</div>
          <div class="trend-footer">
            <span><i class="legend-dot" aria-hidden="true"></i>订单数量</span>
            <strong>{{ formatCount(rangeOrderCount) }} 单</strong>
            <span class="trend-divider"></span>
            <span>订单金额</span>
            <strong>{{ formatMoney(rangeOrderAmount) }}</strong>
          </div>
        </div>
      </section>

      <section class="dashboard-panel todo-panel">
        <header class="panel-header">
          <div>
            <h2>订单待办</h2>
            <p>当前可见订单</p>
          </div>
          <ClipboardList :size="19" class="panel-heading-icon" aria-hidden="true" />
        </header>

        <div v-if="!canReadOrders && !canReadFinishedProducts" class="panel-message">暂无可显示的数据</div>
        <div v-else-if="!todoItems.length" class="panel-message" role="status">
          {{ loading ? '正在加载…' : (orderError || inventoryError ? '待办数据加载失败' : '暂无可显示的数据') }}
        </div>
        <div v-else class="todo-list">
          <button
            v-for="item in todoItems"
            :key="item.label"
            type="button"
            class="todo-row"
            :disabled="!item.path"
            :title="item.path ? `打开${item.label}` : '当前账号没有对应页面权限'"
            @click="item.path && navigate(item.path)"
          >
            <span class="todo-icon" :class="`tone-${item.tone}`">
              <component :is="item.icon" :size="17" aria-hidden="true" />
            </span>
            <span class="todo-label">{{ item.label }}</span>
            <strong class="todo-count">{{ formatCount(item.count) }}</strong>
            <ArrowUpRight v-if="item.path" :size="15" class="todo-arrow" aria-hidden="true" />
          </button>
        </div>
      </section>
    </section>

    <section class="dashboard-columns lower-columns">
      <section class="dashboard-panel product-panel">
        <header class="panel-header">
          <div>
            <h2>商品概览</h2>
            <p>成品档案与库存状态</p>
          </div>
          <PackageCheck :size="19" class="panel-heading-icon" aria-hidden="true" />
        </header>
        <div v-if="!canReadFinishedProducts" class="panel-message">当前账号没有成品库存读取权限。</div>
        <div v-else-if="inventoryError" class="panel-message error-text" role="alert">
          {{ inventoryError }}
          <button type="button" :disabled="loading" @click="loadDashboard">重试</button>
        </div>
        <div v-else-if="loading && inventorySummary === null" class="panel-message" role="status">正在加载…</div>
        <div v-else class="product-overview">
          <div class="product-metrics">
            <div>
              <span>商品档案</span>
              <strong>{{ formatCount(inventorySummary?.products?.total || 0) }}</strong>
            </div>
            <div>
              <span>启用商品</span>
              <strong>{{ formatCount(activeInventoryProductCount) }}</strong>
            </div>
            <div>
              <span>库存预警</span>
              <strong>{{ formatCount(lowStockProductCount) }}</strong>
            </div>
          </div>
          <div class="product-bar-list">
            <div v-for="item in productOverviewBars" :key="item.label" class="product-bar-row">
              <span>{{ item.label }}</span>
              <div class="product-bar-track">
                <span :class="`tone-${item.tone}`" :style="{ width: `${item.width}%` }"></span>
              </div>
              <strong>{{ formatCount(item.value) }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="dashboard-panel staff-panel">
        <header class="panel-header">
          <div>
            <h2>员工概览</h2>
            <p>员工档案数据</p>
          </div>
          <Users :size="19" class="panel-heading-icon" aria-hidden="true" />
        </header>
        <div v-if="!canReadEmployees" class="panel-message">当前账号没有员工读取权限。</div>
        <div v-else-if="employeeError" class="panel-message error-text" role="alert">
          {{ employeeError }}
          <button type="button" :disabled="loading" @click="loadDashboard">重试</button>
        </div>
        <div v-else-if="loading && employees === null" class="panel-message" role="status">正在加载…</div>
        <div v-else class="staff-metrics">
          <div>
            <span>员工档案</span>
            <strong>{{ formatCount(employees?.length || 0) }}</strong>
          </div>
          <div>
            <span>在职员工</span>
            <strong>{{ formatCount(activeEmployeeCount) }}</strong>
          </div>
          <div>
            <span>启用账号</span>
            <strong>{{ formatCount(activeAccountCount) }}</strong>
          </div>
        </div>
      </section>

      <section class="dashboard-panel links-panel">
        <header class="panel-header">
          <div>
            <h2>快捷入口</h2>
            <p>常用业务页面</p>
          </div>
        </header>
        <div v-if="quickLinks.length" class="quick-links">
          <button
            v-for="link in quickLinks"
            :key="link.label"
            type="button"
            class="quick-link"
            @click="navigate(link.path)"
          >
            <component :is="link.icon" :size="17" aria-hidden="true" />
            <span>{{ link.label }}</span>
            <ArrowUpRight :size="14" class="quick-link-arrow" aria-hidden="true" />
          </button>
        </div>
        <div v-else class="panel-message">暂无可用入口</div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowUpRight,
  BadgeCheck,
  ClipboardList,
  PackageCheck,
  RefreshCw,
  ShoppingCart,
  Truck,
  Users
} from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { ADMIN_SALES_ORDER_PERMISSIONS, ADMIN_EMPLOYEE_PERMISSIONS } from '@/utils/accessControl'
import { ADMIN_ROUTE_BRANCH_PERMISSIONS } from '@/utils/adminAccess'
import { PERMISSIONS } from '@/utils/constants'
import { getOrderGroups, getOrderTrend, sumOrderAmounts } from '@/utils/dashboard'

const setHeaderActions = inject('setHeaderActions', null)
const router = useRouter()
const userStore = useUserStore()
const orders = ref(null)
const employees = ref(null)
const inventorySummary = ref(null)
const loading = ref(false)
const orderError = ref('')
const employeeError = ref('')
const inventoryError = ref('')
const refreshedAt = ref(null)
const now = ref(new Date())
let loadVersion = 0
let disposed = false
const selectedRange = ref('week')
const rangeOptions = [
  { value: 'day', label: '日' },
  { value: 'week', label: '周' },
  { value: 'month', label: '月' }
]

const canReadOrders = computed(() => userStore.hasPerm(PERMISSIONS.ORDER_READ))
const canReadEmployees = computed(() => userStore.hasPerm(ADMIN_EMPLOYEE_PERMISSIONS.READ))
const canReadInventory = computed(() => (
  userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS)
  || userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIALS)
))
const canReadFinishedProducts = computed(() => userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS))
const todayLabel = computed(() => new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
}).format(now.value))
const numberValue = value => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}
const orderGroups = computed(() => getOrderGroups(orders.value || [], now.value))

const moneyFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})
const countFormatter = new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 })
const formatMoney = value => moneyFormatter.format(numberValue(value))
const formatCount = value => countFormatter.format(numberValue(value))
const formatTime = date => new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit',
  minute: '2-digit'
}).format(date)

const summaryStats = computed(() => [
  {
    label: '今日订单',
    value: canReadOrders.value && orders.value ? formatCount(orderGroups.value.today.length) : '--',
    detail: '按订单日期',
    icon: ShoppingCart,
    tone: 'green'
  },
  {
    label: '今日订单额',
    value: canReadOrders.value && orders.value
      ? formatMoney(sumOrderAmounts(orderGroups.value.today))
      : '--',
    detail: '订单应收金额（非实收）',
    icon: ClipboardList,
    tone: 'blue'
  },
  {
    label: '库存总值',
    value: canReadInventory.value && inventorySummary.value !== null
      ? formatMoney(inventorySummary.value.inventoryAmount)
      : '--',
    detail: inventoryError.value ? '库存加载失败' : '已入账库存成本（不含税）',
    icon: PackageCheck,
    tone: 'amber'
  },
  {
    label: '本月完成订单额',
    value: canReadOrders.value && orders.value
      ? formatMoney(sumOrderAmounts(orderGroups.value.completed))
      : '--',
    detail: '已完成及已发货',
    icon: BadgeCheck,
    tone: 'coral'
  }
])

const chartBuckets = computed(() => getOrderTrend(orders.value || [], selectedRange.value, now.value))

const trendRangeLabel = computed(() => {
  if (selectedRange.value === 'day') return '今日 · 按小时'
  if (selectedRange.value === 'week') return '本周 · 按日'
  return '本月 · 按日'
})
const rangeOrderCount = computed(() => chartBuckets.value.reduce((sum, bucket) => sum + bucket.count, 0))
const rangeOrderAmount = computed(() => sumOrderAmounts(chartBuckets.value.map(bucket => ({ should_receive: bucket.amount }))))
const chartMaximum = computed(() => Math.max(3, Math.ceil(Math.max(0, ...chartBuckets.value.map(bucket => bucket.count)) / 3) * 3))
const gridLines = computed(() => {
  return [0, 1, 2, 3].map(index => ({
    y: 28 + index * 52,
    value: chartMaximum.value * (3 - index) / 3
  }))
})
const chartPoints = computed(() => {
  const buckets = chartBuckets.value
  if (!buckets.length) return []
  const span = 662 / Math.max(1, buckets.length - 1)
  return buckets.map((bucket, index) => ({
    ...bucket,
    x: buckets.length === 1 ? 373 : 42 + index * span,
    y: 184 - (bucket.count / chartMaximum.value) * 156
  }))
})
const chartPolyline = computed(() => chartPoints.value.map(point => `${point.x},${point.y}`).join(' '))
const chartTicks = computed(() => {
  const points = chartPoints.value
  if (!points.length) return []
  const indexes = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])]
  return indexes.map(index => ({
    key: points[index].key,
    x: points[index].x,
    label: points[index].label
  }))
})

const todoItems = computed(() => [
  {
    label: '待处理订单',
    count: orderGroups.value.pending.length,
    icon: ClipboardList,
    tone: 'amber',
    path: userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS) ? '/admin/sales' : null
  },
  {
    label: '待补充物流',
    count: orderGroups.value.logistics.length,
    icon: Truck,
    tone: 'blue',
    path: userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.LOGISTICS) ? '/admin/sales/logistics' : null
  },
  {
    label: '待过账销售单',
    count: orderGroups.value.audit.length,
    icon: BadgeCheck,
    tone: 'coral',
    path: userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS) ? '/admin/sales' : null
  }
].filter(() => canReadOrders.value && orders.value !== null).concat(
  canReadFinishedProducts.value && inventorySummary.value?.products
    ? [{
        label: '商品库存预警',
        count: lowStockProductCount.value,
        icon: PackageCheck,
        tone: 'amber',
        path: '/admin/inventory'
      }]
    : []
))

const activeEmployeeCount = computed(() => employees.value?.filter(employee => (
  ['active', 'probation'].includes(employee.employmentStatus)
)).length || 0)
const activeAccountCount = computed(() => employees.value?.filter(employee => (
  employee.accountStatus === 'active'
)).length || 0)
const activeInventoryProductCount = computed(() => inventorySummary.value?.products?.enabled || 0)
const lowStockProductCount = computed(() => inventorySummary.value?.products?.lowStock || 0)
const productOverviewBars = computed(() => {
  const total = inventorySummary.value?.products?.total || 0
  const enabled = activeInventoryProductCount.value
  const disabled = inventorySummary.value?.products?.disabled || 0
  const maximum = Math.max(1, total)
  return [
    { label: '启用商品', value: enabled, width: enabled / maximum * 100, tone: 'green' },
    { label: '库存预警', value: lowStockProductCount.value, width: lowStockProductCount.value / maximum * 100, tone: 'amber' },
    { label: '停用商品', value: disabled, width: disabled / maximum * 100, tone: 'coral' }
  ]
})

const quickLinks = computed(() => {
  const links = []
  if (userStore.hasPerm(ADMIN_SALES_ORDER_PERMISSIONS.CREATE)
    && userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS)) {
    links.push({ label: '新增订单', path: '/admin/sales/create', icon: ShoppingCart })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS)) {
    links.push({ label: '订单列表', path: '/admin/sales', icon: ClipboardList })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.LOGISTICS)) {
    links.push({ label: '物流订单', path: '/admin/sales/logistics', icon: Truck })
  }
  if (canReadEmployees.value) {
    links.push({ label: '员工管理', path: '/admin/hr/employees', icon: Users })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS)) {
    links.push({ label: '库存管理', path: '/admin/inventory', icon: PackageCheck })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIALS)) {
    links.push({ label: '原材料库存', path: '/admin/inventory/materials', icon: PackageCheck })
  }
  return links
})

const navigate = path => router.push(path)

const loadDashboard = async () => {
  const version = ++loadVersion
  const current = () => !disposed && version === loadVersion
  now.value = new Date()
  loading.value = true
  orderError.value = ''
  employeeError.value = ''
  inventoryError.value = ''
  const tasks = []
  if (canReadOrders.value) {
    tasks.push(request.get('/orders').then(data => {
      if (!current()) return
      if (!Array.isArray(data)) throw new Error('订单数据格式无效')
      orders.value = data
      orderError.value = ''
    }).catch(error => {
      if (!current()) return
      orders.value = null
      orderError.value = error?.response?.data?.message || error.message || '订单数据加载失败，请重试。'
    }))
  } else {
    orders.value = null
    orderError.value = ''
  }

  if (canReadEmployees.value) {
    tasks.push(request.get('/admin/employees').then(data => {
      if (!current()) return
      if (!data || !Array.isArray(data.employees)) throw new Error('员工数据格式无效')
      employees.value = data.employees
      employeeError.value = ''
    }).catch(error => {
      if (!current()) return
      employees.value = null
      employeeError.value = error?.response?.data?.message || error.message || '员工数据加载失败，请重试。'
    }))
  } else {
    employees.value = null
    employeeError.value = ''
  }

  if (canReadInventory.value) {
    tasks.push(request.get('/admin/dashboard/inventory').then(data => {
      if (!current()) return
      if (!data?.success || !Number.isFinite(data.inventoryAmount)
        || (canReadFinishedProducts.value && !['total', 'enabled', 'disabled', 'lowStock']
          .every(key => Number.isInteger(data.products?.[key]) && data.products[key] >= 0))) {
        throw new Error('库存概览数据格式无效')
      }
      inventorySummary.value = data
    }).catch(error => {
      if (!current()) return
      inventorySummary.value = null
      inventoryError.value = error?.response?.data?.message || error.message || '库存数据加载失败，请重试。'
    }))
  } else {
    inventorySummary.value = null
  }

  try {
    await Promise.all(tasks)
    if (current() && tasks.length && !orderError.value && !employeeError.value && !inventoryError.value) {
      refreshedAt.value = new Date()
    }
  } finally {
    if (current()) loading.value = false
  }
}

onMounted(() => {
  setHeaderActions?.(null)
  void loadDashboard()
})

watch(() => [userStore.id, userStore.isSuperAdmin, userStore.permissions, userStore.storeIds, userStore.warehouseIds, userStore.allStores, userStore.allWarehouses], () => {
  orders.value = null
  employees.value = null
  inventorySummary.value = null
  refreshedAt.value = null
  void loadDashboard()
}, { deep: true })

onUnmounted(() => {
  disposed = true
  loadVersion += 1
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 18px;
  color: #172033;
}

.dashboard-header,
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.dashboard-header p,
.panel-header p {
  margin: 5px 0 0;
  color: #718096;
  font-size: 13px;
}

.icon-button {
  display: inline-grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  border: 1px solid #dbe3eb;
  border-radius: 6px;
  background: #fff;
  color: #526174;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  border-color: #0f9f78;
  color: #08745a;
}

.icon-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.spinning {
  animation: spin 0.9s linear infinite;
}

.access-notice,
.load-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 13px;
  border: 1px solid #f2d19d;
  border-radius: 6px;
  background: #fff9ed;
  color: #87560d;
  font-size: 13px;
}

.load-error {
  border-color: #f0c4c4;
  background: #fff5f5;
  color: #a33333;
}

.load-error button,
.panel-message button {
  border: 0;
  background: transparent;
  color: #08745a;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
}

.load-error button:disabled,
.panel-message button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-item {
  display: flex;
  min-width: 0;
  min-height: 105px;
  align-items: center;
  gap: 13px;
  padding: 16px;
  border: 1px solid #e1e7ee;
  border-radius: 7px;
  background: #fff;
}

.summary-icon,
.todo-icon {
  display: inline-grid;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 7px;
}

.summary-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  color: #64748b;
  font-size: 12px;
}

.summary-value {
  color: #172033;
  font-size: 21px;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.summary-copy small {
  color: #8a96a6;
  font-size: 11px;
}

.tone-green {
  background: #e7f6f0;
  color: #08745a;
}

.tone-blue {
  background: #e9f2fb;
  color: #286496;
}

.tone-amber {
  background: #fff3df;
  color: #a45c0a;
}

.tone-coral {
  background: #fff0eb;
  color: #bd513b;
}

.dashboard-columns {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 1fr);
  gap: 14px;
}

.lower-columns {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.dashboard-panel {
  min-width: 0;
  padding: 18px;
  border: 1px solid #e1e7ee;
  border-radius: 7px;
  background: #fff;
}

.panel-header {
  min-height: 38px;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.panel-header p {
  font-size: 12px;
}

.panel-heading-icon {
  flex: 0 0 auto;
  color: #748397;
}

.range-control {
  display: inline-flex;
  flex: 0 0 auto;
  padding: 3px;
  border: 1px solid #e1e7ee;
  border-radius: 6px;
  background: #f7f9fb;
}

.range-control button {
  min-width: 38px;
  min-height: 30px;
  padding: 4px 9px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #64748b;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.range-control button.active {
  background: #fff;
  color: #08745a;
  box-shadow: 0 1px 3px rgba(23, 32, 51, 0.12);
}

.range-control button:focus-visible,
.todo-row:focus-visible,
.quick-link:focus-visible,
.icon-button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.chart-message,
.panel-message {
  display: flex;
  min-height: 170px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #8290a1;
  font-size: 13px;
  text-align: center;
}

.chart-content {
  position: relative;
}

.trend-chart {
  display: block;
  width: 100%;
  height: 240px;
  overflow: visible;
}

.trend-chart line {
  stroke: #e8edf2;
  stroke-width: 1;
}

.trend-chart > text {
  fill: #8a96a6;
  font-size: 10px;
}

.trend-chart .axis-label {
  fill: #69788a;
  font-size: 11px;
}

.trend-chart polyline {
  fill: none;
  stroke: #0f9f78;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2.5;
}

.trend-chart circle {
  fill: #fff;
  stroke: #0f9f78;
  stroke-width: 2;
}

.empty-range {
  position: absolute;
  inset: 72px 0 auto;
  color: #9aa5b3;
  font-size: 12px;
  text-align: center;
  pointer-events: none;
}

.trend-footer {
  display: flex;
  min-height: 40px;
  align-items: center;
  gap: 9px;
  padding-top: 11px;
  border-top: 1px solid #edf0f4;
  color: #69788a;
  font-size: 12px;
}

.trend-footer strong {
  color: #172033;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 5px;
  border-radius: 50%;
  background: #0f9f78;
}

.trend-divider {
  width: 1px;
  height: 16px;
  margin: 0 4px;
  background: #dce3ea;
}

.todo-list {
  display: flex;
  flex-direction: column;
}

.todo-row {
  display: flex;
  min-width: 0;
  min-height: 56px;
  align-items: center;
  gap: 11px;
  padding: 7px 2px;
  border: 0;
  border-bottom: 1px solid #edf0f4;
  background: transparent;
  color: inherit;
  text-align: left;
}

.todo-row:last-child {
  border-bottom: 0;
}

.todo-row:not(:disabled) {
  cursor: pointer;
}

.todo-row:not(:disabled):hover .todo-label,
.quick-link:hover span {
  color: #08745a;
}

.todo-row:disabled {
  cursor: default;
}

.todo-icon {
  flex-basis: 34px;
  width: 34px;
  height: 34px;
}

.todo-label {
  min-width: 0;
  flex: 1;
  overflow-wrap: anywhere;
  color: #465568;
  font-size: 13px;
}

.todo-count {
  min-width: 26px;
  color: #172033;
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.todo-arrow,
.quick-link-arrow {
  flex: 0 0 auto;
  color: #9aa5b3;
}

.staff-metrics,
.product-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.staff-metrics > div,
.product-metrics > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  padding: 7px 14px;
  border-right: 1px solid #edf0f4;
}

.staff-metrics > div:first-child,
.product-metrics > div:first-child {
  padding-left: 0;
}

.staff-metrics > div:last-child,
.product-metrics > div:last-child {
  padding-right: 0;
  border-right: 0;
}

.staff-metrics span,
.product-metrics span {
  color: #718096;
  font-size: 12px;
}

.staff-metrics strong,
.product-metrics strong {
  color: #172033;
  font-size: 22px;
  font-variant-numeric: tabular-nums;
}

.error-text {
  color: #a33333;
}

.product-bar-list {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.product-bar-row {
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) 36px;
  gap: 10px;
  align-items: center;
  font-size: 12px;
  color: #64748b;
}

.product-bar-row strong {
  text-align: right;
  color: #172033;
  overflow-wrap: anywhere;
}

.product-bar-track {
  height: 6px;
  overflow: hidden;
  border-radius: 3px;
  background: #edf0f4;
}

.product-bar-track > span {
  display: block;
  height: 100%;
  background: currentColor;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.quick-link {
  display: flex;
  min-width: 0;
  min-height: 42px;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  border: 1px solid #e1e7ee;
  border-radius: 5px;
  background: #fff;
  color: #64748b;
  cursor: pointer;
  text-align: left;
}

.quick-link > svg:first-child {
  flex: 0 0 auto;
  color: #08745a;
}

.quick-link span {
  min-width: 0;
  flex: 1;
  overflow-wrap: anywhere;
  color: #465568;
  font-size: 12px;
}

.quick-link:hover {
  border-color: #a9e5d2;
  background: #f7fcfa;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1000px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-columns {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 620px) {
  .dashboard-page {
    gap: 12px;
  }

  .dashboard-header h1 {
    font-size: 19px;
  }

  .summary-grid {
    gap: 8px;
  }

  .summary-item {
    min-height: 94px;
    gap: 9px;
    padding: 11px;
  }

  .summary-icon {
    flex-basis: 34px;
    width: 34px;
    height: 34px;
  }

  .summary-value {
    font-size: 17px;
  }

  .dashboard-panel {
    padding: 14px;
  }

  .trend-chart {
    height: 210px;
  }

  .trend-footer {
    flex-wrap: wrap;
    gap: 6px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinning {
    animation: none;
  }
}
</style>
