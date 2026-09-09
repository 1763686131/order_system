<template>
  <div :class="['stock-record-page', themeClass]">
    <section class="search-panel" aria-label="单据筛选">
      <form class="search-grid" @submit.prevent="applySearch">
        <label class="field-group">
          <span>单据编号</span>
          <span class="input-with-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            <input
              v-model.trim="searchDraft.documentNo"
              type="search"
              :placeholder="`请输入${documentLabel}编号`"
            />
          </span>
        </label>

        <div class="field-group date-field">
          <span>单据日期</span>
          <div class="date-range">
            <input
              v-model="searchDraft.startDate"
              type="date"
              aria-label="开始日期"
              :max="searchDraft.endDate || undefined"
            />
            <span aria-hidden="true">至</span>
            <input
              v-model="searchDraft.endDate"
              type="date"
              aria-label="结束日期"
              :min="searchDraft.startDate || undefined"
            />
          </div>
        </div>

        <label class="field-group">
          <span>仓库</span>
          <input
            v-model.trim="searchDraft.warehouse"
            type="search"
            list="stock-warehouse-options"
            placeholder="输入或选择仓库"
          />
          <datalist id="stock-warehouse-options">
            <option v-for="warehouse in warehouseOptions" :key="warehouse" :value="warehouse" />
          </datalist>
        </label>

        <label class="field-group">
          <span>{{ counterpartyLabel }}</span>
          <input
            v-model.trim="searchDraft.counterparty"
            type="search"
            list="stock-counterparty-options"
            :placeholder="`输入或选择${counterpartyLabel}`"
          />
          <datalist id="stock-counterparty-options">
            <option v-for="party in counterpartyOptions" :key="party" :value="party" />
          </datalist>
        </label>

        <label class="field-group">
          <span>单据状态</span>
          <input
            v-model.trim="searchDraft.statusText"
            type="search"
            list="stock-status-options"
            placeholder="输入或选择状态"
            @input="searchDraft.status = ''"
          />
          <datalist id="stock-status-options">
            <option value="全部状态" />
            <option value="已过账" />
            <option value="已审核" />
            <option value="待审核" />
            <option value="已红冲" />
          </datalist>
        </label>

        <div class="search-actions">
          <button class="button button-secondary" type="button" @click="resetSearch">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M3 12a9 9 0 1 0 3-6.7"></path>
              <path d="M3 4v6h6"></path>
            </svg>
            重置
          </button>
          <button class="button button-primary" type="submit">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            查询
          </button>
        </div>
      </form>
    </section>

    <div v-if="loadMessage" class="load-message" role="status">
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9"></circle>
        <path d="M12 8v5"></path>
        <path d="M12 17h.01"></path>
      </svg>
      <span>{{ loadMessage }}</span>
      <button type="button" @click="loadRecords">重新加载</button>
    </div>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <div class="material-type-tabs" role="tablist" aria-label="物料类型筛选">
            <button
              v-for="tab in materialTypeTabs"
              :key="tab.value"
              :class="['status-tab', { active: materialTypeFilter === tab.value }]"
              type="button"
              role="tab"
              :aria-selected="materialTypeFilter === tab.value"
              @click="setMaterialType(tab.value)"
            >
              {{ tab.label }}
            </button>
          </div>
          <div class="status-tabs" role="tablist" aria-label="状态快捷筛选">
            <button
              v-for="tab in statusTabs"
              :key="tab.value"
              :class="['status-tab', { active: activeStatus === tab.value }]"
              type="button"
              role="tab"
              :aria-selected="activeStatus === tab.value"
              @click="setStatusTab(tab.value)"
            >
              {{ tab.label }}
              <span>{{ tab.count }}</span>
            </button>
          </div>
        </div>

        <div class="toolbar-actions">
          <button
            class="icon-button refresh-button"
            type="button"
            title="刷新列表"
            aria-label="刷新列表"
            :disabled="loading"
            @click="loadRecords"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button class="button button-secondary export-button" type="button" @click="exportExcel">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 3v12"></path>
              <path d="m7 10 5 5 5-5"></path>
              <path d="M5 21h14"></path>
            </svg>
            导出 Excel
          </button>
          <button
            v-if="!isOutbound"
            class="button button-primary create-button"
            type="button"
            @click="handleCreate"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            新增{{ isOutbound ? '出库' : '入库' }}单
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="document-column">单据编号</th>
              <th>业务类型</th>
              <th>单据日期</th>
              <th>仓库</th>
              <th>{{ counterpartyLabel }}</th>
              <th class="material-column">物料名称</th>
              <th class="number-column">总品种数</th>
              <th class="number-column">总数量</th>
              <th class="money-column">价税合计</th>
              <th>制单人</th>
              <th>状态</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 12" :key="cell"><span></span></td>
              </tr>
            </template>
            <tr v-else-if="pagedRecords.length === 0">
              <td colspan="12" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>暂无匹配的{{ documentLabel }}记录</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>
            <tr
              v-for="record in pagedRecords"
              v-else
              :key="record.id || record.documentNo"
              class="record-row"
              tabindex="0"
              @click="openDetail(record)"
              @keydown.enter.prevent="openDetail(record)"
            >
              <td>
                <button class="document-link" type="button" @click.stop="openDetail(record)">
                  {{ record.documentNo }}
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="m9 18 6-6-6-6"></path>
                  </svg>
                </button>
              </td>
              <td><span class="business-type">{{ record.businessType }}</span></td>
              <td class="date-cell">{{ formatDate(record.documentDate) }}</td>
              <td>{{ record.warehouseName }}</td>
              <td class="party-cell" :title="record.counterpartyName">
                {{ record.counterpartyName }}
              </td>
              <td class="material-cell" :title="record.primaryMaterialName">
                <strong>{{ record.primaryMaterialName }}</strong>
                <span v-if="record.varietyCount > 1">等{{ record.varietyCount }}件物品</span>
              </td>
              <td class="number-column">{{ record.varietyCount }}</td>
              <td class="number-column numeric">{{ formatQuantity(record.totalQuantity) }}</td>
              <td class="money-column money-value">¥{{ formatMoney(record.totalAmount) }}</td>
              <td>{{ record.creator }}</td>
              <td>
                <span :class="['status-tag', `status-${record.status}`]">
                  <i aria-hidden="true"></i>
                  {{ statusLabel(record.status) }}
                </span>
              </td>
              <td class="operation-column" @click.stop>
                <div class="row-actions">
                  <button type="button" title="查看详情" @click="openDetail(record)">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"></path>
                      <circle cx="12" cy="12" r="2.5"></circle>
                    </svg>
                  </button>
                  <button
                    v-if="!isOutbound"
                    class="danger-action"
                    type="button"
                    title="红冲或作废"
                    :disabled="record.status !== 'pending'"
                    @click="handleRedFlush(record)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M4 7h16"></path>
                      <path d="M9 7V4h6v3"></path>
                      <path d="M7 7l1 13h8l1-13"></path>
                    </svg>
                  </button>
                  <button type="button" title="打印单据" @click="handlePrint(record)">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M7 8V3h10v5"></path>
                      <path d="M6 18H4a2 2 0 0 1-2-2v-5a3 3 0 0 1 3-3h14a3 3 0 0 1 3 3v5a2 2 0 0 1-2 2h-2"></path>
                      <path d="M7 14h10v7H7z"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredRecords.length }}</strong> 条记录
          <template v-if="filteredRecords.length">，当前 {{ pageStart }}-{{ pageEnd }} 条</template>
        </span>
        <div class="pagination" aria-label="分页">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="10">10 条 / 页</option>
            <option :value="20">20 条 / 页</option>
            <option :value="50">50 条 / 页</option>
          </select>
          <button
            type="button"
            title="上一页"
            aria-label="上一页"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"></path></svg>
          </button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button
            type="button"
            title="下一页"
            aria-label="下一页"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
          </button>
        </div>
      </footer>
    </section>

    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="drawerOpen && selectedRecord" :class="['drawer-layer', themeClass]">
          <div class="drawer-backdrop" @click="closeDrawer"></div>
          <aside
            class="detail-drawer"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="drawerTitleId"
          >
            <header class="drawer-header">
              <div class="drawer-title-wrap">
                <span class="drawer-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M5 3h11l3 3v15H5z"></path>
                    <path d="M16 3v4h4"></path>
                    <path d="M8 12h8M8 16h6"></path>
                  </svg>
                </span>
                <div>
                  <span>{{ documentLabel }}单据明细</span>
                  <h2 :id="drawerTitleId">{{ selectedRecord.documentNo }}</h2>
                </div>
              </div>
              <button class="drawer-close" type="button" title="关闭" aria-label="关闭" @click="closeDrawer">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="drawer-body">
              <section class="drawer-overview">
                <div class="overview-head">
                  <span :class="['status-tag', `status-${selectedRecord.status}`]">
                    <i aria-hidden="true"></i>
                    {{ statusLabel(selectedRecord.status) }}
                  </span>
                  <span>{{ selectedRecord.businessType }}</span>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>单据日期</dt>
                    <dd>{{ formatDate(selectedRecord.documentDate) }}</dd>
                  </div>
                  <div>
                    <dt>仓库</dt>
                    <dd>{{ selectedRecord.warehouseName }}</dd>
                  </div>
                  <div>
                    <dt>{{ counterpartyLabel }}</dt>
                    <dd>{{ selectedRecord.counterpartyName }}</dd>
                  </div>
                  <div>
                    <dt>制单人</dt>
                    <dd>{{ selectedRecord.creator }}</dd>
                  </div>
                </dl>
                <div class="summary-strip">
                  <div><span>物料品种</span><strong>{{ selectedRecord.varietyCount }}</strong></div>
                  <div><span>合计数量</span><strong>{{ formatQuantity(selectedRecord.totalQuantity) }}</strong></div>
                  <div><span>价税合计</span><strong>¥{{ formatMoney(selectedRecord.totalAmount) }}</strong></div>
                </div>
              </section>

              <section class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>物料明细</h3>
                    <span>共 {{ selectedRecord.items.length }} 行</span>
                  </div>
                </div>
                <div class="detail-table-scroll">
                  <table class="detail-table">
                    <thead>
                      <tr>
                        <th>商品编码</th>
                        <th class="material-detail-column">名称规格</th>
                        <th>单位</th>
                        <th class="number-column">数量</th>
                        <th class="number-column">单价</th>
                        <th class="money-column">金额</th>
                        <th>批次号</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in selectedRecord.items" :key="item.id || `${item.code}-${index}`">
                        <td class="item-code">{{ item.code }}</td>
                        <td>
                          <strong>{{ item.name }}</strong>
                          <span>{{ item.specification || '-' }}</span>
                        </td>
                        <td>{{ item.unit }}</td>
                        <td class="number-column numeric">{{ formatQuantity(item.quantity) }}</td>
                        <td class="number-column numeric">¥{{ formatMoney(item.unitPrice, 4) }}</td>
                        <td class="money-column item-amount">¥{{ formatMoney(item.amount) }}</td>
                        <td class="batch-cell">{{ item.batchNo || '-' }}</td>
                      </tr>
                      <tr v-if="selectedRecord.items.length === 0">
                        <td colspan="7" class="drawer-empty">暂无物料明细</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            <footer :class="['drawer-footer', { 'drawer-footer-readonly': isOutbound }]">
              <div v-if="!isOutbound" class="drawer-state-actions">
                <button
                  v-if="selectedRecord.status === 'pending'"
                  class="button button-primary"
                  type="button"
                  :disabled="documentAction.pending"
                  @click="handleReview(selectedRecord)"
                >
                  <span v-if="isDocumentAction(selectedRecord, 'audit')" class="button-spinner" aria-hidden="true"></span>
                  {{ isDocumentAction(selectedRecord, 'audit') ? '正在审核中...' : '审核' }}
                </button>
                <button
                  v-else-if="selectedRecord.status === 'reviewed' || selectedRecord.status === 'posted'"
                  class="button button-secondary"
                  type="button"
                  :disabled="documentAction.pending"
                  @click="handleReverseAudit(selectedRecord)"
                >
                  <span v-if="isDocumentAction(selectedRecord, 'reverse-audit')" class="button-spinner" aria-hidden="true"></span>
                  {{ isDocumentAction(selectedRecord, 'reverse-audit') ? '正在反审核...' : '反审核' }}
                </button>
                <button
                  v-if="selectedRecord.status === 'cancelled'"
                  class="button button-secondary"
                  type="button"
                  :disabled="documentAction.pending"
                  @click="handleRestart(selectedRecord)"
                >
                  重新启用
                </button>
                <button
                  v-if="selectedRecord.status === 'cancelled'"
                  class="button button-danger-light"
                  type="button"
                  :disabled="documentAction.pending"
                  @click="handleDelete(selectedRecord)"
                >
                  删除
                </button>
              </div>
              <button
                v-if="!isOutbound"
                class="button button-danger-light"
                type="button"
                :disabled="selectedRecord.status !== 'pending' || documentAction.pending"
                @click="handleRedFlush(selectedRecord)"
              >
                红冲 / 作废
              </button>
              <div>
                <button class="button button-secondary" type="button" @click="closeDrawer">关闭</button>
                <button class="button button-primary" type="button" @click="handlePrint(selectedRecord)">
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="M7 8V3h10v5"></path>
                    <path d="M6 18H4a2 2 0 0 1-2-2v-5a3 3 0 0 1 3-3h14a3 3 0 0 1 3 3v5a2 2 0 0 1-2 2h-2"></path>
                    <path d="M7 14h10v7H7z"></path>
                  </svg>
                  打印单据
                </button>
              </div>
            </footer>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as XLSX from 'xlsx'
