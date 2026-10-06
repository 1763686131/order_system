<template>
  <section class="supplier-finance-page sf-print-surface">
    <header class="sf-header"><h1>{{ statement.supplier?.name || '供应商' }} · 内部对账</h1><div class="sf-actions"><button class="sf-button" @click="router.push('/admin/finance/payables')"><ArrowLeft :size="16" />返回</button><template v-if="user.hasPerm('admin.finance.supplier_statement.export')"><button class="sf-button icon" title="打印对账单" aria-label="打印对账单" :disabled="loading || printing" @click="printStatement"><Printer :size="18" /></button><button class="sf-button" :disabled="loading" @click="exportStatement"><Download :size="16" />导出 Excel</button></template><button class="sf-button icon" title="刷新" aria-label="刷新" :disabled="loading" @click="load"><RefreshCw :size="18" /></button></div></header>
    <form class="sf-toolbar" @submit.prevent="search"><label class="sf-field">开始日期<input v-model="filters.startDate" type="date" /></label><label class="sf-field">结束日期<input v-model="filters.endDate" type="date" /></label><label class="sf-field">业务类型<select v-model="filters.businessType"><option value="">全部</option><option v-for="(label, key) in businessLabels" :key="key" :value="key">{{ label }}</option></select></label><label class="sf-field">开票状态<select v-model="filters.invoiceStatus"><option value="">全部</option><option v-for="(label, key) in invoiceLabels" :key="key" :value="key">{{ label }}</option></select></label><button class="sf-button primary" :disabled="loading"><Search :size="16" />查询</button></form>
    <p v-if="error" class="sf-error" role="alert">{{ error }}</p>
    <div class="sf-summary"><span>期初应付<strong>{{ formatMoney(statement.opening?.payable) }}</strong></span><span>期间应付变动<strong>{{ formatMoney(statement.changes?.payable) }}</strong></span><span>期末应付<strong>{{ formatMoney(statement.closing?.payable) }}</strong></span><span>期末预付款<strong>{{ formatMoney(statement.closing?.prepayment) }}</strong></span><span>期末贷项<strong>{{ formatMoney(statement.closing?.credit) }}</strong></span></div>
    <div class="sf-table-scroll"><table class="sf-table" style="min-width: 1280px"><thead><tr><th>业务日期 / 审核时间</th><th>单号 / 商品</th><th>业务类型</th><th>未税金额</th><th>税额</th><th>应付增加/减少</th><th>预付款变动</th><th>贷项变动</th><th>应付余额</th><th>开票状态 / 金额</th><th class="sf-no-print">操作</th></tr></thead><tbody><tr v-if="loading"><td colspan="11" class="sf-empty">加载中...</td></tr><tr v-else-if="!statement.items?.length"><td colspan="11" class="sf-empty">本期暂无账务流水</td></tr><tr v-for="row in statement.items" :key="row.id"><td>{{ row.businessDate }}<div class="sf-muted">{{ row.auditedAt }} · {{ row.createdBy }}</div></td><td><button class="sf-link" @click="openSource(row)">{{ row.documentNo }}</button><div class="sf-muted">{{ row.productName }}</div></td><td>{{ businessLabels[row.businessType] || row.businessType }}<div class="sf-muted">{{ row.status === 'reversed' ? '已冲销' : row.status === 'reversal' ? '冲销记录' : '已入账' }}</div></td><td class="sf-number">{{ formatMoney(row.amountExcludingTax) }}</td><td class="sf-number">{{ formatMoney(row.taxAmount) }}</td><td class="sf-number">{{ formatMoney(row.payableChange) }}</td><td class="sf-number">{{ formatMoney(row.prepaymentChange) }}</td><td class="sf-number">{{ formatMoney(row.creditChange) }}</td><td class="sf-number">{{ formatMoney(row.balances.payable) }}</td><td>{{ invoiceLabels[row.invoiceStatus] }}<div class="sf-muted">{{ formatMoney(row.billedAmount) }}</div><div v-if="row.invoiceRemark" class="sf-muted">{{ row.invoiceRemark }}</div></td><td class="sf-no-print"><button v-if="row.status === 'audited' && row.sourceType === 'stock_inbound' && user.hasPerm('admin.purchase.invoice_status.edit')" class="sf-button icon" title="维护开票状态" aria-label="维护开票状态" @click="openInvoice(row)"><FilePenLine :size="16" /></button></td></tr></tbody></table></div>
    <footer class="sf-footer"><span>共 {{ statement.total || 0 }} 条</span><div class="sf-actions"><button class="sf-button icon" :disabled="page <= 1 || loading" aria-label="上一页" @click="page--; load()"><ChevronLeft :size="18" /></button><span>{{ page }} / {{ Math.max(1, Math.ceil((statement.total || 0) / 50)) }}</span><button class="sf-button icon" :disabled="page * 50 >= statement.total || loading" aria-label="下一页" @click="page++; load()"><ChevronRight :size="18" /></button></div></footer>
    <Teleport to="body"><div v-if="invoice" class="sf-modal-layer" @click.self="!saving && (invoice = null)"><form class="supplier-finance-dialog" style="max-width: 520px" @submit.prevent="saveInvoice" role="dialog" aria-modal="true" aria-label="基础开票状态"><header class="sf-header"><h2>基础开票状态 · {{ invoice.documentNo }}</h2><button class="sf-button icon" type="button" title="关闭" :disabled="saving" @click="invoice = null"><X :size="18" /></button></header><div class="sf-dialog-body"><p v-if="invoiceError" class="sf-error" role="alert">{{ invoiceError }}</p><div class="sf-form-grid"><label class="sf-field wide">开票状态<select v-model="invoice.invoiceStatus"><option v-for="(label, key) in invoiceLabels" :key="key" :value="key">{{ label }}</option></select></label><label class="sf-field wide">已开票金额<input v-model.number="invoice.billedAmount" type="number" min="0" step="0.01" required /></label><label class="sf-field wide">开票备注<textarea v-model="invoice.invoiceRemark" maxlength="500" :required="invoice.invoiceStatus === 'difference'" /></label></div></div><footer class="sf-footer"><span>已确认应付 {{ formatMoney(invoice.amountIncludingTax) }}</span><button class="sf-button primary" :disabled="saving"><Save :size="16" />保存</button></footer></form></div></Teleport>
  </section>
