<template>
  <section class="supplier-finance-page">
    <header class="sf-header">
      <h1>供应商退款</h1>
      <div class="sf-actions">
        <button v-if="can('create')" class="sf-button primary" @click="openNew"><Plus :size="16" />新增退款</button>
        <button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button>
      </div>
    </header>
    <form class="sf-toolbar" @submit.prevent="load">
      <label class="sf-field">单号 / 供应商<input v-model.trim="filters.keyword" type="search" /></label>
      <label class="sf-field">门店<select v-model="filters.storeId"><option value="">全部授权门店</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
      <label class="sf-field">供应商<select v-model="filters.supplierId"><option value="">全部供应商</option><option v-for="supplier in suppliersForFilter" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
      <label class="sf-field">状态<select v-model="filters.status"><option value="">全部</option><option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option></select></label>
      <label class="sf-field">开始日期<input v-model="filters.startDate" type="date" /></label>
      <label class="sf-field">结束日期<input v-model="filters.endDate" type="date" /></label>
      <button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button>
    </form>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary">
      <span>单据数<strong>{{ records.length }}</strong></span>
      <span>已审核退款<strong>{{ money(auditedTotal) }}</strong></span>
      <span>银行入账单<strong>{{ auditedCount }}</strong></span>
    </div>
    <div class="sf-table-scroll">
      <table class="sf-table" style="min-width: 1040px">
        <thead><tr><th>退款单号</th><th>供应商 / 门店</th><th>业务日期 / 到账日期</th><th>银行账户</th><th>退款金额</th><th>贷项分配</th><th>状态</th><th>制单 / 审核</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="9" class="sf-empty">加载中...</td></tr>
          <tr v-else-if="!records.length"><td colspan="9" class="sf-empty">暂无供应商退款单</td></tr>
          <tr v-for="row in records" :key="row.id">
            <td><button class="sf-link" @click="openRecord(row.id)">{{ row.documentNo }}</button></td>
            <td>{{ row.supplierName }}<div class="sf-muted">{{ row.storeName }}</div></td>
            <td>{{ row.businessDate }}<div class="sf-muted">到账 {{ row.refundDate }}</div></td>
            <td>{{ row.accountName }}</td>
            <td class="sf-number">{{ money(row.refundAmount) }}</td>
            <td>{{ row.allocations.length }} 笔</td>
            <td><span class="sf-badge">{{ statusLabels[row.status] || row.status }}</span></td>
            <td>{{ row.createdBy }}<div class="sf-muted">{{ row.auditedBy || '-' }}</div></td>
            <td><div class="sf-actions">
              <button v-if="['draft', 'reversed'].includes(row.status) && can('edit')" class="sf-button icon" title="编辑退款草稿" aria-label="编辑退款草稿" @click="openRecord(row.id)"><Pencil :size="16" /></button>
              <button v-if="['draft', 'reversed'].includes(row.status) && can('audit')" class="sf-button icon" title="审核并登记银行入账" aria-label="审核并登记银行入账" @click="act(row, 'audit')"><Check :size="16" /></button>
              <button v-if="row.status === 'audited' && can('reverse_audit')" class="sf-button icon danger" title="反审核" aria-label="反审核" @click="act(row, 'reverse-audit')"><RotateCcw :size="16" /></button>
              <button v-if="['draft', 'reversed'].includes(row.status) && can('delete')" class="sf-button icon danger" title="删除退款草稿" aria-label="删除退款草稿" @click="act(row, 'delete')"><Trash2 :size="16" /></button>
            </div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="dialogOpen" class="sf-modal-layer" @click.self="close">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-label="供应商退款单">
        <header class="sf-header">
          <h2>{{ form.documentNo || (form.id ? '供应商退款详情' : '新增供应商退款') }} <span v-if="form.id" class="sf-badge">{{ statusLabels[form.status] }}</span></h2>
          <button class="sf-button icon" title="关闭" aria-label="关闭" :disabled="saving" @click="close"><X :size="18" /></button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="dialogError" class="sf-error" role="alert">{{ dialogError }}</p>
          <form id="supplier-refund-form" @submit.prevent="save">
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="form.storeId" required :disabled="!editing" @change="changeParty"><option value="">请选择</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
              <label class="sf-field">供应商<select v-model="form.supplierId" required :disabled="!editing" @change="changeParty"><option value="">请选择</option><option v-for="supplier in suppliersForForm" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
              <label class="sf-field">业务日期<input v-model="form.businessDate" type="date" required :disabled="!editing" /></label>
              <label class="sf-field">退款到账日期<input v-model="form.refundDate" type="date" required :disabled="!editing" /></label>
              <label class="sf-field">银行账户<select v-model="form.bankAccountId" required :disabled="!editing"><option value="">请选择</option><option v-for="bank in banksForForm" :key="bank.id" :value="bank.id">{{ bank.accountName }} · {{ bank.bankName }}（余额 {{ money(bank.balance) }}）</option></select></label>
              <label class="sf-field">本次退款金额<input :value="money(allocationTotal)" readonly /></label>
              <label class="sf-field wide">备注<textarea v-model.trim="form.remark" maxlength="500" :disabled="!editing" /></label>
            </div>
            <div class="sf-header sf-section-title">
              <h3>退款贷项分配</h3>
              <button v-if="editing" class="sf-button icon" type="button" title="刷新可用贷项" aria-label="刷新可用贷项" :disabled="creditLoading || !form.supplierId || !form.storeId" @click="loadCredits"><RefreshCw :size="16" /></button>
            </div>
            <p v-if="creditLoading" class="sf-muted">正在读取可退款贷项...</p>
            <div class="sf-table-scroll">
              <table class="sf-table" style="min-width: 820px">
                <thead><tr><th>贷项来源</th><th>贷项总额</th><th>可退款余额</th><th>本次退款</th><th v-if="editing">移除</th></tr></thead>
                <tbody>
                  <tr v-if="!form.allocations.length"><td :colspan="editing ? 5 : 4" class="sf-empty">请选择一笔或多笔可用贷项</td></tr>
                  <tr v-for="(line, index) in form.allocations" :key="`${line.creditTransactionId}-${index}`">
                    <td>{{ creditFor(line)?.documentNo || line.documentNo || `贷项 #${line.creditTransactionId}` }}<div class="sf-muted">{{ creditFor(line)?.businessDate || line.businessDate || '' }} · {{ creditFor(line)?.productName || '' }}</div></td>
                    <td class="sf-number">{{ money(creditFor(line)?.creditAmount ?? line.creditAmount) }}</td>
                    <td class="sf-number">{{ money(creditFor(line)?.availableAmount ?? line.availableAmount ?? 0) }}</td>
                    <td><input v-if="editing" v-model.number="line.amount" type="number" min="0.01" :max="creditFor(line)?.availableAmount" step="0.01" required /><span v-else>{{ money(line.amount) }}</span></td>
                    <td v-if="editing"><button class="sf-button icon danger" type="button" title="移除贷项" aria-label="移除贷项" @click="form.allocations.splice(index, 1)"><Trash2 :size="16" /></button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="editing" class="sf-actions sf-section-title">
              <label class="sf-field" style="min-width: 260px">添加可用贷项<select v-model="creditToAdd" @change="addCredit"><option value="">选择贷项</option><option v-for="credit in availableCredits" :key="credit.creditTransactionId" :value="credit.creditTransactionId">{{ credit.documentNo }} · 可退 {{ money(credit.availableAmount) }}</option></select></label>
            </div>
            <div class="sf-summary"><span>退款贷项数<strong>{{ form.allocations.length }}</strong></span><span>退款合计<strong>{{ money(allocationTotal) }}</strong></span></div>
            <template v-if="form.bankTransactions?.length">
              <div class="sf-header sf-section-title"><h3>银行流水</h3></div>
              <div class="sf-table-scroll"><table class="sf-table"><thead><tr><th>日期</th><th>变动</th><th>余额</th><th>冲销流水</th></tr></thead><tbody><tr v-for="entry in form.bankTransactions" :key="entry.id"><td>{{ entry.businessDate }}</td><td class="sf-number">{{ money(entry.change) }}</td><td class="sf-number">{{ money(entry.balanceAfter) }}</td><td>{{ entry.reversalOfId || '-' }}</td></tr></tbody></table></div>
            </template>
          </form>
        </div>
        <footer class="sf-footer">
          <span v-if="form.id" class="sf-muted">版本 {{ form.version }} · {{ form.createdBy }} · {{ form.createdAt }}</span>
          <div class="sf-actions">
            <button class="sf-button" :disabled="saving" @click="close">关闭</button>
            <button v-if="editing" form="supplier-refund-form" class="sf-button primary" :disabled="saving || creditLoading"><Save :size="16" />{{ saving ? '保存中...' : '保存草稿' }}</button>
            <button v-if="!editing && ['draft', 'reversed'].includes(form.status) && can('edit')" class="sf-button" :disabled="saving" @click="editing = true; loadCredits()"><Pencil :size="16" />编辑</button>
            <button v-if="!editing && ['draft', 'reversed'].includes(form.status) && can('audit')" class="sf-button primary" :disabled="saving" @click="act(form, 'audit')"><Check :size="16" />审核并入账</button>
            <button v-if="!editing && form.status === 'audited' && can('reverse_audit')" class="sf-button danger" :disabled="saving" @click="act(form, 'reverse-audit')"><RotateCcw :size="16" />反审核</button>
          </div>
        </footer>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Pencil, Plus, RefreshCw, RotateCcw, Save, Search, Trash2, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { formatMoney, operationKey } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'