import request from '@/api/request'

const props = defineProps({
  mode: {
    type: String,
    required: true,
    validator: value => ['INBOUND', 'OUTBOUND'].includes(value)
  },
  dataList: {
    type: Array,
    default: undefined
  }
})

const emit = defineEmits([
  'create',
  'view-detail',
  'red-flush',
  'print',
  'review',
  'reverse-audit',
  'restart',
  'delete'
])

const mockInboundRecords = [
  {
    id: 'mock-in-1',
    documentNo: 'RK20260908012',
    documentDate: '2026-09-08',
    type: 'raw-material',
    warehouseName: '一号原料仓',
    supplierName: '华中原料供应有限公司',
    creator: '张敏',
    status: 'posted',
    totalQuantity: 98.5,
    totalAmount: 1374.13,
    items: [
      { id: 1, productCode: 'RM-003', productName: '轻质碳酸钙', specification: '1250目 / 40kg', unit: '公斤', receivedQty: 98.5, unitPrice: 12.3456, totalAmount: 1374.13, batchNo: '20260908-A' }
    ]
  },
  {
    id: 'mock-in-2',
    documentNo: 'RK20260907009',
    documentDate: '2026-09-07',
    type: 'finished-product',
    warehouseName: '成品仓',
    workshop: '大车间',
    creator: '李工',
    status: 'draft',
    totalQuantity: 36,
    totalAmount: 7920,
    items: [
      { id: 2, productCode: 'CP-018', productName: '结构粘钢胶', specification: '20kg / 组', unit: '组', receivedQty: 36, unitPrice: 220, totalAmount: 7920, batchNo: 'CP0907-02' }
    ]
  },
  {
    id: 'mock-in-3',
    documentNo: 'RK20260905003',
    documentDate: '2026-09-05',
    type: 'raw-material',
    warehouseName: '辅料仓',
    supplierName: '恒远化工材料厂',
    creator: '王婷',
    status: 'cancelled',
    totalQuantity: 50,
    totalAmount: 1840,
    items: [
      { id: 3, productCode: 'RM-009', productName: '消泡剂', specification: '通用型 / 25kg', unit: '公斤', receivedQty: 50, unitPrice: 36.8, totalAmount: 1840, batchNo: 'XP0905' }
    ]
  }
]

