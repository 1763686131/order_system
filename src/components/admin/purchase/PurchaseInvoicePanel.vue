<template>
  <section ref="panelElement" class="purchase-invoice-panel supplier-finance-page" aria-label="采购订单发票">
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <SupplierDocumentDialog
      v-if="editor"
      ref="documentEditor"
      :key="editor.key"
      mode="invoice"
      embedded
      :document-id="editor.id"
      :initial-supplier-id="editor.supplierId"
      :options="options"
      :context="documentContext"
      @close="editor = null"
      @updated="onUpdated"
    />
    <template v-else>
      <div class="sf-toolbar invoice-toolbar">
        <h3>发票记录 <span class="sf-muted">{{ invoices.length }} 张</span></h3>
        <div class="sf-actions">
          <button class="sf-button icon" type="button" title="刷新发票记录" aria-label="刷新发票记录" :disabled="loading || reversing" @click="load"><RefreshCw :size="16" /></button>
          <button v-if="fullyBilled && canReverse" class="sf-button danger" type="button" :disabled="actionState.busy || !reversibleInvoices.length" :title="reverseUnavailableReason" @click="requestReverse"><RotateCcw :size="16" />撤销发票</button>
          <button v-else-if="canCreate && !fullyBilled" class="sf-button primary" type="button" :disabled="actionState.busy || !availableSuppliers.length" @click="createInvoice"><Plus :size="16" />登记发票</button>
        </div>
      </div>
      <div class="sf-summary">
        <span>本单已确认开票<strong>{{ formatMoney(confirmedAmount) }}</strong></span>
        <span>本单草稿分配<strong>{{ formatMoney(draftAmount) }}</strong></span>
        <span>已确认待入库<strong>{{ formatMoney(pendingAmount) }}</strong></span>
        <span>本单可开票金额<strong>{{ formatMoney(contextData.availableAmount) }}</strong></span>
      </div>
      <div class="sf-table-scroll">
        <table v-resizable-columns="{ storageKey: 'purchase-order-invoice-records', resizeMode: 'fit', minWidth: 64 }" class="sf-table invoice-record-table">
          <colgroup>
            <col style="width: 160px">
            <col>
            <col>
            <col>
            <col>
            <col>
            <col>
            <col style="width: 64px">
          </colgroup>
          <thead><tr><th>发票号码</th><th>供应商</th><th>发票日期</th><th>状态</th><th class="sf-number">发票价税合计</th><th class="sf-number">本单分配金额</th><th>附件</th><th data-resizable="false">操作</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="sf-empty">加载发票记录中...</td></tr>
            <tr v-else-if="!invoices.length"><td colspan="8" class="sf-empty">{{ contextData.suppliers.length ? '暂无发票记录' : record.sourceType === 'warehouse-inbound' ? '暂无可开票采购应付' : '暂无可开票的已审核采购明细' }}</td></tr>
            <tr v-for="invoice in invoices" :key="invoice.id">
              <td><button class="sf-link" type="button" @click="openInvoice(invoice.id)">{{ invoice.invoiceNo }}</button><div v-if="invoice.hasDifference" class="sf-muted">存在差异</div></td>
              <td>{{ invoice.supplierName }}</td>
              <td>{{ invoice.invoiceDate }}</td>
              <td><span class="sf-badge">{{ documentStatusLabels[invoice.status] || invoice.status }}</span><div v-if="invoice.lockedAt" class="sf-muted">已对账锁定</div></td>
              <td class="sf-number">{{ formatMoney(invoice.amountIncludingTax) }}</td>
              <td class="sf-number">{{ formatMoney(currentAmount(invoice)) }}</td>
              <td>{{ invoice.attachments?.length || 0 }}</td>
              <td><button class="sf-button icon" type="button" title="查看发票" aria-label="查看发票" :disabled="reversing" @click="openInvoice(invoice.id)"><FileText :size="16" /></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
    <CustomModal
      :visible="reverseConfirmOpen"
      :z-index="2147482100"
      title="撤销发票"
      :message="reverseMessage"
      confirm-text="撤销发票"
      :confirm-disabled="!reverseTarget || reversing"
      danger
      @confirm="reverseInvoice"
      @cancel="reverseConfirmOpen = false"
    >
      <template #content>
        <label v-if="reversibleInvoices.length > 1" class="sf-field invoice-reverse-choice">发票
          <select v-model="reverseInvoiceId" aria-label="选择要撤销的发票">
            <option value="">请选择发票</option>
            <option v-for="invoice in reversibleInvoices" :key="invoice.id" :value="invoice.id">{{ invoice.invoiceNo }} · 本单 {{ formatMoney(currentAmount(invoice)) }}</option>
          </select>
        </label>
        <p class="invoice-reverse-message">{{ reverseMessage }}</p>
      </template>
    </CustomModal>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { FileText, Plus, RefreshCw, RotateCcw } from '@lucide/vue'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'