const user = useUserStore()
const statusLabels = { draft: '草稿', audited: '已审核', reversed: '已反审核', cancelled: '已取消' }
const options = ref({ stores: [], suppliers: [], bankAccounts: [] })
const records = ref([])
const credits = ref([])
const filters = reactive({ keyword: '', storeId: '', supplierId: '', status: '', startDate: '', endDate: '' })
const loading = ref(false)
const creditLoading = ref(false)
const saving = ref(false)
const error = ref('')
const dialogError = ref('')
const dialogOpen = ref(false)
const editing = ref(false)
const creditToAdd = ref('')
const form = ref(emptyForm())
const can = action => user.hasPerm(`admin.finance.supplier_refund.${action}`)
const suppliersForFilter = computed(() => options.value.suppliers.filter(row => !filters.storeId || !row.storeId || Number(row.storeId) === Number(filters.storeId)))
const suppliersForForm = computed(() => options.value.suppliers.filter(row => !form.value.storeId || !row.storeId || Number(row.storeId) === Number(form.value.storeId)))
const banksForForm = computed(() => options.value.bankAccounts.filter(row => Number(row.storeId) === Number(form.value.storeId)))
const availableCredits = computed(() => credits.value.filter(row => !form.value.allocations.some(line => Number(line.creditTransactionId) === Number(row.creditTransactionId))))
const allocationTotal = computed(() => Math.round(form.value.allocations.reduce((sum, row) => sum + Number(row.amount || 0), 0) * 100) / 100)
const audited = computed(() => records.value.filter(row => row.status === 'audited'))
const auditedCount = computed(() => audited.value.length)
const auditedTotal = computed(() => audited.value.reduce((sum, row) => sum + Number(row.refundAmount || 0), 0))

