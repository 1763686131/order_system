<template>
  <div class="outbound-page">
    <section class="page-toolbar">
      <div class="search-group">
        <label class="search-field">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7"></circle>
            <path d="m20 20-3.7-3.7"></path>
          </svg>
          <input v-model.trim="filters.keyword" type="search" placeholder="搜索单号、原材料、备注或录入人" />
        </label>
        <label>
          <span>开始日期</span>
          <input v-model="filters.startDate" type="date" />
        </label>
        <label>
          <span>结束日期</span>
          <input v-model="filters.endDate" type="date" />
        </label>
        <button type="button" class="button secondary" @click="resetFilters">重置</button>
      </div>
      <div class="toolbar-actions">
        <button type="button" class="button secondary" :disabled="loading" @click="loadData">
          刷新
        </button>
        <button type="button" class="button primary" @click="openSettings">
          触屏录入设置
        </button>
      </div>
    </section>

    <section class="stats-grid">
      <article>
        <span>全部出库单</span>
        <strong>{{ records.length }}</strong>
        <small>员工触屏端提交记录</small>
      </article>
      <article>
        <span>待审核</span>
        <strong class="warning-text">{{ statusCount.draft }}</strong>
        <small>尚未扣减实际库存</small>
      </article>
      <article>
        <span>已审核</span>
        <strong class="success-text">{{ statusCount.reviewed }}</strong>
        <small>已写入库存出库流水</small>
      </article>
      <article>
        <span>已登记成品量</span>
        <strong>{{ formatNumber(reviewedProducedQuantity) }}</strong>
        <small>已审核记录中的成品数量（kg）</small>
      </article>
    </section>

    <section class="records-panel">
      <header class="records-header">
        <div class="status-tabs">
          <button
            v-for="tab in statusTabs"
            :key="tab.value"
            type="button"
            :class="{ active: filters.status === tab.value }"
            @click="filters.status = tab.value"
          >
            {{ tab.label }}
            <span>{{ tab.count }}</span>
          </button>
        </div>
        <div class="config-summary">
          <span :class="{ configured: settings.configured }"></span>
          {{ settings.configured ? configSummary : '触屏端尚未配置' }}
        </div>
      </header>

      <div v-if="loadError" class="load-error">{{ loadError }}</div>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>出库单号</th>
              <th>录入时间</th>
              <th>原材料</th>
              <th>门店 / 仓库</th>
              <th class="number">出库数量</th>
              <th class="number">成品数量</th>
              <th>备注</th>
              <th>录入人</th>
              <th>状态</th>
              <th>审核信息</th>
              <th class="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="11" class="empty-cell">正在加载原材料出库记录...</td>
            </tr>
            <tr v-else-if="filteredRecords.length === 0">
              <td colspan="11" class="empty-cell">暂无匹配的原材料出库记录</td>
            </tr>
            <tr v-for="record in filteredRecords" v-else :key="record.id">
              <td>
                <button type="button" class="document-link" @click="openDetail(record)">
                  {{ record.documentNo }}
                </button>
              </td>
              <td class="muted">{{ record.createdAt || record.documentDate }}</td>
              <td>
                <div class="material-cell">
                  <strong>{{ record.primaryItem?.productName || '-' }}</strong>
                  <small>
                    {{ record.primaryItem?.productCode || '' }}
                    {{ record.primaryItem?.specification || '' }}
                  </small>
                </div>
              </td>
              <td>
                <div class="location-cell">
                  <strong>{{ record.storeName || '-' }}</strong>
                  <small>{{ record.warehouseName || '-' }}</small>
                </div>
              </td>
              <td class="number quantity">
                {{ formatNumber(record.totalQuantity) }}
                <small>{{ record.primaryItem?.unit || '' }}</small>
              </td>
              <td class="number">{{ formatNumber(record.producedQuantity) }} kg</td>
              <td class="remark-cell" :title="record.remark">{{ record.remark || '-' }}</td>
              <td>{{ record.createdBy || '-' }}</td>
              <td>
                <span :class="['status-badge', `status-${record.status}`]">
                  {{ statusLabel(record.status) }}
                </span>
              </td>
              <td class="muted">
                <template v-if="record.auditedAt">
                  {{ record.auditedBy || '-' }}<br />
                  <small>{{ record.auditedAt }}</small>
                </template>
                <span v-else>-</span>
              </td>
              <td class="actions-column">
                <div class="row-actions">
                  <button type="button" @click="openDetail(record)">详情</button>
                  <button
                    v-if="record.status === 'draft'"
                    type="button"
                    class="audit-action"
                    @click="requestAction('audit', record)"
                  >
                    审核
                  </button>
                  <button
                    v-else-if="record.status === 'reviewed'"
                    type="button"
                    @click="requestAction('reverse', record)"
                  >
                    反审核
                  </button>
                  <button
                    v-else-if="record.status === 'cancelled'"
                    type="button"
                    @click="requestAction('restart', record)"
                  >
                    重新启用
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <teleport to="body">
      <div v-if="settingsVisible" class="modal-layer">
        <section class="settings-modal" role="dialog" aria-modal="true" aria-labelledby="outboundSettingsTitle">
          <header class="modal-header">
            <div>
              <span>原材料出库</span>
              <h2 id="outboundSettingsTitle">触屏端录入设置</h2>
              <p>配置员工触屏机默认使用的门店、仓库与原材料</p>
            </div>
            <button type="button" aria-label="关闭" @click="settingsVisible = false">×</button>
          </header>

          <div class="settings-body">
            <section class="settings-section">
              <div class="section-heading">
                <h3>默认出库位置</h3>
                <p>员工提交草稿时自动保存当前门店和仓库快照</p>
              </div>
              <div class="form-grid">
                <label>
                  <span>默认门店</span>
                  <select v-model="settingsForm.defaultStoreId">
                    <option :value="null">请选择门店</option>
                    <option v-for="store in settings.stores" :key="store.id" :value="store.id">
                      {{ store.name }}
                    </option>
                  </select>
                </label>
                <label>
                  <span>默认仓库</span>
                  <select v-model="settingsForm.defaultWarehouseId">
                    <option :value="null">请选择仓库</option>
                    <option
                      v-for="warehouse in availableWarehouses"
                      :key="warehouse.id"
                      :value="warehouse.id"
                    >
                      {{ warehouse.name }}
                    </option>
                  </select>
                </label>
              </div>
            </section>

            <section class="settings-section">
              <div class="section-heading">
                <h3>触屏端可操作原材料</h3>
                <p>目前只展示默认原材料；保留多选范围，方便以后扩展大按钮切换</p>
              </div>
              <div class="product-options">
                <label v-for="product in settings.products" :key="product.id">
                  <input
                    v-model="settingsForm.allowedProductIds"
                    type="checkbox"
                    :value="product.id"
                  />
                  <span class="checkbox-mark"></span>
                  <span>
                    <strong>{{ product.name }}</strong>
                    <small>
                      {{ product.code || '无编号' }} · {{ product.specification || '无规格' }}
                      · 库存 {{ formatNumber(product.currentStock) }} {{ product.unit }}
                    </small>
                  </span>
                </label>
                <div v-if="settings.products.length === 0" class="products-empty">
                  请先在原材料列表中建立原材料档案
                </div>
              </div>
              <label class="default-product-field">
                <span>默认原材料</span>
                <select v-model="settingsForm.defaultProductId">
                  <option :value="null">请选择默认原材料</option>
                  <option
                    v-for="product in selectedProducts"
                    :key="product.id"
                    :value="product.id"
                  >
                    {{ product.name }}（{{ product.unit || '未设置单位' }}）
                  </option>
                </select>
              </label>
            </section>

            <section class="settings-section compact-section">
              <div class="section-heading">
                <h3>提交与库存提示</h3>
                <p>审核始终会再次校验实时库存</p>
              </div>
              <label class="switch-line">
                <input v-model="settingsForm.showCurrentStock" type="checkbox" />
                <span class="switch-control"></span>
                <span>
                  <strong>触屏端显示当前库存</strong>
                  <small>方便员工录入前了解大致可用数量</small>
                </span>
              </label>
              <label class="switch-line">
                <input v-model="settingsForm.allowInsufficientDraft" type="checkbox" />
                <span class="switch-control"></span>
                <span>
                  <strong>库存不足时仍允许提交草稿</strong>
                  <small>管理员审核时会阻止扣库，并提示实际缺口</small>
                </span>
              </label>
              <div class="readonly-line">
                <span>库存扣减策略</span>
                <strong>先进先出（FIFO）</strong>
              </div>
            </section>

            <div v-if="settingsError" class="form-error">{{ settingsError }}</div>
          </div>

          <footer class="modal-footer">
            <button type="button" class="button secondary" @click="settingsVisible = false">取消</button>
            <button
              type="button"
              class="button primary"
              :disabled="settingsSaving"
              @click="saveSettings"
            >
              {{ settingsSaving ? '正在保存...' : '保存触屏设置' }}
            </button>
          </footer>
        </section>
      </div>

      <div v-if="detailRecord" class="modal-layer">
        <section class="detail-modal" role="dialog" aria-modal="true">
          <header class="modal-header">
            <div>
              <span>原材料出库详情</span>
              <h2>{{ detailRecord.documentNo }}</h2>
              <p>{{ detailRecord.createdAt }} · {{ detailRecord.createdBy || '未记录录入人' }}</p>
            </div>
            <button type="button" aria-label="关闭" @click="detailRecord = null">×</button>
          </header>
          <div class="detail-body">
            <div class="detail-status-line">
              <span :class="['status-badge', `status-${detailRecord.status}`]">
                {{ statusLabel(detailRecord.status) }}
              </span>
              <span>审核后才会扣减原材料库存</span>
            </div>
            <dl class="detail-grid">
              <div><dt>门店</dt><dd>{{ detailRecord.storeName || '-' }}</dd></div>
              <div><dt>仓库</dt><dd>{{ detailRecord.warehouseName || '-' }}</dd></div>
              <div><dt>原材料</dt><dd>{{ detailRecord.primaryItem?.productName || '-' }}</dd></div>
              <div><dt>规格</dt><dd>{{ detailRecord.primaryItem?.specification || '-' }}</dd></div>
              <div>
                <dt>出库数量</dt>
                <dd>{{ formatNumber(detailRecord.totalQuantity) }} {{ detailRecord.primaryItem?.unit }}</dd>
              </div>
              <div><dt>成品数量</dt><dd>{{ formatNumber(detailRecord.producedQuantity) }} kg</dd></div>
              <div class="wide"><dt>备注标签</dt><dd>{{ detailRecord.remark || '无' }}</dd></div>
              <div class="wide">
                <dt>审核信息</dt>
                <dd>
                  {{ detailRecord.auditedAt
                    ? `${detailRecord.auditedBy || '-'} · ${detailRecord.auditedAt}`
                    : '尚未审核' }}
                </dd>
              </div>
            </dl>
          </div>
          <footer class="modal-footer detail-footer">
            <button
              v-if="detailRecord.status === 'draft'"
              type="button"
              class="button danger"
              @click="requestAction('cancel', detailRecord)"
            >
              作废草稿
            </button>
            <div>
              <button type="button" class="button secondary" @click="detailRecord = null">关闭</button>
              <button
                v-if="detailRecord.status === 'draft'"
                type="button"
                class="button primary"
                @click="requestAction('audit', detailRecord)"
              >
                审核并扣减库存
              </button>
              <button
                v-else-if="detailRecord.status === 'reviewed'"
                type="button"
                class="button secondary"
                @click="requestAction('reverse', detailRecord)"
              >
                反审核并回补库存
              </button>
            </div>
          </footer>
        </section>
      </div>

      <div v-if="pendingAction" class="modal-layer confirm-layer">
        <section class="confirm-modal" role="alertdialog" aria-modal="true">
          <div :class="['confirm-icon', { danger: pendingAction.type === 'cancel' }]">!</div>
          <h3>{{ actionCopy.title }}</h3>
          <p>{{ actionCopy.message }}</p>
          <div class="confirm-actions">
            <button type="button" class="button secondary" :disabled="actionLoading" @click="pendingAction = null">
              取消
            </button>
            <button
              type="button"
              :class="['button', pendingAction.type === 'cancel' ? 'danger' : 'primary']"
              :disabled="actionLoading"
              @click="executeAction"
            >
              {{ actionLoading ? '正在处理...' : actionCopy.confirm }}
            </button>
          </div>
        </section>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const loadError = ref('')
