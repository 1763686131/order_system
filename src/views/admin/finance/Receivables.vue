<template>
  <div class="receivables-page">
    <nav v-if="payableMode && canReconcile" class="finance-tabs" aria-label="供应商账务视图">
      <button v-if="canReadBalances" :class="{ active: !reconciliationTab }" @click="setTab('')">应付欠款</button>
      <button :class="{ active: reconciliationTab }" @click="setTab('reconciliation')">正式对账</button>
    </nav>
    <SupplierReconciliationPanel v-if="reconciliationTab && canReconcile" />
    <template v-else-if="canReadBalances">
    <section v-if="!payableMode" class="summary-panel" aria-label="应收欠款合计">
      <div class="summary-formula">
        <div class="summary-item summary-item-result">
          <span>应收欠款</span>
          <strong :class="{ 'negative-amount': Number(totals.receivable) < 0 }">
            {{ formatMoney(totals.receivable) }}
          </strong>
        </div>
        <span class="summary-operator" aria-hidden="true">=</span>
        <div class="summary-item">
          <span>期初欠款</span>
          <strong>{{ formatMoney(totals.initialDebt) }}</strong>
        </div>
        <span class="summary-operator" aria-hidden="true">+</span>
        <div class="summary-item">
          <span>增加应收欠款</span>
          <strong>{{ formatMoney(totals.receivableIncrease) }}</strong>
        </div>
        <span class="summary-operator" aria-hidden="true">-</span>
        <div class="summary-item">
          <span>收回欠款</span>
          <strong>{{ formatMoney(totals.debtRecovered) }}</strong>
        </div>
        <span class="summary-operator" aria-hidden="true">-</span>
        <div class="summary-item">
          <span>优惠</span>
          <strong>{{ formatMoney(totals.discountAmount) }}</strong>
        </div>
      </div>
    </section>
    <section v-else class="summary-panel" aria-label="应付欠款合计">
      <div class="summary-formula payable-summary-formula" role="group" aria-label="净结算额等于应付欠款减预付款减退货贷项">
        <template v-for="column in payableSummaryColumns" :key="column.key">
          <span v-if="column.operator" class="summary-operator" aria-hidden="true">{{ column.operator }}</span>
          <div class="summary-item" :class="{ 'summary-item-result': column.key === 'netSettlement' }">
            <span>{{ column.label }}</span>
            <strong :class="{ 'negative-amount': totals[column.key] < 0 }">{{ formatMoney(totals[column.key]) }}</strong>
          </div>
        </template>
      </div>
    </section>

    <section class="search-panel" :aria-label="`${debtLabel}筛选`">
      <form class="search-grid" :class="{ 'customer-search-grid': !payableMode }" @submit.prevent="handleFilter">
        <label class="field-group">
          <span>{{ partyLabel }}搜索 / 联系电话</span>
          <span class="input-with-icon">
            <Search :size="16" aria-hidden="true" />
            <input v-model.trim="filters.keyword" type="search" :placeholder="`${partyLabel}ID、名称、联系人或联系电话`" />
          </span>
        </label>
        <label v-if="payableMode" class="field-group">
          <span>截止日期</span>
          <input v-model="filters.asOf" type="date" @change="loadReceivables" />
        </label>
        <label v-if="payableMode" class="field-group">
          <span>账龄</span>
          <select v-model="filters.aging" @change="loadReceivables"><option value="">全部</option><option value="0-30">0-30 天</option><option value="31-60">31-60 天</option><option value="61-90">61-90 天</option><option value="90+">90 天以上</option></select>
        </label>
        <div class="search-actions">
          <button class="button button-secondary" type="button" @click="handleReset"><RotateCcw :size="16" />重置</button>
          <button class="button button-primary" type="submit" :disabled="loading"><Search :size="16" />查询</button>
        </div>
      </form>
    </section>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="filter-sliders">
          <div class="store-filter-slider" role="tablist" aria-label="门店筛选">
            <button
              :class="['slider-tab', { active: selectedStoreId === null }]"
              type="button"
              role="tab"
              :aria-selected="selectedStoreId === null"
              @click="setStore(null)"
            >
              全部门店
              <span class="count-badge">{{ allReceivables.length }}</span>
            </button>
            <button
              v-for="store in activeStores"
              :key="store.id"
              :class="['slider-tab', { active: selectedStoreId === store.id }]"
              type="button"
              role="tab"
              :aria-selected="selectedStoreId === store.id"
              @click="setStore(store.id)"
            >
              {{ store.name }}
              <span class="count-badge">{{ storeCount(store.id) }}</span>
            </button>
          </div>

          <div class="status-filter-slider" role="tablist" aria-label="欠款状态筛选">
            <button
              :class="['slider-tab', { active: filters.debtStatus === '' }]"
              type="button"
              role="tab"
              :aria-selected="filters.debtStatus === ''"
              @click="setDebtStatus('')"
            >
              全部
              <span class="count-badge">{{ storeReceivables.length }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.debtStatus === 'outstanding' }]"
              type="button"
              role="tab"
              :aria-selected="filters.debtStatus === 'outstanding'"
              @click="setDebtStatus('outstanding')"
            >
              有欠款
              <span class="count-badge">{{ outstandingCount }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.debtStatus === 'settled' }]"
              type="button"
              role="tab"
              :aria-selected="filters.debtStatus === 'settled'"
              @click="setDebtStatus('settled')"
            >
              无欠款
              <span class="count-badge">{{ settledCount }}</span>
            </button>
          </div>
        </div>

        <div class="toolbar-actions">
          <button v-if="payableMode && user.hasPerm('admin.finance.payable.initial')" class="button button-secondary" @click="openInitial"><Plus :size="16" />录入期初</button>
          <button
            class="icon-button"
            type="button"
            :title="`刷新${debtLabel}`"
            :disabled="loading"
            @click="loadReceivables"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
        </div>
      </header>
      <p v-if="error" class="finance-error" role="alert">{{ error }}</p>

      <div class="table-scroll">
        <table
          v-table-layout="{
            storageKey: payableMode ? 'finance-payables-list' : 'finance-receivables-list',
            resizeMode: 'fit',
            minWidth: 64
          }"
          class="records-table"
        >
          <colgroup>
            <col data-column-key="party-id" data-min-width="80" style="width: 90px">
            <col data-column-key="party-name" data-min-width="120" style="width: 180px">
            <col data-column-key="contact" data-min-width="90" style="width: 105px">
            <col data-column-key="phone" data-min-width="100" style="width: 120px">
            <col
              v-for="column in amountColumns"
              :key="`col-${column.key}`"
              :data-column-key="column.key"
              data-min-width="110"
              style="width: 150px"
            >
            <col data-column-key="actions" data-resizable="false" style="width: 185px">
          </colgroup>
          <thead>
            <tr>
              <th class="customer-id-column" data-column-key="party-id" data-min-width="80">{{ partyLabel }}ID</th>
              <th class="customer-name-column" data-column-key="party-name" data-min-width="120">{{ partyLabel }}</th>
              <th class="contact-column" data-column-key="contact" data-min-width="90">联系人</th>
              <th class="phone-column" data-column-key="phone" data-min-width="100">电话</th>
              <th
                v-for="column in amountColumns"
                :key="column.key"
                class="money-column"
                :data-column-key="column.key"
                data-min-width="110"
              >{{ column.label }}</th>
              <th class="operation-column" data-column-key="actions" data-resizable="false">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in amountColumns.length + 5" :key="cell"><span></span></td>
              </tr>
            </template>

            <tr v-else-if="pagedReceivables.length === 0">
              <td :colspan="amountColumns.length + 5" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>没有符合条件的{{ debtLabel }}记录</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>

            <template v-else>
              <tr v-for="item in pagedReceivables" :key="item.partyId">
                <td class="customer-id-cell">
                  <strong>#{{ item.partyId }}</strong>
                </td>
                <td class="customer-name-cell">
                  <strong :title="item.partyName">{{ item.partyName || '-' }}</strong>
                </td>
                <td class="contact-cell">{{ item.contactPerson || '-' }}</td>
                <td class="phone-cell">{{ item.phone || '-' }}</td>
                <td v-for="column in amountColumns" :key="column.key" class="money-cell" :class="[column.className, { 'negative-amount': Number(item[column.key]) < 0 }]">{{ formatMoney(item[column.key]) }}</td>
                <td class="operation-column">
                  <div class="row-actions">
                    <button
                      class="action-button"
                      type="button"
                      v-if="canStatement"
                      @click="viewDebtDetails(item)"
                    >
                      欠款详情
                    </button>
                    <button
                      class="action-button action-button-primary"
                      type="button"
                      v-if="canPayment"
                      @click="createPayment(item)"
                    >
                      {{ payableMode ? '付款' : '收款' }}
                    </button>
                    <button v-if="payableMode" class="action-button balance-button" title="预付款、贷项核销及记录" aria-label="预付款、贷项核销及记录" @click="balanceSupplier = item"><WalletCards :size="16" /></button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
          <tfoot v-if="!loading && filteredReceivables.length > 0">
            <tr>
              <td colspan="4" class="total-label">合计</td>
              <td v-for="column in amountColumns" :key="column.key" class="money-cell" :class="column.className">{{ formatMoney(totals[column.key]) }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredReceivables.length }}</strong> 条{{ partyLabel }}{{ debtLabel }}记录
        </span>
        <div class="pagination">
          <select v-model.number="pageSize" aria-label="每页显示数量" @change="currentPage = 1">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="50">50 条/页</option>
          </select>
          <button
            type="button"
            title="上一页"
            :disabled="currentPage <= 1"
            @click="currentPage -= 1"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m15 18-6-6 6-6"></path>
            </svg>
          </button>
          <span class="page-number">{{ currentPage }} / {{ totalPages }}</span>
          <button
            type="button"
            title="下一页"
            :disabled="currentPage >= totalPages"
            @click="currentPage += 1"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="m9 18 6-6-6-6"></path>
            </svg>
          </button>
        </div>
      </footer>
    </section>
    </template>
    <p v-else class="finance-error" role="alert">没有查看应付欠款的权限</p>
    <SupplierBalanceDialog v-if="balanceSupplier" :supplier="balanceSupplier" :stores="stores" :default-store="selectedStoreId || route.query.storeId || ''" @close="closeBalance" @updated="loadReceivables" />
    <Teleport to="body">
      <div v-if="initialOpen" class="sf-modal-layer" @click.self="!saving && (initialOpen = false)">
        <form class="supplier-finance-dialog initial-dialog" role="dialog" aria-modal="true" aria-label="供应商期初余额" @submit.prevent="saveInitial">
          <header class="sf-header"><h2>录入供应商期初余额</h2><button type="button" class="sf-button icon" title="关闭" :disabled="saving" @click="initialOpen = false"><X :size="18" /></button></header>
          <div class="sf-dialog-body">
            <p v-if="initialError" class="sf-error" role="alert">{{ initialError }}</p>
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="initial.storeId" required @change="initial.supplierId = ''"><option value="">请选择</option><option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
              <label class="sf-field">供应商<select v-model="initial.supplierId" required><option value="">请选择</option><option v-for="row in initialSuppliers" :key="row.id" :value="row.id">{{ row.supplierName }}</option></select></label>
              <label class="sf-field">业务日期<input v-model="initial.businessDate" type="date" required /></label>
              <label v-for="field in initialFields" :key="field.key" class="sf-field">{{ field.label }}<input v-model.number="initial[field.key]" type="number" min="0" step="0.01" required /></label>
              <label class="sf-field wide">备注<textarea v-model="initial.remark" maxlength="500" /></label>
            </div>
          </div>
          <footer class="sf-footer"><span /><button class="sf-button primary" :disabled="saving"><Check :size="16" />{{ saving ? '保存中...' : '确认录入' }}</button></footer>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, Plus, RotateCcw, Search, WalletCards, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { operationKey } from '@/utils/supplierFinance'
