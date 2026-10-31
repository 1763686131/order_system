<template>
  <div class="payment-history-page">
    <nav v-if="paymentMode && canRefund" class="history-tabs" role="tablist" aria-label="付款历史视图">
      <button v-if="user.hasPerm('admin.route.finance.supplier_payments')" :class="{ active: !refundTab }" role="tab" :aria-selected="!refundTab" @click="setHistoryTab('')">付款历史</button>
      <button :class="{ active: refundTab }" role="tab" :aria-selected="refundTab" @click="setHistoryTab('refund')">退款入账</button>
    </nav>
    <SupplierRefundPanel v-if="refundTab && canRefund" />
    <template v-else>
    <section class="records-panel">
      <header class="records-toolbar">
        <div class="store-filter-area">
          <span class="toolbar-label">{{ paymentMode ? '付款门店' : '收款门店' }}</span>
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
            :title="`刷新${historyLabel}`"
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
          <button v-if="canAction('create')" class="button button-primary" type="button" @click="openCreateModal">
            <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"></path></svg>
            新增{{ documentLabel }}
          </button>
        </div>
      </header>
      <form v-if="paymentMode" class="history-filters" @submit.prevent="loadData">
        <label>单号 / 供应商<input v-model.trim="paymentFilters.keyword" type="search" /></label>
        <label>状态<select v-model="paymentFilters.status"><option value="">全部</option><option v-for="status in ['draft', 'audited', 'reversed', 'cancelled']" :key="status" :value="status">{{ statusLabel(status) }}</option></select></label>
        <label>开始日期<input v-model="paymentFilters.startDate" type="date" /></label>
        <label>结束日期<input v-model="paymentFilters.endDate" type="date" /></label>
        <button class="button button-primary" :disabled="loading"><Search :size="16" />查询</button>
        <label class="invoice-rule"><input v-model="supplierOptions.paymentRequireInvoice" type="checkbox" :disabled="ruleSaving || !user.hasPerm('admin.finance.supplier_payment.rules')" @change="saveInvoiceRule" />见票付款</label>
      </form>

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
                  :aria-label="`选择当前页全部${documentLabel}`"
                  @change="togglePageSelection"
                >
              </th>
              <th>单据日期</th>
              <th>单据编号</th>
              <th>{{ paymentMode ? '供应商' : '客户' }}</th>
              <th class="money-cell">{{ paymentMode ? '付款金额' : '收款金额' }}</th>
              <th :class="{ 'money-cell': !paymentMode }">{{ paymentMode ? '付款账户' : '优惠金额' }}</th>
              <th class="money-cell">{{ paymentMode ? '抵扣应付' : '核销金额' }}</th>
              <th class="money-cell">{{ paymentMode ? '新增预付款' : '本次预收' }}</th>
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
                <strong>没有符合条件的{{ paymentMode ? '付款' : '收款' }}记录</strong>
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
                <button class="document-number" type="button" @click="paymentMode ? openPayment(item.id) : printReceipt(item)">
                  {{ item.documentNo }}
                  <svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
                </button>
              </td>
              <td class="customer-cell" :title="customerTitle(item)">
                <strong>{{ item.partyName || item.customerName || '-' }}</strong>
                <span>{{ item.storeName || '-' }} · #{{ item.customerCode || item.customerId }}</span>
              </td>
              <td class="money-cell amount-main">{{ formatMoney(item.paymentAmount) }}</td>
              <td :class="paymentMode ? 'account-cell' : 'money-cell amount-discount'" :title="item.accountName">{{ paymentMode ? item.accountName || '-' : formatMoney(item.discountAmount) }}</td>
              <td class="money-cell amount-main">{{ formatMoney(item.writeoffAmount) }}</td>
              <td class="money-cell amount-advance">{{ formatMoney(item.advanceAmount) }}</td>
              <td>{{ item.creator || '-' }}</td>
              <td class="center-cell">
                <span :class="['status-badge', `status-${item.status}`]">
                  <i></i>{{ statusLabel(item.status) }}
                </span>
              </td>
              <td :title="item.remark || '-'">{{ item.remark || '-' }}</td>
              <td class="operation-cell">
                <div class="row-actions">
                  <button
                    v-if="isDraft(item) && canAction('audit')"
                    class="action-button action-audit"
                    type="button"
                    :disabled="busyId === item.id"
                    @click="auditReceipt(item)"
                  >
                    审核
                  </button>
                  <button
                    v-else-if="item.status === 'audited' && !item.lockedAt && canAction('reverse_audit')"
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
                    v-if="isDraft(item) && canAction('edit')"
                    class="action-button action-edit"
                    type="button"
                    @click="openEditModal(item)"
                  >
                    修改
                  </button>
                  <button
                    v-if="isDraft(item) && canAction('delete')"
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
              <td :class="{ 'money-cell': !paymentMode }">{{ paymentMode ? '' : formatMoney(totals.discountAmount) }}</td>
              <td class="money-cell">{{ formatMoney(totals.writeoffAmount) }}</td>
              <td class="money-cell">{{ formatMoney(totals.advanceAmount) }}</td>
              <td colspan="4"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <footer class="table-footer">
        <span>共 <strong>{{ filteredReceipts.length }}</strong> 条{{ paymentMode ? '付款' : '收款' }}记录</span>
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
    </template>
    <SupplierDocumentDialog v-if="paymentDialogOpen && paymentMode" :key="paymentDocumentId || 'new-payment'" mode="payment" :document-id="paymentDocumentId" :options="supplierOptions" :initial-supplier-id="paymentSupplierId" :initial-store-id="paymentStoreId" @close="closePayment" @updated="loadData" />
    <CustomModal :visible="Boolean(confirmation)" :title="confirmation?.title || (confirmation?.action === 'audit' ? '审核付款单' : confirmation?.action === 'delete' ? '删除付款单' : '反审核付款单')" :message="confirmation?.message || ''" :danger="confirmation?.action !== 'audit'" :confirm-disabled="Boolean(busyId)" @confirm="performPaymentAction" @cancel="cancelConfirmation" />

    <FinanceDocumentDialog
      v-if="modalVisible"
      :title="`${editingId ? '修改收款单' : '收款单'}${form.documentNo ? ` · ${form.documentNo}` : ''}`"
      aria-label="收款单"
      form-id="receipt-document-form"
      close-label="取消"
      :busy="saving"
      @close="closeModal"
      @submit="saveReceipt"
    >
      <fieldset class="sf-plain-fieldset sf-form-grid" :disabled="saving">
        <label class="sf-field">
          门店
          <select v-model.number="form.storeId" required @change="handleReceiptStoreChange">
            <option value="">请先选择门店</option>
            <option v-for="store in activeStores" :key="store.id" :value="store.id">{{ store.name }}</option>
            <option v-if="form.storeId && !stores.some(store => Number(store.id) === Number(form.storeId))" :value="form.storeId">
              {{ form.storeName || form.storeId }}
            </option>
          </select>
        </label>
        <label class="sf-field">
          客户
          <select v-model.number="form.customerId" required :disabled="!form.storeId" @change="handleCustomerChange">
            <option value="">{{ form.storeId ? '请选择客户' : '请先选择门店' }}</option>
            <option v-for="customer in modalCustomers" :key="customer.id" :value="customer.id">
              {{ customer.customerName }}
            </option>
          </select>
        </label>
        <label class="sf-field">欠款金额<input class="receipt-debt" :value="formatMoney(currentDebt)" readonly></label>
        <label class="sf-field">单据编号<input :value="form.documentNo || '保存时自动生成'" readonly></label>
        <label class="sf-field">单据日期<input v-model="form.documentDate" type="date" required @change="loadNextNumber"></label>
        <label class="sf-field">
          结算账户
          <select v-model="form.settlementAccount">
            <option value="">请选择结算账户</option>
            <option
              v-if="form.settlementAccount && !customerBankAccounts.some(account => (account.value || account.accountName) === form.settlementAccount)"
              :value="form.settlementAccount"
            >
              {{ form.settlementAccount }}
            </option>
            <option v-for="account in customerBankAccounts" :key="account.id" :value="account.value || account.accountName">
              {{ account.label || account.accountName }}
            </option>
          </select>
        </label>
        <label class="sf-field">收款方式<input v-model.trim="form.paymentMethod" maxlength="30" placeholder="微信、银行转账等"></label>
        <label class="sf-field">本次实际收款<input v-model="form.paymentAmount" type="number" min="0.01" step="0.01" required placeholder="0.00"></label>
        <label class="sf-field">优惠金额<input v-model="form.discountAmount" type="number" min="0" step="0.01" placeholder="0.00"></label>
        <label class="sf-field">合计金额<input :value="formatMoney(formTotal)" readonly></label>
        <label class="sf-field">制单人<input v-model.trim="form.creator" maxlength="30"></label>
        <label class="sf-field wide">备注<textarea v-model.trim="form.remark" maxlength="300" placeholder="可填写收款说明、银行流水号等"></textarea></label>
      </fieldset>
      <section class="receipt-allocation">
        <header class="receipt-allocation-header">
          <div>
            <h3>收款抵扣明细</h3>
            <span class="sf-muted">已选 {{ selectedReceivableKeys.length }} / {{ receivableDocuments.length }} 笔</span>
          </div>
          <div class="receipt-allocation-mode" role="group" aria-label="收款抵扣方式">
            <button
              class="sf-button"
              type="button"
              title="按单据日期从早到晚自动抵扣"
              :aria-pressed="receiptAllocationMode === 'fifo'"
              :disabled="saving || receivableLoading"
              @click="receiptAllocationMode = 'fifo'"
            >
              <ListChecks :size="16" />自动抵扣
            </button>
            <button
              class="sf-button"
              type="button"
              :aria-pressed="receiptAllocationMode === 'manual'"
              :disabled="saving || receivableLoading"
              @click="receiptAllocationMode = 'manual'"
            >
              <SquareCheck :size="16" />手动抵扣
            </button>
          </div>
        </header>
        <div v-if="receivableLoading" class="sf-empty">正在加载欠款单据...</div>
        <div v-else-if="receivableError" class="receipt-allocation-error" role="alert">
          <span class="sf-error">{{ receivableError }}</span>
          <button class="sf-button" type="button" :disabled="saving" @click="loadReceivableDocuments(form.customerId)"><RefreshCw :size="16" />重试</button>
        </div>
        <div v-else-if="!form.customerId" class="sf-empty">选择客户后加载欠款单据</div>
        <div v-else-if="!receivableDocuments.length" class="sf-empty">当前没有未抵扣欠款</div>
        <div v-else class="sf-table-scroll receipt-allocation-scroll">
          <table class="sf-table receipt-allocation-table">
            <thead>
              <tr>
                <th class="receipt-check-column"><span class="visually-hidden">选择</span></th>
                <th>欠款单据</th>
                <th class="sf-number">单据金额</th>
                <th class="sf-number">未抵扣金额</th>
                <th class="sf-number">本次抵扣</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="document in receivableDocuments" :key="receivableKey(document)">
                <td>
                  <input
                    v-model="selectedReceivableKeys"
                    type="checkbox"
                    :value="receivableKey(document)"
                    :aria-label="`选择抵扣单据 ${document.documentNo}`"
                    :disabled="saving || receiptAllocationMode !== 'manual' || Number(document.outstandingAmount) <= 0"
                  >
                </td>
                <td>
                  <strong>{{ document.documentNo }}</strong>
                  <span class="receipt-document-date">{{ document.documentDate || '-' }}</span>
                </td>
                <td class="sf-number">{{ formatMoney(document.amount) }}</td>
                <td class="sf-number">{{ formatMoney(document.outstandingAmount) }}</td>
                <td class="sf-number receipt-allocation-amount">
                  {{ formatMoney(allocationAmountByKey[receivableKey(document)] || 0) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="sf-muted receipt-allocation-hint">未抵扣的实收金额转为预收款。</p>
      </section>
      <div class="sf-summary">
        <span>实际收款<strong>{{ formatMoney(form.paymentAmount) }}</strong></span>
        <span>预计核销欠款<strong>{{ formatMoney(previewWriteoff) }}</strong></span>
        <span>预计转入预收<strong>{{ formatMoney(previewAdvance) }}</strong></span>
      </div>
      <p :class="Number(form.discountAmount) > previewWriteoff ? 'sf-error' : 'sf-muted'">
        {{ Number(form.discountAmount) > previewWriteoff ? '抵扣金额不能覆盖优惠金额，请检查金额或所选单据。' : receiptAllocationMode === 'manual' ? '按已选单据抵扣，审核时会复核单据余额。' : '按单据日期从早到晚自动抵扣，审核时以最新欠款为准。' }}
      </p>
      <div class="sf-attachments">
        <div class="sf-actions">
          <strong>附件</strong>
          <button type="button" class="sf-button" :disabled="saving" @click="attachmentInput?.click()">
            <Paperclip :size="16" />{{ attachmentPreview ? '更换附件' : '添加附件' }}
          </button>
          <input ref="attachmentInput" class="sf-file-input" type="file" accept="image/jpeg,image/png,image/webp,image/gif" :disabled="saving" @change="handleAttachment">
          <span class="sf-muted">{{ attachmentPreview ? '图片最大 10MB' : '暂无附件，图片最大 10MB' }}</span>
        </div>
        <ul v-if="attachmentPreview" class="sf-attachment-list">
          <li>
            <a class="receipt-attachment-preview" :href="attachmentPreview" target="_blank" rel="noopener">
              <img :src="attachmentPreview" alt="收款附件预览">
            </a>
            <button class="sf-button icon danger" type="button" title="移除附件" aria-label="移除附件" :disabled="saving" @click="removeAttachment"><X :size="16" /></button>
          </li>
        </ul>
      </div>
      <p class="sf-muted">保存后是待审核草稿，不会立即改变客户账户。</p>
      <template #actions>
        <button class="sf-button primary" type="submit" form="receipt-document-form" :disabled="saving || receivableLoading || Boolean(receivableError)">
          <Save :size="16" />{{ saving ? '保存中...' : '保存草稿' }}
        </button>
      </template>
    </FinanceDocumentDialog>

    <Teleport to="body">
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
import { useRoute, useRouter } from 'vue-router'
import { ListChecks, Paperclip, RefreshCw, Save, Search, SquareCheck, X } from '@lucide/vue'
import * as XLSX from 'xlsx'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { documentStatusLabels, operationKey } from '@/utils/supplierFinance'
import SupplierDocumentDialog from '@/components/admin/purchase/SupplierDocumentDialog.vue'
import SupplierRefundPanel from '@/components/admin/finance/SupplierRefundPanel.vue'
import CustomModal from '@/components/CustomModal.vue'
import FinanceDocumentDialog from '@/components/common/FinanceDocumentDialog.vue'

const props = defineProps({ mode: { type: String, default: 'receipt', validator: value => ['receipt', 'payment'].includes(value) } })
const route = useRoute()
const router = useRouter()
const user = useUserStore()
const paymentMode = computed(() => props.mode === 'payment')
const documentLabel = computed(() => paymentMode.value ? '付款单' : '收款单')
const historyLabel = computed(() => paymentMode.value ? '付款历史' : '收款历史')
const canRefund = computed(() => paymentMode.value && user.hasPerm('admin.route.finance.supplier_refunds'))
const refundTab = computed(() => paymentMode.value && route.query.tab === 'refund')
const supplierOptions = ref({ stores: [], suppliers: [], bankAccounts: [], paymentRequireInvoice: false })
const paymentFilters = reactive({ keyword: '', status: '', startDate: '', endDate: '' })
const paymentDialogOpen = ref(false)
const paymentDocumentId = ref(null)
const paymentSupplierId = ref(null)
const paymentStoreId = ref(null)
const ruleSaving = ref(false)
const confirmation = ref(null)
const actionKeys = new Map()
let receiptConfirmationResolver = null
function confirmReceipt(message, title, action) {
  cancelConfirmation()
  confirmation.value = { message, title, action }
  return new Promise(resolve => { receiptConfirmationResolver = resolve })
}
function cancelConfirmation() {
  confirmation.value = null
  receiptConfirmationResolver?.(false)
  receiptConfirmationResolver = null
}
const canAction = action => !paymentMode.value || user.hasPerm(`admin.finance.supplier_payment.${action}`)
const statusLabel = status => paymentMode.value ? documentStatusLabels[status] || status : status === 'audited' ? '已审核' : '待审核'
const isDraft = item => !item.lockedAt && (item.status === 'draft' || paymentMode.value && item.status === 'reversed')
function setHistoryTab(tab) {
  paymentDialogOpen.value = false
  const query = { ...route.query, tab: tab || undefined }
  delete query.documentId; delete query.create; delete query.supplierId
  router.replace({ query })
}
function openPayment(id = null) {
  paymentDocumentId.value = id
  paymentSupplierId.value = route.query.supplierId ? Number(route.query.supplierId) : null
  paymentStoreId.value = selectedStoreId.value || (route.query.storeId ? Number(route.query.storeId) : null)
  paymentDialogOpen.value = true
}
function closePayment() {
  paymentDialogOpen.value = false
  const query = { ...route.query }
  delete query.documentId; delete query.create; delete query.supplierId
  router.replace({ query })
}
async function saveInvoiceRule() {
  ruleSaving.value = true
  try { await request.put('/supplier-finance/rules', { paymentRequireInvoice: supplierOptions.value.paymentRequireInvoice }) }
  catch (err) { supplierOptions.value.paymentRequireInvoice = !supplierOptions.value.paymentRequireInvoice; showNotice(errorMessage(err, '规则保存失败'), 'error') }
  finally { ruleSaving.value = false }
}
const receipts = ref([])
const stores = ref([])
const customers = ref([])
const bankAccounts = ref([])
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
const receivableDocuments = ref([])
const selectedReceivableKeys = ref([])
const receiptAllocationMode = ref('fifo')
const receivableLoading = ref(false)
const loadedReceivableDebt = ref(null)
const receivableError = ref('')
let noticeTimer = null
let loadRequestToken = 0
let receivableRequestToken = 0
let modalRequestToken = 0

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
  storeId: '',
  storeName: '',
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
  if (!form.storeId) return []
  return customers.value.filter(
    customer => Number(customer.storeId) === Number(form.storeId)
  )
})
const selectedCustomer = computed(() =>
  modalCustomers.value.find(customer => Number(customer.id) === Number(form.customerId))
)
const customerBankAccounts = computed(() => {
  return bankAccounts.value
    .filter(account => Number(account.storeId) === Number(form.storeId))
    .slice()
    .sort((a, b) => Number(Boolean(b.isDefault)) - Number(Boolean(a.isDefault)))
})
const currentDebt = computed(() =>
  Math.max(0, Number(loadedReceivableDebt.value ?? selectedCustomer.value?.receivable) || 0)
)
const receivableDocumentsTotal = computed(() => receivableDocuments.value.reduce(
  (total, document) => total + (Number(document.outstandingAmount) || 0), 0
))
const formTotal = computed(() =>
  Math.max(0, Number(form.paymentAmount) || 0) +
  Math.max(0, Number(form.discountAmount) || 0)
)
const allocationTarget = computed(() => Math.min(
  currentDebt.value,
  receivableDocumentsTotal.value,
  formTotal.value
))
const allocationPreview = computed(() => {
  let remaining = Math.round(allocationTarget.value * 100)
  const allocations = []
  const documentsByKey = new Map(receivableDocuments.value.map(document => [receivableKey(document), document]))
  for (const key of selectedReceivableKeys.value) {
    const document = documentsByKey.get(key)
    if (!document) continue
    const available = Math.max(0, Math.round((Number(document.outstandingAmount) || 0) * 100))
    const amount = Math.min(remaining, available)
    if (amount > 0) {
      allocations.push({
        sourceType: document.sourceType,
        sourceId: document.sourceId,
        documentNo: document.documentNo,
        amount: amount / 100
      })
      remaining -= amount
    }
    if (remaining <= 0) break
  }
  return allocations
})
const allocationAmountByKey = computed(() => Object.fromEntries(
  allocationPreview.value.map(allocation => [
    receivableKey(allocation), allocation.amount
  ])
))
const previewWriteoff = computed(() => allocationPreview.value.reduce(
  (total, allocation) => total + Math.round(allocation.amount * 100), 0
) / 100)
const previewAdvance = computed(() => {
  const payment = Math.max(0, Number(form.paymentAmount) || 0)
  const discount = Math.max(0, Number(form.discountAmount) || 0)
  const cashWriteoff = Math.max(0, previewWriteoff.value - discount)
  return Math.max(0, Math.round((payment - cashWriteoff) * 100) / 100)
})