const records = ref([])
const settings = ref({
  configured: false,
  stores: [],
  warehouses: [],
  products: [],
  allowedProductIds: []
})
const filters = reactive({
  keyword: '',
  startDate: '',
  endDate: '',
  status: 'all'
})

const settingsVisible = ref(false)
const settingsSaving = ref(false)
const settingsError = ref('')
const settingsForm = reactive({
  defaultStoreId: null,
  defaultWarehouseId: null,
  allowedProductIds: [],
  defaultProductId: null,
  showCurrentStock: true,
  allowInsufficientDraft: true
})
const detailRecord = ref(null)
const pendingAction = ref(null)
const actionLoading = ref(false)

const statusCount = computed(() => ({
  draft: records.value.filter(item => item.status === 'draft').length,
  reviewed: records.value.filter(item => item.status === 'reviewed').length,
  cancelled: records.value.filter(item => item.status === 'cancelled').length
}))

const reviewedProducedQuantity = computed(() => records.value
  .filter(item => item.status === 'reviewed')
  .reduce((sum, item) => sum + Number(item.producedQuantity || 0), 0))

const statusTabs = computed(() => [
  { value: 'all', label: '全部', count: records.value.length },
  { value: 'draft', label: '待审核', count: statusCount.value.draft },
  { value: 'reviewed', label: '已审核', count: statusCount.value.reviewed },
  { value: 'cancelled', label: '已作废', count: statusCount.value.cancelled }
])