</template>
<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ChevronLeft, ChevronRight, Download, FilePenLine, Printer, RefreshCw, Save, Search, X } from '@lucide/vue'
import * as XLSX from 'xlsx'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { businessLabels, formatMoney, invoiceLabels } from '@/utils/supplierFinance'
import '@/assets/styles/supplier-finance.css'
const props = defineProps({ supplierId: { type: Number, required: true } })
const route = useRoute()
const router = useRouter()
const user = useUserStore()
const statement = ref({})
const loading = ref(false)
const printing = ref(false)
const saving = ref(false)
const error = ref('')
const invoiceError = ref('')
const invoice = ref(null)
const page = ref(1)
const filters = reactive({ startDate: '', endDate: '', businessType: '', invoiceStatus: '', storeId: route.query.storeId || '' })
const fetchStatement = extra => request({ url: `/suppliers/${props.supplierId}/debt-details`, params: { ...filters, page: page.value, pageSize: 50, ...extra } })
async function load() { loading.value = true; error.value = ''; try { statement.value = await fetchStatement() } catch (err) { error.value = err.response?.data?.message || err.message } finally { loading.value = false } }
function search() { page.value = 1; load() }
function openSource(row) { if (row.sourceType === 'stock_inbound') router.push(`/admin/purchase/inbound/${row.sourceId}`) }
function openInvoice(row) { invoiceError.value = ''; invoice.value = { ...row } }
async function saveInvoice() { saving.value = true; invoiceError.value = ''; try { await request({ url: `/supplier-payables/${invoice.value.id}/invoice`, method: 'PUT', data: invoice.value }); invoice.value = null; await load() } catch (err) { invoiceError.value = err.response?.data?.message || err.message } finally { saving.value = false } }
async function exportStatement() {
  error.value = ''
  try {
    const data = await fetchStatement({ export: '1' })
    const rows = [
      { 单号: '期初余额', 应付余额: data.opening.payable, 预付款余额: data.opening.prepayment, 贷项余额: data.opening.credit },
      ...data.items.map(row => ({ 业务日期: row.businessDate, 审核时间: row.auditedAt, 单号: row.documentNo, 商品: row.productName, 业务类型: businessLabels[row.businessType] || row.businessType, 未税金额: row.amountExcludingTax, 税额: row.taxAmount, 应付变动: row.payableChange, 预付款变动: row.prepaymentChange, 贷项变动: row.creditChange, 应付余额: row.balances.payable, 预付款余额: row.balances.prepayment, 贷项余额: row.balances.credit, 开票状态: invoiceLabels[row.invoiceStatus], 已开票金额: row.billedAmount, 操作人: row.createdBy, 备注: row.invoiceRemark || row.remark })),
      { 单号: '期末余额', 应付余额: data.closing.payable, 预付款余额: data.closing.prepayment, 贷项余额: data.closing.credit }
    ]
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(rows), '供应商对账')
    XLSX.writeFile(workbook, `供应商对账-${data.supplier.name}.xlsx`)
  } catch (err) { error.value = err.response?.data?.message || err.message }
}
async function printStatement() {
  printing.value = true; error.value = ''
  const previous = statement.value
  try {
    statement.value = await fetchStatement({ export: '1' })
    await nextTick()
    window.print()
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { statement.value = previous; printing.value = false }
}
onMounted(load)
</script>