const mockOutboundRecords = [
  {
    id: 'mock-out-1',
    documentNo: 'CK20260909006',
    documentDate: '2026-09-09',
    type: 'sales',
    warehouseName: '成品仓',
    customerName: '武汉海威船舶有限公司',
    creator: '陈洁',
    status: 'posted',
    items: [
      { id: 1, productCode: 'CP-010', productName: '碳纤维胶', specification: '5kg / 桶', unit: '桶', quantity: 10, unitPrice: 113, amount: 1130, batchNo: 'CF0908-01' },
      { id: 2, productCode: 'CP-015', productName: '环氧树脂胶', specification: '25kg / 桶', unit: '桶', quantity: 25, unitPrice: 56.5, amount: 1412.5, batchNo: 'HY0907-03' }
    ]
  },
  {
    id: 'mock-out-2',
    documentNo: 'CK20260908004',
    documentDate: '2026-09-08',
    type: 'transfer',
    warehouseName: '小仓库',
    customerName: '华南工程材料经营部',
    creator: '赵晨',
    status: 'pending',
    items: [
      { id: 3, productCode: 'CP-021', productName: '植筋胶', specification: '360ml / 支', unit: '箱', quantity: 18, unitPrice: 480, amount: 8640, batchNo: 'ZJ0908-04' }
    ]
  },
  {
    id: 'mock-out-3',
    documentNo: 'CK20260906001',
    documentDate: '2026-09-06',
    type: 'sales-return',
    warehouseName: '成品仓',
    customerName: '中建物资武汉分公司',
    creator: '陈洁',
    status: 'cancelled',
    items: [
      { id: 4, productCode: 'CP-008', productName: '灌注胶', specification: '30kg / 组', unit: '组', quantity: 12, unitPrice: 310, amount: 3720, batchNo: 'GZ0905-02' }
    ]
  }
]

const isOutbound = computed(() => props.mode === 'OUTBOUND')
const themeClass = computed(() => isOutbound.value ? 'theme-outbound' : 'theme-inbound')
const documentLabel = computed(() => isOutbound.value ? '出库' : '入库')
const counterpartyLabel = computed(() => isOutbound.value ? '客户名称' : '供应商')
const drawerTitleId = `stock-record-drawer-${Math.random().toString(36).slice(2, 10)}`

const loading = ref(false)
const loadMessage = ref('')
const internalRecords = ref([])
const warehouseMap = ref(new Map())
const supplierMap = ref(new Map())
const selectedRecord = ref(null)
const drawerOpen = ref(false)
const activeStatus = ref('all')
const materialTypeFilter = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)
const localStatusOverrides = ref(new Map())
const hiddenRecordIds = ref(new Set())
const documentAction = reactive({ pending: false, id: '', type: '' })
let loadToken = 0
let detailToken = 0

const emptySearch = () => ({
  documentNo: '',
  startDate: '',
  endDate: '',
  warehouse: '',
  counterparty: '',
  status: '',
  statusText: ''
})

const searchDraft = reactive(emptySearch())
const appliedSearch = reactive(emptySearch())

const toNumber = value => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const firstValue = (...values) => values.find(value => value !== undefined && value !== null && value !== '')

const normalizeStatus = record => {
  const rawStatus = String(firstValue(record.status, record.documentStatus, record.auditStatus, '')).toLowerCase()
  if (['cancelled', 'canceled', 'void', 'voided', 'reversed', 'red-flushed', 'red_flush'].includes(rawStatus)) return 'cancelled'
  if (['reviewed', 'review', 'approved', 'audited', 'audit-passed', 'audit_passed'].includes(rawStatus)) return 'reviewed'
  if (['posted', 'completed'].includes(rawStatus)) return 'posted'
  if (['draft', 'pending', 'reviewing', 'unapproved'].includes(rawStatus)) return 'pending'
  if (isOutbound.value && rawStatus === 'shipped') {
    return toNumber(firstValue(record.audit_state, record.auditState, 0)) === 1 ? 'posted' : 'pending'
  }
  return 'pending'
}

const normalizeMaterialType = (record, items = []) => {
  const itemType = items.find(item => firstValue(
    item.materialType,
    item.material_type,
    item.productType,
    item.product_type,
    item.type
  ))
  const rawType = String(firstValue(
    record.materialType,
    record.material_type,
    record.productType,
    record.product_type,
    record.type,
    record.businessType,
    itemType?.materialType,
    itemType?.material_type,
    itemType?.productType,
    itemType?.product_type,
    itemType?.type,
    ''
  )).toLowerCase()
  if (['raw', 'raw-material', 'raw_material', 'material', 'materials', '原材料', '原料'].includes(rawType)) {
    return 'raw-material'
  }
  if (['finished', 'finished-product', 'finished_product', 'product', '成品'].includes(rawType)) {
    return 'finished-product'
  }
  return isOutbound.value ? 'finished-product' : 'raw-material'
}