const filteredRecords = computed(() => {
  const keyword = filters.keyword.toLowerCase()
  return records.value.filter(record => {
    const matchesStatus = filters.status === 'all' || record.status === filters.status
    const matchesStart = !filters.startDate || record.documentDate >= filters.startDate
    const matchesEnd = !filters.endDate || record.documentDate <= filters.endDate
    const matchesKeyword = !keyword || [
      record.documentNo,
      record.primaryItem?.productName,
      record.primaryItem?.productCode,
      record.remark,
      record.createdBy,
      record.storeName,
      record.warehouseName
    ].some(value => String(value || '').toLowerCase().includes(keyword))
    return matchesStatus && matchesStart && matchesEnd && matchesKeyword
  })
})

const availableWarehouses = computed(() => settings.value.warehouses.filter(warehouse => (
  !settingsForm.defaultStoreId
  || String(warehouse.storeId) === String(settingsForm.defaultStoreId)
)))

const selectedProducts = computed(() => settings.value.products.filter(product => (
  settingsForm.allowedProductIds.some(id => String(id) === String(product.id))
)))

const configSummary = computed(() => {
  const store = settings.value.stores.find(item => String(item.id) === String(settings.value.defaultStoreId))
  const warehouse = settings.value.warehouses.find(
    item => String(item.id) === String(settings.value.defaultWarehouseId)
  )
  const product = settings.value.products.find(
    item => String(item.id) === String(settings.value.defaultProductId)
  )
  return `${store?.name || '-'} / ${warehouse?.name || '-'} / ${product?.name || '-'}`
})

