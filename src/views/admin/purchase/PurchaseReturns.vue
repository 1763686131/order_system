<template>
  <section class="supplier-finance-page">
    <header class="sf-header">
      <h1>采购退货</h1>
      <div class="sf-actions">
        <button v-if="can('create')" class="sf-button primary" @click="openNew"><Plus :size="16" />新增退货</button>
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
      <span>已审核退货金额<strong>{{ money(auditedTotal) }}</strong></span>
      <span>已审核退货单<strong>{{ auditedCount }}</strong></span>
    </div>
    <div class="sf-table-scroll">
      <table class="sf-table" style="min-width: 980px">
        <thead><tr><th>退货单号</th><th>供应商 / 门店</th><th>业务日期</th><th>明细数</th><th>原成本</th><th>供应商确认金额</th><th>状态</th><th>制单 / 审核</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="9" class="sf-empty">加载中...</td></tr>
          <tr v-else-if="!records.length"><td colspan="9" class="sf-empty">暂无采购退货单</td></tr>
          <tr v-for="row in records" :key="row.id">
            <td><button class="sf-link" @click="openRecord(row.id)">{{ row.documentNo }}</button></td>
            <td>{{ row.supplierName }}<div class="sf-muted">{{ row.storeName }}</div></td>
            <td>{{ row.businessDate }}</td>
            <td>{{ row.items.length }}</td>
            <td class="sf-number">{{ money(row.originalCost) }}</td>
            <td class="sf-number">{{ money(row.returnAmount) }}</td>
            <td><span class="sf-badge">{{ statusLabels[row.status] || row.status }}</span></td>
            <td>{{ row.createdBy }}<div class="sf-muted">{{ row.auditedBy || '-' }}</div></td>
            <td><div class="sf-actions">
              <button v-if="row.status === 'draft' && can('edit')" class="sf-button icon" title="编辑草稿" aria-label="编辑草稿" @click="openRecord(row.id)"><Pencil :size="16" /></button>
              <button v-if="['draft', 'reversed'].includes(row.status) && can('audit')" class="sf-button icon" title="审核退货" aria-label="审核退货" @click="act(row, 'audit')"><Check :size="16" /></button>
              <button v-if="row.status === 'audited' && can('reverse_audit')" class="sf-button icon danger" title="反审核" aria-label="反审核" @click="act(row, 'reverse-audit')"><RotateCcw :size="16" /></button>
              <button v-if="['draft', 'reversed'].includes(row.status) && can('delete')" class="sf-button icon danger" title="删除草稿" aria-label="删除草稿" @click="act(row, 'delete')"><Trash2 :size="16" /></button>
            </div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="dialogOpen" class="sf-modal-layer" @click.self="close">
      <section class="supplier-finance-dialog" role="dialog" aria-modal="true" aria-label="采购退货单">
        <header class="sf-header">
          <h2>{{ form.documentNo || (form.id ? '采购退货详情' : '新增采购退货') }} <span v-if="form.id" class="sf-badge">{{ statusLabels[form.status] }}</span></h2>
          <button class="sf-button icon" title="关闭" aria-label="关闭" :disabled="saving" @click="close"><X :size="18" /></button>
        </header>
        <div class="sf-dialog-body">
          <p v-if="dialogError" class="sf-error" role="alert">{{ dialogError }}</p>
          <p v-if="sourceLoading" class="sf-empty">正在读取可退入库批次...</p>
          <form v-else id="purchase-return-form" @submit.prevent="save">
            <div class="sf-form-grid">
              <label class="sf-field">门店<select v-model="form.storeId" required :disabled="!editing" @change="changeParty"><option value="">请选择</option><option v-for="store in options.stores" :key="store.id" :value="store.id">{{ store.name }}</option></select></label>
              <label class="sf-field">供应商<select v-model="form.supplierId" required :disabled="!editing" @change="changeParty"><option value="">请选择</option><option v-for="supplier in suppliersForForm" :key="supplier.id" :value="supplier.id">{{ supplier.supplierName }}</option></select></label>
              <label class="sf-field">业务日期<input v-model="form.businessDate" type="date" required :disabled="!editing" /></label>
              <label class="sf-field wide">备注<textarea v-model.trim="form.remark" maxlength="500" :disabled="!editing" /></label>
            </div>
            <div class="sf-header sf-section-title"><h3>来源入库批次</h3><button v-if="editing" class="sf-button icon" type="button" title="刷新可退批次" aria-label="刷新可退批次" :disabled="sourceLoading" @click="loadSources"><RefreshCw :size="16" /></button></div>
            <div class="sf-table-scroll">
              <table class="sf-table" style="min-width: 1050px">
                <thead><tr><th>来源入库 / 商品</th><th>仓库 / 库位 / 批次</th><th>可退数量</th><th>退货数量</th><th>原单价</th><th>原成本</th><th>确认退货金额</th><th>差异原因</th><th v-if="editing">移除</th></tr></thead>
                <tbody>
                  <tr v-if="!form.items.length"><td :colspan="editing ? 9 : 8" class="sf-empty">请添加至少一条来源入库明细</td></tr>
                  <tr v-for="(line, index) in form.items" :key="`${line.inboundItemId || 'new'}-${index}`">
                    <td><select v-if="editing" :value="line.inboundItemId" @change="selectSource(line, $event.target.value)"><option value="">选择入库明细</option><option v-for="source in sources" :key="source.inboundItemId" :value="source.inboundItemId">{{ source.inboundDocumentNo }} · {{ source.productName }} · {{ source.batchNo || '无批次' }}</option></select><span v-else>{{ line.inboundDocumentNo }} · {{ line.productName }}</span><div class="sf-muted">{{ line.productCode || '' }}</div></td>
                    <td>{{ sourceFor(line)?.warehouseName || '-' }} / {{ sourceFor(line)?.binCode || line.binCode || '-' }} / {{ sourceFor(line)?.batchNo || line.batchNo || '-' }}</td>
                    <td>{{ sourceFor(line)?.availableQuantity ?? line.quantity }}</td>
                    <td><input v-if="editing" v-model.number="line.quantity" type="number" min="0.0001" :max="sourceFor(line)?.availableQuantity" step="0.0001" required @input="syncReturnAmount(line)" /><span v-else>{{ line.quantity }}</span></td>
                    <td class="sf-number">{{ money(sourceFor(line)?.originalUnitPrice ?? line.originalUnitPrice) }}</td>
                    <td class="sf-number">{{ money(originalCost(line)) }}</td>
                    <td><input v-if="editing" v-model.number="line.returnAmount" type="number" min="0" step="0.01" required /><span v-else>{{ money(line.returnAmount) }}</span></td>
                    <td><input v-if="editing" v-model.trim="line.differenceReason" maxlength="500" :placeholder="hasDifference(line) ? '差异时必填' : '无差异可留空'" /><span v-else>{{ line.differenceReason || '-' }}</span></td>
                    <td v-if="editing"><button class="sf-button icon danger" type="button" title="移除此行" aria-label="移除此行" @click="form.items.splice(index, 1)"><Trash2 :size="16" /></button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="sf-actions sf-section-title" v-if="editing"><button class="sf-button" type="button" :disabled="!sources.length" @click="addLine"><Plus :size="16" />添加明细</button></div>
            <div class="sf-summary"><span>按原入库成本退库<strong>{{ money(totalOriginalCost) }}</strong></span><span>供应商确认退货金额<strong>{{ money(totalReturnAmount) }}</strong></span><span>价格差异<strong>{{ money(totalDifference) }}</strong></span></div>
          </form>
        </div>
        <footer class="sf-footer">
          <span v-if="form.id" class="sf-muted">版本 {{ form.version }} · {{ form.createdBy }} · {{ form.createdAt }}</span>
          <div class="sf-actions">
            <button class="sf-button" :disabled="saving" @click="close">关闭</button>
            <button v-if="editing" form="purchase-return-form" class="sf-button primary" :disabled="saving || sourceLoading"><Save :size="16" />{{ saving ? '保存中...' : '保存草稿' }}</button>
            <button v-if="!editing && form.status === 'draft' && can('edit')" class="sf-button" :disabled="saving" @click="editing = true"><Pencil :size="16" />编辑</button>
            <button v-if="!editing && ['draft', 'reversed'].includes(form.status) && can('audit')" class="sf-button primary" :disabled="saving" @click="act(form, 'audit')"><Check :size="16" />审核</button>
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
const options = ref({ stores: [], suppliers: [] })
const records = ref([])
const sources = ref([])
const loading = ref(false)
const sourceLoading = ref(false)
const saving = ref(false)
const error = ref('')
const dialogError = ref('')
const dialogOpen = ref(false)
const editing = ref(false)
const form = ref(emptyForm())
const filters = reactive({ keyword: '', storeId: '', supplierId: '', status: '', startDate: '', endDate: '' })
const can = action => user.hasPerm(`admin.purchase.return.${action}`)
const suppliersForFilter = computed(() => options.value.suppliers.filter(row => !filters.storeId || !row.storeId || Number(row.storeId) === Number(filters.storeId)))
const suppliersForForm = computed(() => options.value.suppliers.filter(row => !form.value.storeId || !row.storeId || Number(row.storeId) === Number(form.value.storeId)))
const audited = computed(() => records.value.filter(row => row.status === 'audited'))
const auditedCount = computed(() => audited.value.length)
const auditedTotal = computed(() => audited.value.reduce((sum, row) => sum + Number(row.returnAmount || 0), 0))
const totalOriginalCost = computed(() => form.value.items.reduce((sum, line) => sum + originalCost(line), 0))
const totalReturnAmount = computed(() => form.value.items.reduce((sum, line) => sum + Number(line.returnAmount || 0), 0))
const totalDifference = computed(() => Math.round((totalOriginalCost.value - totalReturnAmount.value) * 100) / 100)