function receivableKey(document) {
  return `${document.sourceType}:${document.sourceId}`
}

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
  const requestToken = ++loadRequestToken
  loading.value = true
  try {
    if (paymentMode.value) {
      if (!user.hasPerm('admin.route.finance.supplier_payments')) return
      const [options, payments] = await Promise.all([
        request.get('/supplier-finance/options'),
        request.get('/supplier-payments', { params: paymentFilters })
      ])
      if (requestToken !== loadRequestToken) return
      supplierOptions.value = options
      stores.value = options.stores || []
      receipts.value = (payments.items || []).map(row => ({
        ...row, partyName: row.supplierName, customerCode: row.supplierId,
        documentDate: row.businessDate, creator: row.createdBy,
        writeoffAmount: row.allocatedAmount, customerName: row.supplierName,
        settlementAccount: row.accountName, discountAmount: 0
      }))
      selectedIds.value = selectedIds.value.filter(id => receipts.value.some(item => item.id === id))
      return
    }
    const [storeResponse, customerResponse, receiptResponse, bankAccountResponse] = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/customers', method: 'GET', params: { status: 'active' } }),
      request({ url: '/payment-receipts', method: 'GET' }),
      request({ url: '/bank-accounts/options', method: 'GET' })
    ])
    if (requestToken !== loadRequestToken) return
    stores.value = Array.isArray(storeResponse) ? storeResponse : []
    customers.value = Array.isArray(customerResponse) ? customerResponse : []
    receipts.value = Array.isArray(receiptResponse?.items) ? receiptResponse.items : []
    bankAccounts.value = Array.isArray(bankAccountResponse?.data)
      ? bankAccountResponse.data
      : (Array.isArray(bankAccountResponse?.items) ? bankAccountResponse.items : [])
    selectedIds.value = selectedIds.value.filter(id =>
      receipts.value.some(item => item.id === id)
    )
  } catch (error) {
    if (requestToken !== loadRequestToken) return
    console.error(`加载${historyLabel.value}失败:`, error)
    showNotice(errorMessage(error, `加载${historyLabel.value}失败`), 'error')
  } finally {
    if (requestToken === loadRequestToken) loading.value = false
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
  ++modalRequestToken
  ++receivableRequestToken
  receivableDocuments.value = []
  selectedReceivableKeys.value = []
  receiptAllocationMode.value = 'fifo'
  loadedReceivableDebt.value = null
  receivableError.value = ''
  receivableLoading.value = false
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
  if (paymentMode.value) { openPayment(); return }
  resetForm()
  if (selectedStoreId.value !== null) {
    form.storeId = selectedStoreId.value
    form.storeName = stores.value.find(store => Number(store.id) === selectedStoreId.value)?.name || ''
  }
  modalVisible.value = true
  await loadNextNumber()
}
const openQueryCreate = async () => {
  if (paymentMode.value) {
    if (route.query.documentId && !refundTab.value) openPayment(Number(route.query.documentId))
    else if (route.query.create === '1' && !refundTab.value) openPayment()
    return
  }
  if (route.query.create !== '1') return
  resetForm()
  if (route.query.customerId) {
    const customer = customers.value.find(item => Number(item.id) === Number(route.query.customerId))
    if (customer) {
      form.storeId = customer.storeId
      form.storeName = customer.storeName || ''
      form.customerId = customer.id
    }
  } else if (selectedStoreId.value !== null) {
    form.storeId = selectedStoreId.value
    form.storeName = stores.value.find(store => Number(store.id) === selectedStoreId.value)?.name || ''
  }
  modalVisible.value = true
  await handleCustomerChange()
  await loadNextNumber()
}
const openEditModal = async item => {
  if (paymentMode.value) { openPayment(item.id); return }
  resetForm()
  const requestToken = modalRequestToken
  try {
    const receipt = await request.get(`/payment-receipts/${item.id}`)
    if (requestToken !== modalRequestToken) return
    editingId.value = receipt.id
    Object.assign(form, {
      documentNo: receipt.documentNo,
      documentDate: receipt.documentDate,
      storeId: receipt.storeId,
      storeName: receipt.storeName,
      customerId: receipt.customerId,
      settlementAccount: receipt.settlementAccount,
      paymentMethod: receipt.paymentMethod,
      paymentAmount: receipt.paymentAmount,
      discountAmount: receipt.discountAmount,
      creator: receipt.creator || '王醒',
      remark: receipt.remark || '',
      attachmentUrl: receipt.attachmentUrl || ''
    })
    attachmentPreview.value = receipt.attachmentUrl || ''
    receiptAllocationMode.value = receipt.allocationMode === 'manual' ? 'manual' : 'fifo'
    modalVisible.value = true
    const loaded = await loadReceivableDocuments(receipt.customerId)
    if (!loaded || requestToken !== modalRequestToken || Number(form.customerId) !== Number(receipt.customerId)) return
    if (receipt.allocationMode === 'manual') {
      const savedKeys = (receipt.allocations || []).map(receivableKey)
      const openKeys = new Set(receivableDocuments.value.map(receivableKey))
      selectedReceivableKeys.value = savedKeys.filter(key => openKeys.has(key))
      if (savedKeys.some(key => !openKeys.has(key))) {
        receivableError.value = '草稿中有单据已结清或欠款已变化，请刷新欠款明细后重新选择。'
      }
    } else {
      selectOldestReceivables(allocationTarget.value)
    }
  } catch (error) {
    if (requestToken !== modalRequestToken) return
    showNotice(errorMessage(error, '加载收款单失败'), 'error')
  }
}
const closeModal = () => {
  if (saving.value) return
  modalVisible.value = false
  resetForm()
  if (route.query.create || route.query.customerId) {
    const query = { ...route.query }
    delete query.create
    delete query.customerId
    router.replace({ query })
  }
}
const handleReceiptStoreChange = () => {
  ++receivableRequestToken
  receiptAllocationMode.value = 'fifo'
  receivableDocuments.value = []
  selectedReceivableKeys.value = []
  loadedReceivableDebt.value = null
  receivableError.value = ''
  receivableLoading.value = false
  form.storeName = stores.value.find(store => Number(store.id) === Number(form.storeId))?.name || ''
  form.customerId = ''
  form.settlementAccount = ''
}
const loadReceivableDocuments = async customerId => {
  const requestToken = ++receivableRequestToken
  receivableDocuments.value = []
  selectedReceivableKeys.value = []
  loadedReceivableDebt.value = null
  receivableError.value = ''
  if (!customerId) {
    receivableLoading.value = false
    return true
  }
  receivableLoading.value = true
  try {
    const response = await request.get(`/customers/${customerId}/receivable-documents`)
    if (requestToken !== receivableRequestToken || Number(form.customerId) !== Number(customerId)) return false
    receivableDocuments.value = Array.isArray(response?.items) ? response.items : []
    loadedReceivableDebt.value = Number(response?.receivable) || 0
    return true
  } catch (error) {
    if (requestToken !== receivableRequestToken) return false
    receivableError.value = errorMessage(error, '加载客户欠款单据失败')
    return false
  } finally {
    if (requestToken === receivableRequestToken) receivableLoading.value = false
  }
}
const selectOldestReceivables = amount => {
  let remaining = Math.max(0, Math.round((Number(amount) || 0) * 100))
  const selected = []
  for (const document of receivableDocuments.value) {
    if (remaining <= 0) break
    const outstanding = Math.max(0, Math.round((Number(document.outstandingAmount) || 0) * 100))
    if (!outstanding) continue
    selected.push(receivableKey(document))
    remaining -= outstanding
  }
  selectedReceivableKeys.value = selected
}
const handleCustomerChange = async () => {
  receiptAllocationMode.value = 'fifo'
  const store = stores.value.find(
    item => Number(item.id) === Number(form.storeId)
  )
  const account = customerBankAccounts.value.find(item => item.isDefault) ||
    customerBankAccounts.value[0]
  form.settlementAccount = account?.value || account?.accountName || (
    store ? `${store.name}结算账户` : ''
  )
  await loadReceivableDocuments(form.customerId)
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
  if (saving.value || receivableLoading.value || receivableError.value) return
  let validationError = ''
  if (!form.customerId) validationError = '请选择客户'
  else if (!form.documentDate) validationError = '请选择单据日期'
  else if (!(Number(form.paymentAmount) > 0)) validationError = '收款金额必须大于0'
  else if (Number(form.discountAmount) < 0) validationError = '优惠金额不能小于0'
  else if (Number(form.discountAmount) > previewWriteoff.value) {
    validationError = '已选单据的抵扣金额不能覆盖优惠金额，请增加抵扣单据'
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
      allocationMode: receiptAllocationMode.value,
      allocations: receiptAllocationMode.value === 'manual' ? allocationPreview.value.map(({ sourceType, sourceId, amount }) => ({
        sourceType,
        sourceId,
        amount
      })) : [],
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
    if (route.query.create || route.query.customerId) {
      const query = { ...route.query }
      delete query.create; delete query.customerId
      router.replace({ query })
    }
    await loadData()
  } catch (error) {
    console.error('保存收款单失败:', error)
    showNotice(errorMessage(error, '保存收款单失败'), 'error')
  } finally {
    saving.value = false
  }
}

