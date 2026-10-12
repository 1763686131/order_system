<template>
  <section class="statement-page">
    <header class="statement-header">
      <div class="statement-heading">
        <button class="statement-icon" type="button" title="返回欠款列表" aria-label="返回欠款列表" @click="backToList"><ArrowLeft :size="18" /></button>
        <h2>{{ displayName }} · 对账单</h2>
      </div>
      <div class="statement-actions">
        <button class="statement-icon" type="button" :title="sortOrder === 'desc' ? '时间从近到远' : '时间从远到近'" aria-label="切换时间排序" :disabled="loading" @click="toggleSort"><ArrowDownUp :size="17" /></button>
        <button class="statement-icon" type="button" title="刷新" aria-label="刷新" :disabled="loading" @click="load">
          <RefreshCw :size="17" :class="{ spinning: loading }" />
        </button>
        <button v-if="canExport" class="statement-icon" type="button" title="导出" aria-label="导出" :disabled="loading" @click="exportStatement">
          <Download :size="17" />
        </button>
        <button v-if="canExport" class="statement-icon" type="button" title="打印" aria-label="打印" :disabled="loading" @click="printStatement">
          <Printer :size="17" />
        </button>
      </div>
    </header>

    <div v-if="type === 'receivable'" class="statement-summary">
      <div class="summary-result"><span>当前应收欠款</span><strong>{{ money(customerSummary.receivable) }}</strong></div>
      <span class="summary-operator">=</span>
      <div><span>期初欠款</span><strong>{{ money(customerSummary.initialDebt) }}</strong></div>
      <span class="summary-operator">+</span>
      <div><span>增加应收</span><strong>{{ money(customerSummary.receivableIncrease) }}</strong></div>
      <span class="summary-operator">-</span>
      <div><span>收回欠款</span><strong>{{ money(customerSummary.debtRecovered) }}</strong></div>
      <span class="summary-operator">-</span>
      <div><span>优惠</span><strong>{{ money(customerSummary.discountAmount) }}</strong></div>
      <div><span>当前储值</span><strong>{{ money(statement.summary?.storedBalance ?? statement.storedBalance) }}</strong></div>
    </div>
    <div v-else class="statement-summary supplier-summary">
      <div class="balance-formula" role="group" aria-label="净结算额等于期末应付减期末预付款减期末退货贷项">
        <template v-for="item in supplierSummary" :key="item.label">
          <span v-if="item.operator" class="balance-operator" aria-hidden="true">{{ item.operator }}</span>
          <div class="balance-item" :class="{ 'balance-result': !item.operator }"><span>{{ item.label }}</span><strong>{{ money(item.value) }}</strong></div>
        </template>
      </div>
      <div class="balance-formula payable-movement" role="group" aria-label="期末应付等于期初应付加期间应付变动">
        <div class="balance-item balance-result"><span>期末应付</span><strong>{{ money(statement.closing?.payable) }}</strong></div>
        <span class="balance-operator" aria-hidden="true">=</span>
        <div class="balance-item"><span>期初应付</span><strong>{{ money(statement.opening?.payable) }}</strong></div>
        <span class="balance-operator" aria-hidden="true">+</span>
        <div class="balance-item"><span>期间应付变动</span><strong>{{ money(statement.changes?.payable) }}</strong></div>
      </div>
    </div>

    <nav v-if="type === 'payable' && canReconcile" class="statement-tabs" role="tablist" aria-label="供应商对账视图">
      <button role="tab" :aria-selected="activeTab === 'statement'" :class="{ active: activeTab === 'statement' }" @click="activeTab = 'statement'">账务明细</button>
      <button role="tab" :aria-selected="activeTab === 'reconciliation'" :class="{ active: activeTab === 'reconciliation' }" @click="activeTab = 'reconciliation'">正式对账</button>
    </nav>
    <SupplierReconciliationPanel v-if="activeTab === 'reconciliation' && canReconcile" :supplier-id="targetId" :store-id="storeId" @updated="load" />
    <template v-else>
    <section class="statement-search-panel" aria-label="账务明细筛选">
      <form class="statement-search-grid" :class="{ 'customer-search-grid': type === 'receivable' }" @submit.prevent="search">
        <label class="statement-field"><span>业务类型</span><select v-model="filters.businessType"><option value="">全部</option><option v-for="(label, key) in typeOptions" :key="key" :value="key">{{ label }}</option></select></label>
        <div class="statement-field">
          <span>业务日期</span>
          <div class="statement-date-range">
            <input v-model="filters.startDate" type="date" aria-label="开始日期" :max="filters.endDate || undefined" />
            <span aria-hidden="true">至</span>
            <input v-model="filters.endDate" type="date" aria-label="结束日期" :min="filters.startDate || undefined" />
          </div>
        </div>
        <label v-if="type === 'payable'" class="statement-field"><span>开票状态</span><select v-model="filters.invoiceStatus"><option value="">全部</option><option v-for="(label, key) in invoiceLabels" :key="key" :value="key">{{ label }}</option></select></label>
        <div class="statement-search-actions">
          <button class="statement-button" type="button" @click="resetFilters"><RotateCcw :size="16" />重置</button>
          <button class="statement-button primary" :disabled="loading"><Search :size="16" />查询</button>
        </div>
      </form>
    </section>

    <p v-if="error" class="statement-error" role="alert">{{ error }}</p>
    <div class="statement-table-scroll">
      <table
        v-resizable-columns="{
          storageKey: type === 'payable' ? 'finance-debt-details-payable' : 'finance-debt-details-receivable',
          resizeMode: 'fit',
          minWidth: 64
        }"
        class="statement-table"
      >
        <colgroup v-if="type === 'payable'">
          <col data-column-key="business-date" data-min-width="90" style="width: 120px">
          <col data-column-key="document" data-min-width="110" style="width: 180px">
          <col data-column-key="summary" data-min-width="110" style="width: 180px">
          <col data-column-key="amount-excluding-tax" data-min-width="110" style="width: 120px">
          <col data-column-key="tax" data-min-width="90" style="width: 100px">
          <col data-column-key="payable-change" data-min-width="110" style="width: 120px">
          <col data-column-key="prepayment-change" data-min-width="110" style="width: 120px">
          <col data-column-key="credit-change" data-min-width="100" style="width: 120px">
          <col data-column-key="payable-balance" data-min-width="110" style="width: 120px">
          <col data-column-key="invoice-status" data-min-width="100" style="width: 120px">
          <col data-column-key="transaction-status" data-min-width="90" style="width: 100px">
          <col data-column-key="actions" data-resizable="false" style="width: 120px">
        </colgroup>
        <colgroup v-else>
          <col data-column-key="sequence" data-min-width="64" style="width: 70px">
          <col data-column-key="business-date" data-min-width="90" style="width: 120px">
          <col data-column-key="document" data-min-width="110" style="width: 160px">
          <col data-column-key="business-type" data-min-width="100" style="width: 110px">
          <col data-column-key="products" data-min-width="110" style="width: 180px">
          <col data-column-key="quantity" data-min-width="64" style="width: 80px">
          <col data-column-key="unit" data-min-width="64" style="width: 80px">
          <col data-column-key="unit-price" data-min-width="90" style="width: 100px">
          <col data-column-key="original-debt" data-min-width="110" style="width: 120px">
          <col data-column-key="paid-amount" data-min-width="100" style="width: 110px">
          <col data-column-key="debt-amount" data-min-width="110" style="width: 120px">
          <col data-column-key="current-debt" data-min-width="110" style="width: 120px">
        </colgroup>
        <thead v-if="type === 'payable'">
          <tr><th data-column-key="business-date" data-min-width="90">业务日期</th><th class="document-column" data-column-key="document" data-min-width="110">单号 / 类型</th><th data-column-key="summary" data-min-width="110">商品 / 摘要</th><th data-column-key="amount-excluding-tax" data-min-width="110">未税金额</th><th data-column-key="tax" data-min-width="90">税额</th><th data-column-key="payable-change" data-min-width="110">应付变动</th><th data-column-key="prepayment-change" data-min-width="110">预付款变动</th><th data-column-key="credit-change" data-min-width="100">贷项变动</th><th data-column-key="payable-balance" data-min-width="110">应付余额</th><th data-column-key="invoice-status" data-min-width="100">开票状态</th><th data-column-key="transaction-status" data-min-width="90">账务状态</th><th data-column-key="actions" data-resizable="false">操作</th></tr>
        </thead>
        <thead v-else>
          <tr><th data-column-key="sequence" data-min-width="64">序号</th><th data-column-key="business-date" data-min-width="90">业务日期</th><th class="document-column" data-column-key="document" data-min-width="110">单据编号</th><th data-column-key="business-type" data-min-width="100">业务类型</th><th class="product-column" data-column-key="products" data-min-width="110">商品详情</th><th data-column-key="quantity" data-min-width="64">数量</th><th data-column-key="unit" data-min-width="64">单位</th><th data-column-key="unit-price" data-min-width="90">单价</th><th data-column-key="original-debt" data-min-width="110">原单欠款</th><th data-column-key="paid-amount" data-min-width="100">部分付款</th><th data-column-key="debt-amount" data-min-width="110">应收欠款</th><th data-column-key="current-debt" data-min-width="110">当前欠款</th></tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="12" class="statement-empty">加载中...</td></tr>
          <tr v-else-if="!visibleRecords.length"><td colspan="12" class="statement-empty">本期暂无账务流水</td></tr>
          <template v-else-if="type === 'payable'">
            <tr v-for="row in visibleRecords" :key="row.id">
              <td>{{ date(row.businessDate) }}<small>{{ row.createdBy || '-' }}</small></td>
              <td><button v-if="canOpenSource(row)" class="statement-link" type="button" @click="openSource(row)">{{ row.documentNo || '-' }}</button><strong v-else>{{ row.documentNo || '-' }}</strong><small>{{ supplierBusinessLabels[row.businessType] || row.businessType }}</small></td>
              <td>{{ row.productName || row.remark || '-' }}</td>
              <td class="number">{{ money(row.amountExcludingTax) }}</td>
              <td class="number">{{ money(row.taxAmount) }}</td>
              <td class="number" :class="Number(row.payableChange) > 0 ? 'increase' : 'decrease'">{{ money(row.payableChange) }}</td>
              <td class="number">{{ money(row.prepaymentChange) }}</td>
              <td class="number">{{ money(row.creditChange) }}</td>
              <td class="number">{{ money(row.balances?.payable) }}</td>
              <td>{{ invoiceLabels[row.invoiceStatus] || '-' }}<small>{{ money(row.billedAmount) }}</small></td>
              <td>{{ transactionLabels[row.status] || row.status }}</td>
              <td><button v-if="row.status === 'audited' && row.sourceType === 'stock_inbound' && !row.lockedAt && !row.invoiceManaged && user.hasPerm('admin.purchase.invoice_status.edit')" class="statement-link" @click="invoiceError = ''; invoice = { ...row }">开票状态</button></td>
            </tr>
          </template>
          <template v-else>
            <template v-for="(row, index) in visibleRecords" :key="row.id">
              <tr :class="{ expandable: row.products?.length > 1 }" @click="toggleRow(row)" @keydown.enter="toggleRow(row)" :tabindex="row.products?.length > 1 ? 0 : undefined" :aria-expanded="row.products?.length > 1 ? Boolean(expandedRows[row.id]) : undefined">
                <td>{{ (page - 1) * pageSize + index + 1 }}</td>
                <td>{{ date(row.businessDate) }}</td>
                <td><strong>{{ row.docNumber || '-' }}</strong></td>
                <td><span class="business-badge" :class="`business-${row.businessType.toLowerCase()}`">{{ customerTypeLabels[row.businessType] || row.businessType }}</span></td>
                <td :title="displayProducts(row).map(item => item.name).join('、')">{{ displayProducts(row)[0]?.name || '-' }}<span v-if="row.products?.length > 1" class="product-count">+{{ row.products.length - 1 }}</span></td>
                <td class="number">{{ displayProducts(row)[0]?.quantity ?? '-' }}</td>
                <td>{{ displayProducts(row)[0]?.unit || '-' }}</td>
                <td class="number">{{ row.products?.length ? money(displayProducts(row)[0]?.price) : '-' }}</td>
                <td class="number">{{ ['ORDER', 'INITIAL'].includes(row.businessType) ? money(expandedRows[row.id] ? originalAmount(displayProducts(row)[0]) : row.orderAmount) : '-' }}</td>
                <td class="number">{{ row.businessType === 'BALANCE' ? money(row.balanceAmount) : Number(row.paidAmount) > 0 ? money(row.paidAmount) : '-' }}</td>
                <td class="number" :class="Number(row.debtAmount) > 0 ? 'increase' : 'decrease'">{{ row.businessType === 'BALANCE' ? '-' : money(expandedRows[row.id] ? productDebt(row, displayProducts(row)[0]) : row.debtAmount) }}</td>
                <td class="number">{{ money(expandedRows[row.id] ? productCurrentDebt(row, displayProducts(row)[0]) : row.currentDebt) }}</td>
              </tr>
              <tr v-for="(product, productIndex) in expandedRows[row.id] ? displayProducts(row).slice(1) : []" :key="`${row.id}-${productIndex}`" class="product-row">
                <td></td><td>{{ date(row.businessDate) }}</td><td>{{ row.docNumber }}</td><td></td><td>{{ product.name }}</td><td class="number">{{ product.quantity ?? '-' }}</td><td>{{ product.unit || '-' }}</td><td class="number">{{ money(product.price) }}</td><td class="number">{{ ['ORDER', 'INITIAL'].includes(row.businessType) ? money(originalAmount(product)) : '-' }}</td><td></td><td class="number">{{ money(productDebt(row, product)) }}</td><td class="number">{{ money(productCurrentDebt(row, product)) }}</td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <footer class="statement-footer">
      <span>共 {{ recordTotal }} 条</span>
      <div class="statement-pagination">
        <select v-model.number="pageSize" aria-label="每页显示数量" @change="search"><option :value="10">10 条/页</option><option :value="20">20 条/页</option><option :value="50">50 条/页</option></select>
        <button class="statement-icon" type="button" title="上一页" aria-label="上一页" :disabled="page <= 1 || loading" @click="changePage(-1)"><ChevronLeft :size="17" /></button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button class="statement-icon" type="button" title="下一页" aria-label="下一页" :disabled="page >= totalPages || loading" @click="changePage(1)"><ChevronRight :size="17" /></button>
      </div>
    </footer>
    </template>

    <CustomModal :visible="Boolean(invoice)" title="维护基础开票状态" message="" :confirm-disabled="invoiceSaving" @confirm="saveInvoice" @cancel="invoice = null">
      <template #content>
        <div v-if="invoice" class="invoice-form">
          <label>开票状态<select v-model="invoice.invoiceStatus"><option v-for="(label, key) in invoiceLabels" :key="key" :value="key">{{ label }}</option></select></label>
          <label>已开票金额<input v-model.number="invoice.billedAmount" type="number" min="0" step="0.01" /></label>
          <label>开票备注<textarea v-model="invoice.invoiceRemark" maxlength="500" /></label>
          <p v-if="invoiceError" class="statement-error">{{ invoiceError }}</p>
        </div>
      </template>
    </CustomModal>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDownUp, ArrowLeft, ChevronLeft, ChevronRight, Download, Printer, RefreshCw, RotateCcw, Search } from '@lucide/vue'
