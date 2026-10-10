<template>
  <Teleport to="body" :disabled="embedded">
    <div :class="embedded ? 'sf-embedded-layer' : 'sf-modal-layer'" @click.self="close">
      <section ref="documentElement" class="supplier-finance-dialog" :class="{ 'sf-embedded-document': embedded }" :role="embedded ? 'region' : 'dialog'" :aria-modal="embedded ? undefined : true" :aria-label="invoiceMode ? '采购发票登记' : '供应商付款单'">
        <header class="sf-header">
          <h2>{{ invoiceMode ? '采购发票' : '供应商付款' }}{{ form.invoiceNo || form.documentNo ? ` · ${form.invoiceNo || form.documentNo}` : '' }} <span v-if="form.id" class="sf-badge">{{ documentStatusLabels[form.status] }}</span></h2>
          <button v-if="!embedded" type="button" class="sf-button icon" title="关闭" aria-label="关闭" :disabled="busy" @click="close"><X :size="18" /></button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
          <p v-if="loading" class="sf-empty">加载单据中...</p>
          <form v-else-if="!loadFailed" id="supplier-document-form" @submit.prevent="save">
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="form.storeId" required :disabled="readonly || embedded || invoiceMode && !!form.id || !!form.auditedAt" @change="changeParty"><option value="">请选择</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option><option v-if="form.storeId && !options.stores.some(store => Number(store.id) === Number(form.storeId))" :value="form.storeId">{{ form.storeName || form.storeId }}</option></select></label>
              <label class="sf-field">供应商<select v-model="form.supplierId" required :disabled="readonly || invoiceMode && !!form.id || !!form.auditedAt" @change="changeParty"><option value="">请选择</option><option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option><option v-if="form.supplierId && !suppliers.some(supplier => Number(supplier.id) === Number(form.supplierId))" :value="form.supplierId">{{ form.supplierName || form.supplierId }}</option></select></label>
              <label class="sf-field">业务日期<input v-model="form.businessDate" type="date" required :disabled="readonly" /></label>
              <template v-if="invoiceMode">
                <label class="sf-field">发票号码<input v-model.trim="form.invoiceNo" maxlength="100" required :disabled="readonly" /></label>
                <label class="sf-field">发票日期<input v-model="form.invoiceDate" type="date" required :disabled="readonly" /></label>
                <label class="sf-field">发票类型<select v-model="form.invoiceType" required :disabled="readonly"><option value="vat-special">增值税专用发票</option><option value="vat-normal">增值税普通发票</option><option value="vat">增值税发票</option><option value="electronic">电子发票</option><option value="other">其他发票</option><option v-if="form.invoiceType && !['vat-special', 'vat-normal', 'vat', 'electronic', 'other'].includes(form.invoiceType)" :value="form.invoiceType">{{ form.invoiceType }}</option></select></label>
              </template>
              <template v-else>
                <label class="sf-field">银行账户<select v-model="form.bankAccountId" required :disabled="readonly"><option value="">请选择</option><option v-for="bank in banks" :key="bank.id" :value="bank.id">{{ bank.accountName }} · {{ bank.bankName }}</option></select></label>
                <label class="sf-field">付款日期<input v-model="form.paymentDate" type="date" required :disabled="readonly" /></label>
                <label class="sf-field">付款方式<select v-model="form.paymentMethod" required :disabled="readonly"><option value="bank-transfer">银行转账</option><option value="cash">现金账户</option><option value="online">线上支付</option><option value="other">其他</option><option v-if="form.paymentMethod === 'transfer'" value="transfer">银行转账</option><option v-else-if="form.paymentMethod && !['bank-transfer', 'cash', 'online', 'other'].includes(form.paymentMethod)" :value="form.paymentMethod">{{ form.paymentMethod }}</option></select></label>
                <label class="sf-field">本次实际付款<input v-model.number="form.paymentAmount" type="number" min="0.01" step="0.01" required :disabled="readonly" /></label>
                <label class="sf-field wide">未开票付款原因<textarea v-model.trim="form.unbilledReason" maxlength="500" :disabled="readonly" /></label>
                <label v-if="user.hasPerm('admin.finance.supplier_payment.invoice_override') || form.invoiceOverride" class="sf-check wide"><input v-model="form.invoiceOverride" type="checkbox" :disabled="readonly" />财务豁免见票付款</label>
              </template>
              <label class="sf-field wide">备注<textarea v-model="form.remark" maxlength="500" :disabled="readonly" /></label>
            </div>
            <div class="sf-header sf-section-title"><h3>{{ invoiceMode ? '发票分配明细' : '应付核销明细' }}</h3><button v-if="!readonly" class="sf-button icon" type="button" title="刷新可分配余额" aria-label="刷新可分配余额" :disabled="sourcesLoading || !form.supplierId || !form.storeId" @click="loadSources"><RefreshCw :size="16" /></button></div>
            <label v-if="embedded && invoiceMode && !readonly" class="sf-check"><input v-model="includeOtherOrders" type="checkbox" :disabled="busy" />合并同供应商其他单据</label>
            <PayableAllocationTable v-model="form.allocations" :sources="visibleSources" :invoice="invoiceMode" :readonly="readonly" :loading="sourcesLoading" />
            <div class="sf-summary">
              <template v-if="invoiceMode"><span>未税合计<strong>{{ formatMoney(baseTotal) }}</strong></span><span>税额合计<strong>{{ formatMoney(taxTotal) }}</strong></span><span>价税合计<strong>{{ formatMoney(baseTotal + taxTotal) }}</strong></span><span v-if="embedded">本单分配<strong>{{ formatMoney(currentDocumentTotal) }}</strong></span></template>
              <template v-else><span>实际付款<strong>{{ formatMoney(form.paymentAmount) }}</strong></span><span>本次核销<strong>{{ formatMoney(allocatedTotal) }}</strong></span><span>新增预付款<strong :class="{ 'sf-error': advanceTotal < 0 }">{{ formatMoney(advanceTotal) }}</strong></span></template>
            </div>
            <div v-if="invoiceMode" class="sf-form-grid sf-section-title">
              <label class="sf-check wide"><input v-model="form.hasDifference" type="checkbox" :disabled="readonly" />发票金额或税额存在差异</label>
              <label class="sf-field wide">差异原因<textarea v-model="form.differenceReason" maxlength="500" :required="form.hasDifference" :disabled="readonly" /></label>
            </div>
            <SupplierAttachments v-model="form.attachments" :store-id="form.storeId" :readonly="readonly" @uploading="uploading = $event" />
            <template v-if="!invoiceMode && form.bankTransactions?.length">
              <div class="sf-header sf-section-title"><h3>银行流水</h3></div>
              <div class="sf-table-scroll"><table class="sf-table"><thead><tr><th>业务日期</th><th>类型</th><th>银行账户</th><th>余额变动</th><th>变动后余额</th><th>操作人 / 时间</th></tr></thead><tbody><tr v-for="movement in form.bankTransactions" :key="movement.id"><td>{{ movement.businessDate }}</td><td>{{ movement.reversalOfId ? '付款冲销' : '付款扣款' }}</td><td>{{ options.bankAccounts.find(bank => bank.id === movement.bankAccountId)?.accountName || movement.bankAccountId }}</td><td class="sf-number">{{ formatMoney(movement.change) }}</td><td class="sf-number">{{ formatMoney(movement.balanceAfter) }}</td><td>{{ movement.createdBy }}<div class="sf-muted">{{ movement.createdAt }}</div></td></tr></tbody></table></div>
            </template>
            <div v-if="form.id" class="sf-meta">
              <span>制单：{{ form.createdBy }} · {{ form.createdAt }}</span>
              <span v-if="form.confirmedAt || form.auditedAt">{{ invoiceMode ? '确认' : '审核' }}：{{ form.confirmedBy || form.auditedBy }} · {{ form.confirmedAt || form.auditedAt }}</span>
              <span v-if="form.reversedAt">撤销：{{ form.reversedAt }}</span>
            </div>
          </form>
        </div>
        <footer class="sf-footer">
          <button class="sf-button" type="button" :disabled="busy" @click="close"><ArrowLeft v-if="embedded" :size="16" />{{ embedded ? '返回发票记录' : '关闭' }}</button>
          <div class="sf-actions">
            <button v-if="!editing && draft && can('edit')" class="sf-button" :disabled="busy" @click="startEditing"><Pencil :size="16" />编辑</button>
            <button v-if="!editing && draft && can('delete')" class="sf-button icon danger" title="删除单据" aria-label="删除单据" :disabled="busy" @click="confirmAction('delete')"><Trash2 :size="16" /></button>
            <button v-if="editing && !loadFailed && can(form.id ? 'edit' : 'create')" form="supplier-document-form" type="submit" class="sf-button primary" :disabled="busy || !!confirmation"><Save :size="16" />{{ saving ? '保存中...' : '保存草稿' }}</button>
            <button v-if="!editing && draft && can(invoiceMode ? 'confirm' : 'audit')" class="sf-button primary" :disabled="busy" @click="confirmAction('post')"><Check :size="16" />{{ invoiceMode ? '确认发票' : '审核付款' }}</button>
            <button v-if="!editing && posted && can(invoiceMode ? 'reverse_confirm' : 'reverse_audit')" class="sf-button danger" :disabled="busy" @click="confirmAction('reverse')"><RotateCcw :size="16" />{{ invoiceMode ? '撤销确认' : '反审核付款' }}</button>
          </div>
        </footer>
        <div v-if="embedded && confirmation" ref="confirmationPanel" class="sf-inline-confirmation" role="alertdialog" aria-label="确认操作" @keydown.esc.stop="cancelConfirmation">
          <strong>{{ confirmation.title }}</strong>
          <p>{{ confirmation.message }}</p>
          <div class="sf-actions"><button class="sf-button" :disabled="saving" @click="cancelConfirmation">取消</button><button class="sf-button" :class="confirmation.action === 'post' ? 'primary' : 'danger'" :disabled="saving" @click="performAction">{{ saving ? '处理中...' : '确认' }}</button></div>
        </div>
      </section>
    </div>
    <div v-if="!embedded && confirmation" class="sf-modal-layer sf-confirm-layer">
      <section class="supplier-finance-dialog sf-confirm-dialog" role="dialog" aria-modal="true" aria-label="确认操作">
        <header class="sf-header"><h2>{{ confirmation.title }}</h2></header>
        <div class="sf-dialog-body"><p>{{ confirmation.message }}</p></div>
        <footer class="sf-footer"><button class="sf-button" :disabled="saving" @click="confirmation = null">取消</button><button class="sf-button" :class="confirmation.action === 'post' ? 'primary' : 'danger'" :disabled="saving" @click="performAction">{{ saving ? '处理中...' : '确认' }}</button></footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ArrowLeft, Check, Pencil, RefreshCw, RotateCcw, Save, Trash2, X } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { localDate } from '@/composables/documents/documentModels'
