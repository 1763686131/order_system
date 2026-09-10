<template>
  <div class="payment-history-page">
    <section class="records-panel">
      <header class="records-toolbar">
        <div class="store-filter-area">
          <span class="toolbar-label">收款门店</span>
          <div class="store-slider" role="tablist" aria-label="按门店筛选">
            <button
              :class="['slider-tab', { active: selectedStoreId === null }]"
              type="button"
              @click="setStore(null)"
            >
              全部门店
              <span class="count-badge">{{ receipts.length }}</span>
            </button>
            <button
              v-for="store in activeStores"
              :key="store.id"
              :class="['slider-tab', { active: selectedStoreId === store.id }]"
              type="button"
              @click="setStore(store.id)"
            >
              {{ store.name }}
              <span class="count-badge">{{ storeReceiptCount(store.id) }}</span>
            </button>
          </div>
        </div>

        <div class="toolbar-actions">
          <span v-if="selectedIds.length" class="selected-hint">
            已选 <strong>{{ selectedIds.length }}</strong> 条
          </span>
          <button
            class="icon-button"
            type="button"
            title="刷新收款历史"
            :disabled="loading"
            @click="loadData"
          >
            <svg :class="{ spinning: loading }" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button class="button button-secondary" type="button" @click="exportExcel">
            <svg viewBox="0 0 24 24">
              <path d="M12 3v12m-5-5 5 5 5-5M5 20h14"></path>
            </svg>
            导出Excel
          </button>
          <button class="button button-primary" type="button" @click="openCreateModal">
            <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"></path></svg>
            新增收款单
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <colgroup>
            <col class="checkbox-col"><col class="date-col"><col class="number-col">
            <col class="customer-col"><col class="money-col"><col class="money-col">
            <col class="money-col"><col class="money-col"><col class="creator-col">
            <col class="status-col"><col class="remark-col"><col class="operation-col">
          </colgroup>
          <thead>
            <tr>
              <th class="center-cell">
                <input
                  type="checkbox"
                  :checked="allPageSelected"
                  :indeterminate.prop="somePageSelected"
                  aria-label="选择当前页全部收款单"
                  @change="togglePageSelection"
                >
              </th>
              <th>单据日期</th>
              <th>单据编号</th>
              <th>客户</th>
              <th class="money-cell">收款金额</th>
              <th class="money-cell">优惠金额</th>
              <th class="money-cell">核销金额</th>
              <th class="money-cell">本次预收</th>
              <th>制单人</th>
              <th class="center-cell">审核状态</th>
              <th>备注</th>
              <th class="center-cell">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 6" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 12" :key="cell"><span></span></td>
              </tr>
            </template>
            <tr v-else-if="pagedReceipts.length === 0">
              <td colspan="12" class="empty-cell">
                <div class="empty-mark">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 5h16v15H4zM8 3h8v4H8zM8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>当前门店还没有收款记录</strong>
                <span>点击“新增收款单”录入第一笔客户收款</span>
              </td>
            </tr>
            <tr
              v-for="item in pagedReceipts"
              v-else
              :key="item.id"
              :class="{ selected: selectedIds.includes(item.id) }"
            >
              <td class="center-cell">
                <input v-model="selectedIds" type="checkbox" :value="item.id">
              </td>
              <td>{{ item.documentDate }}</td>
              <td>
                <button class="document-number" type="button" @click="printReceipt(item)">
                  {{ item.documentNo }}
                  <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
                </button>
              </td>
              <td class="customer-cell" :title="customerTitle(item)">
                <strong>{{ item.customerName || '-' }}</strong>
                <span>{{ item.storeName || '-' }} · #{{ item.customerCode || item.customerId }}</span>
              </td>
              <td class="money-cell amount-main">{{ formatMoney(item.paymentAmount) }}</td>
              <td class="money-cell amount-discount">{{ formatMoney(item.discountAmount) }}</td>
              <td class="money-cell amount-main">{{ formatMoney(item.writeoffAmount) }}</td>
              <td class="money-cell amount-advance">{{ formatMoney(item.advanceAmount) }}</td>
              <td>{{ item.creator || '-' }}</td>
              <td class="center-cell">
                <span :class="['status-badge', `status-${item.status}`]">
                  <i></i>{{ item.status === 'audited' ? '已审核' : '待审核' }}
                </span>
              </td>
              <td :title="item.remark || '-'">{{ item.remark || '-' }}</td>
              <td class="operation-cell">
                <div class="row-actions">
                  <button
                    v-if="item.status === 'draft'"
                    class="action-button action-audit"
                    type="button"
                    :disabled="busyId === item.id"
                    @click="auditReceipt(item)"
                  >
                    审核
                  </button>
                  <button
                    v-else
                    class="action-button action-reverse"
                    type="button"
                    :disabled="busyId === item.id"
                    @click="reverseAudit(item)"
                  >
                    反审核
                  </button>
                  <button class="action-button action-print" type="button" @click="printReceipt(item)">
                    打印
                  </button>
                  <button
                    v-if="item.status === 'draft'"
                    class="action-button action-edit"
                    type="button"
                    @click="openEditModal(item)"
                  >
                    修改
                  </button>
                  <button
                    v-if="item.status === 'draft'"
                    class="action-button action-delete"
                    type="button"
                    @click="deleteReceipt(item)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
          <tfoot v-if="!loading && filteredReceipts.length">
            <tr>
              <td></td>
              <td colspan="3" class="total-label">当前筛选合计</td>
              <td class="money-cell">{{ formatMoney(totals.paymentAmount) }}</td>
              <td class="money-cell">{{ formatMoney(totals.discountAmount) }}</td>
              <td class="money-cell">{{ formatMoney(totals.writeoffAmount) }}</td>
              <td class="money-cell">{{ formatMoney(totals.advanceAmount) }}</td>
              <td colspan="4"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <footer class="table-footer">
        <span>共 <strong>{{ filteredReceipts.length }}</strong> 条收款记录</span>
        <div class="pagination">
          <select v-model.number="pageSize" @change="currentPage = 1">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="50">50 条/页</option>
          </select>
          <button type="button" :disabled="currentPage <= 1" @click="currentPage -= 1">
            <svg viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"></path></svg>
          </button>
          <span class="page-number">{{ currentPage }} / {{ totalPages }}</span>
          <button type="button" :disabled="currentPage >= totalPages" @click="currentPage += 1">
            <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
          </button>
        </div>
      </footer>
    </section>

    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="modalVisible" class="modal-overlay" @mousedown.self="closeModal">
          <section class="payment-modal" role="dialog" aria-modal="true">
            <header class="modal-header">
              <div class="modal-title-area">
                <span class="modal-icon">
                  <svg viewBox="0 0 24 24">
                    <path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"></path>
                  </svg>
                </span>
                <div>
                  <span>{{ editingId ? '修改收款单' : '收款单录入' }}</span>
                  <h2>{{ form.documentNo || '新收款单' }}</h2>
                </div>
              </div>
              <button class="modal-close" type="button" title="关闭" @click="closeModal">
                <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"></path></svg>
              </button>
            </header>

            <form class="modal-body" @submit.prevent="saveReceipt">
              <section class="form-section">
                <header class="section-header">
                  <span>01</span>
                  <div>
                    <h3>基本信息</h3>
                    <p>收款单自动关联客户、门店与当前欠款。</p>
                  </div>
                </header>
                <div class="form-grid basic-grid">
                  <label class="form-field customer-select-field">
                    <span>客户 <b>*</b></span>
                    <select v-model.number="form.customerId" required @change="handleCustomerChange">
                      <option value="">请选择客户</option>
                      <option
                        v-for="customer in modalCustomers"
                        :key="customer.id"
                        :value="customer.id"
                      >
                        {{ customer.customerName }}（#{{ customer.customerCode || customer.id }}）
                        · 欠款{{ formatMoney(customer.receivable) }}
                      </option>
                    </select>
                  </label>
                  <label class="form-field">
                    <span>欠款金额</span>
                    <span class="readonly-value debt-value">{{ formatMoney(currentDebt) }}</span>
                  </label>
                  <label class="form-field">
                    <span>单据编号</span>
                    <span class="readonly-value document-value">
                      {{ form.documentNo || '保存时自动生成' }}
                    </span>
                  </label>
                  <label class="form-field">
                    <span>单据日期 <b>*</b></span>
                    <input v-model="form.documentDate" type="date" required @change="loadNextNumber">
                  </label>
                </div>
              </section>

              <section class="form-section">
                <header class="section-header">
                  <span>02</span>
                  <div>
                    <h3>收款信息</h3>
                    <p>审核后才核销欠款，多收的实收金额自动转入客户储值。</p>
                  </div>
                </header>
                <div class="form-grid payment-grid">
                  <label class="form-field">
                    <span>结算账户</span>
                    <span class="readonly-value">
                      {{ form.settlementAccount || '选择客户后匹配门店' }}
                    </span>
                  </label>
                  <label class="form-field">
                    <span>收款方式</span>
                    <input v-model.trim="form.paymentMethod" maxlength="30" placeholder="微信、银行转账等">
                  </label>
                  <label class="form-field">
                    <span>收款金额 <b>*</b></span>
                    <span class="money-input">
                      <i>¥</i>
                      <input
                        v-model="form.paymentAmount"
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                        placeholder="0.00"
                      >
                    </span>
                  </label>
                  <label class="form-field">
                    <span>优惠金额</span>
                    <span class="money-input">
                      <i>¥</i>
                      <input
                        v-model="form.discountAmount"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                      >
                    </span>
                  </label>
                  <label class="form-field">
                    <span>合计金额</span>
                    <span class="readonly-value total-value">{{ formatMoney(formTotal) }}</span>
                  </label>
                </div>
                <div class="account-preview">
                  <div>
                    <span>预计核销欠款</span>
                    <strong>{{ formatMoney(previewWriteoff) }}</strong>
                  </div>
                  <div>
                    <span>预计转入预收</span>
                    <strong>{{ formatMoney(previewAdvance) }}</strong>
                  </div>
                  <p :class="{ warning: Number(form.discountAmount) > currentDebt }">
                    {{
                      Number(form.discountAmount) > currentDebt
                        ? '优惠金额不能超过客户当前欠款。'
                        : '当前仅为预览，审核时按客户实时欠款重新计算。'
                    }}
                  </p>
                </div>
              </section>

              <section class="form-section">
                <header class="section-header">
                  <span>03</span>
                  <div>
                    <h3>其他信息</h3>
                    <p>补充制单人、备注与收款凭证，便于后续对账追溯。</p>
                  </div>
                </header>
                <div class="form-grid other-grid">
                  <label class="form-field">
                    <span>制单人</span>
                    <input v-model.trim="form.creator" maxlength="30">
                  </label>
                  <label class="form-field">
                    <span>备注</span>
                    <textarea
                      v-model.trim="form.remark"
                      rows="4"
                      maxlength="300"
                      placeholder="可填写收款说明、银行流水号等"
                    ></textarea>
                  </label>
                  <div class="form-field">
                    <span>上传附件图片</span>
                    <label class="attachment-uploader">
                      <input
                        ref="attachmentInput"
                        type="file"
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        @change="handleAttachment"
                      >
                      <img v-if="attachmentPreview" :src="attachmentPreview" alt="收款附件预览">
                      <span v-else class="upload-placeholder">
                        <svg viewBox="0 0 24 24">
                          <path d="M4 5h16v14H4z"></path>
                          <circle cx="9" cy="10" r="2"></circle>
                          <path d="m4 17 5-4 3 3 2-2 6 5"></path>
                        </svg>
                        <strong>选择收款凭证</strong>
                        <small>图片最大 10MB</small>
                      </span>
                    </label>
                    <button
                      v-if="attachmentPreview"
                      class="remove-attachment"
                      type="button"
                      @click="removeAttachment"
                    >
                      移除附件
                    </button>
                  </div>
                </div>
              </section>
            </form>

            <footer class="modal-footer">
              <span class="draft-tip">
                <svg viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="9"></circle>
                  <path d="M12 8v5M12 17h.01"></path>
                </svg>
                保存后是待审核草稿，不会立即改变客户账户。
              </span>
              <div class="modal-actions">
                <button class="button button-secondary" type="button" @click="closeModal">取消</button>
                <button
                  class="button button-primary"
                  type="button"
                  :disabled="saving"
                  @click="saveReceipt"
                >
                  <svg v-if="saving" class="spinning" viewBox="0 0 24 24">
                    <path d="M20 11a8 8 0 1 0-2.3 5.7"></path>
                  </svg>
                  <svg v-else viewBox="0 0 24 24">
                    <path d="M5 4h12l2 2v14H5zM8 4v6h8V4M8 16h8"></path>
                  </svg>
                  {{ saving ? '保存中...' : '保存收款单' }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>

      <Transition name="notice">
        <div v-if="notice.visible" :class="['page-notice', `notice-${notice.type}`]">
          <svg viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9"></circle>
            <path v-if="notice.type === 'success'" d="m8 12 2.7 2.7L16.5 9"></path>
            <path v-else d="M12 8v5M12 17h.01"></path>
          </svg>
          {{ notice.message }}
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as XLSX from 'xlsx'
import request from '@/api/request'

const receipts = ref([])
const stores = ref([])
const customers = ref([])
const selectedStoreId = ref(null)
const selectedIds = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const busyId = ref(null)
const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const attachmentInput = ref(null)
const attachmentFile = ref(null)
const attachmentPreview = ref('')
const localPreviewUrl = ref('')
let noticeTimer = null

const notice = reactive({ visible: false, type: 'success', message: '' })

const todayText = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const emptyForm = () => ({
  documentNo: '',
  documentDate: todayText(),
  customerId: '',
  settlementAccount: '',
  paymentMethod: '',
  paymentAmount: '',
  discountAmount: 0,
  creator: '王醒',
  remark: '',
  attachmentUrl: ''
})
const form = reactive(emptyForm())

const activeStores = computed(() => stores.value.filter(item => item.status !== 'inactive'))
const filteredReceipts = computed(() =>
  selectedStoreId.value === null
    ? receipts.value
    : receipts.value.filter(item => Number(item.storeId) === selectedStoreId.value)
)
const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredReceipts.value.length / pageSize.value))
)
const pagedReceipts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredReceipts.value.slice(start, start + pageSize.value)
})
const allPageSelected = computed(() =>
  pagedReceipts.value.length > 0 &&
  pagedReceipts.value.every(item => selectedIds.value.includes(item.id))
)
const somePageSelected = computed(() =>
  !allPageSelected.value &&
  pagedReceipts.value.some(item => selectedIds.value.includes(item.id))
)
const totals = computed(() =>
  filteredReceipts.value.reduce((result, item) => {
    result.paymentAmount += Number(item.paymentAmount) || 0
    result.discountAmount += Number(item.discountAmount) || 0
    result.writeoffAmount += Number(item.writeoffAmount) || 0
    result.advanceAmount += Number(item.advanceAmount) || 0
    return result
  }, { paymentAmount: 0, discountAmount: 0, writeoffAmount: 0, advanceAmount: 0 })
)
const modalCustomers = computed(() => {
  if (selectedStoreId.value === null || editingId.value) return customers.value
  return customers.value.filter(
    customer => Number(customer.storeId) === selectedStoreId.value
  )
})
const selectedCustomer = computed(() =>
  customers.value.find(customer => Number(customer.id) === Number(form.customerId))
)
const currentDebt = computed(() =>
  Math.max(0, Number(selectedCustomer.value?.receivable) || 0)
)
const formTotal = computed(() =>
  Math.max(0, Number(form.paymentAmount) || 0) +
  Math.max(0, Number(form.discountAmount) || 0)
)
const previewWriteoff = computed(() => Math.min(currentDebt.value, formTotal.value))
const previewAdvance = computed(() => {
  const payment = Math.max(0, Number(form.paymentAmount) || 0)
  const discount = Math.max(0, Number(form.discountAmount) || 0)
  const cashWriteoff = Math.min(payment, Math.max(0, currentDebt.value - discount))
  return Math.max(0, payment - cashWriteoff)
})

