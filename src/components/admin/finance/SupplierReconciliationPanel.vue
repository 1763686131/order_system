<template>
  <section class="supplier-finance-page">
    <header class="sf-header">
      <h2>正式对账</h2>
      <div class="sf-actions">
        <button v-if="can('create')" class="sf-button primary" @click="openCreate"><Plus :size="16" />新建对账</button>
        <button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button>
      </div>
    </header>
    <section class="reconciliation-search-panel" aria-label="正式对账筛选">
      <form class="reconciliation-search-grid" @submit.prevent="load">
        <label class="sf-field"><span>单号 / 供应商</span><input v-model.trim="filters.keyword" type="search" /></label>
        <label class="sf-field"><span>门店</span><select v-model="filters.storeId"><option value="">全部授权门店</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
        <label v-if="!props.supplierId" class="sf-field"><span>供应商</span><select v-model="filters.supplierId"><option value="">全部供应商</option><option v-for="supplier in suppliersForFilter" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
        <label class="sf-field"><span>状态</span><select v-model="filters.status"><option value="">全部</option><option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option></select></label>
        <div class="sf-field reconciliation-period">
          <span>对账期间</span>
          <div class="reconciliation-date-range">
            <input v-model="filters.periodStart" type="date" aria-label="期间开始" :max="filters.periodEnd || undefined" />
            <span aria-hidden="true">至</span>
            <input v-model="filters.periodEnd" type="date" aria-label="期间结束" :min="filters.periodStart || undefined" />
          </div>
        </div>
        <div class="sf-actions reconciliation-search-actions">
          <button class="sf-button" type="button" @click="resetFilters"><RotateCcw :size="16" />重置</button>
          <button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button>
        </div>
      </form>
    </section>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary">
      <span>对账单数<strong>{{ records.length }}</strong></span>
      <span>已确认<strong>{{ records.filter(row => row.status === 'confirmed').length }}</strong></span>
      <span>已锁定期间<strong>{{ records.filter(row => row.status === 'confirmed').length }}</strong></span>
    </div>
    <div class="sf-table-scroll">
      <table
        v-resizable-columns="{ storageKey: 'finance-reconciliation-list', resizeMode: 'fit', minWidth: 64 }"
        class="sf-table reconciliation-table"
        style="min-width: 1030px"
      >
        <colgroup>
          <col data-column-key="document" data-min-width="110" style="width: 150px">
          <col data-column-key="supplier-store" data-min-width="120" style="width: 180px">
          <col data-column-key="period" data-min-width="120" style="width: 180px">
          <col data-column-key="payable" data-min-width="100" style="width: 120px">
          <col data-column-key="prepayment" data-min-width="100" style="width: 120px">
          <col data-column-key="credit" data-min-width="90" style="width: 120px">
          <col data-column-key="status" data-min-width="90" style="width: 130px">
          <col data-column-key="created-confirmed" data-min-width="120" style="width: 180px">
        </colgroup>
        <thead><tr><th data-column-key="document" data-min-width="110">对账单号</th><th data-column-key="supplier-store" data-min-width="120">供应商 / 门店</th><th data-column-key="period" data-min-width="120">对账期间</th><th data-column-key="payable" data-min-width="100">系统应付期末</th><th data-column-key="prepayment" data-min-width="100">预付款期末</th><th data-column-key="credit" data-min-width="90">贷项期末</th><th data-column-key="status" data-min-width="90">状态</th><th data-column-key="created-confirmed" data-min-width="120">创建 / 确认</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" class="sf-empty">加载中...</td></tr>
          <tr v-else-if="!records.length"><td colspan="8" class="sf-empty">暂无正式对账记录</td></tr>
          <tr v-for="row in records" :key="row.id">
            <td><button class="sf-link" @click="openRecord(row.id)">{{ row.documentNo }}</button></td>
            <td>{{ row.supplierName }}<div class="sf-muted">{{ row.storeName }}</div></td>
            <td>{{ row.periodStart }} 至 {{ row.periodEnd }}</td>
            <td class="sf-number">{{ formatTableMoney(row.snapshot.closing.payable) }}</td>
            <td class="sf-number">{{ formatTableMoney(row.snapshot.closing.prepayment) }}</td>
            <td class="sf-number">{{ formatTableMoney(row.snapshot.closing.credit) }}</td>
            <td><span class="sf-badge">{{ statusLabels[row.status] || row.status }}</span></td>
            <td>{{ row.createdBy }}<div class="sf-muted">{{ row.confirmedBy || '-' }}</div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body"><div v-if="dialogOpen" class="sf-modal-layer" @click.self="close">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-label="供应商正式对账">
        <header class="sf-header">
          <h2>{{ selected?.documentNo || '新建供应商对账' }} <span v-if="selected" class="sf-badge">{{ statusLabels[selected.status] }}</span></h2>
          <button class="sf-button icon" title="关闭" aria-label="关闭" :disabled="saving" @click="close"><X :size="18" /></button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="dialogError" class="sf-error" role="alert">{{ dialogError }}</p>
          <p v-if="detailLoading" class="sf-empty">加载对账单中...</p>
          <form v-else-if="!selected && !detailFailed" id="supplier-reconciliation-create" @submit.prevent="create">
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="createForm.storeId" required @change="changeCreateStore"><option value="">请选择</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
              <label class="sf-field">供应商<select v-model="createForm.supplierId" required :disabled="Boolean(props.supplierId)"><option value="">请选择</option><option v-for="supplier in suppliersForCreate" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
              <label class="sf-field">期间开始<input v-model="createForm.periodStart" type="date" required /></label>
              <label class="sf-field">期间结束<input v-model="createForm.periodEnd" type="date" required /></label>
            </div>
          </form>
          <template v-else-if="selected">
            <div class="sf-summary">
              <span>供应商<strong>{{ selected.supplierName }}</strong></span>
              <span>门店<strong>{{ selected.storeName }}</strong></span>
              <span>期间<strong>{{ selected.periodStart }} 至 {{ selected.periodEnd }}</strong></span>
              <span>交易笔数<strong>{{ selected.snapshot.items.length }}</strong></span>
            </div>
            <div class="sf-header sf-section-title"><h3>系统余额快照</h3><button v-if="selected.status === 'draft' && can('create')" class="sf-button icon" title="刷新快照" aria-label="刷新快照" :disabled="saving" @click="refreshSnapshot"><RefreshCw :size="16" /></button></div>
            <div class="sf-summary">
              <span>期初应付<strong>{{ money(selected.snapshot.opening.payable) }}</strong></span>
              <span>本期应付变动<strong>{{ money(selected.snapshot.changes.payable) }}</strong></span>
              <span>期末应付<strong>{{ money(selected.snapshot.closing.payable) }}</strong></span>
              <span>期末预付款<strong>{{ money(selected.snapshot.closing.prepayment) }}</strong></span>
              <span>期末贷项<strong>{{ money(selected.snapshot.closing.credit) }}</strong></span>
            </div>
            <div class="sf-table-scroll">
              <table
                v-resizable-columns="{ storageKey: 'finance-reconciliation-snapshot', resizeMode: 'fit', minWidth: 64 }"
                class="sf-table reconciliation-table"
                style="min-width: 1120px"
              >
                <colgroup>
                  <col data-column-key="business-date" data-min-width="90" style="width: 120px">
                  <col data-column-key="document-type" data-min-width="110" style="width: 180px">
                  <col data-column-key="summary" data-min-width="110" style="width: 180px">
                  <col data-column-key="payable-change" data-min-width="100" style="width: 120px">
                  <col data-column-key="prepayment-change" data-min-width="100" style="width: 120px">
                  <col data-column-key="credit-change" data-min-width="90" style="width: 120px">
                  <col data-column-key="status" data-min-width="90" style="width: 120px">
                  <col data-column-key="balances" data-min-width="140" style="width: 220px">
                </colgroup>
                <thead><tr><th data-column-key="business-date" data-min-width="90">业务日期</th><th data-column-key="document-type" data-min-width="110">单号 / 业务类型</th><th data-column-key="summary" data-min-width="110">商品 / 摘要</th><th data-column-key="payable-change" data-min-width="100">应付变动</th><th data-column-key="prepayment-change" data-min-width="100">预付款变动</th><th data-column-key="credit-change" data-min-width="90">贷项变动</th><th data-column-key="status" data-min-width="90">状态</th><th data-column-key="balances" data-min-width="140">余额（应付 / 预付 / 贷项）</th></tr></thead>
                <tbody>
                  <tr v-if="!selected.snapshot.items.length"><td colspan="8" class="sf-empty">该期间没有账务变动</td></tr>
                  <tr v-for="item in selected.snapshot.items" :key="item.id">
                    <td>{{ item.businessDate }}</td>
                    <td>{{ item.documentNo }}<div class="sf-muted">{{ businessLabels[item.businessType] || item.businessType }}</div></td>
                    <td>{{ item.productName || item.remark || '-' }}</td>
                    <td class="sf-number">{{ formatTableMoney(item.payableChange) }}</td>
                    <td class="sf-number">{{ formatTableMoney(item.prepaymentChange) }}</td>
                    <td class="sf-number">{{ formatTableMoney(item.creditChange) }}</td>
                    <td><span class="sf-badge">{{ transactionStatus[item.status] || item.status }}</span></td>
                    <td>{{ formatTableMoney(item.balances.payable) }} / {{ formatTableMoney(item.balances.prepayment) }} / {{ formatTableMoney(item.balances.credit) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="selected.status === 'draft' && can('confirm')" class="sf-section-title">
              <div class="sf-header"><h3>供应商确认</h3></div>
              <div class="sf-form-grid">
                <label class="sf-field">供应商确认应付<input v-model="confirmation.payableBalance" type="number" min="0" step="0.01" required /></label>
                <label class="sf-field">供应商确认预付款<input v-model="confirmation.prepaymentBalance" type="number" min="0" step="0.01" required /></label>
                <label class="sf-field">供应商确认贷项<input v-model="confirmation.creditBalance" type="number" min="0" step="0.01" required /></label>
                <label class="sf-field">确认人 / 联系人<input v-model.trim="confirmation.supplierContact" maxlength="120" required /></label>
                <label class="sf-field wide">确认方式及记录<textarea v-model.trim="confirmation.confirmationNote" maxlength="500" required /></label>
                <label class="sf-field wide">差异原因<textarea v-model.trim="confirmation.differenceReason" maxlength="500" placeholder="余额与系统不一致时必填" /></label>
              </div>
            </div>
            <div v-else-if="selected.supplierBalances" class="sf-section-title">
              <div class="sf-summary">
                <span>供应商确认应付<strong>{{ money(selected.supplierBalances.payable) }}</strong></span>
                <span>确认预付款<strong>{{ money(selected.supplierBalances.prepayment) }}</strong></span>
                <span>确认贷项<strong>{{ money(selected.supplierBalances.credit) }}</strong></span>
                <span v-if="selected.differenceReason">差异原因<strong>{{ selected.differenceReason }}</strong></span>
              </div>
              <p v-if="confirmationDisplay.contact || confirmationDisplay.note" class="sf-muted">确认记录：{{ confirmationDisplay.contact }} {{ confirmationDisplay.note }}</p>
              <p v-if="selected.lockedAt" class="sf-muted">期间已锁定：{{ selected.lockedAt }}</p>
            </div>
          </template>
        </div>
        <footer class="sf-footer">
          <span v-if="selected" class="sf-muted">版本 {{ selected.version }} · {{ selected.createdBy }} · {{ selected.createdAt }}</span>
          <div class="sf-actions">
            <button class="sf-button" :disabled="saving" @click="close">关闭</button>
            <button v-if="!selected && !detailLoading && !detailFailed && can('create')" form="supplier-reconciliation-create" class="sf-button primary" :disabled="saving"><Save :size="16" />生成快照</button>
            <template v-if="selected?.status === 'draft'">
              <button v-if="can('cancel')" class="sf-button danger" :disabled="saving" @click="cancel"><X :size="16" />取消草稿</button>
              <button v-if="can('confirm')" class="sf-button primary" :disabled="saving" @click="requestConfirmation('confirm')"><Check :size="16" />确认并锁定期间</button>
            </template>
          </div>
        </footer>
      </section>
    </div></Teleport>
    <CustomModal :visible="Boolean(pendingAction)" :title="pendingAction === 'confirm' ? '确认并锁定期间' : '取消对账草稿'" :message="pendingAction === 'confirm' ? '确认后将锁定该供应商、门店截至期末的账务，锁定期间不能修改、审核或反审核。确定继续？' : '确定取消这张尚未确认的对账草稿？'" :danger="pendingAction === 'cancel'" :confirm-disabled="saving" @confirm="performAction" @cancel="pendingAction = ''" />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Plus, RefreshCw, RotateCcw, Save, Search, X } from '@lucide/vue'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { businessLabels, formatTableMoney, operationKey } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({ supplierId: { type: [String, Number], default: '' }, storeId: { type: [String, Number], default: '' } })
const emit = defineEmits(['updated'])
const user = useUserStore()
const pendingAction = ref('')
const actionKeys = new Map()
const statusLabels = { draft: '草稿', confirmed: '已确认并锁期', cancelled: '已取消' }
const transactionStatus = { audited: '已审核', reversed: '已冲销', reversal: '冲销流水' }
const options = ref({ stores: [], suppliers: [] })
const records = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const dialogError = ref('')
const dialogOpen = ref(false)
const detailLoading = ref(false)
const detailFailed = ref(false)
const selected = ref(null)
const filters = reactive({ keyword: '', storeId: props.storeId, supplierId: props.supplierId, status: '', periodStart: '', periodEnd: '' })
const createForm = ref(emptyCreate())
const confirmation = ref(emptyConfirmation())
const can = action => user.hasPerm(`admin.finance.supplier_reconciliation.${action}`)
const suppliersForFilter = computed(() => options.value.suppliers.filter(row => !filters.storeId || !row.storeId || Number(row.storeId) === Number(filters.storeId)))
const suppliersForCreate = computed(() => options.value.suppliers.filter(row => !createForm.value.storeId || !row.storeId || Number(row.storeId) === Number(createForm.value.storeId)))
const confirmationDisplay = computed(() => {
  try { return selected.value?.confirmationNote ? JSON.parse(selected.value.confirmationNote) : {} }
  catch { return { contact: '', note: selected.value?.confirmationNote || '' } }
})

function emptyCreate() {
  const today = localDate()
  return { supplierId: props.supplierId, storeId: props.storeId, periodStart: `${today.slice(0, 7)}-01`, periodEnd: today, idempotencyKey: operationKey() }
}
function emptyConfirmation() {
  return { payableBalance: '', prepaymentBalance: '', creditBalance: '', supplierContact: '', confirmationNote: '', differenceReason: '' }
}
function money(value) { return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function setConfirmation(row) {
  confirmation.value = {
    payableBalance: row.snapshot.closing.payable,
    prepaymentBalance: row.snapshot.closing.prepayment,
    creditBalance: row.snapshot.closing.credit,
    supplierContact: '', confirmationNote: '', differenceReason: ''
  }
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await request.get('/supplier-reconciliations', { params: filters })
    records.value = result.items || []
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
function resetFilters() {
  Object.assign(filters, { keyword: '', storeId: props.storeId, supplierId: props.supplierId, status: '', periodStart: '', periodEnd: '' })
  load()
}
function openCreate() {
  selected.value = null
  detailLoading.value = false
  detailFailed.value = false
  createForm.value = emptyCreate()
  confirmation.value = emptyConfirmation()
  dialogError.value = ''
  dialogOpen.value = true
}
function changeCreateStore() {
  if (!suppliersForCreate.value.some(row => Number(row.id) === Number(createForm.value.supplierId))) createForm.value.supplierId = ''
}
async function openRecord(id) {
  dialogError.value = ''
  dialogOpen.value = true
  selected.value = null
  detailLoading.value = true
  detailFailed.value = false
  try {
    selected.value = await request.get(`/supplier-reconciliations/${id}`)
    setConfirmation(selected.value)
  } catch (err) { detailFailed.value = true; dialogError.value = err.response?.data?.message || err.message }
  finally { detailLoading.value = false }
}
function close() {
  if (saving.value) return
  dialogOpen.value = false
}
async function create() {
  if (saving.value || detailLoading.value || detailFailed.value || !can('create')) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post('/supplier-reconciliations', {
      ...createForm.value
    })
    selected.value = response.reconciliation
    setConfirmation(selected.value)
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function refreshSnapshot() {
  if (!selected.value || saving.value || !can('create')) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/refresh`, {
      version: selected.value.version, idempotencyKey: actionKey('refresh')
    })
    selected.value = response.reconciliation
    setConfirmation(selected.value)
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function confirm() {
  if (!selected.value || saving.value || !can('confirm')) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/confirm`, {
      version: selected.value.version, idempotencyKey: actionKey('confirm'),
      supplierBalances: {
        payableBalance: confirmation.value.payableBalance,
        prepaymentBalance: confirmation.value.prepaymentBalance,
        creditBalance: confirmation.value.creditBalance
      },
      supplierContact: confirmation.value.supplierContact,
      confirmationNote: confirmation.value.confirmationNote,
      differenceReason: confirmation.value.differenceReason
    })
    selected.value = response.reconciliation
    emit('updated')
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function cancel() {
  requestConfirmation('cancel')
}
function actionKey(action) {
  const key = `${action}:${selected.value?.id}:${selected.value?.version}`
  if (!actionKeys.has(key)) actionKeys.set(key, operationKey())
  return actionKeys.get(key)
}
function requestConfirmation(action) { if (!saving.value && selected.value) pendingAction.value = action }
async function performAction() {
  const action = pendingAction.value
  pendingAction.value = ''
  if (action === 'confirm') { await confirm(); return }
  if (action !== 'cancel' || !selected.value || saving.value || !can('cancel')) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/cancel`, {
      version: selected.value.version, idempotencyKey: actionKey('cancel')
    })
    selected.value = response.reconciliation
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}

onMounted(async () => {
  try { options.value = await request.get('/supplier-reconciliations/options') }
  catch (err) { error.value = err.response?.data?.message || err.message }
  await load()
})
</script>

<style scoped>
.reconciliation-search-panel { padding: 18px 20px; background: #fff; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
.reconciliation-search-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; align-items: end; }
.reconciliation-search-grid .sf-field { gap: 7px; }
.reconciliation-search-grid .sf-field > span { font-size: 12px; font-weight: 600; }
.reconciliation-search-grid input, .reconciliation-search-grid select { height: 38px; min-height: 0; padding: 0 11px; border-radius: 5px; }
.reconciliation-search-grid input:focus, .reconciliation-search-grid select:focus { border-color: #0f9f78; box-shadow: 0 0 0 3px rgba(15, 159, 120, .12); }
.reconciliation-period { grid-column: span 2; }
.reconciliation-date-range { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 8px; }
.reconciliation-date-range > span { font-size: 12px; color: #8a96a8; }
.reconciliation-search-actions { justify-content: flex-end; }
.reconciliation-search-actions .sf-button { height: 38px; padding: 0 15px; gap: 7px; border-radius: 5px; font-size: 13px; font-weight: 600; white-space: nowrap; }
.reconciliation-table th, .reconciliation-table td, .reconciliation-table .sf-number { text-align: left; }
.reconciliation-table th, .reconciliation-table td { border: 1px solid #edf1f5; }
.reconciliation-table.resizable-columns-table th, .reconciliation-table.resizable-columns-table td { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reconciliation-table th:last-child, .reconciliation-table td:last-child { padding-right: 24px; }
@media (max-width: 1280px) {
  .reconciliation-search-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 780px) {
  .reconciliation-search-panel { padding: 14px 16px; }
  .reconciliation-search-grid { grid-template-columns: minmax(0, 1fr); }
  .reconciliation-period { grid-column: auto; }
}
</style>