const actionCopy = computed(() => {
  const record = pendingAction.value?.record
  const copies = {
    audit: {
      title: '确认审核原材料出库单？',
      message: `审核后将从“${record?.warehouseName || '-'}”按先进先出扣减 ${formatNumber(record?.totalQuantity)} ${record?.primaryItem?.unit || ''}，操作会写入库存流水。`,
      confirm: '确认审核'
    },
    reverse: {
      title: '确认反审核？',
      message: '系统会按照原出库流水，将数量回补到此前扣减的批次与库位。',
      confirm: '确认反审核'
    },
    cancel: {
      title: '确认作废草稿？',
      message: '草稿尚未扣减库存，作废后可在已作废列表中重新启用。',
      confirm: '确认作废'
    },
    restart: {
      title: '确认重新启用？',
      message: '单据会恢复为待审核状态，库存不会发生变化。',
      confirm: '重新启用'
    }
  }
  return copies[pendingAction.value?.type] || { title: '', message: '', confirm: '确认' }
})

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const statusLabel = status => ({
  draft: '待审核',
  reviewed: '已审核',
  cancelled: '已作废'
}[status] || status)

const resetFilters = () => {
  filters.keyword = ''
  filters.startDate = ''
  filters.endDate = ''
  filters.status = 'all'
}