const formatMoney = value => `¥${(Number(value) || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})}`
const customerTitle = item =>
  [item.customerName, item.contactPerson, item.phone].filter(Boolean).join(' · ')
const errorMessage = (error, fallback) =>
  error?.response?.data?.error || error?.response?.data?.message || error?.message || fallback

const showNotice = (message, type = 'success') => {
  if (noticeTimer) window.clearTimeout(noticeTimer)
  Object.assign(notice, { visible: true, message, type })
  noticeTimer = window.setTimeout(() => { notice.visible = false }, 3200)
}

const loadData = async () => {
  loading.value = true
  try {
    const [storeResponse, customerResponse, receiptResponse] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/customers', method: 'GET', params: { status: 'active' } }),
      request({ url: '/payment-receipts', method: 'GET' })
    ])
    stores.value = Array.isArray(storeResponse) ? storeResponse : []
    customers.value = Array.isArray(customerResponse) ? customerResponse : []
    receipts.value = Array.isArray(receiptResponse?.items) ? receiptResponse.items : []
    selectedIds.value = selectedIds.value.filter(id =>
      receipts.value.some(item => item.id === id)
    )
  } catch (error) {
    console.error('加载收款历史失败:', error)
    showNotice(errorMessage(error, '加载收款历史失败'), 'error')
  } finally {
    loading.value = false
  }
}