const normalizeItem = (item = {}, index) => {
  const quantity = toNumber(firstValue(
    item.receivedQty,
    item.received_qty,
    item.outboundQty,
    item.outbound_qty,
    item.quantity,
    item.qty,
    0
  ))
  const unitPrice = toNumber(firstValue(
    item.unitPrice,
    item.unit_price,
    item.taxIncludedPrice,
    item.tax_included_price,
    item.price,
    0
  ))
  return {
    ...item,
    id: firstValue(item.id, item.itemId, item.line_no, index + 1),
    code: String(firstValue(item.productCode, item.product_code, item.code, item.sku, '-')),
    name: String(firstValue(item.productName, item.product_name, item.goodsName, item.goods_name, item.name, '未命名商品')),
    specification: String(firstValue(item.specification, item.spec, item.model, '')),
    unit: String(firstValue(item.unit, item.unitName, item.unit_name, '-')),
    quantity,
    unitPrice,
    amount: toNumber(firstValue(item.totalAmount, item.total_amount, item.amount, quantity * unitPrice)),
    batchNo: String(firstValue(item.batchNo, item.batch_no, item.batch, ''))
  }
}

const businessTypeLabel = record => {
  const type = String(firstValue(record.businessType, record.receiptType, record.type, '')).toLowerCase()
  const labels = isOutbound.value
    ? {
        1: '销售出库',
        sales: '销售出库',
        sale: '销售出库',
        transfer: '调拨出库',
        production: '生产领料',
        'sales-return': '退货出库'
      }
    : {
        'raw-material': '原材料采购入库',
        raw: '原材料采购入库',
        'finished-product': '成品生产完工入库',
        finished: '成品生产完工入库',
        purchase: '采购入库'
      }
  return labels[type] || firstValue(record.businessTypeName, record.typeName, record.businessType, documentLabel.value)
}

const normalizeRecord = record => {
  const rawItems = firstValue(record.items, record.details, record.orderGoods, record.order_goods, [])
  const items = (Array.isArray(rawItems) ? rawItems : []).map(normalizeItem)
  const warehouseId = firstValue(record.warehouseId, record.warehouse_id)
  const supplierId = firstValue(record.supplierId, record.supplier_id)
  const itemWarehouse = items.find(item => item.warehouseName || item.warehouse_name)
  const warehouseName = firstValue(
    record.warehouseName,
    record.warehouse_name,
    itemWarehouse?.warehouseName,
    itemWarehouse?.warehouse_name,
    warehouseMap.value.get(String(warehouseId)),
    '未分配仓库'
  )
  const counterpartyName = isOutbound.value
    ? firstValue(record.customerName, record.customer_name, record.orderClient, record.order_client, record.clientName, '未关联客户')
    : firstValue(
        record.supplierName,
        record.supplier_name,
        supplierMap.value.get(String(supplierId)),
        record.workshop ? `车间：${record.workshop}` : '',
        '未关联供应商'
      )
  const distinctItems = new Set(items.map(item => String(firstValue(item.productId, item.product_id, item.code, item.name))))
  const totalQuantity = toNumber(firstValue(
    record.totalQuantity,
    record.total_quantity,
    items.reduce((sum, item) => sum + item.quantity, 0)
  ))
  const totalAmount = toNumber(firstValue(
    record.totalAmount,
    record.total_amount,
    record.shouldReceive,
    record.should_receive,
    items.reduce((sum, item) => sum + item.amount, 0)
  ))

  const id = firstValue(record.id, record.documentId, record.document_id, record.documentNo, record.order_number)
  const baseStatus = normalizeStatus(record)
  const status = localStatusOverrides.value.get(String(id)) || baseStatus
  return {
    source: record,
    id,
    documentNo: String(firstValue(record.documentNo, record.document_no, record.orderNumber, record.order_number, record.code, '-')),
    documentDate: firstValue(
      record.documentDate,
      record.document_date,
      record.orderDate,
      record.order_date,
      record.shippedDate,
      record.shipped_date,
      record.date,
      record.createdAt,
      record.created_at,
      ''
    ),
    businessType: businessTypeLabel(record),
    materialType: normalizeMaterialType(record, items),
    productType: normalizeMaterialType(record, items),
    warehouseName: String(warehouseName),
    counterpartyName: String(counterpartyName),
    primaryMaterialName: String(firstValue(
      record.primaryMaterialName,
      record.primary_material_name,
      items[0]?.name,
      record.productName,
      record.product_name,
      record.goodsName,
      record.goods_name,
      '未命名物料'
    )),
    varietyCount: Math.max(
      toNumber(firstValue(record.varietyCount, record.totalVarieties, record.total_varieties, 0)),
      distinctItems.size
    ),
    totalQuantity,
    totalAmount,
    creator: String(firstValue(record.creatorName, record.creator, record.createdBy, record.created_by, '-')),
    status,
    items
  }
}

const sourceRecords = computed(() => Array.isArray(props.dataList) ? props.dataList : internalRecords.value)
const records = computed(() => sourceRecords.value
  .filter(Boolean)
  .map(normalizeRecord)
  .filter(record => !hiddenRecordIds.value.has(String(record.id))))

const warehouseOptions = computed(() => (
  [...new Set(records.value.map(record => record.warehouseName).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, 'zh-CN'))
))

const counterpartyOptions = computed(() => (
  [...new Set(records.value.map(record => record.counterpartyName).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, 'zh-CN'))
))

const statusLabel = status => ({
  posted: '已过账',
  reviewed: '已审核',
  pending: '待审核',
  cancelled: '已红冲'
}[status] || '待审核')

const materialTypeTabs = [
  { value: 'all', label: '全部' },
  { value: 'raw-material', label: '原材料' },
  { value: 'finished-product', label: '成品' }
]

const statusTabs = computed(() => [
  { value: 'all', label: '全部', count: records.value.length },
  { value: 'posted', label: '已过账', count: records.value.filter(item => ['posted', 'reviewed'].includes(item.status)).length },
  { value: 'pending', label: '待审核', count: records.value.filter(item => item.status === 'pending').length },
  { value: 'cancelled', label: '已红冲', count: records.value.filter(item => item.status === 'cancelled').length }
])

const dateOnly = value => {
  if (!value) return ''
  const match = String(value).match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (!match) return ''
  return `${match[1]}-${String(match[2]).padStart(2, '0')}-${String(match[3]).padStart(2, '0')}`
}

const formatDate = value => dateOnly(value) || '-'