function emptyForm() {
  return { supplierId: '', storeId: '', businessDate: localDate(), refundDate: localDate(), bankAccountId: '', allocations: [], remark: '', status: 'draft', version: 1 }
}
function money(value) { return formatMoney(value) }
function creditFor(line) { return credits.value.find(row => Number(row.creditTransactionId) === Number(line.creditTransactionId)) }
async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await request.get('/supplier-refunds', { params: filters })
    records.value = result.items || []
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
async function loadCredits() {
  credits.value = []
  if (!form.value.supplierId || !form.value.storeId) return
  creditLoading.value = true
  try {
    const result = await request.get(`/suppliers/${form.value.supplierId}/supplier-refund-credits`, { params: { storeId: form.value.storeId } })
    credits.value = result.items || []
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { creditLoading.value = false }
}
function changeParty() {
  form.value.allocations = []
  form.value.bankAccountId = ''
  dialogError.value = ''
  if (!suppliersForForm.value.some(row => Number(row.id) === Number(form.value.supplierId))) form.value.supplierId = ''
  loadCredits()
}
function addCredit() {
  const credit = credits.value.find(row => Number(row.creditTransactionId) === Number(creditToAdd.value))
  if (credit) form.value.allocations.push({ creditTransactionId: credit.creditTransactionId, amount: credit.availableAmount })
  creditToAdd.value = ''
}
function openNew() {
  form.value = emptyForm()
  credits.value = []
  dialogError.value = ''
  editing.value = true
  dialogOpen.value = true
}
async function openRecord(id) {
  dialogError.value = ''
  credits.value = []
  editing.value = false
  dialogOpen.value = true
  try {
    const row = await request.get(`/supplier-refunds/${id}`)
    form.value = { ...row, allocations: row.allocations.map(item => ({ ...item })) }
    editing.value = ['draft', 'reversed'].includes(row.status) && can('edit')
    if (editing.value) await loadCredits()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
}
function close() {
  if (saving.value) return
  dialogOpen.value = false
}
async function save() {
  if (!form.value.allocations.length || form.value.allocations.some(line => Number(line.amount) <= 0 || Number(line.amount) > Number(creditFor(line)?.availableAmount ?? line.availableAmount ?? 0))) {
    dialogError.value = '请为退款选择可用贷项，并确保每笔金额不超过可退款余额。'
    return
  }
  if (!form.value.bankAccountId) {
    dialogError.value = '请选择本门店的银行账户。'
    return
  }
  saving.value = true
  dialogError.value = ''
  try {
    const payload = {
      supplierId: form.value.supplierId, storeId: form.value.storeId,
      businessDate: form.value.businessDate, refundDate: form.value.refundDate,
      bankAccountId: form.value.bankAccountId, refundAmount: allocationTotal.value,
      allocations: form.value.allocations.map(row => ({ creditTransactionId: row.creditTransactionId, amount: row.amount })),
      remark: form.value.remark, version: form.value.version, idempotencyKey: operationKey()
    }
    const response = await request({
      url: form.value.id ? `/supplier-refunds/${form.value.id}` : '/supplier-refunds',
      method: form.value.id ? 'PUT' : 'POST', data: payload
    })
    form.value = response.refund
    editing.value = false
    await load()
    await loadCredits()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function act(row, action) {
  const labels = { audit: '审核该退款，并将款项记入所选银行账户？', 'reverse-audit': '反审核该退款，并冲销银行入账、恢复贷项？', delete: '删除该退款草稿？' }
  if (!window.confirm(labels[action])) return
  saving.value = true
  dialogError.value = ''
  error.value = ''
  try {
    const suffix = action === 'audit' ? '/audit' : action === 'reverse-audit' ? '/reverse-audit' : ''
    const response = await request({
      url: `/supplier-refunds/${row.id}${suffix}`, method: action === 'delete' ? 'DELETE' : 'POST',
      data: { version: row.version, idempotencyKey: operationKey() }
    })
    if (dialogOpen.value && Number(form.value.id) === Number(row.id) && action !== 'delete') {
      form.value = response.refund
      editing.value = false
    }
    if (action === 'delete') dialogOpen.value = false
    await load()
    if (dialogOpen.value) await loadCredits()
  } catch (err) {
    const message = err.response?.data?.message || err.message
    if (dialogOpen.value) dialogError.value = message
    else error.value = message
  } finally { saving.value = false }
}

onMounted(async () => {
  try { options.value = await request.get('/supplier-refunds/options') }
  catch (err) { error.value = err.response?.data?.message || err.message }
  await load()
})
</script>