const setStore = storeId => {
  selectedStoreId.value = storeId
  selectedIds.value = []
  currentPage.value = 1
}
const storeReceiptCount = storeId =>
  receipts.value.filter(item => Number(item.storeId) === Number(storeId)).length
const togglePageSelection = () => {
  const pageIds = pagedReceipts.value.map(item => item.id)
  selectedIds.value = allPageSelected.value
    ? selectedIds.value.filter(id => !pageIds.includes(id))
    : Array.from(new Set([...selectedIds.value, ...pageIds]))
}

const clearLocalPreview = () => {
  if (localPreviewUrl.value) URL.revokeObjectURL(localPreviewUrl.value)
  localPreviewUrl.value = ''
}
const resetForm = () => {
  Object.assign(form, emptyForm())
  editingId.value = null
  attachmentFile.value = null
  attachmentPreview.value = ''
  clearLocalPreview()
  if (attachmentInput.value) attachmentInput.value.value = ''
}
const loadNextNumber = async () => {
  if (editingId.value || !form.documentDate) return
  try {
    const response = await request({
      url: '/payment-receipts/next-number',
      method: 'GET',
      params: { date: form.documentDate }
    })
    form.documentNo = response?.documentNo || ''
  } catch (error) {
    form.documentNo = ''
    console.error('获取收款单号失败:', error)
  }
}
const openCreateModal = async () => {
  resetForm()
  modalVisible.value = true
  await loadNextNumber()
}
const openEditModal = item => {
  resetForm()
  editingId.value = item.id
  Object.assign(form, {
    documentNo: item.documentNo,
    documentDate: item.documentDate,
    customerId: item.customerId,
    settlementAccount: item.settlementAccount,
    paymentMethod: item.paymentMethod,
    paymentAmount: item.paymentAmount,
    discountAmount: item.discountAmount,
    creator: item.creator || '王醒',
    remark: item.remark || '',
    attachmentUrl: item.attachmentUrl || ''
  })
  attachmentPreview.value = item.attachmentUrl || ''
  modalVisible.value = true
}
const closeModal = () => {
  if (saving.value) return
  modalVisible.value = false
  window.setTimeout(resetForm, 180)
}
const handleCustomerChange = () => {
  const store = stores.value.find(
    item => Number(item.id) === Number(selectedCustomer.value?.storeId)
  )
  form.settlementAccount = store ? `${store.name}结算账户` : ''
}