const loadData = async () => {
  loading.value = true
  loadError.value = ''
  const results = await Promise.allSettled([
    request({ url: '/material-outbounds', method: 'GET', params: { limit: 1000 } }),
    request({ url: '/material-outbound-settings', method: 'GET' })
  ])
  if (results[0].status === 'fulfilled') {
    records.value = Array.isArray(results[0].value) ? results[0].value : []
  } else {
    loadError.value = results[0].reason?.response?.data?.message || '原材料出库记录加载失败。'
  }
  if (results[1].status === 'fulfilled') {
    settings.value = results[1].value || settings.value
  } else if (!loadError.value) {
    loadError.value = results[1].reason?.response?.data?.message || '触屏端配置加载失败。'
  }
  loading.value = false
}

const openSettings = () => {
  settingsForm.defaultStoreId = settings.value.defaultStoreId ?? null
  settingsForm.defaultWarehouseId = settings.value.defaultWarehouseId ?? null
  settingsForm.allowedProductIds = [...(settings.value.allowedProductIds || [])]
  settingsForm.defaultProductId = settings.value.defaultProductId ?? null
  settingsForm.showCurrentStock = settings.value.showCurrentStock !== false
  settingsForm.allowInsufficientDraft = settings.value.allowInsufficientDraft !== false
  settingsError.value = ''
  settingsVisible.value = true
}

const saveSettings = async () => {
  settingsError.value = ''
  if (!settingsForm.defaultStoreId || !settingsForm.defaultWarehouseId) {
    settingsError.value = '请选择默认门店和默认仓库。'
    return
  }
  if (settingsForm.allowedProductIds.length === 0) {
    settingsError.value = '请至少选择一种触屏端可操作原材料。'
    return
  }
  if (!settingsForm.defaultProductId) {
    settingsError.value = '请选择默认原材料。'
    return
  }

  settingsSaving.value = true
  try {
    const response = await request({
      url: '/material-outbound-settings',
      method: 'PUT',
      data: {
        ...settingsForm,
        deductionStrategy: 'fifo'
      }
    })
    settings.value = response.settings || settings.value
    settingsVisible.value = false
  } catch (error) {
    settingsError.value = error?.response?.data?.message || '触屏端设置保存失败。'
  } finally {
    settingsSaving.value = false
  }
}

const openDetail = record => {
  detailRecord.value = record
}

const requestAction = (type, record) => {
  pendingAction.value = { type, record }
}