import SupplierBalanceDialog from '@/components/admin/purchase/SupplierBalanceDialog.vue'
import SupplierReconciliationPanel from '@/components/admin/finance/SupplierReconciliationPanel.vue'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({ mode: { type: String, default: 'receivable', validator: value => ['receivable', 'payable'].includes(value) } })
const router = useRouter()
const route = useRoute()
const user = useUserStore()
const payableMode = computed(() => props.mode === 'payable')
const partyLabel = computed(() => payableMode.value ? '供应商' : '客户')
const debtLabel = computed(() => payableMode.value ? '应付欠款' : '应收欠款')
const canReadBalances = computed(() => !payableMode.value || user.hasPerm('admin.route.finance.payables'))
const canReconcile = computed(() => payableMode.value && user.hasPerm('admin.route.finance.supplier_reconciliations'))
const canStatement = computed(() => !payableMode.value || user.hasPerm('admin.finance.supplier_statement.read'))
const canPayment = computed(() => user.hasPerm(payableMode.value ? 'admin.route.finance.supplier_payments' : 'admin.route.finance.payment_history'))
const reconciliationTab = computed(() => payableMode.value && route.query.tab === 'reconciliation')
const balanceSupplier = ref(null)
const suppliers = ref([])
const error = ref('')
const initialOpen = ref(false)
const initialError = ref('')
const saving = ref(false)
const initial = reactive({})
const initialFields = [{ key: 'payableAmount', label: '期初应付' }, { key: 'prepaymentAmount', label: '期初预付款' }, { key: 'creditAmount', label: '期初贷项' }]
const initialSuppliers = computed(() => suppliers.value.filter(row => !row.storeId || Number(row.storeId) === Number(initial.storeId)))
const amountColumns = computed(() => payableMode.value ? [
  { key: 'confirmedPayable', label: '已确认应付' },
  { key: 'allocatedAmount', label: '已核销', className: 'recovered-amount' },
  { key: 'payableBalance', label: '应付欠款', className: 'receivable-amount' },
  { key: 'prepaymentBalance', label: '预付款', className: 'recovered-amount' },
  { key: 'creditBalance', label: '退货贷项', className: 'recovered-amount' },
  { key: 'netSettlement', label: '净结算额' }
] : [
  { key: 'initialDebt', label: '期初欠款' },
  { key: 'receivableIncrease', label: '增加的应收欠款', className: 'increase-amount' },
  { key: 'debtRecovered', label: '收回欠款', className: 'recovered-amount' },
  { key: 'discountAmount', label: '优惠', className: 'discount-amount' },
  { key: 'receivable', label: '应收欠款', className: 'receivable-amount' }
])
const payableSummaryColumns = computed(() => [
  { ...amountColumns.value[5] },
  { ...amountColumns.value[2], operator: '=' },
  { ...amountColumns.value[3], operator: '-' },
  { ...amountColumns.value[4], operator: '-' }
])

