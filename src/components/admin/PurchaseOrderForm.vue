<template>
  <main class="purchase-order-page">
    <header class="page-header">
      <div>
        <h1>{{ auditMode ? '审核采购申请' : (viewMode ? '采购申请详情' : (isEdit ? '编辑采购申请' : '新增采购申请')) }}</h1>
        <p class="subtitle">申请人填写门店、申请日期和物料数量；采购审核时再补充每项供应商与采购单价。</p>
      </div>
      <button class="btn btn-light" type="button" @click="goBack">返回列表</button>
    </header>

    <Transition name="notice">
      <div v-if="notice" class="notice" :class="{ error: noticeType === 'error' }" role="status" aria-live="polite">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path v-if="noticeType === 'success'" d="m8 12 2.7 2.7L16.5 9"></path>
          <path v-else d="M12 8v5M12 17h.01"></path>
        </svg>
        {{ notice }}
      </div>
    </Transition>
    <section v-if="loading" class="card loading-card">正在加载采购订单资料…</section>
    <section v-else-if="loadFailed" class="card loading-card">采购资料加载失败，请返回列表后重试。</section>
    <form v-else class="card" novalidate @submit.prevent="save('pending')">
      <div class="form-grid">
        <label><span>申请门店 <b>*</b></span><select v-model="form.storeId" :disabled="fieldsDisabled" required><option value="">请选择门店</option><option v-for="store in stores" :key="store.id" :value="String(store.id)">{{ store.name }}</option></select></label>
        <label><span>申请日期 <b>*</b></span><input v-model="form.orderDate" type="date" :disabled="fieldsDisabled" required @change="syncExpectedDate" /></label>
        <label><span>预计到货日期</span><input v-model="form.expectedDate" type="date" :disabled="fieldsDisabled" @input="expectedDateAuto = false" /></label>
        <label class="wide"><span>申请备注</span><input v-model.trim="form.remark" maxlength="500" :disabled="fieldsDisabled" placeholder="申请用途、交期等补充说明" /></label>
      </div>

      <div class="section-title"><div><h2>申请物料明细</h2><span>{{ auditMode ? '审核时必须补充每项物料的供应商和单价。' : '供应商、单价和金额可以暂时留空，由采购审核时补充。' }}</span></div><button v-if="!viewMode" class="btn btn-light" type="button" :disabled="saving" @click="addRow">＋ 添加物料</button></div>
      <div class="table-wrap">
        <table>
          <colgroup>
            <col style="width: 44px" /><col style="width: 210px" /><col style="width: 110px" /><col style="width: 130px" /><col style="width: 65px" />
            <col style="width: 110px" /><col style="width: 180px" /><col style="width: 110px" /><col style="width: 120px" /><col style="width: 180px" /><col v-if="!viewMode" style="width: 48px" />
          </colgroup>
          <thead><tr><th class="index">序号</th><th>原材料 <b>*</b></th><th>编码</th><th>规格型号</th><th>单位</th><th class="number">采购数量 <b>*</b></th><th>采购供应商<span v-if="auditMode"> <b>*</b></span></th><th class="number">采购单价<span v-if="auditMode"> <b>*</b></span></th><th class="number">金额</th><th>备注</th><th v-if="!viewMode"></th></tr></thead>
          <tbody>
            <tr v-for="(item, index) in form.items" :key="item.key">
              <td class="index">{{ index + 1 }}</td>
              <td><select v-model="item.productId" :disabled="fieldsDisabled || !form.storeId" required aria-label="原材料" @change="selectProduct(item)"><option value="">{{ form.storeId ? '请选择原材料' : '请先选择门店' }}</option><option v-if="item.productId && !products.some(product => String(product.id) === item.productId)" :value="item.productId">{{ item.productName }}</option><option v-for="product in products" :key="product.id" :value="String(product.id)">{{ product.code ? `${product.code} · ` : '' }}{{ product.name }}</option></select></td>
              <td class="muted" :title="item.productCode">{{ item.productCode }}</td>
              <td class="muted" :title="item.specification">{{ item.specification }}</td>
              <td class="muted">{{ item.unit }}</td>
              <td class="number"><input v-if="item.productId" v-model.number="item.orderedQty" :disabled="fieldsDisabled" aria-label="采购数量" type="number" min="0.0001" step="0.0001" required @input="syncAmount(item)" /><span v-else class="blank-cell"></span></td>
              <td><select v-if="item.productId" v-model="item.supplierId" :disabled="fieldsDisabled" :required="auditMode" aria-label="采购供应商"><option value="">{{ auditMode ? '请选择采购供应商' : '暂不指定（选填）' }}</option><option v-if="item.supplierId && !suppliers.some(supplier => String(supplier.id) === item.supplierId)" :value="item.supplierId">{{ item.supplierName }}</option><option v-for="supplier in suppliers" :key="supplier.id" :value="String(supplier.id)">{{ supplier.supplierName || supplier.name }}</option></select><span v-else class="blank-cell"></span></td>
              <td class="number"><input v-if="item.productId" v-model.number="item.unitPrice" :disabled="fieldsDisabled" :required="auditMode" aria-label="采购单价" type="number" min="0" step="0.0001" @input="syncAmount(item)" /><span v-else class="blank-cell"></span></td>
              <td class="number"><input v-if="item.productId" v-model.number="item.amount" :disabled="fieldsDisabled" aria-label="金额" type="number" min="0" step="0.01" /><span v-else class="blank-cell"></span></td>
              <td><input v-if="item.productId" v-model.trim="item.remark" :disabled="fieldsDisabled" aria-label="物料备注" maxlength="500" /><span v-else class="blank-cell"></span></td>
              <td v-if="!viewMode"><button class="icon-btn" type="button" title="删除明细" aria-label="删除明细" :disabled="saving || form.items.length === 1" @click="removeRow(index)">×</button></td>
            </tr>
          </tbody>
          <tfoot><tr><td colspan="5">合计</td><td class="number">{{ totalQuantity }}</td><td></td><td></td><td class="number">{{ formatMoney(totalAmount) }}</td><td :colspan="viewMode ? 1 : 2"></td></tr></tfoot>
        </table>
      </div>

      <footer class="form-footer">
        <span v-if="form.status" class="status" :class="`status-${form.status}`">{{ statusLabel(form.status) }}</span>
        <div><button class="btn btn-light" type="button" @click="goBack">取消</button><template v-if="auditMode"><button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? '审核中…' : '补充并审核通过' }}</button></template><template v-else-if="!viewMode"><button class="btn btn-secondary" type="button" :disabled="saving" @click="save('draft')">保存草稿</button><button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? '保存中…' : '提交审核' }}</button></template></div>
      </footer>
    </form>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { localDate } from '@/composables/documents/documentModels'