import { useUserStore } from '@/stores/user'
import { documentStatusLabels, formatMoney, operationKey } from '@/utils/supplierFinance'
import SupplierDocumentDialog from './SupplierDocumentDialog.vue'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({
  record: { type: Object, required: true },
  initialInvoiceId: { type: Number, default: null }
})
const emit = defineEmits(['updated', 'error'])
const user = useUserStore()
const invoices = ref([])
const contextData = ref({ suppliers: [], availableAmount: 0 })
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const reversing = ref(false)
const reverseConfirmOpen = ref(false)
const reverseInvoiceId = ref('')
const reverseKeys = new Map()
let loadSequence = 0
const editor = ref(null)
const documentEditor = ref(null)
const panelElement = ref(null)
const canCreate = computed(() => user.hasPerm('admin.purchase.invoice.create'))
const canReverse = computed(() => user.hasPerm('admin.purchase.invoice.reverse_confirm'))
const queryContext = computed(() => props.record.sourceType === 'warehouse-inbound'
  ? { inboundId: Number(props.record.inboundId) }
  : { purchaseOrderId: Number(props.record.id) })
const documentContext = computed(() => ({ ...queryContext.value, storeId: contextData.value.storeId }))
const availableSuppliers = computed(() => contextData.value.suppliers.filter(row => row.availableAmount > 0))
const invoiceAmount = computed(() => Math.max(
  Number(props.record.totalTaxIncludedAmount ?? (Number(props.record.totalAmount || 0) + Number(props.record.totalTaxAmount || 0))),
  Number(props.record.confirmedPayable || 0)
))
const fullyBilled = computed(() => invoiceAmount.value > 0 &&
  Math.round(Number(props.record.billedAmount || 0) * 100) >= Math.round(invoiceAmount.value * 100))
const reversibleInvoices = computed(() => invoices.value.filter(invoice =>
  invoice.status === 'confirmed' && !invoice.lockedAt && currentAmount(invoice) > 0))
const reverseUnavailableReason = computed(() => reversibleInvoices.value.length ? '' :
  invoices.value.some(invoice => invoice.status === 'confirmed' && invoice.lockedAt)
    ? '已对账锁定的发票不能撤销'
    : '暂无可撤销的已确认发票，基础开票记录需在原登记入口处理')
const actionState = computed(() => ({
  fullyBilled: fullyBilled.value,
  canCreate: canCreate.value,
  canReverse: canReverse.value,
  hasSources: contextData.value.suppliers.length > 0,
  canRegister: loaded.value && availableSuppliers.value.length > 0,
  canRevoke: loaded.value && reversibleInvoices.value.length > 0,
  busy: !loaded.value || loading.value || reversing.value || reverseConfirmOpen.value,
  reverseUnavailableReason: reverseUnavailableReason.value
}))
const reverseTarget = computed(() => reversibleInvoices.value.find(invoice => Number(invoice.id) === Number(reverseInvoiceId.value)))
const reverseMessage = computed(() => {
  const invoice = reverseTarget.value
  if (!invoice) return '请选择本单关联的已确认发票。每次只撤销选中的一张发票。'
  const otherDocuments = (invoice.allocations || []).some(row => !belongsToCurrent(row) && Number(row.amountIncludingTax) > 0)
  return `确认撤销发票「${invoice.invoiceNo}」吗？\n价税合计 ¥ ${formatMoney(invoice.amountIncludingTax)}，本单分配 ¥ ${formatMoney(currentAmount(invoice))}。\n将撤销整张发票的全部开票分配，已发生的付款保持不变。${otherDocuments ? '\n该发票还关联其他单据，这些单据的开票分配也会一并撤销。' : ''}`
})
const options = computed(() => ({
  stores: [{ id: contextData.value.storeId, name: contextData.value.storeName }],
  suppliers: editor.value?.id ? contextData.value.suppliers : availableSuppliers.value,
  bankAccounts: []
}))
function belongsToCurrent(row) {
  return queryContext.value.purchaseOrderId
    ? Number(row.purchaseOrderId) === queryContext.value.purchaseOrderId
    : row.sourceType === 'stock_inbound' && Number(row.sourceId) === queryContext.value.inboundId
}
function currentAmount(invoice) {
  return (invoice.allocations || []).reduce((sum, row) =>
    sum + (belongsToCurrent(row) ? Math.round(Number(row.amountIncludingTax || 0) * 100) : 0), 0) / 100
}
const confirmedAmount = computed(() => sumFor(['confirmed']))
const draftAmount = computed(() => sumFor(['draft', 'reversed']))
const pendingAmount = computed(() => invoices.value.filter(row => row.status === 'confirmed').reduce((sum, invoice) =>
  sum + (invoice.allocations || []).filter(row => Number(row.purchaseOrderId) === queryContext.value.purchaseOrderId)
    .reduce((total, row) => total + Math.round(Number(row.pendingInboundAmount || 0) * 100), 0), 0) / 100)
