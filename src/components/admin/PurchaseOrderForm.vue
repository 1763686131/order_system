<template>
  <main class="purchase-order-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">PURCHASE ORDER</p>
        <h1>{{ viewMode ? '采购订单详情' : (isEdit ? '编辑采购订单' : '新增采购订单') }}</h1>
        <p class="subtitle">先提交采购订单，审核通过后即可从采购入库补充仓库、批次和实收数量。</p>
      </div>
      <button class="btn btn-light" type="button" @click="goBack">返回列表</button>
    </header>

    <div v-if="notice" class="notice" :class="{ error: noticeType === 'error' }">{{ notice }}</div>
    <section v-if="loading" class="card loading-card">正在加载采购订单资料…</section>
    <form v-else class="card" @submit.prevent="save('pending')">
      <div class="form-grid">
        <label><span>采购日期 <b>*</b></span><input v-model="form.orderDate" type="date" :disabled="viewMode" required /></label>
        <label><span>预计到货日期</span><input v-model="form.expectedDate" type="date" :disabled="viewMode" /></label>
        <label><span>供应商 <b>*</b></span><select v-model="form.supplierId" :disabled="viewMode" required><option value="">请选择供应商</option><option v-for="supplier in suppliers" :key="supplier.id" :value="String(supplier.id)">{{ supplier.supplierName || supplier.name }}</option></select></label>
        <label><span>门店</span><select v-model="form.storeId" :disabled="viewMode"><option value="">请选择门店</option><option v-for="store in stores" :key="store.id" :value="String(store.id)">{{ store.name }}</option></select></label>
        <label class="wide"><span>备注</span><input v-model.trim="form.remark" maxlength="500" :disabled="viewMode" placeholder="采购用途、交期等补充说明" /></label>
      </div>

      <div class="section-title"><div><h2>采购明细</h2><span>单价和金额可以暂时留空，入库时还可以补充。</span></div><button v-if="!viewMode" class="btn btn-light" type="button" @click="addRow">＋ 添加物料</button></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th class="index">#</th><th>原材料 <b>*</b></th><th>编码</th><th>规格型号</th><th>单位</th><th>采购数量 <b>*</b></th><th>单价</th><th>金额</th><th>备注</th><th v-if="!viewMode"></th></tr></thead>
          <tbody>
            <tr v-for="(item, index) in form.items" :key="item.key">
              <td class="index">{{ index + 1 }}</td>
              <td><select v-model="item.productId" :disabled="viewMode" required @change="selectProduct(item)"><option value="">请选择原材料</option><option v-for="product in products" :key="product.id" :value="String(product.id)">{{ product.code ? `${product.code} · ` : '' }}{{ product.name }}</option></select></td>
              <td class="muted">{{ item.productCode || '—' }}</td>
              <td class="muted">{{ item.specification || '—' }}</td>
              <td class="muted">{{ item.unit || '—' }}</td>
              <td><input v-model.number="item.orderedQty" :disabled="viewMode" type="number" min="0.0001" step="0.0001" required @input="syncAmount(item)" /></td>
              <td><input v-model.number="item.unitPrice" :disabled="viewMode" type="number" min="0" step="0.0001" @input="syncAmount(item)" /></td>
              <td><input v-model.number="item.amount" :disabled="viewMode" type="number" min="0" step="0.01" /></td>
              <td><input v-model.trim="item.remark" :disabled="viewMode" maxlength="500" /></td>
              <td v-if="!viewMode"><button class="icon-btn" type="button" title="删除明细" @click="removeRow(index)">×</button></td>
            </tr>
          </tbody>
          <tfoot><tr><td colspan="5">合计</td><td>{{ totalQuantity }}</td><td></td><td>{{ formatMoney(totalAmount) }}</td><td :colspan="viewMode ? 1 : 2"></td></tr></tfoot>
        </table>
      </div>

      <footer class="form-footer">
        <span v-if="form.status" class="status">状态：{{ statusLabel(form.status) }}</span>
        <div><button class="btn btn-light" type="button" @click="goBack">取消</button><template v-if="!viewMode"><button class="btn btn-secondary" type="button" :disabled="saving" @click="save('draft')">保存草稿</button><button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? '保存中…' : '提交审核' }}</button></template></div>
      </footer>
    </form>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { localDate } from '@/composables/documents/documentModels'