import { documentStatusLabels, formatMoney, invoiceSourceKey, operationKey, sumMoney } from '@/utils/supplierFinance'
import PayableAllocationTable from './PayableAllocationTable.vue'
import SupplierAttachments from './SupplierAttachments.vue'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({
  mode: { type: String, required: true }, documentId: { type: Number, default: null },
  options: { type: Object, required: true }, embedded: Boolean,
  context: { type: Object, default: null }, initialSupplierId: { type: Number, default: null }
})
const emit = defineEmits(['close', 'updated'])
const user = useUserStore()
const invoiceMode = computed(() => props.mode === 'invoice')
const endpoint = computed(() => invoiceMode.value ? '/purchase-invoices' : '/supplier-payments')
const form = ref({
  storeId: props.context?.storeId || '', supplierId: props.initialSupplierId || '', businessDate: localDate(), paymentDate: localDate(), invoiceDate: localDate(),
  invoiceNo: '', invoiceType: 'vat-special', paymentMethod: 'bank-transfer', bankAccountId: '',
  paymentAmount: '', unbilledReason: '', invoiceOverride: false, hasDifference: false,
  differenceReason: '', attachments: [], allocations: [], remark: '', status: 'draft', idempotencyKey: operationKey()
})
const sources = ref([])
const loading = ref(false)
const loadFailed = ref(false)
const sourcesLoading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const editing = ref(!props.documentId)
const error = ref('')
const confirmation = ref(null)
const confirmationPanel = ref(null)
const documentElement = ref(null)
const includeOtherOrders = ref(false)
const savedSnapshot = ref(JSON.stringify(form.value))
const dirty = computed(() => editing.value && JSON.stringify(form.value) !== savedSnapshot.value)
const actionKeys = new Map()
const busy = computed(() => loading.value || saving.value || uploading.value || sourcesLoading.value)
const draft = computed(() => form.value.id && !form.value.lockedAt && ['draft', 'reversed'].includes(form.value.status))
const posted = computed(() => !form.value.lockedAt && form.value.status === (invoiceMode.value ? 'confirmed' : 'audited'))
const readonly = computed(() => !editing.value || busy.value || !!confirmation.value)
const suppliers = computed(() => props.options.suppliers.filter(row => !row.storeId || Number(row.storeId) === Number(form.value.storeId)))
const banks = computed(() => props.options.bankAccounts.filter(row => Number(row.storeId) === Number(form.value.storeId)))
const allocatedTotal = computed(() => sumMoney(form.value.allocations, 'amount'))
const baseTotal = computed(() => sumMoney(form.value.allocations, 'amountExcludingTax'))
const taxTotal = computed(() => sumMoney(form.value.allocations, 'taxAmount'))
const advanceTotal = computed(() => Math.round((Number(form.value.paymentAmount || 0) - allocatedTotal.value) * 100) / 100)
const can = action => user.hasPerm(`${invoiceMode.value ? 'admin.purchase.invoice' : 'admin.finance.supplier_payment'}.${action}`)
let sourceRequest = 0
let leaveResolver = null
function matchesContext(row) {
  if (!props.context) return true
  return props.context.purchaseOrderId
    ? Number(row.purchaseOrderId) === Number(props.context.purchaseOrderId)
    : row.sourceType === 'stock_inbound' && Number(row.sourceId) === Number(props.context.inboundId)
}
const visibleSources = computed(() => includeOtherOrders.value ? sources.value : sources.value.filter(row =>
  matchesContext(row) || form.value.allocations.some(entry => invoiceSourceKey(entry) === invoiceSourceKey(row))))