function sumFor(statuses) {
  return invoices.value.filter(row => statuses.includes(row.status))
    .reduce((sum, row) => sum + Math.round(currentAmount(row) * 100), 0) / 100
}
async function load() {
  const sequence = ++loadSequence
  loading.value = true
  loaded.value = false
  error.value = ''
  try {
    const [context, result] = await Promise.all([
      request.get('/purchase-invoices/context', { params: queryContext.value }),
      request.get('/purchase-invoices', { params: queryContext.value })
    ])
    if (sequence !== loadSequence) return false
    contextData.value = context
    invoices.value = result.items
    loaded.value = true
    return true
  } catch (err) {
    if (sequence === loadSequence) error.value = err.response?.data?.message || err.message
    return false
  } finally { if (sequence === loadSequence) loading.value = false }
}
function createInvoice() {
  if (!canCreate.value || fullyBilled.value || actionState.value.busy || !availableSuppliers.value.length) return
  editor.value = { id: null, supplierId: availableSuppliers.value.length === 1 ? availableSuppliers.value[0].id : null, key: 'new' }
}
function openInvoice(id) {
  if (reversing.value || reverseConfirmOpen.value) return
  editor.value = { id: Number(id), key: Number(id) }
}
function resetEditor() { editor.value = null }
function requestReverse(id) {
  if (!canReverse.value || actionState.value.busy || !reversibleInvoices.value.length) return
  reverseInvoiceId.value = typeof id === 'number' ? id : reversibleInvoices.value.length === 1 ? reversibleInvoices.value[0].id : ''
  reverseConfirmOpen.value = true
}
async function reverseInvoice() {
  const invoice = reverseTarget.value
  if (!invoice || reversing.value || !canReverse.value) return
  reverseConfirmOpen.value = false
  reversing.value = true
  error.value = ''
  const key = `${invoice.id}:${invoice.version}`
  if (!reverseKeys.has(key)) reverseKeys.set(key, operationKey())
  try {
    await request.post(`/purchase-invoices/${invoice.id}/reverse-confirm`, {
      version: invoice.version, idempotencyKey: reverseKeys.get(key)
    })
    await onUpdated()
  } catch (err) {
    const message = err.response?.data?.message || err.message
    await load()
    error.value = message
    emit('error', message)
  } finally { reversing.value = false }
}
watch(reverseConfirmOpen, async visible => {
  if (!visible) return
  await nextTick()
  document.querySelector('.custom-modal-overlay .btn-modal-cancel')?.focus()
})
watch(editor, async () => {
  await nextTick()
  panelElement.value?.parentElement?.scrollTo({ top: 0 })
})
async function onUpdated() {
  await load()
  emit('updated')
}
async function requestLeave() {
  if (reversing.value || reverseConfirmOpen.value) return false
  return documentEditor.value ? documentEditor.value.requestLeave() : true
}
onMounted(async () => {
  if (await load() && props.initialInvoiceId) {
    if (invoices.value.some(row => row.id === props.initialInvoiceId)) openInvoice(props.initialInvoiceId)
    else error.value = '该发票未关联当前单据'
  }
})
defineExpose({ requestLeave, createInvoice, requestReverse, resetEditor, actionState })
</script>

<style scoped>
.purchase-invoice-panel { padding: 0; min-height: 0; background: #fff; }
.invoice-toolbar { justify-content: space-between; padding-top: 0; }
.invoice-toolbar h3 { margin: 0; font-size: 15px; }
.invoice-toolbar h3 span { margin-left: 8px; }
.invoice-record-table { min-width: 850px; }
.invoice-record-table th:first-child { width: 160px; }
.invoice-record-table th:last-child { width: 64px; }
.invoice-reverse-choice { margin-bottom: 16px; text-align: left; }
.invoice-reverse-message { margin: 0; color: #596579; font-size: 14px; line-height: 1.6; white-space: pre-line; overflow-wrap: anywhere; }
</style>