const props = defineProps({
  action: { type: String, default: 'create' },
  documentId: { type: Number, default: null }
})

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const notice = ref('')
const noticeType = ref('success')
const stores = ref([])
const suppliers = ref([])
const products = ref([])
const units = ref([])
const form = ref({ orderNo: '', orderDate: localDate(), expectedDate: '', storeId: '', supplierId: '', remark: '', status: 'draft', items: [] })
const viewMode = computed(() => props.action === 'view' || !['draft', 'pending'].includes(form.value.status))
const isEdit = computed(() => Boolean(props.documentId))
const totalQuantity = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.orderedQty) || 0), 0).toFixed(2))
const totalAmount = computed(() => form.value.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0))

const makeRow = () => ({ key: `${Date.now()}-${Math.random()}`, productId: '', productCode: '', productName: '', specification: '', unit: '', orderedQty: '', unitPrice: '', amount: '', remark: '' })
const showNotice = (message, type = 'success') => { notice.value = message; noticeType.value = type; window.clearTimeout(showNotice.timer); showNotice.timer = window.setTimeout(() => { notice.value = '' }, 3600) }
const formatMoney = value => Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const statusLabel = status => ({ draft: '草稿', pending: '待审核', approved: '已审核', partial: '部分入库', completed: '已完成', cancelled: '已取消' }[status] || status)
const addRow = () => form.value.items.push(makeRow())
const removeRow = index => { if (form.value.items.length > 1) form.value.items.splice(index, 1) }
const selectProduct = item => {
  const product = products.value.find(candidate => String(candidate.id) === String(item.productId))
  if (!product) return
  item.productCode = product.code || ''
  item.productName = product.name || ''
  item.specification = product.specification || ''
  item.unit = units.value.find(unit => String(unit.id) === String(product.unitId))?.name || product.unit || ''
  syncAmount(item)
}
const syncAmount = item => { if (item.unitPrice !== '' && item.unitPrice != null && item.orderedQty !== '' && item.orderedQty != null) item.amount = Number((Number(item.unitPrice) * Number(item.orderedQty)).toFixed(2)) }
const normalize = data => {
  form.value = { orderNo: data.orderNo || '', orderDate: data.orderDate || '', expectedDate: data.expectedDate || '', storeId: data.storeId ? String(data.storeId) : '', supplierId: data.supplierId ? String(data.supplierId) : '', remark: data.remark || '', status: data.status || 'draft', items: (data.items || []).map(item => ({ key: `${item.orderItemId || item.id}`, productId: item.productId ? String(item.productId) : '', productCode: item.productCode || '', productName: item.productName || '', specification: item.specification || '', unit: item.unit || '', orderedQty: item.orderedQty ?? '', unitPrice: item.unitPrice ?? '', amount: item.amount ?? '', remark: item.remark || '' })) }
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
  } catch (error) { showNotice(error?.response?.data?.message || error.message || '加载采购订单资料失败', 'error') } finally { loading.value = false }
}
const save = async status => {
  if (saving.value || viewMode.value) return
  const lines = form.value.items.filter(item => item.productId)
  if (!form.value.orderDate || !form.value.supplierId || !lines.length || lines.some(item => !item.orderedQty || Number(item.orderedQty) <= 0)) { showNotice('请填写采购日期、供应商和有效的物料数量', 'error'); return }
  saving.value = true
  try {
    const payload = { ...form.value, storeId: form.value.storeId ? Number(form.value.storeId) : null, supplierId: Number(form.value.supplierId), status, items: lines.map(item => ({ productId: Number(item.productId), productCode: item.productCode, productName: item.productName, specification: item.specification, unit: item.unit, orderedQty: Number(item.orderedQty), unitPrice: item.unitPrice === '' ? null : Number(item.unitPrice), amount: item.amount === '' ? null : Number(item.amount), remark: item.remark })) }
    const response = await request({ url: props.documentId ? `/purchase-orders/${props.documentId}` : '/purchase-orders', method: props.documentId ? 'PUT' : 'POST', data: payload })
    if (!response?.success) throw new Error(response?.message || '保存失败')
    const saved = response.purchaseOrder || {}
    if (!props.documentId && saved.orderId) form.value.orderNo = saved.orderNo
    showNotice(status === 'pending' ? '采购订单已提交审核' : '采购订单草稿已保存')
    window.setTimeout(goBack, 500)
  } catch (error) { showNotice(error?.response?.data?.message || error.message || '保存采购订单失败', 'error') } finally { saving.value = false }
}
const goBack = () => router.push({ name: 'admin-purchase-orders' })
onMounted(load)
</script>