const currentDocumentTotal = computed(() => form.value.allocations.reduce((total, row) =>
  total + (matchesContext(row) ? Math.round((Number(row.amountExcludingTax || 0) + Number(row.taxAmount || 0)) * 100) : 0), 0) / 100)
function cancelConfirmation() {
  confirmation.value = null
  leaveResolver?.(false)
  leaveResolver = null
}
async function requestLeave() {
  if (busy.value || confirmation.value) return false
  if (!props.embedded || !dirty.value) return true
  confirmation.value = { action: 'discard', title: '放弃未保存修改', message: '当前发票有未保存修改，确定放弃吗？' }
  return new Promise(resolve => { leaveResolver = resolve })
}
async function close() { if (await requestLeave()) emit('close') }
async function load() {
  loading.value = true
  try {
    if (props.documentId) form.value = await request.get(`${endpoint.value}/${props.documentId}`)
    savedSnapshot.value = JSON.stringify(form.value)
    await loadSources()
  } catch (err) { loadFailed.value = true; error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
async function loadSources() {
  const sequence = ++sourceRequest
  sources.value = []
  if (!form.value.supplierId || !form.value.storeId) { sourcesLoading.value = false; return }
  sourcesLoading.value = true
  try {
    const result = invoiceMode.value && props.embedded
      ? await request.get('/purchase-invoices/sources', { params: { storeId: form.value.storeId, supplierId: form.value.supplierId, invoiceId: form.value.id || undefined } })
      : await request.get(`/suppliers/${form.value.supplierId}/${invoiceMode.value ? 'invoice-payables' : 'payables'}/allocatable`, { params: { storeId: form.value.storeId } })
    if (sequence === sourceRequest) sources.value = result.items
  } catch (err) { if (sequence === sourceRequest) error.value = err.response?.data?.message || err.message }
  finally { if (sequence === sourceRequest) sourcesLoading.value = false }
}
function changeParty() {
  form.value.allocations = []
  form.value.bankAccountId = ''
  form.value.attachments = []
  if (!suppliers.value.some(row => Number(row.id) === Number(form.value.supplierId))) form.value.supplierId = ''
  loadSources()
}
async function startEditing() {
  if (busy.value || confirmation.value) return
  savedSnapshot.value = JSON.stringify(form.value)
  editing.value = true
  await loadSources()
  if (props.embedded) {
    await nextTick()
    documentElement.value?.scrollIntoView({ block: 'start' })
  }
}
async function save() {
  if (busy.value || confirmation.value || !can(form.value.id ? 'edit' : 'create')) return
  if (props.embedded && currentDocumentTotal.value <= 0) {
    error.value = '请为当前单据分配开票金额'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value, allocations: form.value.allocations.filter(row => invoiceMode.value
      ? Number(row.amountExcludingTax || 0) + Number(row.taxAmount || 0) > 0 : Number(row.amount || 0) > 0) }
    if (invoiceMode.value) {
      payload.amountExcludingTax = baseTotal.value
      payload.taxAmount = taxTotal.value
      payload.amountIncludingTax = Math.round((baseTotal.value + taxTotal.value) * 100) / 100
    }
    const response = await request({ url: form.value.id ? `${endpoint.value}/${form.value.id}` : endpoint.value, method: form.value.id ? 'PUT' : 'POST', data: payload })
    form.value = response[invoiceMode.value ? 'invoice' : 'payment']
    savedSnapshot.value = JSON.stringify(form.value)
    editing.value = false
    emit('updated')
    await loadSources()
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
function confirmAction(action) {
  if (busy.value || confirmation.value) return
  const labels = {
    delete: { title: '删除单据', message: '确定删除当前单据？有历史审核的单据将保留为已作废记录。' },
    post: { title: invoiceMode.value ? '确认采购发票' : '审核供应商付款', message: invoiceMode.value ? '确认当前发票？订单开票记录将保留，已有入库应付的部分同步更新开票分配。' : `将从银行账户扣减 ${formatMoney(form.value.paymentAmount)} 元，核销 ${formatMoney(allocatedTotal.value)} 元应付，并新增 ${formatMoney(advanceTotal.value)} 元预付款。` },
    reverse: { title: invoiceMode.value ? '撤销发票确认' : '反审核付款', message: invoiceMode.value ? '将撤销当前发票的开票分配，已发生的付款保持不变。' : '将冲销当前付款并恢复银行余额与应付核销。已使用的预付款须先撤销后续核销。' }
  }
  confirmation.value = { ...labels[action], action }
}
async function performAction() {
  const action = confirmation.value.action
  if (action === 'discard') {
    savedSnapshot.value = JSON.stringify(form.value)
    confirmation.value = null
    leaveResolver?.(true)
    leaveResolver = null
    return
  }
  const suffix = action === 'post' ? invoiceMode.value ? 'confirm' : 'audit' : invoiceMode.value ? 'reverse-confirm' : 'reverse-audit'
  const key = `${action}:${form.value.id}:${form.value.version}`
  if (!actionKeys.has(key)) actionKeys.set(key, operationKey())
  saving.value = true
  error.value = ''
  try {
    const response = await request({
      url: `${endpoint.value}/${form.value.id}${action === 'delete' ? '' : `/${suffix}`}`,
      method: action === 'delete' ? 'DELETE' : 'POST',
      data: { version: form.value.version, idempotencyKey: actionKeys.get(key) }
    })
    confirmation.value = null
    emit('updated')
    if (action === 'delete') emit('close')
    else { form.value = response[invoiceMode.value ? 'invoice' : 'payment']; await loadSources() }
  } catch (err) { confirmation.value = null; error.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
onMounted(load)
watch(confirmation, async value => {
  if (!value || !props.embedded) return
  await nextTick()
  confirmationPanel.value?.querySelector('button')?.focus()
})
defineExpose({ requestLeave })
</script>