const filteredRecords = computed(() => {
  const keyword = appliedSearch.documentNo.toLowerCase()
  return records.value.filter(record => {
    const date = dateOnly(record.documentDate)
    const matchesDocument = !keyword || record.documentNo.toLowerCase().includes(keyword)
    const matchesStart = !appliedSearch.startDate || (date && date >= appliedSearch.startDate)
    const matchesEnd = !appliedSearch.endDate || (date && date <= appliedSearch.endDate)
    const warehouseKeyword = appliedSearch.warehouse.toLowerCase()
    const partyKeyword = appliedSearch.counterparty.toLowerCase()
    const matchesWarehouse = !warehouseKeyword || record.warehouseName.toLowerCase().includes(warehouseKeyword)
    const matchesParty = !partyKeyword || record.counterpartyName.toLowerCase().includes(partyKeyword)
    const statusFilter = activeStatus.value === 'all' ? appliedSearch.status : activeStatus.value
    const matchesStatus = statusesMatch(record.status, statusFilter)
    const matchesMaterialType = materialTypeFilter.value === 'all' || record.materialType === materialTypeFilter.value
    return matchesDocument && matchesStart && matchesEnd && matchesWarehouse && matchesParty && matchesStatus && matchesMaterialType
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value)))
const pagedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})
const pageStart = computed(() => filteredRecords.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredRecords.value.length))

const formatMoney = (value, maximumFractionDigits = 2) => Number(toNumber(value)).toLocaleString('zh-CN', {
  minimumFractionDigits: maximumFractionDigits === 4 ? 2 : maximumFractionDigits,
  maximumFractionDigits
})

const formatQuantity = value => Number(toNumber(value)).toLocaleString('zh-CN', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2
})

const statusTextMap = {
  '': '全部状态',
  all: '全部状态',
  posted: '已过账',
  reviewed: '已审核',
  pending: '待审核',
  cancelled: '已红冲'
}

const statusValueFromText = value => {
  const query = String(value || '').trim().toLowerCase()
  if (!query || ['全部', '全部状态', 'all'].includes(query)) return ''
  if (['已过账', 'posted'].some(item => item.includes(query) || query.includes(item))) return 'posted'
  if (['已审核', 'reviewed', 'approved', 'audited'].some(item => item.includes(query) || query.includes(item))) return 'reviewed'
  if (['待审核', 'draft', 'pending', 'unapproved'].some(item => item.includes(query) || query.includes(item))) return 'pending'
  if (['已红冲', '已作废', 'cancelled', 'canceled'].some(item => item.includes(query) || query.includes(item))) return 'cancelled'
  return ''
}

const statusesMatch = (recordStatus, filterStatus) => {
  if (!filterStatus || filterStatus === 'all') return true
  if (filterStatus === 'posted') return ['posted', 'reviewed'].includes(recordStatus)
  return recordStatus === filterStatus
}

const applySearch = () => {
  searchDraft.status = searchDraft.statusText
    ? statusValueFromText(searchDraft.statusText)
    : (searchDraft.status || '')
  searchDraft.statusText = statusTextMap[searchDraft.status] || searchDraft.statusText || ''
  Object.assign(appliedSearch, searchDraft)
  activeStatus.value = searchDraft.status || 'all'
  currentPage.value = 1
}

const resetSearch = () => {
  Object.assign(searchDraft, emptySearch())
  Object.assign(appliedSearch, emptySearch())
  activeStatus.value = 'all'
  materialTypeFilter.value = 'all'
  currentPage.value = 1
}

const setStatusTab = status => {
  activeStatus.value = status
  searchDraft.status = status === 'all' ? '' : status
  searchDraft.statusText = statusTextMap[status] || ''
  appliedSearch.status = searchDraft.status
  appliedSearch.statusText = searchDraft.statusText
  currentPage.value = 1
}

const setMaterialType = type => {
  materialTypeFilter.value = type
  currentPage.value = 1
}

const loadReferenceMaps = async token => {
  if (isOutbound.value) {
    const result = await Promise.allSettled([
      request({ url: '/warehouses', method: 'GET' })
    ])
    if (token !== loadToken || props.mode !== 'OUTBOUND') return
    const warehouses = result[0].status === 'fulfilled' && Array.isArray(result[0].value)
      ? result[0].value
      : []
    warehouseMap.value = new Map(warehouses.map(item => [String(item.id), item.name || item.warehouseName]))
    return
  }

  const result = await Promise.allSettled([
    request({ url: '/warehouses', method: 'GET' }),
    request({ url: '/suppliers', method: 'GET' })
  ])
  if (token !== loadToken || props.mode !== 'INBOUND') return
  const warehouses = result[0].status === 'fulfilled' && Array.isArray(result[0].value)
    ? result[0].value
    : []
  const suppliers = result[1].status === 'fulfilled' && Array.isArray(result[1].value)
    ? result[1].value
    : []
  warehouseMap.value = new Map(warehouses.map(item => [String(item.id), item.name || item.warehouseName]))
  supplierMap.value = new Map(suppliers.map(item => [String(item.id), item.supplierName || item.name]))
}

const loadRecords = async () => {
  const token = ++loadToken

  if (Array.isArray(props.dataList)) {
    loading.value = false
    loadMessage.value = ''
    await loadReferenceMaps(token)
    return
  }

  const currentMode = props.mode
  loading.value = true
  loadMessage.value = ''
  try {
    const results = await Promise.allSettled(
      isOutbound.value
        ? [
            request({ url: '/orders', method: 'GET' }),
            request({ url: '/warehouses', method: 'GET' })
          ]
        : [
            request({ url: '/stock-inbounds', method: 'GET' }),
            request({ url: '/warehouses', method: 'GET' }),
            request({ url: '/suppliers', method: 'GET' })
          ]
    )
    const recordsResult = results[0]
    if (token !== loadToken || currentMode !== props.mode) return

    if (recordsResult.status !== 'fulfilled' || !Array.isArray(recordsResult.value)) {
      throw recordsResult.reason || new Error(`${documentLabel.value}记录格式错误`)
    }

    const warehousesResult = results[1]
    const warehouses = warehousesResult.status === 'fulfilled' && Array.isArray(warehousesResult.value)
      ? warehousesResult.value
      : []

    warehouseMap.value = new Map(warehouses.map(item => [String(item.id), item.name || item.warehouseName]))
    if (isOutbound.value) {
      // The outbound ledger must include pending orders as well as shipped ones:
      // pending rows are the records that can be reviewed from the drawer.
      internalRecords.value = recordsResult.value
    } else {
      const suppliersResult = results[2]
      const suppliers = suppliersResult.status === 'fulfilled' && Array.isArray(suppliersResult.value)
        ? suppliersResult.value
        : []
      supplierMap.value = new Map(suppliers.map(item => [String(item.id), item.supplierName || item.name]))
      internalRecords.value = recordsResult.value
    }

    const relatedFailed = warehousesResult.status === 'rejected'
      || (!isOutbound.value && results[2].status === 'rejected')
    if (relatedFailed) {
      loadMessage.value = '部分基础资料加载失败，单据数据已正常显示。'
    }
  } catch (error) {
    if (token !== loadToken || currentMode !== props.mode) return
    console.error(`加载${documentLabel.value}记录失败:`, error)
    internalRecords.value = isOutbound.value ? mockOutboundRecords : mockInboundRecords
    loadMessage.value = `暂时无法连接${documentLabel.value}接口，当前显示本地预览数据。`
  } finally {
    if (token === loadToken && currentMode === props.mode) loading.value = false
  }
}