import * as XLSX from 'xlsx'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'
import { useUserStore } from '@/stores/user'
import { businessLabels as supplierBusinessLabels, invoiceLabels } from '@/utils/supplierFinance'
import SupplierReconciliationPanel from '@/components/admin/finance/SupplierReconciliationPanel.vue'

const props = defineProps({
  type: { type: String, required: true, validator: value => ['receivable', 'payable'].includes(value) },
  targetId: { type: [String, Number], required: true },
  targetName: { type: String, default: '' },
  storeId: { type: [String, Number], default: '' }
})
const router = useRouter()
const user = useUserStore()
const records = ref([])
const statement = ref({})
const loading = ref(false)
const error = ref('')
const page = ref(1)
const pageSize = ref(20)
const sortOrder = ref('desc')
const activeTab = ref('statement')
const expandedRows = reactive({})
let loadToken = 0
const invoice = ref(null)
const invoiceSaving = ref(false)
const invoiceError = ref('')
const filters = reactive({ businessType: '', startDate: '', endDate: '', invoiceStatus: '' })
const customerTypeLabels = { ORDER: '销售订单', RETURN: '退货单', PAYMENT: '收款单', INITIAL: '期初欠款', BALANCE: '储值调整' }
const transactionLabels = { audited: '已入账', reversed: '已冲销', reversal: '冲销流水' }
const typeOptions = computed(() => props.type === 'payable' ? supplierBusinessLabels : customerTypeLabels)
const displayName = computed(() => props.targetName || statement.value.supplier?.name || statement.value.customerName || `${props.type === 'payable' ? '供应商' : '客户'}#${props.targetId}`)
const canExport = computed(() => props.type === 'receivable' || user.hasPerm('admin.finance.supplier_statement.export'))
const canReconcile = computed(() => props.type === 'payable' && user.hasPerm('admin.route.finance.supplier_reconciliations'))
const filteredRecords = computed(() => props.type === 'payable' ? records.value : records.value.filter(row => {
  const businessDate = String(row.businessDate || '').slice(0, 10)
  return (!filters.businessType || row.businessType === filters.businessType)
    && (!filters.startDate || businessDate >= filters.startDate)
    && (!filters.endDate || businessDate <= filters.endDate)
}).slice().sort((left, right) => {
  const result = String(left.businessDate || '').localeCompare(String(right.businessDate || ''))
    || (Number(left.transactionId) || 0) - (Number(right.transactionId) || 0)
    || String(left.id).localeCompare(String(right.id))
  return sortOrder.value === 'asc' ? result : -result
}))
const visibleRecords = computed(() => props.type === 'payable' ? records.value : filteredRecords.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const recordTotal = computed(() => props.type === 'payable' ? Number(statement.value.total || 0) : filteredRecords.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(recordTotal.value / pageSize.value)))
const customerSummary = computed(() => ({
  initialDebt: statement.value.summary?.initialDebt || 0,
  receivableIncrease: statement.value.summary?.receivableIncrease || 0,
  debtRecovered: statement.value.summary?.debtRecovered || 0,
  discountAmount: statement.value.summary?.discountAmount || 0,
  receivable: statement.value.summary?.receivable ?? statement.value.totalReceivable ?? 0
}))
const supplierSummary = computed(() => {
  const closing = statement.value.closing || {}
  const netSettlement = (Math.round(Number(closing.payable || 0) * 100)
    - Math.round(Number(closing.prepayment || 0) * 100)
    - Math.round(Number(closing.credit || 0) * 100)) / 100
  return [
    { label: '净结算额', value: netSettlement },
    { label: '期末应付', value: closing.payable, operator: '=' },
    { label: '期末预付款', value: closing.prepayment, operator: '-' },
    { label: '期末退货贷项', value: closing.credit, operator: '-' }
  ]
})
const money = value => `¥${(Number(value) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const date = value => value ? String(value).slice(0, 10) : '-'
const apiParams = extra => ({ ...filters, storeId: props.storeId || undefined, page: page.value, pageSize: pageSize.value, sortOrder: sortOrder.value, ...extra })
function backToList() {
  const listPath = `/admin/finance/${props.type === 'payable' ? 'payables' : 'receivables'}`
  const previous = router.options.history.state.back
  if (typeof previous === 'string') {
    const url = new URL(previous, window.location.origin)
    if (url.pathname === listPath && !url.searchParams.has('statementId') && (url.searchParams.get('storeId') || '') === String(props.storeId || '')) {
      router.back()
      return
    }
  }
  router.replace({ path: listPath, query: props.storeId ? { storeId: props.storeId } : {} })
}
function toggleRow(row) { if (row.products?.length > 1) expandedRows[row.id] = !expandedRows[row.id] }
function displayProducts(row) { return sortOrder.value === 'desc' ? (row.products || []).slice().reverse() : row.products || [] }
function originalAmount(product) { return Number(product?.price || 0) * Number(product?.quantity ?? 1) }
function productDebt(row, product) {
  if (product?.allocatedDebt != null) return Number(product.allocatedDebt)
  const subtotal = item => Number(item.subtotal ?? originalAmount(item))
  const total = (row.products || []).reduce((sum, item) => sum + subtotal(item), 0)
  return total ? Number(row.debtAmount || 0) * subtotal(product) / total : Number(row.debtAmount || 0) / (row.products?.length || 1)
}
function productCurrentDebt(row, product) {
  const index = row.products?.indexOf(product) ?? -1
  return Number(row.currentDebt || 0) - Number(row.debtAmount || 0)
    + (row.products || []).slice(0, index + 1).reduce((sum, item) => sum + productDebt(row, item), 0)
}

async function load() {
  const token = ++loadToken
  loading.value = true
  error.value = ''
  try {
    if (props.type === 'payable') {
      const result = await request.get(`/suppliers/${props.targetId}/debt-details`, { params: apiParams() })
      if (token !== loadToken) return
      statement.value = result
      records.value = statement.value.items || []
    } else {
      const result = await request.get(`/customers/${props.targetId}/debt-details`, { params: { expandProducts: true } })
      if (token !== loadToken) return
      statement.value = result
      records.value = statement.value.records || []
    }
  } catch (err) {
    if (token !== loadToken) return
    error.value = err.response?.data?.error || err.response?.data?.message || err.message || '加载对账单失败'
    records.value = []
  } finally {
    if (token === loadToken) loading.value = false
  }
}
function search() {
  page.value = 1
  if (filters.startDate && filters.endDate && filters.startDate > filters.endDate) { error.value = '开始日期不能晚于结束日期'; return }
  error.value = ''
  if (props.type === 'payable') load()
}
function changePage(delta) { page.value += delta; if (props.type === 'payable') load() }
function toggleSort() { sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'; search() }
function resetFilters() {
  Object.assign(filters, { businessType: '', startDate: '', endDate: '', invoiceStatus: '' })
  page.value = 1
  load()
}
const sourcePermissions = { stock_inbound: 'admin.route.purchase.inbound', purchase_return: 'admin.route.purchase.returns', supplier_payment: 'admin.route.finance.supplier_payments', supplier_refund: 'admin.route.finance.supplier_refunds', supplier_balance: 'admin.route.finance.payables' }
function canOpenSource(row) { return Boolean(sourcePermissions[row.sourceType] && user.hasPerm(sourcePermissions[row.sourceType])) }
function openSource(row) {
  if (!canOpenSource(row)) return
  const paths = { stock_inbound: `/admin/purchase/inbound/${row.sourceId}`, purchase_return: `/admin/purchase/returns/${row.sourceId}` }
  if (row.sourceType === 'supplier_payment' || row.sourceType === 'supplier_refund') {
    router.push({ name: 'admin-supplier-payments', query: { tab: row.sourceType === 'supplier_refund' ? 'refund' : undefined, documentId: row.sourceId } })
  } else if (row.sourceType === 'supplier_balance') router.push({ name: 'admin-finance-payables', query: { balanceSupplierId: row.supplierId, storeId: row.storeId } })
  else router.push(paths[row.sourceType])
}
async function exportStatement() {
  if (!canExport.value) return
  try {
    const data = props.type === 'payable'
      ? await request.get(`/suppliers/${props.targetId}/debt-details`, { params: { ...apiParams(), export: '1' } })
      : statement.value
    if (props.type === 'payable') {
      const balanceRow = (label, balance) => ({ 单号: label, 应付余额: balance.payable, 预付款余额: balance.prepayment, 贷项余额: balance.credit })
      const rows = [
        balanceRow('期初余额', data.opening),
        ...data.items.map(row => ({ 业务日期: row.businessDate, 审核时间: row.auditedAt, 单号: row.documentNo, 商品: row.productName, 业务类型: supplierBusinessLabels[row.businessType] || row.businessType, 未税金额: row.amountExcludingTax, 税额: row.taxAmount, 应付变动: row.payableChange, 预付款变动: row.prepaymentChange, 贷项变动: row.creditChange, 应付余额: row.balances.payable, 预付款余额: row.balances.prepayment, 贷项余额: row.balances.credit, 开票状态: invoiceLabels[row.invoiceStatus], 已开票金额: row.billedAmount, 状态: transactionLabels[row.status], 操作人: row.createdBy, 备注: row.invoiceRemark || row.remark })),
        balanceRow('期末余额', data.closing)
      ]
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(rows), '供应商对账')
      XLSX.writeFile(workbook, `${displayName.value}-对账单.xlsx`)
      return
    }
    const rows = filteredRecords.value.flatMap(row => (displayProducts(row).length ? displayProducts(row) : [null]).map(product => ({
      业务日期: row.businessDate, 单号: row.docNumber, 业务类型: customerTypeLabels[row.businessType] || row.businessType, 商品: product?.name || '', 数量: product?.quantity ?? '', 单位: product?.unit || '', 单价: product?.price ?? '', 本单变动: product ? productDebt(row, product) : row.debtAmount, 当前欠款: product ? productCurrentDebt(row, product) : row.currentDebt
    })))
    const csv = [Object.keys(rows[0] || { 记录: '' }), ...rows.map(row => Object.values(row))]
      .map(row => row.map(cell => `"${String(cell ?? '').replaceAll('"', '""')}"`).join(',')).join('\n')
    const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `${displayName.value}-对账单.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) { error.value = err.response?.data?.message || err.message }
}
async function printStatement() {
  if (!canExport.value) return
  const printWindow = window.open('', '_blank', 'width=1200,height=800')
  if (!printWindow) { error.value = '浏览器拦截了打印窗口，请允许弹窗后重试'; return }
  try {
    const data = props.type === 'payable'
      ? await request.get(`/suppliers/${props.targetId}/debt-details`, { params: { ...apiParams(), export: '1' } })
      : null
    const rows = data?.items || filteredRecords.value
    const escape = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    const headers = props.type === 'payable' ? ['业务日期', '单号', '业务类型', '商品', '应付变动', '预付款变动', '贷项变动', '应付余额'] : ['业务日期', '单号', '业务类型', '商品', '数量', '单位', '单价', '本单变动', '当前欠款']
    const body = rows.flatMap(row => props.type === 'payable' ? [[row.businessDate, row.documentNo, supplierBusinessLabels[row.businessType] || row.businessType, row.productName, money(row.payableChange), money(row.prepaymentChange), money(row.creditChange), money(row.balances.payable)]] : (displayProducts(row).length ? displayProducts(row) : [null]).map(product => [row.businessDate, row.docNumber, customerTypeLabels[row.businessType] || row.businessType, product?.name, product?.quantity, product?.unit, product ? money(product.price) : '', money(product ? productDebt(row, product) : row.debtAmount), money(product ? productCurrentDebt(row, product) : row.currentDebt)]))
    printWindow.document.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${escape(displayName.value)}对账单</title><style>body{font:13px Arial,"Microsoft YaHei";padding:24px;color:#172033}h1{font-size:20px}table{width:100%;border-collapse:collapse}th,td{padding:8px;border:1px solid #cbd5e1;text-align:left}</style></head><body><h1>${escape(displayName.value)} · 对账单</h1>${data ? `<p>期初应付 ${money(data.opening.payable)}　期末应付 ${money(data.closing.payable)}　期末预付款 ${money(data.closing.prepayment)}　期末贷项 ${money(data.closing.credit)}</p>` : ''}<table><thead><tr>${headers.map(label => `<th>${label}</th>`).join('')}</tr></thead><tbody>${body.map(row => `<tr>${row.map(value => `<td>${escape(value)}</td>`).join('')}</tr>`).join('')}</tbody></table><script>window.addEventListener('load',()=>window.print())<\/script></body></html>`)
    printWindow.document.close()
  } catch (err) { printWindow.close(); error.value = err.response?.data?.message || err.message }
}
async function saveInvoice() {
  if (!invoice.value || invoiceSaving.value) return
  invoiceSaving.value = true
  invoiceError.value = ''
  try {
    await request.put(`/supplier-payables/${invoice.value.id}/invoice`, invoice.value)
    invoice.value = null
    await load()
  } catch (err) { invoiceError.value = err.response?.data?.message || err.message }
  finally { invoiceSaving.value = false }
}
watch(totalPages, pages => {
  if (page.value <= pages) return
  page.value = pages
  if (props.type === 'payable') load()
})
watch(() => [props.type, props.targetId, props.storeId], () => { page.value = 1; load() })
onBeforeUnmount(() => { ++loadToken })
onMounted(load)
</script>