const auditReceipt = async item => {
  if (paymentMode.value) {
    confirmation.value = {
      action: 'audit', item,
      message: `审核付款单 ${item.documentNo}？将扣减账户 ${formatMoney(item.paymentAmount)}，并自动抵扣最新应付欠款，超出欠款的部分转为预付款。`
    }
    return
  }
  const prompt = [
    `确定审核收款单 ${item.documentNo} 吗？`,
    `实收 ${formatMoney(item.paymentAmount)}，优惠 ${formatMoney(item.discountAmount)}。`,
    item.allocationMode === 'manual'
      ? `按已选单据抵扣 ${formatMoney(item.writeoffAmount)}，转入预收 ${formatMoney(item.advanceAmount)}；审核时会复核单据余额。`
      : '审核后会立即核销客户欠款，多收金额转为客户储值。'
  ].join('\n')
  if (!await confirmReceipt(prompt, '审核收款单', 'audit')) return
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
  if (paymentMode.value) { confirmation.value = { action: 'reverse-audit', item, message: `反审核付款单 ${item.documentNo}？将恢复银行余额和应付核销，已使用的预付款需先撤销后续核销。` }; return }
  if (!await confirmReceipt(`确定反审核收款单 ${item.documentNo} 吗？\n系统会恢复本单核销的欠款并撤回本单预收。`, '反审核收款单', 'reverse-audit')) return
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
  if (paymentMode.value) { confirmation.value = { action: 'delete', item, message: `删除付款单 ${item.documentNo}？有审核历史的单据将保留为已作废记录。` }; return }
  if (!await confirmReceipt(`确定删除待审核收款单 ${item.documentNo} 吗？`, '删除收款单', 'delete')) return
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
    <title>${documentLabel.value} ${escapeHtml(item.documentNo)}</title>
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
    <h1>${documentLabel.value}</h1><p class="sub">${escapeHtml(item.storeName)} · ${escapeHtml(item.documentNo)}</p>
    <section class="meta">
      <div><span>单据日期</span><strong>${escapeHtml(item.documentDate)}</strong></div>
      <div><span>${paymentMode.value ? '供应商' : '客户'}</span><strong>${escapeHtml(item.customerName)}</strong></div>
      <div><span>审核状态</span><strong>${statusLabel(item.status)}</strong></div>
      <div><span>结算账户</span><strong>${escapeHtml(item.settlementAccount || '-')}</strong></div>
      <div><span>${paymentMode.value ? '付款方式' : '收款方式'}</span><strong>${escapeHtml(item.paymentMethod || '-')}</strong></div>
      <div><span>制单人</span><strong>${escapeHtml(item.creator || '-')}</strong></div>
    </section>
    <table><thead><tr><th>金额项目</th><th>${paymentMode.value ? '付款金额' : '收款金额'}</th>${paymentMode.value ? '' : '<th>优惠金额</th>'}<th>${paymentMode.value ? '抵扣应付' : '核销金额'}</th><th>${paymentMode.value ? '新增预付款' : '本次预收'}</th></tr></thead>
    <tbody><tr><td>本次${paymentMode.value ? '付款' : '收款'}</td><td>${formatMoney(item.paymentAmount)}</td>${paymentMode.value ? '' : `<td>${formatMoney(item.discountAmount)}</td>`}<td>${formatMoney(item.writeoffAmount)}</td><td>${formatMoney(item.advanceAmount)}</td></tr></tbody></table>
    <div class="remark">备注：${escapeHtml(item.remark || '无')}</div>${attachment}
    <div class="sign"><span>${paymentMode.value ? '供应商' : '客户'}签字：________________</span><span>经办人：${escapeHtml(item.creator || '王醒')}</span></div>
    <script>window.addEventListener('load',()=>window.print())<\/script></body></html>
  `)
  printWindow.document.close()
}

const exportExcel = () => {
  if (!filteredReceipts.value.length) {
    showNotice(`当前没有可导出的${paymentMode.value ? '付款' : '收款'}记录`, 'error')
    return
  }
  const rows = filteredReceipts.value.map(item => ({
    '单据日期': item.documentDate,
    '单据编号': item.documentNo,
    '门店': item.storeName,
    [paymentMode.value ? '供应商' : '客户']: item.customerName,
    [paymentMode.value ? '供应商编号' : '客户编号']: item.customerCode || item.customerId,
    [paymentMode.value ? '付款金额' : '收款金额']: Number(item.paymentAmount) || 0,
    ...(paymentMode.value ? {} : { '优惠金额': Number(item.discountAmount) || 0 }),
    [paymentMode.value ? '抵扣应付' : '核销金额']: Number(item.writeoffAmount) || 0,
    [paymentMode.value ? '新增预付款' : '本次预收']: Number(item.advanceAmount) || 0,
    '制单人': item.creator,
    '审核状态': statusLabel(item.status),
    [paymentMode.value ? '付款方式' : '收款方式']: item.paymentMethod,
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
  XLSX.utils.book_append_sheet(workbook, sheet, historyLabel.value)
  const storeName = selectedStoreId.value === null
    ? '全部门店'
    : activeStores.value.find(store => store.id === selectedStoreId.value)?.name || '门店'
  XLSX.writeFile(workbook, `${historyLabel.value}-${storeName}-${todayText()}.xlsx`)
  showNotice(`已导出 ${rows.length} 条${paymentMode.value ? '付款' : '收款'}记录`)
}
async function performPaymentAction() {
  if (receiptConfirmationResolver) {
    confirmation.value = null
    receiptConfirmationResolver(true)
    receiptConfirmationResolver = null
    return
  }
  if (!confirmation.value || busyId.value) return
  const { action, item } = confirmation.value
  const permission = action === 'reverse-audit' ? 'reverse_audit' : action
  if (!canAction(permission)) return
  const key = `${action}:${item.id}:${item.version}`
  if (!actionKeys.has(key)) actionKeys.set(key, operationKey())
  busyId.value = item.id
  confirmation.value = null
  try {
    await request({ url: `/supplier-payments/${item.id}${action === 'delete' ? '' : `/${action}`}`, method: action === 'delete' ? 'DELETE' : 'POST', data: { version: item.version, idempotencyKey: actionKeys.get(key) } })
    await loadData()
    showNotice(action === 'audit' ? '付款审核成功' : action === 'delete' ? '付款单已删除' : '反审核成功')
  } catch (err) { showNotice(errorMessage(err, '操作失败'), 'error') }
  finally { busyId.value = null }
}

watch([allocationTarget, receivableDocuments, receiptAllocationMode], () => {
  if (receiptAllocationMode.value === 'fifo') selectOldestReceivables(allocationTarget.value)
}, { flush: 'sync' })
watch(totalPages, pages => {
  if (currentPage.value > pages) currentPage.value = pages
})
watch(modalVisible, visible => {
  document.body.style.overflow = visible ? 'hidden' : ''
})
onMounted(async () => {
  selectedStoreId.value = route.query.storeId ? Number(route.query.storeId) : null
  await loadData()
  await openQueryCreate()
})
watch(() => route.query.create, value => {
  if (value === '1') openQueryCreate()
})
watch(() => route.query.documentId, id => { if (paymentMode.value && id && !refundTab.value) openPayment(Number(id)) })
watch(() => props.mode, async () => {
  cancelConfirmation()
  resetForm()
  Object.assign(paymentFilters, { keyword: '', status: '', startDate: '', endDate: '' })
  modalVisible.value = false; paymentDialogOpen.value = false; receipts.value = []; selectedIds.value = []
  selectedStoreId.value = route.query.storeId ? Number(route.query.storeId) : null
  currentPage.value = 1
  await loadData()
  await openQueryCreate()
})
onBeforeUnmount(() => {
  ++loadRequestToken
  ++receivableRequestToken
  ++modalRequestToken
  cancelConfirmation()
  document.body.style.overflow = ''
  clearLocalPreview()
  if (noticeTimer) window.clearTimeout(noticeTimer)
})
</script>

<style scoped>
.history-tabs { display: flex; gap: 8px; padding-bottom: 12px; }
.history-tabs button { height: 36px; padding: 0 16px; color: #596579; background: transparent; border: 0; border-bottom: 2px solid transparent; font: inherit; cursor: pointer; }
.history-tabs button.active { color: #08745a; border-color: #0f9f78; font-weight: 600; }
.history-filters { display: flex; flex-wrap: wrap; align-items: end; gap: 12px; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; }
.history-filters label { display: grid; gap: 5px; font-size: 12px; color: #596579; }
.history-filters input:not([type="checkbox"]), .history-filters select { height: 34px; max-width: 100%; padding: 0 8px; border: 1px solid #cbd5e1; border-radius: 5px; }
.history-filters .invoice-rule { display: flex; align-items: center; gap: 8px; height: 34px; }
.status-reversed { color: #a4510b; background: #fff3df; }.status-cancelled { color: #b4232f; background: #f1f2f4; }
.payment-history-page {
  --accent:#0f9f78;--accent-rgb:15,159,120;--accent-dark:#08745a;
  --accent-soft:#e9f8f3;--accent-border:#a9e5d2;--page-bg:#f4f7f8;
  --border:#e2e8f0;--border-strong:#cbd5e1;--text:#172033;
  --text-secondary:#596579;--text-muted:#8a96a8;
  width:100%;min-width:0;min-height:calc(100vh - 100px);overflow-x:hidden;color:var(--text);
  background:var(--page-bg);font-size:14px;
}
*{box-sizing:border-box}button,input,select,textarea{font:inherit}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
svg{fill:none;stroke:currentColor;stroke-linecap:round;stroke-linejoin:round;stroke-width:1.8}
.records-panel{width:100%;min-width:0;overflow:hidden;background:#fff;border:1px solid var(--border);border-radius:7px;box-shadow:0 3px 14px rgba(15,23,42,.045)}
.records-toolbar{display:flex;min-width:0;min-height:68px;align-items:center;justify-content:space-between;gap:20px;padding:11px 16px;border-bottom:1px solid var(--border)}
.store-filter-area{display:flex;min-width:0;align-items:center;gap:11px;flex:1 1 auto}.toolbar-label{flex:0 0 auto;color:var(--text-secondary);font-size:12px;font-weight:650}
.store-slider{display:flex;min-width:0;max-width:min(760px,52vw);align-items:center;gap:6px;overflow-x:auto;padding:4px;background:#f1f5f9;border-radius:8px;box-shadow:inset 0 1px 3px rgba(0,0,0,.08);scrollbar-width:thin}
.slider-tab{display:inline-flex;height:36px;flex:0 0 auto;align-items:center;gap:7px;padding:0 15px;color:var(--text-secondary);background:transparent;border:0;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap}
.slider-tab:hover{color:var(--accent-dark);background:rgba(var(--accent-rgb),.1)}.slider-tab.active{color:#fff;background:var(--accent);box-shadow:0 2px 6px rgba(var(--accent-rgb),.3)}
.count-badge{display:inline-flex;min-width:20px;height:20px;align-items:center;justify-content:center;padding:0 6px;background:rgba(0,0,0,.1);border-radius:10px;font-size:11px;font-weight:700}.slider-tab.active .count-badge{background:rgba(255,255,255,.25)}
.toolbar-actions,.row-actions,.pagination{display:flex;align-items:center;gap:8px}.toolbar-actions{flex:0 0 auto}.selected-hint{color:var(--text-secondary);font-size:12px}.selected-hint strong{color:var(--accent-dark)}
.button{display:inline-flex;height:38px;align-items:center;justify-content:center;gap:7px;padding:0 15px;border:1px solid transparent;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;white-space:nowrap}
.button:disabled{cursor:not-allowed;opacity:.5}.button svg{width:16px;height:16px}.button-primary{color:#fff;background:var(--accent);border-color:var(--accent);box-shadow:0 2px 5px rgba(var(--accent-rgb),.18)}.button-primary:hover:not(:disabled){background:var(--accent-dark)}
.button-secondary{color:#445066;background:#fff;border-color:var(--border-strong)}.button-secondary:hover{color:var(--accent-dark);background:var(--accent-soft);border-color:var(--accent-border)}
.icon-button{display:inline-flex;width:36px;height:36px;align-items:center;justify-content:center;padding:0;color:#667085;background:#fff;border:1px solid var(--border-strong);border-radius:5px;cursor:pointer}.icon-button:hover:not(:disabled){color:var(--accent-dark);background:var(--accent-soft)}.icon-button:disabled{opacity:.45}.icon-button svg{width:17px;height:17px}
.spinning{animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.table-scroll{width:100%;max-width:100%;min-width:0;overflow-x:auto;overscroll-behavior-x:contain}
.records-table{width:100%;min-width:1440px;border-collapse:collapse;table-layout:fixed}.checkbox-col{width:44px}.date-col{width:104px}.number-col{width:150px}.customer-col{width:170px}.money-col{width:112px}.creator-col{width:80px}.status-col{width:100px}.remark-col{width:130px}.operation-col{width:220px}
.records-table th{height:45px;padding:0 12px;color:#566176;background:#f8fafc;border-bottom:1px solid var(--border);font-size:12px;font-weight:650;text-align:left;white-space:nowrap}
.records-table td{height:57px;padding:9px 12px;overflow:hidden;color:#344054;border-bottom:1px solid #edf1f5;text-overflow:ellipsis;white-space:nowrap}.records-table tbody tr:hover{background:rgba(var(--accent-rgb),.08)}.records-table tbody tr.selected{background:rgba(var(--accent-rgb),.12)}
.center-cell,.operation-cell{text-align:center!important}.center-cell input{width:15px;height:15px;accent-color:var(--accent);cursor:pointer}.money-cell{text-align:right!important;font-variant-numeric:tabular-nums}
.document-number{display:inline-flex;max-width:100%;align-items:center;gap:4px;padding:0;overflow:hidden;color:var(--accent-dark);background:transparent;border:0;cursor:pointer;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.document-number:hover{text-decoration:underline}.document-number svg{width:13px;height:13px}
.customer-cell strong,.customer-cell span{display:block;overflow:hidden;text-overflow:ellipsis}.customer-cell span{margin-top:3px;color:var(--text-muted);font-size:11px}.amount-main{font-weight:700}.amount-discount{color:#a4510b!important;font-weight:650}.amount-advance{color:#07805f!important;font-weight:700}
.status-badge{display:inline-flex;min-height:25px;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:650}.status-badge i{width:6px;height:6px;background:currentColor;border-radius:50%}.status-draft{color:#a4510b;background:#fff3df}.status-audited{color:#16647a;background:#e7f5f8}
.row-actions{justify-content:center;flex-wrap:wrap}.action-button{display:inline-flex;height:30px;align-items:center;justify-content:center;padding:0 10px;border:1px solid transparent;border-radius:4px;cursor:pointer;font-size:12px;font-weight:650;white-space:nowrap}.action-button:disabled{opacity:.45}
.action-audit{color:#fff;background:#0f9f78}.action-reverse{color:#8a470c;background:#fff7e8;border-color:#f3c887}.action-print{color:#445066;background:#fff;border-color:var(--border-strong)}.action-edit{color:#fff;background:#2563eb}.action-delete{color:#dc3545;background:#fff;border-color:#f0a5ad}
.action-audit:hover{background:#08745a}.action-reverse:hover{background:#ffedc8}.action-print:hover{background:#f1f5f9}.action-edit:hover{background:#1d4ed8}.action-delete:hover{color:#fff;background:#dc3545}
.records-table tfoot{background:#f8fafc;border-top:2px solid var(--border);font-weight:700}.total-label{padding-left:20px!important}.empty-cell{height:290px!important;color:var(--text-muted)!important;text-align:center}.empty-cell strong,.empty-cell span{display:block}.empty-cell strong{margin-top:11px;color:#4c586b}.empty-cell span{margin-top:5px;font-size:12px}
.empty-mark{display:inline-flex;width:48px;height:48px;align-items:center;justify-content:center;color:#aab4c0;background:#f1f4f7;border-radius:50%}.empty-mark svg{width:24px;height:24px}.skeleton-row span{display:block;width:78%;height:10px;background:linear-gradient(90deg,#eef2f5 25%,#e2e8ee 50%,#eef2f5 75%);background-size:200% 100%;border-radius:3px;animation:shimmer 1.25s linear infinite}@keyframes shimmer{to{background-position:-200% 0}}
.table-footer{display:flex;min-width:0;min-height:58px;align-items:center;justify-content:space-between;gap:12px;padding:10px 16px;color:var(--text-secondary);border-top:1px solid var(--border);font-size:12px}.table-footer strong{color:var(--text)}.pagination select{height:32px;padding:0 8px;border:1px solid var(--border-strong);border-radius:5px}.pagination button{display:inline-flex;width:31px;height:31px;align-items:center;justify-content:center;color:var(--text-secondary);background:#fff;border:1px solid var(--border-strong);border-radius:5px}.pagination button:disabled{opacity:.45}.pagination svg{width:15px;height:15px}.page-number{min-width:58px;text-align:center}
.sf-field .receipt-debt{color:#dc3545;font-weight:700}
.sf-field input[readonly]{background:#f8fafc}
.receipt-allocation{margin-top:20px;border-top:1px solid #e2e8f0}
.receipt-allocation-header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:14px 0}
.receipt-allocation-header>div{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;min-width:0}
.receipt-allocation-header>.receipt-allocation-mode{align-items:center;flex-direction:row;flex-wrap:nowrap;gap:0}
.receipt-allocation-mode .sf-button{border-radius:0}
.receipt-allocation-mode .sf-button:first-child{border-radius:4px 0 0 4px}
.receipt-allocation-mode .sf-button:last-child{margin-left:-1px;border-radius:0 4px 4px 0}
.receipt-allocation-mode .sf-button[aria-pressed="true"]{position:relative;color:#08745a;background:#e8f6f0;border-color:#0f9f78}
.receipt-allocation-header h3{margin:0;color:#172033;font-size:14px}
.receipt-allocation-scroll{max-height:260px;border:1px solid #e2e8f0;border-radius:4px}
.receipt-allocation-table{min-width:640px;table-layout:fixed}
.receipt-allocation-table th,.receipt-allocation-table td{padding:8px 10px}
.receipt-allocation-table th:first-child,.receipt-allocation-table td:first-child{width:42px;text-align:center}
.receipt-allocation-table th:nth-child(2){width:34%}
.receipt-allocation-table td:nth-child(2) strong,.receipt-document-date{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.receipt-document-date{margin-top:3px;color:#8a96a8;font-size:11px}
.receipt-allocation-table input[type="checkbox"]{width:16px;height:16px;accent-color:#0f9f78;cursor:pointer}
.receipt-allocation-amount{color:#08745a;font-weight:700}
.receipt-allocation-hint{margin:8px 0 0}
.receipt-allocation-error{display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:10px 0}
.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.receipt-attachment-preview{display:block;max-width:240px}
.receipt-attachment-preview img{display:block;max-width:100%;max-height:160px;object-fit:contain}
.page-notice{position:fixed;top:24px;left:50%;z-index:4000;display:flex;min-width:0;min-height:44px;align-items:center;gap:9px;max-width:min(520px,calc(100vw - 32px));padding:10px 16px;color:#172033;background:#fff;border:1px solid #dfe5ec;border-radius:6px;box-shadow:0 10px 30px rgba(15,23,42,.16);transform:translateX(-50%);font-size:13px;font-weight:600;line-height:1.5;overflow-wrap:anywhere}.page-notice svg{width:19px;height:19px;flex:0 0 19px}.notice-success svg{color:#0f9f78}.notice-error svg{color:#dc3545}
.notice-enter-active,.notice-leave-active{transition:opacity .18s,transform .18s}.notice-enter-from,.notice-leave-to{opacity:0;transform:translate(-50%,-8px)}
@media(max-width:1280px){.records-toolbar{align-items:flex-start;flex-direction:column}.store-filter-area{width:100%}.store-slider{max-width:none;flex:1}.toolbar-actions{width:100%;align-self:stretch;justify-content:flex-end;flex-wrap:wrap}}
@media(max-width:780px){.records-toolbar,.store-filter-area{align-items:stretch}.store-filter-area{flex-direction:column}.toolbar-actions{width:100%;justify-content:space-between}.table-footer{align-items:flex-start;flex-direction:column}.pagination{align-self:flex-end}}
@media(max-width:600px){.receipt-allocation-header{align-items:flex-start}.receipt-allocation-header>div{align-items:flex-start;flex-direction:column;gap:4px}}
</style>