const handleAttachment = event => {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    showNotice('请选择图片格式的收款附件', 'error')
    event.target.value = ''
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    showNotice('附件图片不能超过10MB', 'error')
    event.target.value = ''
    return
  }
  clearLocalPreview()
  attachmentFile.value = file
  localPreviewUrl.value = URL.createObjectURL(file)
  attachmentPreview.value = localPreviewUrl.value
}
const removeAttachment = () => {
  attachmentFile.value = null
  form.attachmentUrl = ''
  attachmentPreview.value = ''
  clearLocalPreview()
  if (attachmentInput.value) attachmentInput.value.value = ''
}
const uploadAttachment = async () => {
  if (!attachmentFile.value) return form.attachmentUrl
  const uploadData = new FormData()
  uploadData.append('attachment', attachmentFile.value)
  const response = await request({
    url: '/payment-receipts/attachments',
    method: 'POST',
    data: uploadData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response?.attachmentUrl || ''
}

const saveReceipt = async () => {
  let validationError = ''
  if (!form.customerId) validationError = '请选择客户'
  else if (!form.documentDate) validationError = '请选择单据日期'
  else if (!(Number(form.paymentAmount) > 0)) validationError = '收款金额必须大于0'
  else if (Number(form.discountAmount) < 0) validationError = '优惠金额不能小于0'
  else if (Number(form.discountAmount) > currentDebt.value) {
    validationError = '优惠金额不能超过客户当前欠款'
  }
  if (validationError) {
    showNotice(validationError, 'error')
    return
  }

  saving.value = true
  try {
    const payload = {
      customerId: form.customerId,
      documentDate: form.documentDate,
      settlementAccount: form.settlementAccount,
      paymentMethod: form.paymentMethod,
      paymentAmount: Number(form.paymentAmount),
      discountAmount: Number(form.discountAmount) || 0,
      creator: form.creator || '王醒',
      remark: form.remark,
      attachmentUrl: await uploadAttachment()
    }
    const response = await request({
      url: editingId.value
        ? `/payment-receipts/${editingId.value}`
        : '/payment-receipts',
      method: editingId.value ? 'PUT' : 'POST',
      data: payload
    })
    showNotice(response?.message || '收款单保存成功')
    modalVisible.value = false
    resetForm()
    await loadData()
  } catch (error) {
    console.error('保存收款单失败:', error)
    showNotice(errorMessage(error, '保存收款单失败'), 'error')
  } finally {
    saving.value = false
  }
}

const auditReceipt = async item => {
  const prompt = [
    `确定审核收款单 ${item.documentNo} 吗？`,
    `实收 ${formatMoney(item.paymentAmount)}，优惠 ${formatMoney(item.discountAmount)}。`,
    '审核后会立即核销客户欠款，多收金额转为客户储值。'
  ].join('\n')
  if (!window.confirm(prompt)) return
  busyId.value = item.id
  try {
    const response = await request({
      url: `/payment-receipts/${item.id}/audit`,
      method: 'POST'
    })
    showNotice(response?.message || '收款单审核成功')
    await loadData()
  } catch (error) {
    showNotice(errorMessage(error, '审核失败'), 'error')
  } finally {
    busyId.value = null
  }
}
const reverseAudit = async item => {
  if (!window.confirm(
    `确定反审核收款单 ${item.documentNo} 吗？\n系统会恢复本单核销的欠款并撤回本单预收。`
  )) return
  busyId.value = item.id
  try {
    const response = await request({
      url: `/payment-receipts/${item.id}/audit`,
      method: 'DELETE'
    })
    showNotice(response?.message || '反审核成功')
    await loadData()
  } catch (error) {
    showNotice(errorMessage(error, '反审核失败'), 'error')
  } finally {
    busyId.value = null
  }
}
const deleteReceipt = async item => {
  if (!window.confirm(`确定删除待审核收款单 ${item.documentNo} 吗？`)) return
  busyId.value = item.id
  try {
    const response = await request({
      url: `/payment-receipts/${item.id}`,
      method: 'DELETE'
    })
    showNotice(response?.message || '收款单已删除')
    selectedIds.value = selectedIds.value.filter(id => id !== item.id)
    await loadData()
  } catch (error) {
    showNotice(errorMessage(error, '删除失败'), 'error')
  } finally {
    busyId.value = null
  }
}

const escapeHtml = value => String(value ?? '')
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#039;')

const printReceipt = item => {
  const printWindow = window.open('', '_blank', 'width=900,height=760')
  if (!printWindow) {
    showNotice('浏览器拦截了打印窗口，请允许弹窗后重试', 'error')
    return
  }
  const attachment = item.attachmentUrl
    ? `<div class="attachment"><p>附件凭证</p><img src="${escapeHtml(item.attachmentUrl)}"></div>`
    : ''
  printWindow.document.write(`
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
    <title>收款单 ${escapeHtml(item.documentNo)}</title>
    <style>
      *{box-sizing:border-box}body{padding:36px;color:#172033;font:14px/1.6 Arial,"Microsoft YaHei"}
      h1{text-align:center;letter-spacing:5px}.sub{text-align:center;color:#667085}
      .meta{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid #cbd5e1}
      .meta div{padding:12px 15px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0}
      .meta span{display:block;color:#667085;font-size:12px}.meta strong{font-size:16px}
      table{width:100%;margin-top:22px;border-collapse:collapse}th,td{padding:12px;border:1px solid #cbd5e1;text-align:right}
      th:first-child,td:first-child{text-align:left}th{background:#f8fafc}
      .remark{min-height:72px;margin-top:22px;padding:12px;border:1px solid #cbd5e1}
      .attachment img{max-width:420px;max-height:300px;object-fit:contain}.sign{display:flex;justify-content:space-between;margin-top:45px}
    </style></head><body>
    <h1>收款单</h1><p class="sub">${escapeHtml(item.storeName)} · ${escapeHtml(item.documentNo)}</p>
    <section class="meta">
      <div><span>单据日期</span><strong>${escapeHtml(item.documentDate)}</strong></div>
      <div><span>客户</span><strong>${escapeHtml(item.customerName)}</strong></div>
      <div><span>审核状态</span><strong>${item.status === 'audited' ? '已审核' : '待审核'}</strong></div>
      <div><span>结算账户</span><strong>${escapeHtml(item.settlementAccount || '-')}</strong></div>
      <div><span>收款方式</span><strong>${escapeHtml(item.paymentMethod || '-')}</strong></div>
      <div><span>制单人</span><strong>${escapeHtml(item.creator || '-')}</strong></div>
    </section>
    <table><thead><tr><th>金额项目</th><th>收款金额</th><th>优惠金额</th><th>核销金额</th><th>本次预收</th></tr></thead>
    <tbody><tr><td>本次收款</td><td>${formatMoney(item.paymentAmount)}</td><td>${formatMoney(item.discountAmount)}</td><td>${formatMoney(item.writeoffAmount)}</td><td>${formatMoney(item.advanceAmount)}</td></tr></tbody></table>
    <div class="remark">备注：${escapeHtml(item.remark || '无')}</div>${attachment}
    <div class="sign"><span>客户签字：________________</span><span>经办人：${escapeHtml(item.creator || '王醒')}</span></div>
    <script>window.addEventListener('load',()=>window.print())<\/script></body></html>
  `)
  printWindow.document.close()
}

const exportExcel = () => {
  if (!filteredReceipts.value.length) {
    showNotice('当前没有可导出的收款记录', 'error')
    return
  }
  const rows = filteredReceipts.value.map(item => ({
    '单据日期': item.documentDate,
    '单据编号': item.documentNo,
    '门店': item.storeName,
    '客户': item.customerName,
    '客户编号': item.customerCode || item.customerId,
    '收款金额': Number(item.paymentAmount) || 0,
    '优惠金额': Number(item.discountAmount) || 0,
    '核销金额': Number(item.writeoffAmount) || 0,
    '本次预收': Number(item.advanceAmount) || 0,
    '制单人': item.creator,
    '审核状态': item.status === 'audited' ? '已审核' : '待审核',
    '收款方式': item.paymentMethod,
    '结算账户': item.settlementAccount,
    '备注': item.remark
  }))
  const sheet = XLSX.utils.json_to_sheet(rows)
  sheet['!cols'] = [
    { wch: 12 }, { wch: 20 }, { wch: 14 }, { wch: 18 }, { wch: 12 },
    { wch: 13 }, { wch: 13 }, { wch: 13 }, { wch: 13 }, { wch: 10 },
    { wch: 10 }, { wch: 14 }, { wch: 20 }, { wch: 28 }
  ]
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, '收款历史')
  const storeName = selectedStoreId.value === null
    ? '全部门店'
    : activeStores.value.find(store => store.id === selectedStoreId.value)?.name || '门店'
  XLSX.writeFile(workbook, `收款历史-${storeName}-${todayText()}.xlsx`)
  showNotice(`已导出 ${rows.length} 条收款记录`)
}

watch(totalPages, pages => {
  if (currentPage.value > pages) currentPage.value = pages
})
watch(modalVisible, visible => {
  document.body.style.overflow = visible ? 'hidden' : ''
})
onMounted(loadData)
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  clearLocalPreview()
  if (noticeTimer) window.clearTimeout(noticeTimer)
})
</script>