const props = defineProps({
  action: { type: String, default: 'create' },
  documentId: { type: Number, default: null }
})

const router = useRouter()
const loading = ref(true)
const loadFailed = ref(false)
const saving = ref(false)
const notice = ref('')
const noticeType = ref('success')
const stores = ref([])
const suppliers = ref([])
const products = ref([])
const units = ref([])
const expectedDateAuto = ref(true)
const initialDate = localDate()
const form = ref({ orderNo: '', orderDate: initialDate, expectedDate: dateAfter(initialDate, 7), storeId: '', remark: '', status: 'draft', items: [] })
const auditMode = computed(() => props.action === 'audit' && form.value.status === 'pending')
const viewMode = computed(() => props.action === 'view' || (props.action === 'audit' && !auditMode.value) || !['draft', 'pending'].includes(form.value.status))
const fieldsDisabled = computed(() => viewMode.value || saving.value)
const isEdit = computed(() => Boolean(props.documentId))
const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.orderedQty) || 0), 0).toFixed(2))
const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0))

function dateAfter(dateText, days) {
  const date = new Date(`${dateText}T00:00:00`)
  date.setDate(date.getDate() + days)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
let redirectTimer
const makeRow = () => ({ key: `${Date.now()}-${Math.random()}`, productId: '', productCode: '', productName: '', specification: '', unit: '', orderedQty: '', supplierId: '', supplierName: '', unitPrice: '', amount: '', remark: '' })
const showNotice = (message, type = 'success') => { notice.value = message; noticeType.value = type; window.clearTimeout(showNotice.timer); showNotice.timer = window.setTimeout(() => { notice.value = '' }, type === 'error' ? 5000 : 3000) }
const formatMoney = value => Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const statusLabel = status => ({ draft: '草稿', pending: '待审核', approved: '已审核', partial: '部分入库', completed: '已完成', cancelled: '已取消' }[status] || status)
const addRow = () => form.value.items.push(makeRow())
const removeRow = index => { if (form.value.items.length > 1) form.value.items.splice(index, 1) }
const selectProduct = item => {
  const product = products.value.find(candidate => String(candidate.id) === String(item.productId))
  if (!product) {
    Object.assign(item, { productCode: '', productName: '', specification: '', unit: '' })
    return
  }
  item.productCode = product.code || ''
  item.productName = product.name || ''
  item.specification = product.specification || ''
  item.unit = units.value.find(unit => String(unit.id) === String(product.unitId))?.name || product.unit || ''
  syncAmount(item)
}
const syncAmount = item => { if (item.unitPrice !== '' && item.unitPrice != null && item.orderedQty !== '' && item.orderedQty != null) item.amount = Number((Number(item.unitPrice) * Number(item.orderedQty)).toFixed(2)) }
const syncExpectedDate = () => {
  if (expectedDateAuto.value && form.value.orderDate) form.value.expectedDate = dateAfter(form.value.orderDate, 7)
}
const normalize = data => {
  form.value = {
    orderNo: data.orderNo || '', orderDate: data.orderDate || '', expectedDate: data.expectedDate || '',
    storeId: data.storeId ? String(data.storeId) : '', remark: data.remark || '', status: data.status || 'draft',
    items: (data.items || []).map(item => ({
      ...makeRow(), orderItemId: item.orderItemId || item.id,
      productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '',
      productName: item.productName || '', specification: item.specification || '', unit: item.unit || '',
      orderedQty: item.orderedQty ?? '', supplierId: item.supplierId ? String(item.supplierId) : '',
      supplierName: item.supplierName || '', unitPrice: item.unitPrice ?? '', amount: item.amount ?? '', remark: item.remark || ''
    }))
  }
  expectedDateAuto.value = !data.expectedDate || data.expectedDate === dateAfter(form.value.orderDate, 7)
  if (!form.value.items.length) addRow()
}
const load = async () => {
  try {
    const [storeData, supplierData, productData, unitData] = await Promise.all([request({ url: '/stores', method: 'GET' }), request({ url: '/suppliers', method: 'GET' }), request({ url: '/raw-material-products', method: 'GET' }), request({ url: '/products/units/measurements', method: 'GET' })])
    stores.value = Array.isArray(storeData) ? storeData.filter(item => item.status !== 'inactive') : []
    suppliers.value = Array.isArray(supplierData) ? supplierData.filter(item => item.status !== 'inactive') : []
    products.value = Array.isArray(productData) ? productData.filter(item => item.enabled !== false) : []
    units.value = Array.isArray(unitData) ? unitData : []
    if (props.documentId) normalize(await request({ url: `/purchase-orders/${props.documentId}`, method: 'GET' }))
    else addRow()
  } catch (error) { loadFailed.value = true; showNotice(error?.response?.data?.message || error.message || '加载采购订单资料失败', 'error') } finally { loading.value = false }
}
const save = async status => {
  if (saving.value || viewMode.value || loading.value || loadFailed.value) return
  const lines = form.value.items.filter(item => item.productId)
  if (!form.value.orderDate || !form.value.storeId || !lines.length || lines.some(item => !Number.isFinite(Number(item.orderedQty)) || Number(item.orderedQty) <= 0)) { showNotice('请填写申请日期、申请门店和有效的物料数量', 'error'); return }
  const hasValue = value => value !== '' && value != null
  if (lines.some(item => [item.unitPrice, item.amount].some(value => hasValue(value) && (!Number.isFinite(Number(value)) || Number(value) < 0)))) { showNotice('采购单价和金额必须为非负数', 'error'); return }
  const isAudit = auditMode.value
  if (isAudit && lines.some(item => !item.supplierId || !hasValue(item.unitPrice))) { showNotice('审核前请为每项物料补充供应商和采购单价', 'error'); return }
  saving.value = true
  let savedSuccessfully = false
  try {
    const payload = {
      ...form.value, storeId: Number(form.value.storeId), supplierId: null, status: isAudit ? 'pending' : status,
      items: lines.map(item => ({
        orderItemId: item.orderItemId, productId: Number(item.productId), productCode: item.productCode,
        productName: item.productName, specification: item.specification, unit: item.unit,
        orderedQty: Number(item.orderedQty), supplierId: item.supplierId ? Number(item.supplierId) : null,
        unitPrice: hasValue(item.unitPrice) ? Number(item.unitPrice) : null,
        amount: hasValue(item.amount) ? Number(item.amount) : null, remark: item.remark
      }))
    }
    const response = await request({
      url: isAudit
        ? `/purchase-orders/${props.documentId}/audit`
        : (props.documentId ? `/purchase-orders/${props.documentId}` : '/purchase-orders'),
      method: isAudit ? 'POST' : (props.documentId ? 'PUT' : 'POST'),
      data: payload
    })
    if (!response?.success) throw new Error(response?.message || '保存失败')
    savedSuccessfully = true
    if (response.purchaseOrder) normalize(response.purchaseOrder)
    showNotice(isAudit ? '采购申请已审核通过' : (status === 'pending' ? '采购申请已提交审核' : '采购申请草稿已保存'))
    redirectTimer = window.setTimeout(goBack, 500)
  } catch (error) { showNotice(error?.response?.data?.message || error.message || '保存采购申请失败', 'error') } finally { if (!savedSuccessfully) saving.value = false }
}
const goBack = () => router.push({ name: 'admin-purchase-orders' })
onMounted(load)
onBeforeUnmount(() => { window.clearTimeout(showNotice.timer); window.clearTimeout(redirectTimer) })
</script>

<style scoped>
.purchase-order-page {
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
  min-height: 100%; min-width: 0; padding: 20px;
  color: var(--text); background: var(--page-bg); font-size: 14px;
}
.purchase-order-page * { box-sizing: border-box; }
.page-header, .section-title, .form-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.page-header { margin-bottom: 14px; }
h1 { margin: 0; font-size: 18px; font-weight: 650; }
.subtitle { margin: 7px 0 0; color: var(--text-secondary); font-size: 12px; line-height: 1.6; }
.card { padding: 18px 20px; background: var(--panel-bg); border: 1px solid var(--border); border-radius: 7px; box-shadow: 0 4px 16px rgba(15, 23, 42, .03); }
.loading-card { color: var(--text-secondary); }
.form-grid { display: grid; grid-template-columns: minmax(200px, 1fr) minmax(160px, 240px) minmax(160px, 240px); gap: 14px; padding-bottom: 18px; border-bottom: 1px solid var(--border); }
label { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
label span { color: var(--text-secondary); font-size: 12px; font-weight: 600; }
label b, th b { color: #dc3545; }
label.wide { grid-column: 1 / -1; }
input, select { width: 100%; height: 38px; padding: 0 11px; color: var(--text); background: var(--panel-bg); border: 1px solid var(--border-strong); border-radius: 5px; font: inherit; }
input:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(var(--accent-rgb), .1); }
button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
input:disabled, select:disabled { color: var(--text-secondary); background: #f8fafc; cursor: not-allowed; }
.section-title { padding: 16px 0 12px; }
.section-title > div { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; }
h2 { margin: 0; font-size: 14px; font-weight: 650; }
.section-title span { color: var(--text-muted); font-size: 12px; }
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 5px; }
table { width: 100%; min-width: 1407px; table-layout: fixed; border-collapse: collapse; }
th, td { height: 48px; padding: 9px 8px; border-bottom: 1px solid #edf1f5; text-align: left; font-size: 12px; }
th { height: 45px; color: var(--text-secondary); background: #f8fafc; font-weight: 650; white-space: nowrap; }
tbody tr:hover { background: rgba(var(--accent-rgb), .04); }
td input, td select { height: 28px; padding: 0 7px; background: transparent; border-color: transparent; font-size: 12px; }
td input:focus, td select:focus { background: var(--panel-bg); }
td input:disabled, td select:disabled { background: transparent; }
.index { text-align: center; color: var(--text-muted); }
.number, .number input { text-align: right; font-variant-numeric: tabular-nums; }
.muted { overflow: hidden; color: var(--text-secondary); text-overflow: ellipsis; white-space: nowrap; }
.blank-cell { display: block; min-height: 28px; }
tfoot td { height: 45px; background: #f8fafc; border-bottom: 0; color: var(--text-secondary); font-weight: 650; }
.icon-btn { width: 28px; height: 28px; border: 0; border-radius: 5px; color: #dc3545; background: transparent; cursor: pointer; font-size: 18px; }
.icon-btn:hover:not(:disabled) { background: #fff0ef; }
.form-footer { flex-wrap: wrap; padding-top: 14px; }
.form-footer > div { display: flex; flex-wrap: wrap; gap: 8px; margin-left: auto; }
.status { display: inline-flex; align-items: center; min-height: 25px; padding: 3px 9px; border-radius: 999px; background: #f1f2f4; color: var(--text-secondary); font-size: 12px; font-weight: 650; }
.status-pending, .status-partial { background: #fff3df; color: #a4510b; }
.status-approved { background: #e7f5f8; color: #16647a; }
.status-completed { background: #eaf8f1; color: #13734f; }
.status-cancelled { color: #b4232f; }
.btn { display: inline-flex; height: 38px; align-items: center; justify-content: center; flex-shrink: 0; padding: 0 15px; border: 1px solid transparent; border-radius: 5px; font: inherit; font-size: 13px; font-weight: 600; white-space: nowrap; cursor: pointer; transition: background .18s, border-color .18s, color .18s; }
.btn-primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.btn-primary:hover:not(:disabled) { background: var(--accent-dark); border-color: var(--accent-dark); }
.btn-secondary { color: var(--accent-dark); background: var(--accent-soft); border-color: var(--accent-border); }
.btn-light { color: var(--text-secondary); background: var(--panel-bg); border-color: var(--border-strong); }
.btn-light:hover:not(:disabled), .btn-secondary:hover:not(:disabled) { color: var(--accent-dark); background: var(--accent-soft); border-color: var(--accent-border); }
button:disabled { opacity: .45; cursor: not-allowed; }
.notice { position: fixed; top: 24px; left: 50%; z-index: 3000; display: flex; align-items: center; gap: 9px; max-width: min(520px, calc(100vw - 32px)); min-height: 44px; padding: 10px 16px; color: var(--text); background: #fff; border: 1px solid #dfe5ec; border-radius: 6px; box-shadow: 0 10px 30px rgba(15, 23, 42, .16); transform: translateX(-50%); font-size: 13px; font-weight: 600; line-height: 1.5; overflow-wrap: anywhere; }
.notice svg { flex: 0 0 19px; width: 19px; height: 19px; color: var(--accent); fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.notice.error svg { color: #dc3545; }
.notice-enter-active, .notice-leave-active { transition: opacity .18s, transform .18s; }
.notice-enter-from, .notice-leave-to { opacity: 0; transform: translate(-50%, -8px); }
@media (max-width: 900px) { .purchase-order-page { padding: 16px; } .form-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .card { padding: 16px; } .page-header { align-items: flex-start; } }
@media (max-width: 600px) { .page-header { flex-wrap: wrap; } .form-grid { grid-template-columns: minmax(0, 1fr); } .section-title { align-items: flex-start; } .form-footer > div { width: 100%; margin-left: 0; justify-content: flex-end; } .notice { top: 12px; } }
@media (prefers-reduced-motion: reduce) { .btn, .notice-enter-active, .notice-leave-active { transition: none; } }
</style>
