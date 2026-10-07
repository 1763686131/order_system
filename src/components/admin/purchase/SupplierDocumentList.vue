<template>
  <section class="supplier-finance-page">
    <header class="sf-header">
      <h1>{{ invoiceMode ? '采购发票登记' : '供应商付款' }}</h1>
      <div class="sf-actions">
        <button v-if="canCreate" class="sf-button primary" @click="open(null)"><Plus :size="16" />{{ invoiceMode ? '登记发票' : '新增付款' }}</button>
        <button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button>
      </div>
    </header>
    <form class="sf-toolbar" @submit.prevent="search">
      <label class="sf-field">单号 / 供应商<input v-model.trim="filters.keyword" type="search" /></label>
      <label class="sf-field">门店<select v-model="filters.storeId"><option value="">全部授权门店</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
      <label class="sf-field">状态<select v-model="filters.status"><option value="">全部</option><option v-for="status in statuses" :key="status" :value="status">{{ documentStatusLabels[status] }}</option></select></label>
      <label v-if="invoiceMode" class="sf-field">开票差异<select v-model="filters.hasDifference"><option value="">全部</option><option value="true">存在差异</option><option value="false">无差异</option></select></label>
      <label class="sf-field">开始日期<input v-model="filters.startDate" type="date" /></label>
      <label class="sf-field">结束日期<input v-model="filters.endDate" type="date" /></label>
      <button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button>
    </form>
    <div v-if="!invoiceMode" class="sf-toolbar">
      <label class="sf-check"><input v-model="invoiceRule" type="checkbox" :disabled="ruleSaving || !user.hasPerm('admin.finance.supplier_payment.rules')" @change="saveRule" />见票付款</label>
    </div>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary">
      <span>记录数<strong>{{ records.length }}</strong></span>
      <span>{{ invoiceMode ? '已确认发票金额' : '已审核实付金额' }}<strong>{{ formatMoney(totalPosted) }}</strong></span>
      <span v-if="!invoiceMode">已审核新增预付款<strong>{{ formatMoney(totalAdvance) }}</strong></span>
      <span v-else>差异发票<strong>{{ records.filter(row => row.hasDifference && row.status === 'confirmed').length }}</strong></span>
    </div>
    <div class="sf-table-scroll">
      <table class="sf-table" style="min-width: 1140px">
        <thead><tr><th>{{ invoiceMode ? '发票号码' : '付款单号' }}</th><th>供应商 / 门店</th><th>业务日期</th><th>{{ invoiceMode ? '未税金额' : '实际付款' }}</th><th>{{ invoiceMode ? '税额' : '应付核销' }}</th><th>{{ invoiceMode ? '价税合计' : '新增预付款' }}</th><th>状态</th><th>制单 / 审核</th><th>备注</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="9" class="sf-empty">加载中...</td></tr>
          <tr v-else-if="!records.length"><td colspan="9" class="sf-empty">{{ invoiceMode ? '暂无采购发票' : '暂无供应商付款单' }}</td></tr>
          <tr v-for="row in visibleRecords" :key="row.id">
            <td><button class="sf-link" @click="open(row.id)">{{ row.invoiceNo || row.documentNo }}</button></td>
            <td>{{ row.supplierName }}<div class="sf-muted">{{ row.storeName || storeName(row.storeId) }}</div></td>
            <td>{{ row.businessDate }}<div class="sf-muted">{{ invoiceMode ? row.invoiceDate : row.paymentDate }}</div></td>
            <td class="sf-number">{{ formatMoney(invoiceMode ? row.amountExcludingTax : row.paymentAmount) }}</td>
            <td class="sf-number">{{ formatMoney(invoiceMode ? row.taxAmount : row.allocatedAmount) }}</td>
            <td class="sf-number">{{ formatMoney(invoiceMode ? row.amountIncludingTax : row.advanceAmount) }}</td>
            <td><span class="sf-badge">{{ documentStatusLabels[row.status] }}</span><div v-if="row.hasDifference" class="sf-error">开票有差异</div></td>
            <td>{{ row.createdBy }}<div class="sf-muted">{{ row.confirmedBy || row.auditedBy || '-' }}</div></td>
            <td>{{ row.remark || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <footer class="sf-footer">
      <span>共 {{ records.length }} 条</span><div class="sf-actions"><button class="sf-button icon" title="上一页" aria-label="上一页" :disabled="page <= 1" @click="page--"><ChevronLeft :size="18" /></button><span>{{ page }} / {{ pages }}</span><button class="sf-button icon" title="下一页" aria-label="下一页" :disabled="page >= pages" @click="page++"><ChevronRight :size="18" /></button></div>
    </footer>
    <SupplierDocumentDialog v-if="dialogOpen" :key="selectedId || 'new'" :mode="mode" :document-id="selectedId" :options="options" @close="closeDialog" @updated="load" />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, ChevronRight, Plus, RefreshCw, Search } from '@lucide/vue'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { documentStatusLabels, formatMoney, sumMoney } from '@/utils/supplierFinance'
import SupplierDocumentDialog from './SupplierDocumentDialog.vue'
import '@/assets/styles/supplier-finance.css'
const props = defineProps({ mode: { type: String, required: true } })
const user = useUserStore()
const route = useRoute()
const router = useRouter()
const invoiceMode = computed(() => props.mode === 'invoice')
const endpoint = computed(() => invoiceMode.value ? '/purchase-invoices' : '/supplier-payments')
const records = ref([])
const options = ref({ stores: [], suppliers: [], bankAccounts: [] })
const filters = reactive({ keyword: '', storeId: '', status: '', hasDifference: '', startDate: '', endDate: '' })
const loading = ref(false)
const error = ref('')
const page = ref(1)
const dialogOpen = ref(false)
const selectedId = ref(null)
const invoiceRule = ref(false)
const ruleSaving = ref(false)
const pages = computed(() => Math.max(1, Math.ceil(records.value.length / 50)))
const visibleRecords = computed(() => records.value.slice((page.value - 1) * 50, page.value * 50))
const statuses = computed(() => ['draft', invoiceMode.value ? 'confirmed' : 'audited', 'reversed', 'cancelled'])
const canCreate = computed(() => user.hasPerm(invoiceMode.value ? 'admin.purchase.invoice.create' : 'admin.finance.supplier_payment.create'))
const posted = computed(() => records.value.filter(row => row.status === (invoiceMode.value ? 'confirmed' : 'audited')))
const totalPosted = computed(() => sumMoney(posted.value, invoiceMode.value ? 'amountIncludingTax' : 'paymentAmount'))
const totalAdvance = computed(() => sumMoney(posted.value, 'advanceAmount'))
const storeName = id => options.value.stores.find(row => row.id === id)?.name || '-'
async function load() {
  loading.value = true
  error.value = ''
  try { const result = await request.get(endpoint.value, { params: filters }); records.value = result.items; page.value = Math.min(page.value, pages.value) }
  catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
function search() { page.value = 1; load() }
function open(id) { selectedId.value = id; dialogOpen.value = true }
function closeDialog() {
  dialogOpen.value = false
  if (route.query.documentId) { const query = { ...route.query }; delete query.documentId; router.replace({ query }) }
}
async function saveRule() {
  ruleSaving.value = true
  try { await request.put('/supplier-finance/rules', { paymentRequireInvoice: invoiceRule.value }) }
  catch (err) { invoiceRule.value = !invoiceRule.value; error.value = err.response?.data?.message || err.message }
  finally { ruleSaving.value = false }
}
watch(() => route.query.documentId, id => { if (id && Number(id) > 0) open(Number(id)) })
onMounted(async () => {
  try {
    options.value = await request.get('/supplier-finance/options')
    invoiceRule.value = options.value.paymentRequireInvoice
    await load()
    if (route.query.documentId) open(Number(route.query.documentId))
  } catch (err) { error.value = err.response?.data?.message || err.message }
})
</script>