<style scoped>
.payment-history-page {
  --accent:#0f9f78;--accent-rgb:15,159,120;--accent-dark:#08745a;
  --accent-soft:#e9f8f3;--accent-border:#a9e5d2;--page-bg:#f4f7f8;
  --border:#e2e8f0;--border-strong:#cbd5e1;--text:#172033;
  --text-secondary:#596579;--text-muted:#8a96a8;
  min-width:0;min-height:calc(100vh - 100px);color:var(--text);
  background:var(--page-bg);font-size:14px;
}
*{box-sizing:border-box}button,input,select,textarea{font:inherit}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}
.records-panel{overflow:hidden;background:#fff;border:1px solid var(--border);border-radius:7px;box-shadow:0 3px 14px rgba(15,23,42,.045)}
.records-toolbar{display:flex;min-height:68px;align-items:center;justify-content:space-between;gap:20px;padding:11px 16px;border-bottom:1px solid var(--border)}
.store-filter-area{display:flex;min-width:0;align-items:center;gap:11px}.toolbar-label{flex:0 0 auto;color:var(--text-secondary);font-size:12px;font-weight:650}
.store-slider{display:flex;min-width:0;max-width:min(760px,52vw);align-items:center;gap:6px;overflow-x:auto;padding:4px;background:#f1f5f9;border-radius:8px;box-shadow:inset 0 1px 3px rgba(0,0,0,.08);scrollbar-width:thin}
.slider-tab{display:inline-flex;height:36px;flex:0 0 auto;align-items:center;gap:7px;padding:0 15px;color:var(--text-secondary);background:transparent;border:0;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap}
.slider-tab:hover{color:var(--accent-dark);background:rgba(var(--accent-rgb),.1)}.slider-tab.active{color:#fff;background:var(--accent);box-shadow:0 2px 6px rgba(var(--accent-rgb),.3)}
.count-badge{display:inline-flex;min-width:20px;height:20px;align-items:center;justify-content:center;padding:0 6px;background:rgba(0,0,0,.1);border-radius:10px;font-size:11px;font-weight:700}.slider-tab.active .count-badge{background:rgba(255,255,255,.25)}
.toolbar-actions,.row-actions,.pagination,.modal-actions{display:flex;align-items:center;gap:8px}.toolbar-actions{flex:0 0 auto}.selected-hint{color:var(--text-secondary);font-size:12px}.selected-hint strong{color:var(--accent-dark)}
.button{display:inline-flex;height:38px;align-items:center;justify-content:center;gap:7px;padding:0 15px;border:1px solid transparent;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap}
.button:disabled{cursor:not-allowed;opacity:.5}.button svg{width:16px;height:16px}.button-primary{color:#fff;background:var(--accent);border-color:var(--accent);box-shadow:0 2px 5px rgba(var(--accent-rgb),.18)}.button-primary:hover:not(:disabled){background:var(--accent-dark)}
.button-secondary{color:#445066;background:#fff;border-color:var(--border-strong)}.button-secondary:hover{color:var(--accent-dark);background:var(--accent-soft);border-color:var(--accent-border)}
.icon-button{display:inline-flex;width:36px;height:36px;align-items:center;justify-content:center;padding:0;color:#667085;background:#fff;border:1px solid var(--border-strong);border-radius:5px;cursor:pointer}.icon-button:hover:not(:disabled){color:var(--accent-dark);background:var(--accent-soft)}.icon-button:disabled{opacity:.45}.icon-button svg{width:17px;height:17px}
.spinning{animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.table-scroll{overflow-x:auto}
.records-table{width:100%;min-width:1840px;border-collapse:collapse;table-layout:fixed}.checkbox-col{width:50px}.date-col{width:112px}.number-col{width:168px}.customer-col{width:190px}.money-col{width:125px}.creator-col{width:90px}.status-col{width:105px}.remark-col{width:180px}.operation-col{width:355px}
.records-table th{height:45px;padding:0 12px;color:#566176;background:#f8fafc;border-bottom:1px solid var(--border);font-size:12px;font-weight:650;text-align:left;white-space:nowrap}
.records-table td{height:57px;padding:9px 12px;overflow:hidden;color:#344054;border-bottom:1px solid #edf1f5;text-overflow:ellipsis;white-space:nowrap}.records-table tbody tr:hover{background:rgba(var(--accent-rgb),.08)}.records-table tbody tr.selected{background:rgba(var(--accent-rgb),.12)}
.center-cell,.operation-cell{text-align:center!important}.center-cell input{width:15px;height:15px;accent-color:var(--accent);cursor:pointer}.money-cell{text-align:right!important;font-variant-numeric:tabular-nums}
.document-number{display:inline-flex;max-width:100%;align-items:center;gap:4px;padding:0;overflow:hidden;color:var(--accent-dark);background:transparent;border:0;cursor:pointer;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.document-number:hover{text-decoration:underline}.document-number svg{width:13px;height:13px}
.customer-cell strong,.customer-cell span{display:block;overflow:hidden;text-overflow:ellipsis}.customer-cell span{margin-top:3px;color:var(--text-muted);font-size:11px}.amount-main{font-weight:700}.amount-discount{color:#a4510b!important;font-weight:650}.amount-advance{color:#07805f!important;font-weight:700}
.status-badge{display:inline-flex;min-height:25px;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:650}.status-badge i{width:6px;height:6px;background:currentColor;border-radius:50%}.status-draft{color:#a4510b;background:#fff3df}.status-audited{color:#16647a;background:#e7f5f8}
.row-actions{justify-content:center}.action-button{display:inline-flex;height:30px;align-items:center;justify-content:center;padding:0 10px;border:1px solid transparent;border-radius:4px;cursor:pointer;font-size:12px;font-weight:650}.action-button:disabled{opacity:.45}
.action-audit{color:#fff;background:#0f9f78}.action-reverse{color:#8a470c;background:#fff7e8;border-color:#f3c887}.action-print{color:#445066;background:#fff;border-color:var(--border-strong)}.action-edit{color:#fff;background:#2563eb}.action-delete{color:#dc3545;background:#fff;border-color:#f0a5ad}
.action-audit:hover{background:#08745a}.action-reverse:hover{background:#ffedc8}.action-print:hover{background:#f1f5f9}.action-edit:hover{background:#1d4ed8}.action-delete:hover{color:#fff;background:#dc3545}
.records-table tfoot{background:#f8fafc;border-top:2px solid var(--border);font-weight:700}.total-label{padding-left:20px!important}.empty-cell{height:290px!important;color:var(--text-muted)!important;text-align:center}.empty-cell strong,.empty-cell span{display:block}.empty-cell strong{margin-top:11px;color:#4c586b}.empty-cell span{margin-top:5px;font-size:12px}
.empty-mark{display:inline-flex;width:48px;height:48px;align-items:center;justify-content:center;color:#aab4c0;background:#f1f4f7;border-radius:50%}.empty-mark svg{width:24px;height:24px}.skeleton-row span{display:block;width:78%;height:10px;background:linear-gradient(90deg,#eef2f5 25%,#e2e8ee 50%,#eef2f5 75%);background-size:200% 100%;border-radius:3px;animation:shimmer 1.25s linear infinite}@keyframes shimmer{to{background-position:-200% 0}}
.table-footer{display:flex;min-height:58px;align-items:center;justify-content:space-between;padding:10px 16px;color:var(--text-secondary);border-top:1px solid var(--border);font-size:12px}.table-footer strong{color:var(--text)}.pagination select{height:32px;padding:0 8px;border:1px solid var(--border-strong);border-radius:5px}.pagination button{display:inline-flex;width:31px;height:31px;align-items:center;justify-content:center;color:var(--text-secondary);background:#fff;border:1px solid var(--border-strong);border-radius:5px}.pagination button:disabled{opacity:.45}.pagination svg{width:15px;height:15px}.page-number{min-width:58px;text-align:center}
.modal-overlay{position:fixed;inset:0;z-index:2200;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(15,23,42,.42);backdrop-filter:blur(1px)}
.payment-modal{display:flex;width:min(1040px,calc(100vw - 48px));max-height:min(900px,calc(100vh - 48px));flex-direction:column;overflow:hidden;color:#172033;background:#f4f7f9;border:1px solid #dfe5ec;border-radius:8px;box-shadow:0 24px 70px rgba(15,23,42,.24)}
.modal-header{display:flex;min-height:78px;align-items:center;justify-content:space-between;padding:14px 20px;background:#fff;border-bottom:1px solid #dfe5ec}.modal-title-area{display:flex;align-items:center;gap:12px}.modal-title-area>div>span{color:#7a8799;font-size:11px;font-weight:650}.modal-title-area h2{margin:3px 0 0;font-size:18px}.modal-icon{display:inline-flex;width:40px;height:40px;align-items:center;justify-content:center;color:#08745a;background:#e9f8f3;border-radius:7px}.modal-icon svg{width:22px;height:22px}
.modal-close{display:inline-flex;width:34px;height:34px;align-items:center;justify-content:center;color:#718096;background:transparent;border:0;border-radius:5px;cursor:pointer}.modal-close:hover{background:#f1f5f9}.modal-close svg{width:19px;height:19px}
.modal-body{display:flex;min-height:0;flex:1;flex-direction:column;gap:12px;overflow-y:auto;padding:14px}.form-section{padding:16px;background:#fff;border:1px solid #dfe5ec;border-radius:7px}.section-header{display:flex;align-items:center;gap:10px;margin-bottom:15px;padding-bottom:11px;border-bottom:1px solid #edf1f5}.section-header>span{display:inline-flex;width:31px;height:31px;align-items:center;justify-content:center;color:#08745a;background:#e9f8f3;border-radius:5px;font-size:11px;font-weight:800}.section-header h3{margin:0;font-size:14px}.section-header p{margin:2px 0 0;color:#8a96a8;font-size:11px}
.form-grid{display:grid;gap:14px}.basic-grid{grid-template-columns:1.35fr .85fr 1fr .85fr}.payment-grid{grid-template-columns:1.25fr 1fr 1fr 1fr 1fr}.other-grid{grid-template-columns:.65fr 1.5fr 1fr;align-items:start}.form-field{display:flex;min-width:0;flex-direction:column;gap:7px}.form-field>span:first-child{color:#596579;font-size:12px;font-weight:650}.form-field b{color:#dc3545}
.form-field input,.form-field select,.form-field textarea{width:100%;color:#172033;background:#fff;border:1px solid #cbd5e1;border-radius:5px;outline:none}.form-field input,.form-field select{height:38px;padding:0 11px}.form-field textarea{min-height:98px;padding:10px 11px;resize:vertical}.form-field input:focus,.form-field select:focus,.form-field textarea:focus{border-color:#0f9f78;box-shadow:0 0 0 3px rgba(15,159,120,.12)}
.readonly-value{display:flex;min-height:38px;align-items:center;padding:0 11px;overflow:hidden;color:#445066;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px;text-overflow:ellipsis;white-space:nowrap}.debt-value{color:#dc3545;font-weight:750}.document-value{color:#08745a;font-weight:700}.money-input{position:relative}.money-input i{position:absolute;top:10px;left:11px;color:#7a8799;font-style:normal}.money-input input{padding-left:28px}.total-value{font-size:15px;font-weight:800}
.account-preview{display:grid;grid-template-columns:180px 180px 1fr;align-items:center;gap:14px;margin-top:14px;padding:12px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px}.account-preview div{padding-right:14px;border-right:1px solid #e2e8f0}.account-preview span,.account-preview strong{display:block}.account-preview span{color:#7a8799;font-size:11px}.account-preview strong{margin-top:3px;font-size:15px}.account-preview div:nth-child(2) strong{color:#07805f}.account-preview p{margin:0;color:#7a8799;font-size:11px}.account-preview p.warning{color:#b4232f;font-weight:650}
.attachment-uploader{position:relative;display:flex;min-height:130px;align-items:center;justify-content:center;overflow:hidden;background:#fafcfd;border:1px dashed #aeb9c8;border-radius:5px;cursor:pointer}.attachment-uploader:hover{background:#f0faf6;border-color:#0f9f78}.attachment-uploader input{position:absolute;width:1px;height:1px;opacity:0}.attachment-uploader img{width:100%;height:160px;object-fit:contain}.upload-placeholder{display:flex;align-items:center;flex-direction:column;color:#718096}.upload-placeholder svg{width:29px;height:29px;margin-bottom:8px;color:#0f9f78}.upload-placeholder strong{font-size:12px}.upload-placeholder small{margin-top:4px;font-size:10px}.remove-attachment{align-self:flex-start;padding:0;color:#dc3545;background:transparent;border:0;cursor:pointer;font-size:11px}
.modal-footer{display:flex;min-height:68px;align-items:center;justify-content:space-between;gap:16px;padding:12px 18px;background:#fff;border-top:1px solid #dfe5ec}.draft-tip{display:flex;align-items:center;gap:7px;color:#7a8799;font-size:11px}.draft-tip svg{width:16px;height:16px;color:#a4510b}
.page-notice{position:fixed;top:24px;left:50%;z-index:3000;display:flex;min-height:44px;align-items:center;gap:9px;max-width:min(520px,calc(100vw - 32px));padding:10px 16px;color:#172033;background:#fff;border:1px solid #dfe5ec;border-radius:6px;box-shadow:0 10px 30px rgba(15,23,42,.16);transform:translateX(-50%);font-size:13px;font-weight:600}.page-notice svg{width:19px;height:19px}.notice-success svg{color:#0f9f78}.notice-error svg{color:#dc3545}
.modal-fade-enter-active,.modal-fade-leave-active{transition:opacity .2s}.modal-fade-enter-active .payment-modal,.modal-fade-leave-active .payment-modal{transition:transform .2s,opacity .2s}.modal-fade-enter-from,.modal-fade-leave-to{opacity:0}.modal-fade-enter-from .payment-modal,.modal-fade-leave-to .payment-modal{opacity:0;transform:translateY(10px) scale(.985)}.notice-enter-active,.notice-leave-active{transition:opacity .18s,transform .18s}.notice-enter-from,.notice-leave-to{opacity:0;transform:translate(-50%,-8px)}
@media(max-width:1280px){.records-toolbar{align-items:flex-start;flex-direction:column}.store-filter-area{width:100%}.store-slider{max-width:none;flex:1}.toolbar-actions{align-self:flex-end}.basic-grid,.payment-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.other-grid{grid-template-columns:.7fr 1.3fr}.other-grid .form-field:last-child{grid-column:1/-1}}
@media(max-width:780px){.records-toolbar,.store-filter-area{align-items:stretch}.store-filter-area{flex-direction:column}.toolbar-actions{width:100%;flex-wrap:wrap}.modal-overlay{padding:0}.payment-modal{width:100vw;height:100vh;max-height:100vh;border:0;border-radius:0}.basic-grid,.payment-grid,.other-grid,.account-preview{grid-template-columns:1fr}.account-preview div{padding:0 0 10px;border-right:0;border-bottom:1px solid #e2e8f0}.modal-footer{align-items:stretch;flex-direction:column}.modal-actions{justify-content:flex-end}}
</style>