const handleCreate = () => {
  if (isOutbound.value) return
  emit('create', { mode: props.mode })
}

const openDetail = async record => {
  const token = ++detailToken
  const currentMode = props.mode
  selectedRecord.value = record
  drawerOpen.value = true
  emit('view-detail', record)

  if (!isOutbound.value && record.items.length === 0 && record.id && !Array.isArray(props.dataList)) {
    try {
      const detail = await request({ url: `/stock-inbounds/${record.id}`, method: 'GET' })
      if (token === detailToken && currentMode === props.mode && selectedRecord.value?.id === record.id) {
        selectedRecord.value = normalizeRecord(detail)
      }
    } catch (error) {
      console.error('加载入库单详情失败:', error)
    }
  }
}

const closeDrawer = () => {
  detailToken += 1
  drawerOpen.value = false
  selectedRecord.value = null
}

const isDocumentAction = (record, type) => (
  documentAction.pending
  && documentAction.type === type
  && String(documentAction.id) === String(record?.id)
)

const beginDocumentAction = (record, type) => {
  if (documentAction.pending || record?.id === undefined || record?.id === null || record?.id === '') return false
  Object.assign(documentAction, { pending: true, id: record.id, type })
  return true
}

const finishDocumentAction = () => {
  Object.assign(documentAction, { pending: false, id: '', type: '' })
}

const responseRecord = (response, fallback, status) => (
  response?.stockIn
  || response?.stockInbound
  || response?.receipt
  || { ...(fallback?.source || fallback), status }
)

const applyServerRecord = (record, source, fallbackStatus) => {
  const id = String(record.id)
  const status = normalizeStatus(source || { status: fallbackStatus })
  const overrides = new Map(localStatusOverrides.value)
  overrides.set(id, status)
  localStatusOverrides.value = overrides

  if (!Array.isArray(props.dataList)) {
    const index = internalRecords.value.findIndex(item => String(firstValue(item.id, item.documentId, item.document_id)) === id)
    if (index >= 0) internalRecords.value.splice(index, 1, source)
  }
  selectedRecord.value = normalizeRecord(source)
  return selectedRecord.value
}

const handleRedFlush = record => {
  if (!isOutbound.value && record?.status === 'pending') emit('red-flush', record)
}

const handleReview = async record => {
  if (isOutbound.value || record?.status !== 'pending' || !beginDocumentAction(record, 'audit')) return
  try {
    const response = await request({ url: `/stock-inbounds/${record.id}/audit`, method: 'POST' })
    const updated = applyServerRecord(record, responseRecord(response, record, 'reviewed'), 'reviewed')
    emit('review', updated)
  } catch (error) {
    window.alert(error?.response?.data?.message || error?.message || '审核失败，请稍后重试')
  } finally {
    finishDocumentAction()
  }
}

const handleReverseAudit = async record => {
  if (
    isOutbound.value
    || !['reviewed', 'posted'].includes(record?.status)
    || !beginDocumentAction(record, 'reverse-audit')
  ) return
  try {
    const response = await request({ url: `/stock-inbounds/${record.id}/audit`, method: 'DELETE' })
    const updated = applyServerRecord(record, responseRecord(response, record, 'draft'), 'draft')
    emit('reverse-audit', updated)
  } catch (error) {
    window.alert(error?.response?.data?.message || error?.message || '反审核失败，请稍后重试')
  } finally {
    finishDocumentAction()
  }
}

const handleRestart = async record => {
  if (isOutbound.value || record?.status !== 'cancelled' || !beginDocumentAction(record, 'restart')) return
  try {
    const response = await request({ url: `/stock-inbounds/${record.id}/restart`, method: 'POST' })
    const updated = applyServerRecord(record, responseRecord(response, record, 'draft'), 'draft')
    emit('restart', updated)
  } catch (error) {
    window.alert(error?.response?.data?.message || error?.message || '重新启用失败，请稍后重试')
  } finally {
    finishDocumentAction()
  }
}

const handleDelete = async record => {
  if (
    isOutbound.value
    || record?.status !== 'cancelled'
    || record?.id === undefined
    || record?.id === null
    || record?.id === ''
    || !beginDocumentAction(record, 'delete')
  ) return
  if (!window.confirm(`确定永久删除已红冲单据“${record.documentNo}”吗？`)) {
    finishDocumentAction()
    return
  }
  try {
    await request({ url: `/stock-inbounds/${record.id}`, method: 'DELETE' })
    const hidden = new Set(hiddenRecordIds.value)
    hidden.add(String(record.id))
    hiddenRecordIds.value = hidden
    closeDrawer()
    emit('delete', record)
  } catch (error) {
    window.alert(error?.response?.data?.message || error?.message || '删除失败，请稍后重试')
  } finally {
    finishDocumentAction()
  }
}

const handlePrint = async record => {
  selectedRecord.value = record
  drawerOpen.value = true
  emit('print', record)
  await nextTick()
  window.print()
}

const exportExcel = () => {
  const rows = filteredRecords.value.map(record => ({
    单据编号: record.documentNo,
    业务类型: record.businessType,
    单据日期: formatDate(record.documentDate),
    仓库: record.warehouseName,
    [counterpartyLabel.value]: record.counterpartyName,
    物料名称: record.primaryMaterialName,
    总品种数: record.varietyCount,
    总数量: record.totalQuantity,
    价税合计: record.totalAmount,
    制单人: record.creator,
    状态: statusLabel(record.status)
  }))
  const worksheet = XLSX.utils.json_to_sheet(rows, {
    header: ['单据编号', '业务类型', '单据日期', '仓库', counterpartyLabel.value, '物料名称', '总品种数', '总数量', '价税合计', '制单人', '状态']
  })
  worksheet['!cols'] = [
    { wch: 20 }, { wch: 18 }, { wch: 13 }, { wch: 16 }, { wch: 26 },
    { wch: 20 }, { wch: 10 }, { wch: 12 }, { wch: 15 }, { wch: 12 }, { wch: 10 }
  ]
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, `${documentLabel.value}记录`)
  XLSX.writeFile(workbook, `${documentLabel.value}记录-${new Date().toISOString().slice(0, 10)}.xlsx`)
}

const handleKeydown = event => {
  if (event.key === 'Escape' && drawerOpen.value) closeDrawer()
}

watch([filteredRecords, pageSize], () => {
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
})

watch(() => props.mode, () => {
  resetSearch()
  localStatusOverrides.value = new Map()
  hiddenRecordIds.value = new Set()
  closeDrawer()
  loadRecords()
})

watch(() => props.dataList, () => {
  currentPage.value = 1
  loadRecords()
}, { deep: true })

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadRecords()
})

onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))

defineExpose({ formatMoney, formatDate, reload: loadRecords, openDetail, closeDrawer })
</script>

<style scoped>
.stock-record-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  min-width: 0;
  min-height: calc(100vh - 100px);
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

.theme-outbound {
  --accent: #2563eb;
  --accent-rgb: 37, 99, 235;
  --accent-dark: #1d4ed8;
  --accent-soft: #edf4ff;
  --accent-border: #bfd3ff;
}

.drawer-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
}

.drawer-layer.theme-outbound {
  --accent: #2563eb;
  --accent-rgb: 37, 99, 235;
  --accent-dark: #1d4ed8;
  --accent-soft: #edf4ff;
  --accent-border: #bfd3ff;
}

* {
  box-sizing: border-box;
}

button,
input,
select {
  font: inherit;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
.record-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.search-panel {
  padding: 18px 20px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(155px, 1fr) minmax(280px, 1.45fr) minmax(140px, 0.85fr) minmax(160px, 1fr) minmax(130px, 0.75fr) auto;
  gap: 14px;
  align-items: end;
}

.field-group {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.field-group > span:first-child {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-group input,
.field-group select,
.pagination select {
  width: 100%;
  height: 38px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field-group input,
.field-group select {
  padding: 0 11px;
}

.field-group input::placeholder {
  color: #a2adba;
}

.field-group input:focus,
.field-group select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.input-with-icon {
  position: relative;
  display: block;
}

.input-with-icon svg {
  position: absolute;
  top: 11px;
  left: 11px;
  z-index: 1;
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.input-with-icon input {
  padding-left: 35px;
}

.date-range {
  display: grid;
  grid-template-columns: minmax(118px, 1fr) auto minmax(118px, 1fr);
  gap: 7px;
  align-items: center;
}

.date-range > span {
  color: var(--text-muted);
  font-size: 12px;
}

.search-actions,
.toolbar-actions,
.row-actions,
.drawer-footer > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.button svg {
  width: 16px;
  height: 16px;
}

.button-spinner {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.button:disabled,
.icon-button:disabled,
.row-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 2px 5px rgba(var(--accent-rgb), 0.18);
}

.button-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.button-secondary {
  color: #445066;
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-danger-light {
  color: #b42318;
  background: #fff;
  border-color: #f6b9b5;
}

.button-danger-light:hover:not(:disabled) {
  background: #fff1f0;
  border-color: #ed8c86;
}

.load-message {
  display: flex;
  min-height: 40px;
  margin-top: 12px;
  align-items: center;
  gap: 9px;
  padding: 8px 13px;
  color: #854d0e;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  font-size: 12px;
}

.load-message svg {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
}

.load-message button {
  margin-left: auto;
  padding: 4px 8px;
  color: #854d0e;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-weight: 600;
}

.records-panel {
  margin-top: 14px;
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 3px 14px rgba(15, 23, 42, 0.045);
}

.records-toolbar {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-filters {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.material-type-tabs {
  display: flex;
  align-items: center;
  gap: 3px;
  padding-right: 10px;
  border-right: 1px solid var(--border);
}

.status-tabs {
  display: flex;
  align-items: center;
  gap: 3px;
}

.status-tab {
  display: inline-flex;
  height: 34px;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.status-tab:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.status-tab.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.status-tab span {
  display: inline-flex;
  min-width: 20px;
  height: 19px;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  color: #69768a;
  background: #eef2f6;
  border-radius: 999px;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.status-tab.active span {
  color: var(--accent-dark);
  background: #fff;
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-button svg {
  width: 17px;
  height: 17px;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-scroll,
.detail-table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1320px;
  border-collapse: collapse;
  table-layout: fixed;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.records-table tbody tr:last-child td {
  border-bottom: 0;
}

.record-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.record-row:hover {
  background: rgba(var(--accent-rgb), 0.035);
}

.records-table .document-column { width: 174px; }
.records-table th:nth-child(2) { width: 150px; }
.records-table th:nth-child(3) { width: 112px; }
.records-table th:nth-child(4) { width: 130px; }
.records-table th:nth-child(5) { width: 190px; }
.records-table th:nth-child(6) { width: 155px; }
.records-table th:nth-child(7) { width: 90px; }
.records-table th:nth-child(8) { width: 105px; }
.records-table th:nth-child(9) { width: 135px; }
.records-table th:nth-child(10) { width: 95px; }
.records-table th:nth-child(11) { width: 104px; }
.records-table .operation-column { width: 126px; text-align: center; }

.number-column,
.money-column {
  text-align: right !important;
}

.numeric,
.money-value,
.item-amount,
.item-code,
.batch-cell {
  font-variant-numeric: tabular-nums;
}

.document-link {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  padding: 3px 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  cursor: pointer;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-link:hover {
  text-decoration: underline;
}

.document-link svg {
  width: 13px;
  height: 13px;
  flex: 0 0 auto;
}

.business-type {
  color: #41516a;
  font-size: 13px;
  font-weight: 600;
}

.date-cell,
.party-cell {
  color: var(--text-secondary);
}

.material-cell {
  max-width: 170px;
}

.material-cell strong,
.material-cell span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-cell strong {
  color: #283548;
  font-size: 13px;
  font-weight: 650;
}

.material-cell span {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
}

.money-value {
  color: #182230 !important;
  font-weight: 750;
}

.status-tag {
  display: inline-flex;
  min-height: 25px;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.status-tag i {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
}

.status-posted {
  color: #13734f;
  background: #eaf8f1;
}

.status-reviewed {
  color: #16647a;
  background: #e7f5f8;
}

.status-pending {
  color: #a4510b;
  background: #fff3df;
}

.status-cancelled {
  color: #b4232f;
  background: #f1f2f4;
}

.row-actions {
  justify-content: center;
}

.row-actions button {
  display: inline-flex;
  width: 29px;
  height: 29px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid #d9e0e8;
  border-radius: 4px;
  cursor: pointer;
}

.row-actions button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.row-actions .danger-action:hover:not(:disabled) {
  color: #b42318;
  background: #fff1f0;
  border-color: #f4aaa5;
}

.row-actions svg {
  width: 14px;
  height: 14px;
}

.empty-cell {
  height: 290px !important;
  color: var(--text-muted) !important;
  text-align: center;
}

.empty-cell strong,
.empty-cell span {
  display: block;
}

.empty-cell strong {
  margin-top: 11px;
  color: #4c586b;
  font-size: 14px;
}

.empty-cell span {
  margin-top: 5px;
  font-size: 12px;
}

.empty-mark {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  color: #9aa6b6;
  background: #f1f4f7;
  border-radius: 50%;
}

.empty-mark svg {
  width: 24px;
  height: 24px;
}

.skeleton-row td span {
  display: block;
  width: 78%;
  height: 10px;
  background: linear-gradient(90deg, #edf1f5 25%, #f8fafc 50%, #edf1f5 75%);
  background-size: 200% 100%;
  border-radius: 3px;
  animation: skeleton 1.25s infinite linear;
}

@keyframes skeleton {
  to { background-position: -200% 0; }
}

.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  color: var(--text-secondary);
  background: #fff;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.table-footer strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination select {
  width: 103px;
  height: 32px;
  padding: 0 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.pagination button {
  display: inline-flex;
  width: 31px;
  height: 31px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #526074;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  color: var(--accent-dark);
  border-color: var(--accent);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.pagination button svg {
  width: 14px;
  height: 14px;
}

.pagination > span {
  min-width: 50px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.drawer-layer {
  position: fixed;
  inset: 0;
  z-index: 2147482000;
}

.drawer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.detail-drawer {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  width: min(820px, 88vw);
  height: 100%;
  flex-direction: column;
  overflow: hidden;
  color: #172033;
  background: #f4f7f9;
  box-shadow: -18px 0 55px rgba(15, 23, 42, 0.2);
}

.drawer-header {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #dfe5ec;
}

.drawer-title-wrap {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.drawer-mark {
  display: inline-flex;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 7px;
}

.drawer-mark svg {
  width: 21px;
  height: 21px;
}

.drawer-title-wrap > div {
  min-width: 0;
}

.drawer-title-wrap span:not(.drawer-mark) {
  color: #758195;
  font-size: 11px;
  font-weight: 600;
}

.drawer-title-wrap h2 {
  margin: 3px 0 0;
  overflow: hidden;
  color: #172033;
  font-size: 18px;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.drawer-close:hover {
  color: #273245;
  background: #f0f3f6;
}

.drawer-close svg {
  width: 20px;
  height: 20px;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
}

.drawer-overview,
.detail-section {
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.drawer-overview {
  padding: 17px;
}

.overview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #edf1f5;
}

.overview-head > span:last-child {
  color: #5e6a7e;
  font-size: 12px;
  font-weight: 600;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 22px;
  margin: 17px 0;
}

.meta-grid > div {
  min-width: 0;
}

.meta-grid dt {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.meta-grid dd {
  margin: 0;
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  overflow: hidden;
  background: #f8fafb;
  border: 1px solid #e5eaf0;
  border-radius: 6px;
}

.summary-strip > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  padding: 13px 15px;
  border-right: 1px solid #e5eaf0;
}

.summary-strip > div:last-child {
  border-right: 0;
}

.summary-strip span {
  color: #7a8698;
  font-size: 11px;
}

.summary-strip strong {
  overflow: hidden;
  color: #243145;
  font-size: 16px;
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-strip > div:last-child strong {
  color: var(--accent-dark);
}

.detail-section {
  margin-top: 15px;
  overflow: hidden;
}

.section-heading {
  display: flex;
  min-height: 53px;
  align-items: center;
  justify-content: space-between;
  padding: 11px 15px;
  border-bottom: 1px solid #e5eaf0;
}

.section-heading > div {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.section-heading h3 {
  margin: 0;
  color: #263348;
  font-size: 14px;
  letter-spacing: 0;
}

.section-heading span {
  color: #8a96a8;
  font-size: 11px;
}

.detail-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  table-layout: fixed;
}

.detail-table th {
  height: 39px;
  padding: 0 10px;
  color: #647086;
  background: #f8fafb;
  border-bottom: 1px solid #e5eaf0;
  font-size: 11px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.detail-table td {
  height: 55px;
  padding: 8px 10px;
  color: #3c485b;
  border-bottom: 1px solid #edf1f5;
  font-size: 12px;
}

.detail-table tr:last-child td {
  border-bottom: 0;
}

.detail-table th:nth-child(1) { width: 100px; }
.detail-table .material-detail-column { width: 185px; }
.detail-table th:nth-child(3) { width: 65px; }
.detail-table th:nth-child(4) { width: 80px; }
.detail-table th:nth-child(5) { width: 100px; }
.detail-table th:nth-child(6) { width: 110px; }
.detail-table th:nth-child(7) { width: 115px; }

.detail-table td strong,
.detail-table td span {
  display: block;
}

.detail-table td strong {
  overflow: hidden;
  color: #283548;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-table td span {
  margin-top: 3px;
  overflow: hidden;
  color: #8a96a8;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-code,
.batch-cell {
  color: #556277 !important;
  font-family: Consolas, "Courier New", monospace;
}

.item-amount {
  color: #263348 !important;
  font-weight: 700;
}

.drawer-empty {
  height: 150px !important;
  color: #8a96a8 !important;
  text-align: center;
}

.drawer-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  background: #fff;
  border-top: 1px solid #dfe5ec;
}

.drawer-footer-readonly {
  justify-content: flex-end;
}

.drawer-state-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.24s ease;
}

.drawer-enter-active .detail-drawer,
.drawer-leave-active .detail-drawer {
  transition: transform 0.28s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .detail-drawer,
.drawer-leave-to .detail-drawer {
  transform: translateX(100%);
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .search-actions {
    justify-content: flex-end;
  }
}

@media (max-width: 780px) {
  .search-panel {
    padding: 14px;
  }

  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .date-field,
  .search-actions {
    grid-column: 1 / -1;
  }

  .records-toolbar,
  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .records-toolbar {
    padding: 12px;
  }

  .status-tabs {
    width: 100%;
    overflow-x: auto;
  }

  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions .export-button,
  .toolbar-actions .create-button {
    flex: 1;
  }

  .table-footer {
    gap: 12px;
  }

  .pagination {
    width: 100%;
    justify-content: space-between;
  }

  .detail-drawer {
    width: 100vw;
  }
}

@media (max-width: 520px) {
  .search-grid {
    grid-template-columns: 1fr;
  }

  .date-field,
  .search-actions {
    grid-column: auto;
  }

  .date-range {
    grid-template-columns: 1fr;
  }

  .date-range > span {
    display: none;
  }

  .search-actions .button {
    flex: 1;
  }

  .refresh-button {
    display: none;
  }

  .status-tab {
    flex: 0 0 auto;
  }

  .drawer-header,
  .drawer-body,
  .drawer-footer {
    padding-left: 13px;
    padding-right: 13px;
  }

  .meta-grid,
  .summary-strip {
    grid-template-columns: 1fr;
  }

  .summary-strip > div {
    border-right: 0;
    border-bottom: 1px solid #e5eaf0;
  }

  .summary-strip > div:last-child {
    border-bottom: 0;
  }

  .drawer-footer {
    align-items: stretch;
    flex-direction: column-reverse;
  }

  .drawer-footer > div,
  .drawer-footer .button {
    width: 100%;
  }
}

@media print {
  .drawer-backdrop,
  .drawer-close,
  .drawer-footer {
    display: none !important;
  }

  .detail-drawer {
    position: fixed;
    inset: 0;
    width: 100%;
    height: auto;
    overflow: visible;
    background: #fff;
    box-shadow: none;
  }

  .drawer-body {
    overflow: visible;
  }
}
</style>