function emptyForm() {
  return { supplierId: '', storeId: '', businessDate: localDate(), remark: '', items: [], status: 'draft', version: 1 }
}
function money(value) { return formatMoney(value) }
function sourceFor(line) { return sources.value.find(row => Number(row.inboundItemId) === Number(line.inboundItemId)) }
function originalCost(line) {
  const source = sourceFor(line)
  return Math.round(Number(source?.originalUnitPrice ?? line.originalUnitPrice ?? 0) * Number(line.quantity || 0) * 100) / 100
}
function hasDifference(line) { return Math.abs(originalCost(line) - Number(line.returnAmount || 0)) >= 0.01 }
function syncReturnAmount(line) {
  const source = sourceFor(line)
  if (source) line.returnAmount = Math.round(Number(source.originalUnitPrice) * Number(line.quantity || 0) * 100) / 100
}
function addLine() { form.value.items.push({ inboundItemId: '', quantity: 1, returnAmount: 0, differenceReason: '' }) }
function selectSource(line, id) {
  line.inboundItemId = Number(id) || ''
  line.quantity = 1
  const source = sourceFor(line)
  line.returnAmount = source ? Math.round(Number(source.originalUnitPrice) * 100) / 100 : 0
}
async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await request.get('/purchase-returns', { params: filters })
    records.value = result.items || []
  } catch (err) { error.value = err.response?.data?.message || err.message }
  finally { loading.value = false }
}
async function loadSources() {
  sources.value = []
  if (!form.value.supplierId || !form.value.storeId) return
  sourceLoading.value = true
  try {
    const result = await request.get(`/suppliers/${form.value.supplierId}/purchase-return-sources`, { params: { storeId: form.value.storeId } })
    sources.value = result.items || []
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { sourceLoading.value = false }
}
function changeParty() {
  form.value.items = []
  dialogError.value = ''
  if (!suppliersForForm.value.some(row => Number(row.id) === Number(form.value.supplierId))) form.value.supplierId = ''
  loadSources()
}
function openNew() {
  form.value = emptyForm()
  sources.value = []
  dialogError.value = ''
  editing.value = true
  dialogOpen.value = true
}
async function openRecord(id) {
  dialogError.value = ''
  sources.value = []
  editing.value = false
  dialogOpen.value = true
  try {
    const row = await request.get(`/purchase-returns/${id}`)
    form.value = { ...row, items: row.items.map(line => ({ ...line, inboundItemId: line.inboundItemId })) }
    editing.value = row.status === 'draft' && can('edit')
    await loadSources()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
}
function close() {
  if (saving.value) return
  dialogOpen.value = false
}
async function save() {
  if (!form.value.items.length || form.value.items.some(line => !line.inboundItemId || Number(line.quantity) <= 0 || (hasDifference(line) && !line.differenceReason))) {
    dialogError.value = '请补全退货明细；退货金额与原成本不一致时必须填写差异原因。'
    return
  }
  saving.value = true
  dialogError.value = ''
  try {
    const payload = {
      supplierId: form.value.supplierId, storeId: form.value.storeId,
      businessDate: form.value.businessDate, remark: form.value.remark,
      version: form.value.version, idempotencyKey: operationKey(),
      items: form.value.items.map(line => ({
        inboundItemId: line.inboundItemId, quantity: line.quantity,
        returnAmount: line.returnAmount, differenceReason: line.differenceReason
      }))
    }
    const response = await request({
      url: form.value.id ? `/purchase-returns/${form.value.id}` : '/purchase-returns',
      method: form.value.id ? 'PUT' : 'POST', data: payload
    })
    form.value = response.purchaseReturn
    editing.value = false
    await load()
    await loadSources()
  } catch (err) { dialogError.value = err.response?.data?.message || err.message }
  finally { saving.value = false }
}
async function act(row, action) {
  const labels = { audit: '审核该采购退货并扣减对应批次库存？', 'reverse-audit': '反审核该退货并冲销账务、恢复库存？', delete: '删除该退货草稿？' }
  if (!window.confirm(labels[action])) return
  saving.value = true
  dialogError.value = ''
  error.value = ''
  try {
    const suffix = action === 'audit' ? '/audit' : action === 'reverse-audit' ? '/reverse-audit' : ''
    const response = await request({
      url: `/purchase-returns/${row.id}${suffix}`, method: action === 'delete' ? 'DELETE' : 'POST',
      data: { version: row.version, idempotencyKey: operationKey() }
    })
    if (dialogOpen.value && Number(form.value.id) === Number(row.id) && action !== 'delete') {
      form.value = response.purchaseReturn
      editing.value = false
    }
    if (action === 'delete') dialogOpen.value = false
    await load()
    if (dialogOpen.value) await loadSources()
  } catch (err) {
    const message = err.response?.data?.message || err.message
    if (dialogOpen.value) dialogError.value = message
    else error.value = message
  } finally { saving.value = false }
}

onMounted(async () => {
  try { options.value = await request.get('/purchase-returns/options') }
  catch (err) { error.value = err.response?.data?.message || err.message }
  await load()
})
</script>
