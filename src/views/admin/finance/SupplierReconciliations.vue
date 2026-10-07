<template>
  <section class="supplier-finance-page">
    <header class="sf-header">
      <h1>供应商正式对账</h1>
      <div class="sf-actions">
        <button v-if="can('create')" class="sf-button primary" @click="openCreate"><Plus :size="16" />新建对账</button>
        <button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button>
      </div>
    </header>
    <form class="sf-toolbar" @submit.prevent="load">
      <label class="sf-field">单号 / 供应商<input v-model.trim="filters.keyword" type="search" /></label>
      <label class="sf-field">门店<select v-model="filters.storeId"><option value="">全部授权门店</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
      <label class="sf-field">供应商<select v-model="filters.supplierId"><option value="">全部供应商</option><option v-for="supplier in suppliersForFilter" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
      <label class="sf-field">状态<select v-model="filters.status"><option value="">全部</option><option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="sf-field">期间开始<input v-model="filters.periodStart" type="date" /></label>
      <label class="sf-field">期间结束<input v-model="filters.periodEnd" type="date" /></label>
      <button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button>
    </form>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary">
      <span>对账单数<strong>{{ records.length }}</strong></span>
      <span>已确认<strong>{{ records.filter(row => row.status === 'confirmed').length }}</strong></span>
      <span>已锁定期间<strong>{{ records.filter(row => row.status === 'confirmed').length }}</strong></span>
    </div>
    <div class="sf-table-scroll">
      <table class="sf-table" style="min-width: 1030px">
        <thead><tr><th>对账单号</th><th>供应商 / 门店</th><th>对账期间</th><th>系统应付期末</th><th>预付款期末</th><th>贷项期末</th><th>状态</th><th>创建 / 确认</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" class="sf-empty">加载中...</td></tr>
          <tr v-else-if="!records.length"><td colspan="8" class="sf-empty">暂无正式对账记录</td></tr>
          <tr v-for="row in records" :key="row.id">
            <td><button class="sf-link" @click="openRecord(row.id)">{{ row.documentNo }}</button></td>
            <td>{{ row.supplierName }}<div class="sf-muted">{{ row.storeName }}</div></td>
            <td>{{ row.periodStart }} 至 {{ row.periodEnd }}</td>
            <td class="sf-number">{{ money(row.snapshot.closing.payable) }}</td>
            <td class="sf-number">{{ money(row.snapshot.closing.prepayment) }}</td>
            <td class="sf-number">{{ money(row.snapshot.closing.credit) }}</td>
            <td><span class="sf-badge">{{ statusLabels[row.status] || row.status }}</span></td>
            <td>{{ row.createdBy }}<div class="sf-muted">{{ row.confirmedBy || '-' }}</div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="dialogOpen" class="sf-modal-layer" @click.self="close">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-label="供应商正式对账">
        <header class="sf-header">
          <h2>{{ selected?.documentNo || '新建供应商对账' }} <span v-if="selected" class="sf-badge">{{ statusLabels[selected.status] }}</span></h2>
          <button class="sf-button icon" title="关闭" aria-label="关闭" :disabled="saving" @click="close"><X :size="18" /></button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="dialogError" class="sf-error" role="alert">{{ dialogError }}</p>
          <form v-if="!selected" id="supplier-reconciliation-create" @submit.prevent="create">
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="createForm.storeId" required @change="changeCreateStore"><option value="">请选择</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
              <label class="sf-field">供应商<select v-model="createForm.supplierId" required><option value="">请选择</option><option v-for="supplier in suppliersForCreate" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
              <label class="sf-field">期间开始<input v-model="createForm.periodStart" type="date" required /></label>
              <label class="sf-field">期间结束<input v-model="createForm.periodEnd" type="date" required /></label>
            </div>
          </form>
          <template v-else>
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
              <table class="sf-table" style="min-width: 1120px">
                <thead><tr><th>业务日期</th><th>单号 / 业务类型</th><th>商品 / 摘要</th><th>应付变动</th><th>预付款变动</th><th>贷项变动</th><th>状态</th><th>余额（应付 / 预付 / 贷项）</th></tr></thead>
                <tbody>
                  <tr v-if="!selected.snapshot.items.length"><td colspan="8" class="sf-empty">该期间没有账务变动</td></tr>
                  <tr v-for="item in selected.snapshot.items" :key="item.id">
                    <td>{{ item.businessDate }}</td>
                    <td>{{ item.documentNo }}<div class="sf-muted">{{ businessLabels[item.businessType] || item.businessType }}</div></td>
                    <td>{{ item.productName || item.remark || '-' }}</td>
                    <td class="sf-number">{{ money(item.payableChange) }}</td>
                    <td class="sf-number">{{ money(item.prepaymentChange) }}</td>
                    <td class="sf-number">{{ money(item.creditChange) }}</td>
                    <td><span class="sf-badge">{{ transactionStatus[item.status] || item.status }}</span></td>
                    <td>{{ money(item.balances.payable) }} / {{ money(item.balances.prepayment) }} / {{ money(item.balances.credit) }}</td>
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
            <button v-if="!selected && can('create')" form="supplier-reconciliation-create" class="sf-button primary" :disabled="saving"><Save :size="16" />生成快照</button>
            <template v-if="selected?.status === 'draft'">
              <button v-if="can('cancel')" class="sf-button danger" :disabled="saving" @click="cancel"><X :size="16" />取消草稿</button>
              <button v-if="can('confirm')" class="sf-button primary" :disabled="saving" @click="confirm"><Check :size="16" />确认并锁定期间</button>
            </template>
          </div>
        </footer>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Plus, RefreshCw, Save, Search, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { operationKey } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'