const receivables = ref([])
const allReceivables = ref([])
const stores = ref([])
const selectedStoreId = ref(null)
const loading = ref(false)
const storesLoaded = ref(false)
let loadRequestToken = 0
const currentPage = ref(1)
const pageSize = ref(20)
const filters = reactive({
  keyword: '',
  debtStatus: '',
  asOf: '',
  aging: ''
})

const activeStores = computed(() => stores.value.filter(store => store.status !== 'inactive'))

const storeReceivables = computed(() => receivables.value)

const matchesSearch = item => {
  const keyword = filters.keyword.toLowerCase()
  const searchText = [
    item.partyId,
    item.partyCode,
    item.partyName,
    item.contactPerson,
    item.phone
  ].join(' ').toLowerCase()

  return !keyword || searchText.includes(keyword)
}

const filteredReceivables = computed(() => storeReceivables.value.filter(item => {
  if (!matchesSearch(item)) return false
  if (filters.debtStatus === 'outstanding') return Number(item.receivable) > 0
  if (filters.debtStatus === 'settled') return Number(item.receivable) <= 0
  return true
}))

const outstandingCount = computed(() =>
  storeReceivables.value.filter(item => Number(item.receivable) > 0).length
)

const settledCount = computed(() =>
  storeReceivables.value.filter(item => Number(item.receivable) <= 0).length
)