const executeAction = async () => {
  const action = pendingAction.value
  if (!action || actionLoading.value) return
  actionLoading.value = true
  try {
    const requests = {
      audit: { url: `/material-outbounds/${action.record.id}/audit`, method: 'POST' },
      reverse: { url: `/material-outbounds/${action.record.id}/audit`, method: 'DELETE' },
      cancel: { url: `/material-outbounds/${action.record.id}`, method: 'DELETE' },
      restart: { url: `/material-outbounds/${action.record.id}/restart`, method: 'POST' }
    }
    await request(requests[action.type])
    pendingAction.value = null
    detailRecord.value = null
    await loadData()
    window.dispatchEvent(new CustomEvent('refresh-material-outbounds'))
  } catch (error) {
    loadError.value = error?.response?.data?.message || `${actionCopy.value.title}失败`
    pendingAction.value = null
  } finally {
    actionLoading.value = false
  }
}

watch(
  () => settingsForm.defaultStoreId,
  () => {
    if (
      settingsForm.defaultWarehouseId
      && !availableWarehouses.value.some(
        item => String(item.id) === String(settingsForm.defaultWarehouseId)
      )
    ) {
      settingsForm.defaultWarehouseId = null
    }
  }
)

watch(
  () => [...settingsForm.allowedProductIds],
  () => {
    if (
      settingsForm.defaultProductId
      && !settingsForm.allowedProductIds.some(
        id => String(id) === String(settingsForm.defaultProductId)
      )
    ) {
      settingsForm.defaultProductId = settingsForm.allowedProductIds[0] ?? null
    }
  }
)

onMounted(loadData)

defineExpose({ reload: loadData })
</script>

<style scoped>
.outbound-page {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --border: #dfe5ec;
  --text: #172033;
  --muted: #7a8698;
  color: var(--text);
}

* {
  box-sizing: border-box;
}

button,
input,
select {
  font: inherit;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.page-toolbar,
.records-panel,
.stats-grid article {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 7px;
}

.page-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 15px 17px;
}

.search-group,
.toolbar-actions,
.row-actions,
.modal-footer,
.modal-footer > div,
.confirm-actions {
  display: flex;
  align-items: center;
  gap: 9px;
}

.search-group > label:not(.search-field) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-group label > span {
  color: #667085;
  font-size: 12px;
  font-weight: 600;
}

.search-field {
  position: relative;
  display: block;
  width: 280px;
}

.search-field svg {
  position: absolute;
  top: 11px;
  left: 11px;
  width: 16px;
  height: 16px;
  color: #94a3b8;
}

.search-field input {
  padding-left: 35px;
}

.page-toolbar input,
.settings-modal select {
  height: 38px;
  color: #344054;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  outline: none;
}