const user = useUserStore()
const statusLabels = { draft: '草稿', confirmed: '已确认并锁期', cancelled: '已取消' }
const transactionStatus = { audited: '已审核', reversed: '已冲销', reversal: '冲销流水' }
const businessLabels = {
  INITIAL: '期初余额',
  PURCHASE_INBOUND: '采购入库应付',
  INDEPENDENT_PURCHASE_INBOUND: '独立入库应付',
  PAYMENT: '供应商付款核销',
  ADVANCE_PAYMENT: '新增预付款',
  PURCHASE_RETURN: '采购退货',
  PURCHASE_RETURN_ADJUSTMENT: '退货价格调整',
  SUPPLIER_REFUND: '供应商退款',
  CREDIT_ALLOCATION: '贷项核销'
}
const options = ref({ stores: [], suppliers: [] })
const records = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const dialogError = ref('')
const dialogOpen = ref(false)
const selected = ref(null)
const filters = reactive({ keyword: '', storeId: '', supplierId: '', status: '', periodStart: '', periodEnd: '' })
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
  return { supplierId: '', storeId: '', periodStart: `${today.slice(0, 7)}-01`, periodEnd: today }
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
function openCreate() {
  selected.value = null
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
  try {
    selected.value = await request.get(`/supplier-reconciliations/${id}`)
    setConfirmation(selected.value)
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
}
function close() {
  if (saving.value) return
  dialogOpen.value = false
}
async function create() {
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post('/supplier-reconciliations', {
      ...createForm.value, idempotencyKey: operationKey()
    })
    selected.value = response.reconciliation
    setConfirmation(selected.value)
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function refreshSnapshot() {
  if (!selected.value) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/refresh`, {
      version: selected.value.version, idempotencyKey: operationKey()
    })
    selected.value = response.reconciliation
    setConfirmation(selected.value)
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function confirm() {
  if (!selected.value) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/confirm`, {
      version: selected.value.version, idempotencyKey: operationKey(),
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
    await load()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function cancel() {
  if (!selected.value || !window.confirm('取消这张尚未确认的对账草稿？')) return
  saving.value = true
  dialogError.value = ''
  try {
    const response = await request.post(`/supplier-reconciliations/${selected.value.id}/cancel`, {
      version: selected.value.version, idempotencyKey: operationKey()
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
