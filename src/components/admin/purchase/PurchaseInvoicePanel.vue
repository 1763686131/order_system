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
          <button class="sf-button icon" type="button" title="刷新发票记录" aria-label="刷新发票记录" :disabled="loading" @click="load"><RefreshCw :size="16" /></button>
          <button v-if="canCreate" class="sf-button primary" type="button" :disabled="loading || !availableSuppliers.length" @click="createInvoice"><Plus :size="16" />登记发票</button>
        </div>
      </div>
      <div class="sf-summary">
        <span>本单已确认开票<strong>{{ formatMoney(confirmedAmount) }}</strong></span>
        <span>本单草稿分配<strong>{{ formatMoney(draftAmount) }}</strong></span>
        <span>已确认待入库<strong>{{ formatMoney(pendingAmount) }}</strong></span>
        <span>本单可开票金额<strong>{{ formatMoney(contextData.availableAmount) }}</strong></span>
      </div>
      <div class="sf-table-scroll">
        <table class="sf-table invoice-record-table">
          <thead><tr><th>发票号码</th><th>供应商</th><th>发票日期</th><th>状态</th><th class="sf-number">发票价税合计</th><th class="sf-number">本单分配金额</th><th>附件</th><th>操作</th></tr></thead>
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
              <td><button class="sf-button icon" type="button" title="查看发票" aria-label="查看发票" @click="openInvoice(invoice.id)"><FileText :size="16" /></button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { FileText, Plus, RefreshCw } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { documentStatusLabels, formatMoney } from '@/utils/supplierFinance'
import SupplierDocumentDialog from './SupplierDocumentDialog.vue'
import '@/assets/styles/supplier-finance.css'

const props = defineProps({
  record: { type: Object, required: true },
  initialInvoiceId: { type: Number, default: null }
})
const emit = defineEmits(['updated'])
const user = useUserStore()
const invoices = ref([])
const contextData = ref({ suppliers: [], availableAmount: 0 })
const loading = ref(false)
const error = ref('')
let loadSequence = 0
const editor = ref(null)
const documentEditor = ref(null)
const panelElement = ref(null)
const canCreate = computed(() => user.hasPerm('admin.purchase.invoice.create'))
const queryContext = computed(() => props.record.sourceType === 'warehouse-inbound'
  ? { inboundId: Number(props.record.inboundId) }
  : { purchaseOrderId: Number(props.record.id) })
const documentContext = computed(() => ({ ...queryContext.value, storeId: contextData.value.storeId }))
const availableSuppliers = computed(() => contextData.value.suppliers.filter(row => row.availableAmount > 0))
const options = computed(() => ({
  stores: [{ id: contextData.value.storeId, name: contextData.value.storeName }],
  suppliers: editor.value?.id ? contextData.value.suppliers : availableSuppliers.value,
  bankAccounts: []
}))
function currentAmount(invoice) {
  return (invoice.allocations || []).reduce((sum, row) => {
    const belongs = queryContext.value.purchaseOrderId
      ? Number(row.purchaseOrderId) === queryContext.value.purchaseOrderId
      : row.sourceType === 'stock_inbound' && Number(row.sourceId) === queryContext.value.inboundId
    return sum + (belongs ? Math.round(Number(row.amountIncludingTax || 0) * 100) : 0)
  }, 0) / 100
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
  error.value = ''
  try {
    const [context, result] = await Promise.all([
      request.get('/purchase-invoices/context', { params: queryContext.value }),
      request.get('/purchase-invoices', { params: queryContext.value })
    ])
    if (sequence !== loadSequence) return false
    contextData.value = context
    invoices.value = result.items
    return true
  } catch (err) {
    if (sequence === loadSequence) error.value = err.response?.data?.message || err.message
    return false
  } finally { if (sequence === loadSequence) loading.value = false }
}
function createInvoice() {
  editor.value = { id: null, supplierId: availableSuppliers.value.length === 1 ? availableSuppliers.value[0].id : null, key: 'new' }
}
function openInvoice(id) {
  editor.value = { id: Number(id), key: Number(id) }
}
watch(editor, async () => {
  await nextTick()
  panelElement.value?.parentElement?.scrollTo({ top: 0 })
})
async function onUpdated() {
  await load()
  emit('updated')
}
async function requestLeave() {
  return documentEditor.value ? documentEditor.value.requestLeave() : true
}
onMounted(async () => {
  if (await load() && props.initialInvoiceId) {
    if (invoices.value.some(row => row.id === props.initialInvoiceId)) openInvoice(props.initialInvoiceId)
    else error.value = '该发票未关联当前单据'
  }
})
defineExpose({ requestLeave })
</script>

<style scoped>
.purchase-invoice-panel { padding: 0; min-height: 0; background: #fff; }
.invoice-toolbar { justify-content: space-between; padding-top: 0; }
.invoice-toolbar h3 { margin: 0; font-size: 15px; }
.invoice-toolbar h3 span { margin-left: 8px; }
.invoice-record-table { min-width: 850px; }
.invoice-record-table th:first-child { width: 160px; }
.invoice-record-table th:last-child { width: 64px; }
</style>