.page-toolbar input {
  padding: 0 10px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.button.primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.button.secondary {
  color: #475569;
  background: #fff;
  border-color: #cbd5e1;
}

.button.danger {
  color: #b42318;
  background: #fff;
  border-color: #f2aaa5;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.stats-grid article {
  padding: 17px 19px;
}

.stats-grid span,
.stats-grid small {
  display: block;
  color: var(--muted);
  font-size: 12px;
}

.stats-grid strong {
  display: block;
  margin: 8px 0 5px;
  font-size: 26px;
}

.warning-text {
  color: #b45309;
}

.success-text {
  color: var(--accent-dark);
}

.records-panel {
  margin-top: 12px;
  overflow: hidden;
}

.records-header {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 15px;
  border-bottom: 1px solid var(--border);
}

.status-tabs {
  display: flex;
  gap: 4px;
}

.status-tabs button {
  display: inline-flex;
  min-height: 34px;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  color: #667085;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
}

.status-tabs button.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.status-tabs button span {
  min-width: 19px;
  padding: 2px 5px;
  background: #eef2f6;
  border-radius: 999px;
  font-size: 11px;
  text-align: center;
}

.config-summary {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
  overflow: hidden;
  color: #7a8698;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-summary > span {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  background: #f59e0b;
  border-radius: 50%;
}

.config-summary > span.configured {
  background: var(--accent);
}

.load-error,
.form-error {
  padding: 10px 13px;
  color: #b42318;
  background: #fff1f0;
  border-bottom: 1px solid #fecaca;
  font-size: 12px;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 1380px;
  border-collapse: collapse;
  table-layout: fixed;
}

th {
  height: 44px;
  padding: 0 11px;
  color: #667085;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
}

td {
  height: 62px;
  padding: 9px 11px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

tbody tr:hover {
  background: #fbfcfd;
}

th:nth-child(1) { width: 155px; }
th:nth-child(2) { width: 148px; }
th:nth-child(3) { width: 170px; }
th:nth-child(4) { width: 145px; }
th:nth-child(5) { width: 105px; }
th:nth-child(6) { width: 105px; }
th:nth-child(7) { width: 120px; }
th:nth-child(8) { width: 95px; }
th:nth-child(9) { width: 94px; }
th:nth-child(10) { width: 145px; }
th:nth-child(11) { width: 166px; }

.number {
  text-align: right;
}

.quantity {
  color: #172033;
  font-weight: 750;
}

.quantity small {
  color: #7a8698;
  font-weight: 500;
}

.muted,
.muted small {
  color: #7a8698;
}

.material-cell,
.location-cell {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.material-cell strong,
.location-cell strong {
  overflow: hidden;
  color: #283548;
  text-overflow: ellipsis;
}

.material-cell small,
.location-cell small {
  overflow: hidden;
  color: #8a96a8;
  font-size: 11px;
  text-overflow: ellipsis;
}

.document-link {
  padding: 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  cursor: pointer;
  font-weight: 750;
}

.remark-cell {
  max-width: 120px;
}

.status-badge {
  display: inline-flex;
  min-height: 25px;
  align-items: center;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status-draft {
  color: #a4510b;
  background: #fff3df;
}

.status-reviewed {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.status-cancelled {
  color: #b4232f;
  background: #f1f2f4;
}

.actions-column {
  text-align: center;
}

.row-actions {
  justify-content: center;
}

.row-actions button {
  height: 29px;
  padding: 0 9px;
  color: #526074;
  background: #fff;
  border: 1px solid #d9e0e8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.row-actions .audit-action {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.empty-cell {
  height: 260px;
  color: #8a96a8;
  text-align: center;
}

.modal-layer {
  position: fixed;
  inset: 0;
  z-index: 2147482500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.46);
}

.settings-modal,
.detail-modal {
  display: flex;
  width: min(780px, calc(100vw - 48px));
  max-height: calc(100vh - 48px);
  flex-direction: column;
  overflow: hidden;
  background: #f4f7f8;
  border: 1px solid #dbe3ea;
  border-radius: 9px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
}

.detail-modal {
  width: min(680px, calc(100vw - 48px));
}

.modal-header {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 19px;
  background: #fff;
  border-bottom: 1px solid #dfe5ec;
}

.modal-header span {
  color: var(--accent);
  font-size: 11px;
  font-weight: 750;
}

.modal-header h2 {
  margin: 3px 0 2px;
  font-size: 19px;
}

.modal-header p {
  margin: 0;
  color: #7a8698;
  font-size: 12px;
}

.modal-header > button {
  width: 36px;
  height: 36px;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: 26px;
}

.settings-body,
.detail-body {
  overflow-y: auto;
  padding: 16px;
}

.settings-section {
  overflow: hidden;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.settings-section + .settings-section {
  margin-top: 13px;
}

.section-heading {
  padding: 12px 14px;
  border-bottom: 1px solid #e5eaf0;
}

.section-heading h3 {
  margin: 0;
  font-size: 14px;
}

.section-heading p {
  margin: 4px 0 0;
  color: #8a96a8;
  font-size: 11px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
}

.form-grid label,
.default-product-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.form-grid label > span,
.default-product-field > span {
  color: #596579;
  font-size: 12px;
  font-weight: 650;
}

.settings-modal select {
  width: 100%;
  padding: 0 10px;
}

.product-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  max-height: 230px;
  overflow-y: auto;
  padding: 14px;
}

.product-options label {
  position: relative;
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 9px;
  padding: 11px;
  background: #f8fafc;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  cursor: pointer;
}

.product-options input {
  position: absolute;
  opacity: 0;
}

.checkbox-mark {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  background: #fff;
  border: 1.5px solid #aeb9c7;
  border-radius: 4px;
}

.product-options input:checked + .checkbox-mark {
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: inset 0 0 0 3px #fff;
}

.product-options label > span:last-child {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.product-options strong,
.product-options small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-options strong {
  font-size: 13px;
}

.product-options small {
  color: #7a8698;
  font-size: 11px;
}

.products-empty {
  grid-column: 1 / -1;
  padding: 28px;
  color: #8a96a8;
  text-align: center;
}

.default-product-field {
  padding: 0 14px 14px;
}

.compact-section {
  padding-bottom: 3px;
}

.switch-line,
.readonly-line {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid #edf1f5;
}

.switch-line {
  cursor: pointer;
}

.switch-line input {
  position: absolute;
  opacity: 0;
}

.switch-control {
  position: relative;
  width: 35px;
  height: 20px;
  flex: 0 0 auto;
  background: #cbd5e1;
  border-radius: 999px;
}

.switch-control::after {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 14px;
  height: 14px;
  content: '';
  background: #fff;
  border-radius: 50%;
  transition: transform 0.18s ease;
}

.switch-line input:checked + .switch-control {
  background: var(--accent);
}

.switch-line input:checked + .switch-control::after {
  transform: translateX(15px);
}

.switch-line > span:last-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.switch-line strong,
.readonly-line strong {
  font-size: 12px;
}

.switch-line small,
.readonly-line span {
  color: #7a8698;
  font-size: 11px;
}

.readonly-line {
  justify-content: space-between;
}

.form-error {
  margin-top: 13px;
  border: 1px solid #fecaca;
  border-radius: 6px;
}

.modal-footer {
  justify-content: flex-end;
  min-height: 65px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #dfe5ec;
}

.detail-status-line {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.detail-status-line > span:last-child {
  color: #7a8698;
  font-size: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 13px 0 0;
  overflow: hidden;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.detail-grid > div {
  min-width: 0;
  padding: 13px 15px;
  border-right: 1px solid #edf1f5;
  border-bottom: 1px solid #edf1f5;
}

.detail-grid > div:nth-child(2n) {
  border-right: 0;
}

.detail-grid .wide {
  grid-column: 1 / -1;
  border-right: 0;
}

.detail-grid dt {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.detail-grid dd {
  margin: 0;
  color: #283548;
  font-size: 13px;
  font-weight: 650;
}

.detail-footer {
  justify-content: space-between;
}

.confirm-layer {
  z-index: 2147483000;
}

.confirm-modal {
  width: min(400px, calc(100vw - 40px));
  padding: 26px;
  text-align: center;
  background: #fff;
  border-radius: 9px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.25);
}

.confirm-icon {
  display: inline-flex;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #f59e0b;
  border-radius: 50%;
  font-size: 23px;
  font-weight: 850;
}

.confirm-icon.danger {
  background: #dc2626;
}

.confirm-modal h3 {
  margin: 14px 0 8px;
  font-size: 18px;
}

.confirm-modal p {
  margin: 0;
  color: #667085;
  line-height: 1.7;
  font-size: 13px;
}

.confirm-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 20px;
}

@media (max-width: 1100px) {
  .page-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .search-group {
    align-items: stretch;
    flex-direction: column;
  }

  .search-field {
    width: 100%;
  }

  .stats-grid,
  .form-grid,
  .product-options,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-grid > div,
  .detail-grid > div:nth-child(2n) {
    border-right: 0;
  }

  .records-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .settings-modal,
  .detail-modal {
    width: calc(100vw - 20px);
    max-height: calc(100vh - 20px);
  }
}
</style>