<style scoped>
.statement-page {
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
  width: 100%; min-width: 0; min-height: 100%; color: var(--text); background: var(--page-bg); font-size: 14px;
}
.statement-page, .statement-page * { box-sizing: border-box; }
.statement-page button, .statement-page input, .statement-page select { font: inherit; }
.statement-page button:focus-visible, .statement-page input:focus-visible, .statement-page select:focus-visible, .expandable:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.statement-header, .statement-footer, .statement-actions, .statement-pagination { display: flex; align-items: center; }
.statement-header { justify-content: space-between; flex-wrap: wrap; gap: 14px; padding-bottom: 14px; border-bottom: 1px solid #e2e8f0; }
.statement-heading { display: flex; flex: 1 1 280px; min-width: 0; align-items: center; gap: 12px; }
.statement-header h2 { margin: 0; min-width: 0; font-size: 18px; overflow-wrap: anywhere; }
.statement-header span, .statement-summary span, .statement-summary small { color: #596579; font-size: 12px; }
.statement-actions, .statement-pagination { gap: 8px; }
.statement-icon { display: inline-flex; flex: 0 0 34px; width: 34px; height: 34px; align-items: center; justify-content: center; color: #596579; background: #fff; border: 1px solid #cbd5e1; border-radius: 5px; cursor: pointer; }
.statement-icon:disabled { cursor: not-allowed; opacity: .45; }
.statement-summary { display: flex; align-items: center; gap: 14px; padding: 16px 0; overflow-x: auto; }
.statement-summary > div { min-width: 120px; display: grid; gap: 5px; text-align: center; }
.statement-summary strong { font-size: 18px; font-variant-numeric: tabular-nums; }
.statement-summary.supplier-summary { display: block; overflow: visible; }
.supplier-summary > .balance-formula { display: grid; grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr) 24px minmax(0, 1fr) 24px minmax(0, 1fr); align-items: center; gap: 6px; }
.balance-item { display: grid; min-width: 0; gap: 5px; text-align: center; }
.balance-item strong { overflow-wrap: anywhere; }
.supplier-summary .balance-operator { color: var(--text-muted); font-size: 16px; text-align: center; }
.supplier-summary > .payable-movement { grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr) 24px minmax(0, 1fr); margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
.payable-movement strong { font-size: 16px; }
.statement-search-panel { padding: 18px 20px; background: var(--panel-bg); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.statement-search-grid { display: grid; grid-template-columns: minmax(160px, 1fr) minmax(280px, 1.45fr) minmax(160px, 1fr) auto; gap: 14px; align-items: end; }
.statement-search-grid.customer-search-grid { grid-template-columns: minmax(160px, 1fr) minmax(280px, 1.45fr) auto; }
.statement-field { display: flex; min-width: 0; flex-direction: column; gap: 7px; }
.statement-field > span { color: var(--text-secondary); font-size: 12px; font-weight: 600; }
.statement-field input, .statement-field select { width: 100%; min-width: 0; height: 38px; padding: 0 11px; color: var(--text); background: var(--panel-bg); border: 1px solid var(--border-strong); border-radius: 5px; }
.statement-field input:focus, .statement-field select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(var(--accent-rgb), .12); }
.statement-date-range { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 8px; }
.statement-date-range > span { color: var(--text-muted); font-size: 12px; }
.statement-search-actions { display: flex; align-items: center; gap: 8px; }
.statement-page .statement-button { display: inline-flex; height: 38px; align-items: center; justify-content: center; gap: 7px; padding: 0 15px; color: var(--text-secondary); background: var(--panel-bg); border: 1px solid var(--border-strong); border-radius: 5px; cursor: pointer; font-size: 13px; font-weight: 600; white-space: nowrap; }
.statement-page .statement-button.primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.statement-button:hover:not(:disabled) { color: var(--accent-dark); background: var(--accent-soft); border-color: var(--accent-border); }
.statement-button.primary:hover:not(:disabled) { color: #fff; background: var(--accent-dark); }
.statement-button:disabled { cursor: not-allowed; opacity: .45; }
.statement-error { padding: 10px 0; color: #b4232f; }
.statement-table-scroll { margin-top: 14px; overflow: auto; background: #fff; border: 1px solid #e2e8f0; }
.statement-table { width: 100%; min-width: 1550px; border-collapse: collapse; table-layout: fixed; }
.document-column { width: 180px; }.product-column { width: 180px; }
.statement-tabs { display: flex; gap: 8px; margin-bottom: 12px; }.statement-tabs button { height: 36px; padding: 0 16px; color: #596579; background: transparent; border: 0; border-bottom: 2px solid transparent; cursor: pointer; }.statement-tabs button.active { color: #08745a; border-color: #0f9f78; }
.statement-pagination select { height: 34px; padding: 0 8px; border: 1px solid #cbd5e1; border-radius: 5px; }
.expandable { cursor: pointer; }.expandable:hover, .product-row { background: #f3fbf8; }.product-count { display: inline-block; margin-left: 6px; padding: 2px 5px; color: #08745a; background: #e9f8f3; border-radius: 4px; font-size: 11px; }
.business-badge { display: inline-block; padding: 4px 6px; background: #eef3f5; border-radius: 4px; font-size: 12px; }.business-initial { color: #fff; background: #d97706; }.business-balance { color: #fff; background: #0891b2; }
.statement-table th, .statement-table td { padding: 10px 12px; border-bottom: 1px solid #edf1f5; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.statement-table th:last-child, .statement-table td:last-child { padding-right: 24px; }
.statement-table th { height: 44px; color: #596579; background: #f8fafc; font-size: 12px; }
.statement-table td { height: 52px; color: #344054; font-size: 13px; }
.statement-table small { display: block; margin-top: 3px; color: #8a96a8; font-size: 11px; }
.statement-table .number { font-variant-numeric: tabular-nums; }
.increase { color: #dc3545 !important; }.decrease { color: #07805f !important; }
.statement-link { padding: 0; color: #08745a; background: transparent; border: 0; cursor: pointer; font-weight: 650; }
.statement-empty { height: 220px !important; color: #8a96a8 !important; text-align: center !important; }
.statement-footer { justify-content: space-between; flex-wrap: wrap; gap: 10px; min-height: 58px; padding: 10px 16px; color: #596579; background: var(--panel-bg); border-top: 1px solid var(--border); font-size: 12px; }
.invoice-form { display: grid; gap: 12px; text-align: left; }.invoice-form label { display: grid; gap: 6px; }.invoice-form input, .invoice-form select, .invoice-form textarea { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font: inherit; }
.spinning { animation: spin .8s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1280px) {
  .statement-search-grid, .statement-search-grid.customer-search-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .statement-search-actions { justify-content: flex-end; }
}
@media (max-width: 780px) {
  .statement-actions { margin-left: auto; }
  .statement-summary { flex-wrap: wrap; }
  .statement-summary > div { flex: 1 1 40%; }
  .summary-operator { display: none; }
  .supplier-summary > .balance-formula { grid-template-columns: 24px minmax(0, 1fr); row-gap: 10px; }
  .balance-item { text-align: left; }
  .balance-result { grid-column: 1 / -1; text-align: center; }
  .statement-search-panel { padding: 14px 16px; }
  .statement-search-grid, .statement-search-grid.customer-search-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