<style scoped>
.purchase-order-page { min-height: 100%; padding: 28px; background: #f5f7f9; color: #17202b; }
.page-header, .section-title, .form-footer { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.page-header { margin-bottom: 20px; } .eyebrow { margin: 0 0 6px; color: #1f6f8b; font-size: 11px; letter-spacing: .14em; font-weight: 700; } h1 { margin: 0; font-size: 25px; } .subtitle { margin: 7px 0 0; color: #7a8792; font-size: 13px; }
.card { background: #fff; border: 1px solid #e5e9ed; border-radius: 10px; padding: 22px; box-shadow: 0 8px 24px rgba(31, 51, 68, .04); } .loading-card { color: #73808c; }
.form-grid { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 16px; padding-bottom: 22px; border-bottom: 1px solid #edf0f2; } label { display: flex; flex-direction: column; gap: 7px; min-width: 0; } label span { font-size: 12px; color: #6d7a86; } label b, th b { color: #c25d55; } label.wide { grid-column: span 2; }
input, select { width: 100%; height: 38px; padding: 0 10px; border: 1px solid #dce3e8; border-radius: 6px; color: #17202b; background: #fff; font: inherit; outline: none; } input:focus, select:focus { border-color: #1f6f8b; box-shadow: 0 0 0 3px rgba(31,111,139,.1); } input:disabled, select:disabled { background: #f6f8f9; color: #65717b; }
.section-title { padding: 22px 0 14px; } h2 { margin: 0; font-size: 17px; } .section-title span { color: #8a959e; font-size: 12px; } .table-wrap { overflow-x: auto; border: 1px solid #e7ebee; border-radius: 7px; } table { width: 100%; min-width: 1040px; border-collapse: collapse; } th, td { padding: 10px 9px; border-bottom: 1px solid #eef1f3; text-align: left; font-size: 12px; } th { color: #6b7782; background: #fafbfc; font-weight: 600; white-space: nowrap; } td input, td select { height: 34px; min-width: 82px; font-size: 12px; } .index { width: 40px; text-align: center; color: #9aa4ac; } .muted { color: #72808b; white-space: nowrap; } tfoot td { background: #fbfcfd; font-weight: 700; color: #53616c; } .icon-btn { width: 28px; height: 28px; border: 0; border-radius: 50%; color: #bd5c55; background: #fff0ef; cursor: pointer; font-size: 18px; }
.form-footer { padding-top: 20px; } .form-footer > div { display: flex; gap: 9px; } .status { color: #71808c; font-size: 12px; } .btn { height: 36px; padding: 0 15px; border: 1px solid transparent; border-radius: 6px; font: inherit; cursor: pointer; } .btn-primary { color: #fff; background: #1f6f8b; } .btn-secondary { color: #1f6f8b; background: #edf6f8; border-color: #cfe3e8; } .btn-light { color: #44515c; background: #fff; border-color: #dce3e8; } .btn:disabled { opacity: .55; cursor: not-allowed; }
.notice { margin-bottom: 14px; padding: 10px 13px; border-radius: 6px; color: #24694d; background: #eaf7f0; font-size: 13px; } .notice.error { color: #a24743; background: #fff0ef; }
@media (max-width: 900px) { .purchase-order-page { padding: 18px; } .form-grid { grid-template-columns: repeat(2, minmax(150px, 1fr)); } label.wide { grid-column: span 2; } .page-header { align-items: flex-start; } }
</style>