const storeCount = storeId => allReceivables.value.filter(
  item => Number(item.storeId) === Number(storeId)
).length

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredReceivables.value.length / pageSize.value))
)

const pagedReceivables = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredReceivables.value.slice(start, start + pageSize.value)
})

const totals = computed(() => Object.fromEntries(amountColumns.value.map(column => [
  column.key,
  filteredReceivables.value.reduce((sum, row) => sum + Math.round(Number(row[column.key] || 0) * 100), 0) / 100
])))

const formatMoney = value => {
  const amount = Number(value) || 0
  return `¥${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}

const loadReceivables = async () => {
  const requestStoreId = selectedStoreId.value
  const requestToken = ++loadRequestToken
  loading.value = true
  error.value = ''
  try {
    if (!canReadBalances.value) return
    const receivableRequest = request({
      url: payableMode.value ? '/suppliers/payables' : '/customers/receivables',
      method: 'GET',
      params: { storeId: requestStoreId ?? undefined, ...(payableMode.value ? { asOf: filters.asOf, aging: filters.aging } : {}) }
    })
    const storeRequest = storesLoaded.value
      ? Promise.resolve(null)
      : request({ url: payableMode.value ? '/supplier-finance/options' : '/stores', method: 'GET' })
    const [receivableResult, storeResult] = await Promise.allSettled([
      receivableRequest,
      storeRequest
    ])

    if (requestToken !== loadRequestToken) return
    if (receivableResult.status === 'rejected') throw receivableResult.reason

    if (storeResult.status === 'fulfilled' && storeResult.value) {
      stores.value = payableMode.value ? storeResult.value.stores || [] : storeResult.value
      suppliers.value = storeResult.value.suppliers || []
      storesLoaded.value = true
    }

    const response = receivableResult.value
    const items = payableMode.value ? response : response?.items
    receivables.value = (Array.isArray(items) ? items : []).map(row => ({
      ...row,
      partyId: payableMode.value ? row.supplierId : row.customerId,
      partyCode: payableMode.value ? row.supplierCode : row.customerCode,
      partyName: payableMode.value ? row.supplierName : row.customerName,
      receivable: payableMode.value ? row.payableBalance : row.receivable
    }))
    if (requestStoreId === null) allReceivables.value = receivables.value
  } catch (error) {
    if (requestToken !== loadRequestToken) return
    console.error(`加载${debtLabel.value}失败:`, error)
    receivables.value = []
    showError(error, `加载${debtLabel.value}失败，请稍后重试`)
  } finally {
    if (requestToken === loadRequestToken) loading.value = false
  }
}

const handleFilter = () => {
  currentPage.value = 1
  if (payableMode.value) loadReceivables()
}

const handleReset = () => {
  filters.keyword = ''
  filters.debtStatus = ''
  filters.asOf = ''
  filters.aging = ''
  selectedStoreId.value = null
  currentPage.value = 1
  receivables.value = []
  loadReceivables()
}

const setStore = storeId => {
  selectedStoreId.value = storeId === null ? null : Number(storeId)
  currentPage.value = 1
  receivables.value = []
  loadReceivables()
}

const setDebtStatus = status => {
  filters.debtStatus = status
  currentPage.value = 1
}

const viewDebtDetails = item => router.push({
  name: 'admin-finance-debt-details',
  params: { type: props.mode, targetId: item.partyId },
  query: { name: item.partyName, storeId: selectedStoreId.value ?? undefined }
})
const showError = (err, fallback) => { error.value = err?.response?.data?.error || err?.response?.data?.message || err?.message || fallback }
const createPayment = item => router.push({
  name: payableMode.value ? 'admin-supplier-payments' : 'admin-finance-payment-history',
  query: { create: '1', [payableMode.value ? 'supplierId' : 'customerId']: item.partyId, storeId: selectedStoreId.value || item.storeId || undefined }
})
function clearQuery(keys) {
  const query = { ...route.query }
  keys.forEach(key => delete query[key])
  router.replace({ query })
}
function closeBalance() { balanceSupplier.value = null; if (route.query.balanceSupplierId) clearQuery(['balanceSupplierId']) }
function setTab(tab) { router.replace({ query: { ...route.query, tab: tab || undefined } }) }
function openInitial() {
  Object.assign(initial, { supplierId: '', storeId: selectedStoreId.value || '', businessDate: localDate(), payableAmount: 0, prepaymentAmount: 0, creditAmount: 0, remark: '', idempotencyKey: operationKey() })
  initialError.value = ''
  initialOpen.value = true
}
async function saveInitial() {
  saving.value = true
  initialError.value = ''
  try { await request.post(`/suppliers/${initial.supplierId}/initial-balances`, initial); initialOpen.value = false; await loadReceivables() }
  catch (err) { initialError.value = err?.response?.data?.message || err.message }
  finally { saving.value = false }
}
function openQueryDialog() {
  if (route.query.balanceSupplierId && payableMode.value && canReadBalances.value) {
    balanceSupplier.value = receivables.value.find(row => row.supplierId === Number(route.query.balanceSupplierId)) || null
  }
}

watch(totalPages, pages => {
  if (currentPage.value > pages) currentPage.value = pages
})

watch(() => props.mode, async () => {
  ++loadRequestToken
  balanceSupplier.value = null; initialOpen.value = false
  storesLoaded.value = false; receivables.value = []; allReceivables.value = []
  selectedStoreId.value = route.query.storeId ? Number(route.query.storeId) : null
  Object.assign(filters, { keyword: '', debtStatus: '', asOf: '', aging: '' })
  currentPage.value = 1
  await loadReceivables()
  openQueryDialog()
})
watch(() => route.query.balanceSupplierId, openQueryDialog)
onMounted(async () => {
  selectedStoreId.value = route.query.storeId ? Number(route.query.storeId) : null
  await loadReceivables()
  openQueryDialog()
})
onBeforeUnmount(() => { ++loadRequestToken })
</script>

<style scoped>
.finance-tabs { display: flex; gap: 8px; padding: 0 0 12px; }
.finance-tabs button { min-height: 36px; padding: 0 16px; border: 0; border-bottom: 2px solid transparent; color: #596579; background: transparent; cursor: pointer; }
.finance-tabs button.active { color: #08745a; border-color: #0f9f78; font-weight: 600; }
.finance-error { padding: 12px 16px; color: #b4232f; }
.balance-button { width: 30px; padding: 0; flex-shrink: 0; }
.initial-dialog { max-width: 620px; }
.receivables-page {
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
  min-width: 0;
  min-height: calc(100vh - 100px);
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

* {
  box-sizing: border-box;
}

button,
input,
select {
  font: inherit;
}

button:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.summary-panel {
  overflow-x: auto;
  padding: 14px 18px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.summary-formula {
  display: flex;
  min-width: 760px;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.summary-item {
  display: flex;
  min-width: 0;
  flex: 1 1 0;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  text-align: center;
}

.summary-item span {
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.summary-item strong {
  overflow: hidden;
  color: #243145;
  font-size: 21px;
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-item-result strong {
  color: #243145;
}

.summary-operator {
  flex: 0 0 24px;
  color: #8a96a8;
  font-size: 16px;
  font-weight: 500;
  text-align: center;
}

.search-panel { margin-top: 14px; padding: 18px 20px; background: var(--panel-bg); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.search-grid { display: grid; grid-template-columns: minmax(240px, 1.5fr) minmax(160px, 1fr) minmax(160px, 1fr) auto; gap: 14px; align-items: end; }
.customer-search-grid { grid-template-columns: minmax(240px, 1fr) auto; }

.field-group {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.field-group > span:first-child {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-group input,
.field-group select {
  width: 100%;
  min-width: 0;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field-group input::placeholder {
  color: #a2adba;
}

.field-group input:focus,
.field-group select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.input-with-icon {
  position: relative;
  display: block;
}

.input-with-icon svg {
  position: absolute;
  top: 11px;
  left: 11px;
  z-index: 1;
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.input-with-icon input {
  padding-left: 35px;
}

.search-actions,
.toolbar-actions,
.row-actions,
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
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
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.button svg {
  width: 16px;
  height: 16px;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 2px 5px rgba(var(--accent-rgb), 0.18);
}

.button-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.button-secondary {
  color: #445066;
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button:disabled { cursor: not-allowed; opacity: .45; }

.records-panel {
  margin-top: 14px;
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 3px 14px rgba(15, 23, 42, 0.045);
}

.records-toolbar {
  display: flex;
  flex-wrap: wrap;
  min-height: 62px;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.filter-sliders {
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  flex: 0 1 auto;
  align-items: center;
  gap: 8px;
}

.records-toolbar > .filter-sliders {
  flex: 0 1 auto;
  max-width: 100%;
}

.records-toolbar > .toolbar-actions {
  flex: 0 0 auto;
  margin-left: auto;
}

.store-filter-slider,
.status-filter-slider {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.store-filter-slider {
  max-width: 390px;
  overflow-x: auto;
}

.store-filter-slider .slider-tab {
  padding-right: 13px;
  padding-left: 13px;
}

.slider-tab {
  display: inline-flex;
  flex-shrink: 0;
  white-space: nowrap;
  height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 16px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease;
}

.slider-tab:hover {
  color: var(--accent-dark);
  background: rgba(var(--accent-rgb), 0.1);
}

.slider-tab.active {
  color: #fff;
  background: var(--accent);
  box-shadow: 0 2px 6px rgba(var(--accent-rgb), 0.3);
}

.count-badge {
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
}

.slider-tab.active .count-badge {
  background: rgba(255, 255, 255, 0.25);
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.icon-button svg {
  width: 17px;
  height: 17px;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1420px;
  border-collapse: collapse;
  table-layout: fixed;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.records-table.resizable-columns-table th {
  overflow: hidden;
  text-overflow: ellipsis;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.records-table tbody tr:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.customer-id-column {
  width: 90px;
}

.customer-name-column {
  width: 180px;
}

.contact-column {
  width: 105px;
}

.phone-column {
  width: 120px;
}

.money-column,
.money-cell {
  width: 150px;
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.operation-column {
  width: 185px;
  text-align: center !important;
}

.customer-id-cell strong,
.customer-name-cell strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.customer-id-cell strong {
  color: var(--accent-dark);
  font-size: 13px;
  font-weight: 700;
}

.customer-name-cell strong {
  color: #243145;
  font-size: 15px;
  font-weight: 650;
}

.contact-cell,
.phone-cell {
  color: var(--text-secondary);
  font-size: 12px;
}

.phone-cell {
  font-variant-numeric: tabular-nums;
}

.increase-amount,
.receivable-amount {
  color: #dc3545 !important;
  font-weight: 700;
}

.negative-amount,
.summary-item-result strong.negative-amount,
.receivable-amount.negative-amount,
.receivable-amount.negative-amount strong {
  color: #07805f !important;
}

.receivable-amount strong,
.receivable-amount span {
  display: block;
}

.receivable-amount span {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 500;
}

.recovered-amount {
  color: #07805f !important;
  font-weight: 650;
}

.discount-amount {
  color: #a4510b !important;
  font-weight: 650;
}

.row-actions {
  justify-content: center;
}

.action-button {
  display: inline-flex;
  height: 30px;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  color: #445066;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.action-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.action-button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.action-button-primary:hover {
  color: #fff;
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.records-table tfoot {
  color: var(--text);
  background: #f8fafc;
  border-top: 2px solid var(--border);
  font-weight: 700;
}

.total-label {
  padding-left: 20px !important;
  text-align: left;
}

.empty-cell {
  height: 290px !important;
  color: var(--text-muted) !important;
  text-align: center;
}

.empty-cell strong,
.empty-cell span {
  display: block;
}

.empty-cell strong {
  margin-top: 11px;
  color: #4c586b;
  font-size: 14px;
}

.empty-cell span {
  margin-top: 5px;
  font-size: 12px;
}

.empty-mark {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  color: #aab4c0;
  background: #f1f4f7;
  border-radius: 50%;
}

.empty-mark svg {
  width: 24px;
  height: 24px;
}

.skeleton-row span {
  display: block;
  width: 78%;
  height: 10px;
  background: linear-gradient(90deg, #eef2f5 25%, #e2e8ee 50%, #eef2f5 75%);
  background-size: 200% 100%;
  border-radius: 3px;
  animation: shimmer 1.25s linear infinite;
}

@keyframes shimmer {
  to { background-position: -200% 0; }
}

.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 16px;
  color: var(--text-secondary);
  background: #fff;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.table-footer strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.pagination select {
  height: 32px;
  padding: 0 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
}

.pagination button {
  display: inline-flex;
  width: 31px;
  height: 31px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.pagination svg {
  width: 15px;
  height: 15px;
}

.page-number {
  min-width: 58px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1280px) {
  .records-toolbar {
    flex-wrap: wrap;
  }

  .filter-sliders {
    max-width: 100%;
    overflow-x: auto;
  }

  .search-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }

  .search-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 780px) {
  .summary-panel {
    overflow-x: visible;
  }

  .summary-formula {
    display: grid;
    min-width: 0;
    grid-template-columns: 24px minmax(0, 1fr);
    row-gap: 10px;
  }

  .summary-formula .summary-item {
    align-items: flex-start;
    text-align: left;
  }

  .summary-formula .summary-item-result {
    grid-column: 1 / -1;
    align-items: center;
    text-align: center;
  }

  .summary-formula .summary-operator:nth-child(2) {
    grid-column: 1;
    grid-row: 2;
  }

  .summary-formula .summary-item:nth-child(3) {
    grid-column: 2;
    grid-row: 2;
  }

  .summary-formula .summary-operator:nth-child(4) {
    grid-column: 1;
    grid-row: 3;
  }

  .summary-formula .summary-item:nth-child(5) {
    grid-column: 2;
    grid-row: 3;
  }

  .summary-formula .summary-operator:nth-child(6) {
    grid-column: 1;
    grid-row: 4;
  }

  .summary-formula .summary-item:nth-child(7) {
    grid-column: 2;
    grid-row: 4;
  }

  .summary-formula .summary-operator:nth-child(8) {
    grid-column: 1;
    grid-row: 5;
  }

  .summary-formula .summary-item:nth-child(9) {
    grid-column: 2;
    grid-row: 5;
  }

  .search-panel { padding: 14px 16px; }
  .search-grid { grid-template-columns: minmax(0, 1fr); }

  .records-toolbar,
  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .records-toolbar > .toolbar-actions {
    margin-left: 0;
  }

  .filter-sliders {
    width: 100%;
    align-items: stretch;
  }

  .store-filter-slider,
  .status-filter-slider {
    max-width: 100%;
    overflow-x: auto;
  }
}
</style>
