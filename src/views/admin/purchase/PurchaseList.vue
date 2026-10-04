<template>
  <div class="purchase-list-page" :class="{ 'is-inbound': isInbound }">
    <Transition name="notice">
      <div v-if="notice" class="page-notice" role="status">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="m8 12 2.7 2.7L16.5 9"></path>
        </svg>
        <span>{{ notice }}</span>
        <button type="button" title="关闭提示" @click="notice = ''">×</button>
      </div>
    </Transition>

    <section class="search-panel">
      <div class="search-grid">
        <label class="search-field keyword-field">
          <span class="field-label">关键词</span>
          <span class="input-with-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="6.5"></circle>
              <path d="m16 16 4.5 4.5"></path>
            </svg>
            <input
              v-model.trim="filters.keyword"
              type="search"
              :placeholder="isInbound ? '单号、供应商、物料名称' : '单号、供应商、物料名称'"
              @keyup.enter="applyFilters"
            />
          </span>
        </label>

        <div class="search-field date-field">
          <span class="field-label">{{ isInbound ? '入库日期' : '采购日期' }}</span>
          <div class="date-range">
            <input
              v-model="filters.startDate"
              type="date"
              :max="filters.endDate || undefined"
              aria-label="开始日期"
            />
            <span aria-hidden="true">至</span>
            <input
              v-model="filters.endDate"
              type="date"
              :min="filters.startDate || undefined"
              aria-label="结束日期"
            />
          </div>
        </div>

        <label class="search-field">
          <span class="field-label">状态</span>
          <select v-model="filters.status">
            <option value="all">全部状态</option>
            <option v-for="option in statusOptions" :key="option.key" :value="option.key">
              {{ option.label }}
            </option>
          </select>
        </label>

        <div class="search-actions">
          <button class="button button-primary" type="button" @click="applyFilters">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="6.5"></circle>
              <path d="m16 16 4.5 4.5"></path>
            </svg>
            查询
          </button>
          <button class="button button-ghost" type="button" @click="resetFilters">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 4v6h6"></path>
              <path d="M5.3 15a8 8 0 1 0 .4-8.3L4 10"></path>
            </svg>
            重置
          </button>
        </div>
      </div>
    </section>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <div class="toolbar-heading">
            <div class="page-kicker">{{ isInbound ? '采购执行' : '采购管理' }}</div>
            <h1>{{ isInbound ? '采购入库' : '采购订单' }}</h1>
          </div>

          <div class="status-filter-slider" role="tablist" aria-label="采购状态筛选">
            <button
              v-for="tab in statusTabs"
              :key="tab.key"
              :class="['slider-tab', { active: filters.status === tab.key }]"
              type="button"
              role="tab"
              :aria-selected="filters.status === tab.key"
              @click="setStatusFilter(tab.key)"
            >
              {{ tab.label }}
              <span class="count-badge">{{ tab.count }}</span>
            </button>
          </div>

          <div v-if="selectedIds.size" class="selection-count">
            已选中 <strong>{{ selectedIds.size }}</strong> 项
          </div>
        </div>

        <div class="toolbar-actions">
          <span class="record-count">共 {{ filteredRecords.length }} 条记录</span>
          <button class="icon-button refresh-button" type="button" title="刷新列表" @click="refreshData">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 11a8.1 8.1 0 0 0-14.8-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.8 4L21 14"></path>
              <path d="M21 20v-6h-6"></path>
            </svg>
          </button>
          <button class="button button-export" type="button" title="导出 Excel" @click="exportRecords">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v12"></path>
              <path d="m7 10 5 5 5-5"></path>
              <path d="M4 21h16"></path>
            </svg>
            导出 Excel
          </button>
          <button class="button button-primary" type="button" @click="createRecord">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            {{ isInbound ? '新增入库单' : '新增采购单' }}
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="checkbox-column">
                <input
                  type="checkbox"
                  :checked="isAllPageSelected"
                  :indeterminate="isSomePageSelected"
                  aria-label="选择当前页"
                  @change="togglePageSelection"
                />
              </th>
              <th>{{ isInbound ? '入库单号' : '采购单号' }}</th>
              <th>{{ isInbound ? '入库日期' : '采购日期' }}</th>
              <th>供应商</th>
              <th>物料摘要</th>
              <th>数量 / 进度</th>
              <th>仓库</th>
              <th>含税金额</th>
              <th>状态</th>
              <th>备注</th>
              <th class="action-column">操作</th>
            </tr>
          </thead>
          <tbody v-if="loading">
            <tr v-for="index in 6" :key="`skeleton-${index}`" class="skeleton-row">
              <td v-for="column in 11" :key="column"><span></span></td>
            </tr>
          </tbody>
          <tbody v-else-if="paginatedRecords.length">
            <tr
              v-for="record in paginatedRecords"
              :key="record.id"
              class="record-row"
              :class="{ selected: isSelected(record.id) }"
              tabindex="0"
              @click="openDetail(record)"
              @keydown.enter.self.prevent="openDetail(record)"
            >
              <td class="checkbox-column">
                <input
                  type="checkbox"
                  :checked="isSelected(record.id)"
                  :aria-label="`选择${getRecordNo(record)}`"
                  @click.stop
                  @change="toggleSelection(record.id)"
                />
              </td>
              <td>
                <button class="document-link" type="button" @click.stop="openDetail(record)">
                  {{ getRecordNo(record) }}
                </button>
              </td>
              <td class="date-cell">{{ formatDate(recordDate(record)) }}</td>
              <td>
                <div class="primary-cell">{{ record.supplierName }}</div>
                <div class="secondary-cell">{{ isInbound ? record.inspector : record.contact }}</div>
              </td>
              <td>
                <div class="primary-cell item-summary">{{ record.itemSummary }}</div>
                <div class="secondary-cell">{{ record.itemCount }} 项物料</div>
              </td>
              <td>
                <div class="quantity-cell">
                  <strong>{{ formatNumber(quantityValue(record)) }}</strong>
                  <span>{{ isInbound ? `/ ${formatNumber(record.expectedQuantity)} ${record.items?.[0]?.unit || '件'}` : '件' }}</span>
                </div>
                <div v-if="isInbound" class="progress-cell">
                  <span class="progress-track"><i :style="{ width: `${recordProgress(record)}%` }"></i></span>
                  <small>{{ recordProgress(record) }}%</small>
                </div>
              </td>
              <td>{{ record.warehouseName }}</td>
              <td class="amount-cell">¥ {{ formatMoney(record.totalAmount) }}</td>
              <td>
                <span class="status-tag" :class="`status-${getStatusClass(record.status)}`">
                  <i></i>{{ getStatusLabel(record.status) }}
                </span>
              </td>
              <td class="remark-cell" :title="record.remark || ''">{{ record.remark || '—' }}</td>
              <td class="action-column" @click.stop>
                <div class="row-actions">
                  <button class="table-action" type="button" title="查看详情" @click="openDetail(record)">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="2.5"></circle>
                    </svg>
                  </button>
                  <button
                    v-if="isInbound"
                    class="table-action"
                    type="button"
                    title="打印入库单"
                    @click="printRecord(record)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M6 9V3h12v6"></path>
                      <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                      <path d="M6 14h12v7H6z"></path>
                    </svg>
                  </button>
                  <button
                    v-if="canEdit(record)"
                    class="table-action"
                    type="button"
                    :title="isInbound ? '编辑入库单' : '查看采购单'"
                    @click="editRecord(record)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 20h9"></path>
                      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="11" class="empty-cell">
                <div class="empty-state">
                  <div class="empty-icon">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v13a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 18.5Z"></path>
                      <path d="M8 8h8M8 12h8M8 16h5"></path>
                    </svg>
                  </div>
                  <strong>暂无{{ isInbound ? '采购入库' : '采购订单' }}记录</strong>
                  <span>调整筛选条件，或创建一条新的{{ isInbound ? '入库单' : '采购单' }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-footer">
        <div class="selection-summary">
          已选择 <strong>{{ selectedIds.size }}</strong> 条
          <button v-if="selectedIds.size" type="button" @click="clearSelection">清空</button>
        </div>
        <div class="pagination">
          <span>共 {{ filteredRecords.length }} 条</span>
          <button type="button" :disabled="currentPage === 1" @click="currentPage -= 1">上一页</button>
          <button
            v-for="page in pageNumbers"
            :key="page"
            type="button"
            :class="{ active: page === currentPage }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
          <button type="button" :disabled="currentPage === totalPages" @click="currentPage += 1">下一页</button>
        </div>
      </div>
    </section>

    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="detailModalOpen && selectedRecord" class="detail-modal-layer" @click.self="closeDetail">
          <article
            class="detail-modal"
            role="dialog"
            aria-modal="true"
            :aria-label="isInbound ? '采购入库详情' : '采购订单详情'"
            tabindex="-1"
            @keydown.esc="closeDetail"
          >
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M5 3h11l3 3v15H5z"></path>
                    <path d="M16 3v4h4"></path>
                    <path d="M8 12h8M8 16h6"></path>
                  </svg>
                </span>
                <div>
                  <span class="modal-kicker">{{ isInbound ? 'PURCHASE INBOUND' : 'PURCHASE ORDER' }}</span>
                  <h2>{{ isInbound ? '采购入库详情' : '采购订单详情' }}</h2>
                  <button class="modal-document-no" type="button" @click="copyDocumentNo">
                    {{ getRecordNo(selectedRecord) }}
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <rect x="8" y="8" width="11" height="11" rx="1.5"></rect>
                      <path d="M5 16H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1 1h11a1 1 0 0 1 1 1v1"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <button class="modal-close" type="button" title="关闭" @click="closeDetail">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <div class="detail-overview">
                <div>
                  <span class="detail-label">当前状态</span>
                  <span class="status-tag large" :class="`status-${getStatusClass(selectedRecord.status)}`">
                    <i></i>{{ getStatusLabel(selectedRecord.status) }}
                  </span>
                </div>
                <div>
                  <span class="detail-label">{{ isInbound ? '入库日期' : '采购日期' }}</span>
                  <strong>{{ formatDate(recordDate(selectedRecord)) }}</strong>
                </div>
                <div>
                  <span class="detail-label">含税金额</span>
                  <strong class="overview-amount">¥ {{ formatMoney(selectedRecord.totalAmount) }}</strong>
                </div>
              </div>

              <section class="detail-section">
                <div class="section-heading">
                  <h3>基础信息</h3>
                  <span>共 {{ selectedRecord.itemCount }} 项物料</span>
                </div>
                <div class="meta-grid">
                  <div><span>供应商</span><strong>{{ selectedRecord.supplierName }}</strong></div>
                  <div><span>收货仓库</span><strong>{{ selectedRecord.warehouseName }}</strong></div>
                  <div><span>{{ isInbound ? '验收人员' : '采购人员' }}</span><strong>{{ isInbound ? selectedRecord.inspector : selectedRecord.contact }}</strong></div>
                  <div><span>{{ isInbound ? '质检单号' : '预计到货' }}</span><strong>{{ isInbound ? selectedRecord.qualityNo || '—' : selectedRecord.expectedDate || '—' }}</strong></div>
                </div>
              </section>

              <section class="detail-section">
                <div class="section-heading">
                  <h3>采购物料明细</h3>
                  <span>{{ isInbound ? `${formatNumber(selectedRecord.receivedQuantity)} / ${formatNumber(selectedRecord.expectedQuantity)} 已入库` : `合计 ${formatNumber(selectedRecord.totalQuantity)} 件` }}</span>
                </div>
                <div class="detail-items-scroll">
                  <table class="detail-items-table">
                    <thead>
                      <tr>
                        <th>物料编码</th>
                        <th>物料名称</th>
                        <th>规格型号</th>
                        <th>单位</th>
                        <th>计划数量</th>
                        <th v-if="isInbound">实收数量</th>
                        <th>含税单价</th>
                        <th>金额</th>
                        <th v-if="isInbound">批次 / 库位</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in selectedRecord.items" :key="`${selectedRecord.id}-${item.productCode}`">
                        <td>{{ item.productCode }}</td>
                        <td>{{ item.goodsName }}</td>
                        <td>{{ item.specification || '—' }}</td>
                        <td>{{ item.unit }}</td>
                        <td>{{ formatNumber(item.expectedQty ?? item.quantity) }}</td>
                        <td v-if="isInbound">{{ formatNumber(item.receivedQty ?? item.quantity) }}</td>
                        <td>¥ {{ formatMoney(item.price) }}</td>
                        <td>¥ {{ formatMoney(item.amount) }}</td>
                        <td v-if="isInbound">{{ item.batchNo || '—' }} / {{ item.binCode || '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section class="detail-section remark-section">
                <div class="section-heading"><h3>备注</h3></div>
                <p>{{ selectedRecord.remark || '暂无备注' }}</p>
              </section>
            </div>

            <footer class="detail-modal-footer">
              <button class="button button-ghost" type="button" @click="closeDetail">关闭</button>
              <div class="footer-actions">
                <button v-if="isInbound" class="button button-secondary" type="button" @click="printRecord(selectedRecord)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 9V3h12v6"></path>
                    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                    <path d="M6 14h12v7H6z"></path>
                  </svg>
                  打印入库单
                </button>
                <button v-if="canEdit(selectedRecord)" class="button button-primary" type="button" @click="editRecord(selectedRecord)">
                  {{ isInbound ? '编辑入库单' : '查看采购单' }}
                </button>
              </div>
            </footer>
          </article>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  mode: {
    type: String,
    default: 'orders',
    validator: value => ['orders', 'inbound'].includes(value)
  }
})

const router = useRouter()
const isInbound = computed(() => props.mode === 'inbound')

const mockOrders = [
  {
    id: 1,
    orderNo: 'CG20261003001',
    purchaseDate: '2026-10-03',
    expectedDate: '2026-10-08',
    supplierName: '华中原料供应有限公司',
    warehouseName: '一号原料仓',
    contact: '李强',
    itemSummary: '环氧树脂 E-51 等 3 项',
    itemCount: 3,
    totalQuantity: 340,
    receivedQuantity: 340,
    totalAmount: 28650,
    status: 'completed',
    remark: '按生产计划分批到货',
    items: [
      { productCode: 'RM-001', goodsName: '环氧树脂 E-51', specification: '工业级，20kg/桶', unit: '桶', quantity: 120, price: 128, amount: 15360 },
      { productCode: 'RM-014', goodsName: '促进剂 DMP-30', specification: '25kg/箱', unit: '箱', quantity: 80, price: 86, amount: 6880 },
      { productCode: 'RM-021', goodsName: '玻璃纤维短切毡', specification: '450g/㎡', unit: '卷', quantity: 140, price: 45.07, amount: 6310 }
    ]
  },
  {
    id: 2,
    orderNo: 'CG20261002003',
    purchaseDate: '2026-10-02',
    expectedDate: '2026-10-10',
    supplierName: '东莞新材科技有限公司',
    warehouseName: '二号辅料仓',
    contact: '周敏',
    itemSummary: '无碱玻璃纤维布等 2 项',
    itemCount: 2,
    totalQuantity: 520,
    receivedQuantity: 220,
    totalAmount: 19840,
    status: 'partial',
    remark: '首批已到货，余量待供应商确认',
    items: [
      { productCode: 'RM-033', goodsName: '无碱玻璃纤维布', specification: '200g/㎡，1m宽', unit: '卷', quantity: 320, price: 31.5, amount: 10080 },
      { productCode: 'RM-041', goodsName: '聚酯薄膜', specification: '0.18mm，透明', unit: '卷', quantity: 200, price: 48.8, amount: 9760 }
    ]
  },
  {
    id: 3,
    orderNo: 'CG20261001006',
    purchaseDate: '2026-10-01',
    expectedDate: '2026-10-06',
    supplierName: '江南化工原料厂',
    warehouseName: '一号原料仓',
    contact: '陈杰',
    itemSummary: '不饱和聚酯树脂 191 等 2 项',
    itemCount: 2,
    totalQuantity: 260,
    receivedQuantity: 0,
    totalAmount: 22400,
    status: 'confirmed',
    remark: '请提前一天预约送货',
    items: [
      { productCode: 'RM-005', goodsName: '不饱和聚酯树脂 191', specification: '200kg/桶', unit: '桶', quantity: 100, price: 186, amount: 18600 },
      { productCode: 'RM-012', goodsName: '固化剂 MEKP', specification: '20kg/桶', unit: '桶', quantity: 160, price: 23.75, amount: 3800 }
    ]
  },
  {
    id: 4,
    orderNo: 'CG20260929002',
    purchaseDate: '2026-09-29',
    expectedDate: '2026-10-05',
    supplierName: '华南包装材料有限公司',
    warehouseName: '包装材料仓',
    contact: '赵琳',
    itemSummary: '缠绕膜、纸护角等 4 项',
    itemCount: 4,
    totalQuantity: 960,
    receivedQuantity: 0,
    totalAmount: 12960,
    status: 'pending',
    remark: '',
    items: [
      { productCode: 'PK-001', goodsName: 'PE 缠绕膜', specification: '50cm×300m', unit: '卷', quantity: 400, price: 18, amount: 7200 },
      { productCode: 'PK-008', goodsName: '纸护角', specification: '50×50×5mm', unit: '根', quantity: 400, price: 6.2, amount: 2480 },
      { productCode: 'PK-011', goodsName: '打包带', specification: 'PET，16mm', unit: '卷', quantity: 80, price: 28, amount: 2240 },
      { productCode: 'PK-013', goodsName: '打包扣', specification: '16mm', unit: '包', quantity: 80, price: 13, amount: 1040 }
    ]
  },
  {
    id: 5,
    orderNo: 'CG20260927004',
    purchaseDate: '2026-09-27',
    expectedDate: '2026-10-02',
    supplierName: '华中原料供应有限公司',
    warehouseName: '一号原料仓',
    contact: '李强',
    itemSummary: '碳酸钙填料等 2 项',
    itemCount: 2,
    totalQuantity: 680,
    receivedQuantity: 0,
    totalAmount: 8640,
    status: 'cancelled',
    remark: '因配方调整取消',
    items: [
      { productCode: 'RM-067', goodsName: '活性碳酸钙', specification: '1250目，25kg/袋', unit: '袋', quantity: 480, price: 12, amount: 5760 },
      { productCode: 'RM-071', goodsName: '氢氧化铝', specification: '1250目，25kg/袋', unit: '袋', quantity: 200, price: 14.4, amount: 2880 }
    ]
  }
]

const mockInbounds = [
  {
    id: 101,
    inboundNo: 'RK20261003001',
    documentDate: '2026-10-03',
    supplierName: '华中原料供应有限公司',
    warehouseName: '一号原料仓',
    inspector: '王海',
    qualityNo: 'QC20261003008',
    itemSummary: '环氧树脂 E-51 等 3 项',
    itemCount: 3,
    expectedQuantity: 340,
    receivedQuantity: 340,
    totalAmount: 28650,
    status: 'posted',
    remark: '外观及批次核对无误',
    items: [
      { productCode: 'RM-001', goodsName: '环氧树脂 E-51', specification: '工业级，20kg/桶', unit: '桶', expectedQty: 120, receivedQty: 120, price: 128, amount: 15360, batchNo: 'E510610A', binCode: 'A-01-02' },
      { productCode: 'RM-014', goodsName: '促进剂 DMP-30', specification: '25kg/箱', unit: '箱', expectedQty: 80, receivedQty: 80, price: 86, amount: 6880, batchNo: 'DMP0610', binCode: 'A-02-01' },
      { productCode: 'RM-021', goodsName: '玻璃纤维短切毡', specification: '450g/㎡', unit: '卷', expectedQty: 140, receivedQty: 140, price: 45.07, amount: 6310, batchNo: 'GF1003', binCode: 'B-01-03' }
    ]
  },
  {
    id: 102,
    inboundNo: 'RK20261002002',
    documentDate: '2026-10-02',
    supplierName: '东莞新材科技有限公司',
    warehouseName: '二号辅料仓',
    inspector: '王海',
    qualityNo: 'QC20261002006',
    itemSummary: '无碱玻璃纤维布等 2 项',
    itemCount: 2,
    expectedQuantity: 220,
    receivedQuantity: 220,
    totalAmount: 10080,
    status: 'reviewed',
    remark: '已完成质检，等待过账',
    items: [
      { productCode: 'RM-033', goodsName: '无碱玻璃纤维布', specification: '200g/㎡，1m宽', unit: '卷', expectedQty: 160, receivedQty: 160, price: 31.5, amount: 5040, batchNo: 'GF1002A', binCode: 'C-01-01' },
      { productCode: 'RM-041', goodsName: '聚酯薄膜', specification: '0.18mm，透明', unit: '卷', expectedQty: 60, receivedQty: 60, price: 84, amount: 5040, batchNo: 'PET1002', binCode: 'C-01-02' }
    ]
  },
  {
    id: 103,
    inboundNo: 'RK20261002001',
    documentDate: '2026-10-02',
    supplierName: '华南包装材料有限公司',
    warehouseName: '包装材料仓',
    inspector: '刘芳',
    qualityNo: '',
    itemSummary: 'PE 缠绕膜等 2 项',
    itemCount: 2,
    expectedQuantity: 260,
    receivedQuantity: 240,
    totalAmount: 7520,
    status: 'draft',
    remark: '其中 20 卷外包装破损，待确认',
    items: [
      { productCode: 'PK-001', goodsName: 'PE 缠绕膜', specification: '50cm×300m', unit: '卷', expectedQty: 200, receivedQty: 190, price: 18, amount: 3420, batchNo: 'FM1002', binCode: 'D-01-01' },
      { productCode: 'PK-008', goodsName: '纸护角', specification: '50×50×5mm', unit: '根', expectedQty: 60, receivedQty: 50, price: 82, amount: 4100, batchNo: 'PC1002', binCode: 'D-02-01' }
    ]
  },
  {
    id: 104,
    inboundNo: 'RK20260930003',
    documentDate: '2026-09-30',
    supplierName: '江南化工原料厂',
    warehouseName: '一号原料仓',
    inspector: '刘芳',
    qualityNo: 'QC20260930009',
    itemSummary: '不饱和聚酯树脂 191',
    itemCount: 1,
    expectedQuantity: 100,
    receivedQuantity: 100,
    totalAmount: 18600,
    status: 'cancelled',
    remark: '批次标签不符合要求，已退回',
    items: [
      { productCode: 'RM-005', goodsName: '不饱和聚酯树脂 191', specification: '200kg/桶', unit: '桶', expectedQty: 100, receivedQty: 100, price: 186, amount: 18600, batchNo: 'RES0930', binCode: '—' }
    ]
  }
]

const cloneRecords = records => records.map(record => ({
  ...record,
  items: (record.items || []).map(item => ({ ...item }))
}))

const orderRecords = ref(cloneRecords(mockOrders))
const inboundRecords = ref(cloneRecords(mockInbounds))
const filters = ref({ keyword: '', status: 'all', startDate: '', endDate: '' })
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 30
const selectedIds = ref(new Set())
const selectedRecord = ref(null)
const detailModalOpen = ref(false)
const notice = ref('')

const sourceRecords = computed(() => (isInbound.value ? inboundRecords.value : orderRecords.value))

const statusTabs = computed(() => {
  const statuses = isInbound.value
    ? [
        { key: 'all', label: '全部' },
        { key: 'draft', label: '草稿' },
        { key: 'reviewed', label: '已审核' },
        { key: 'posted', label: '已入库' },
        { key: 'cancelled', label: '已作废' }
      ]
    : [
        { key: 'all', label: '全部' },
        { key: 'pending', label: '待确认' },
        { key: 'confirmed', label: '已确认' },
        { key: 'partial', label: '部分入库' },
        { key: 'completed', label: '已完成' },
        { key: 'cancelled', label: '已取消' }
      ]

  return statuses.map(tab => ({
    ...tab,
    count: tab.key === 'all'
      ? sourceRecords.value.length
      : sourceRecords.value.filter(record => record.status === tab.key).length
  }))
})

const statusOptions = computed(() => statusTabs.value.filter(tab => tab.key !== 'all'))

const filteredRecords = computed(() => {
  const keyword = filters.value.keyword.toLowerCase()
  const { status, startDate, endDate } = filters.value

  return sourceRecords.value
    .filter(record => {
      const searchable = [
        isInbound.value ? record.inboundNo : record.orderNo,
        record.supplierName,
        record.warehouseName,
        record.itemSummary
      ].join(' ').toLowerCase()
      const date = recordDate(record)
      return (!keyword || searchable.includes(keyword))
        && (status === 'all' || record.status === status)
        && (!startDate || date >= startDate)
        && (!endDate || date <= endDate)
    })
    .sort((a, b) => recordDate(b).localeCompare(recordDate(a)))
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize)))
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredRecords.value.slice(start, start + pageSize)
})
const pageNumbers = computed(() => Array.from({ length: totalPages.value }, (_, index) => index + 1))
const currentPageIds = computed(() => paginatedRecords.value.map(record => record.id))
const isAllPageSelected = computed(() => currentPageIds.value.length > 0 && currentPageIds.value.every(id => selectedIds.value.has(id)))
const isSomePageSelected = computed(() => currentPageIds.value.some(id => selectedIds.value.has(id)) && !isAllPageSelected.value)

watch(
  () => props.mode,
  () => {
    filters.value = { keyword: '', status: 'all', startDate: '', endDate: '' }
    currentPage.value = 1
    selectedIds.value = new Set()
    closeDetail()
  }
)

watch(
  () => [filters.value.keyword, filters.value.status, filters.value.startDate, filters.value.endDate],
  () => {
    currentPage.value = 1
    selectedIds.value = new Set()
  }
)

watch(totalPages, value => {
  if (currentPage.value > value) currentPage.value = value
})

function recordDate(record) {
  return isInbound.value ? record.documentDate : record.purchaseDate
}

function getRecordNo(record) {
  return isInbound.value ? record.inboundNo : record.orderNo
}

function formatDate(value) {
  if (!value) return '—'
  return value.replace(/-/g, '.')
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function quantityValue(record) {
  return isInbound.value ? record.receivedQuantity : record.totalQuantity
}

function recordProgress(record) {
  if (!record.expectedQuantity) return 0
  return Math.min(100, Math.round((record.receivedQuantity / record.expectedQuantity) * 100))
}

function getStatusLabel(status) {
  const tab = statusTabs.value.find(item => item.key === status)
  return tab?.label || status
}

function getStatusClass(status) {
  if (status === 'pending' || status === 'draft') return 'pending'
  if (status === 'confirmed' || status === 'reviewed') return 'confirmed'
  if (status === 'partial') return 'processing'
  if (status === 'completed' || status === 'posted') return 'completed'
  return 'rejected'
}

function canEdit(record) {
  return !isInbound.value || !['reviewed', 'posted', 'cancelled'].includes(record.status)
}

function applyFilters() {
  currentPage.value = 1
}

function resetFilters() {
  filters.value = { keyword: '', status: 'all', startDate: '', endDate: '' }
}

function setStatusFilter(status) {
  filters.value.status = status
  currentPage.value = 1
}

function toggleSelection(id) {
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

function togglePageSelection(event) {
  const next = new Set(selectedIds.value)
  if (event.target.checked) {
    currentPageIds.value.forEach(id => next.add(id))
  } else {
    currentPageIds.value.forEach(id => next.delete(id))
  }
  selectedIds.value = next
}

function isSelected(id) {
  return selectedIds.value.has(id)
}

function clearSelection() {
  selectedIds.value = new Set()
}

function openDetail(record) {
  selectedRecord.value = record
  detailModalOpen.value = true
}

function closeDetail() {
  detailModalOpen.value = false
  selectedRecord.value = null
}

function showNotice(message) {
  notice.value = message
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => {
    notice.value = ''
  }, 3200)
}

function createRecord() {
  if (isInbound.value) {
    router.push({ name: 'admin-purchase-inbound-create' })
    return
  }
  showNotice('采购订单新增接口待接入，当前页面使用演示数据')
}

function editRecord(record) {
  if (!isInbound.value) {
    openDetail(record)
    showNotice('采购订单编辑接口待接入，当前先展示订单详情')
    return
  }
  router.push({ name: 'admin-purchase-inbound-edit', params: { id: record.id } })
}

function printRecord(record) {
  if (!isInbound.value) return
  router.push({ path: `/admin/purchase/inbound/${record.id}`, query: { print: '1' } })
}

function exportRecords() {
  showNotice('导出接口待接入，当前列表为演示数据')
}

function refreshData() {
  loading.value = true
  window.setTimeout(() => {
    if (isInbound.value) {
      inboundRecords.value = cloneRecords(mockInbounds)
    } else {
      orderRecords.value = cloneRecords(mockOrders)
    }
    loading.value = false
    showNotice('列表已刷新')
  }, 350)
}

function copyDocumentNo() {
  const documentNo = selectedRecord.value ? getRecordNo(selectedRecord.value) : ''
  if (!documentNo) return
  navigator.clipboard?.writeText(documentNo)
  showNotice(`已复制单号 ${documentNo}`)
}
</script>

<style scoped>
:global(body) {
  background: #f4f6f8;
}

.purchase-list-page {
  --ink: #17202b;
  --muted: #718096;
  --line: #e7ebef;
  --soft-line: #f0f2f5;
  --panel: #ffffff;
  --accent: #1f6f8b;
  --accent-dark: #14536a;
  --green: #24865c;
  --amber: #b8781f;
  --red: #bd5c55;
  min-height: 100%;
  padding: 24px 28px 36px;
  color: var(--ink);
}

.search-panel,
.records-panel {
  width: 100%;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.search-panel {
  padding: 20px 22px;
  margin-bottom: 18px;
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1.7fr) repeat(3, minmax(140px, 0.8fr)) auto;
  gap: 14px;
  align-items: end;
}

.search-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.field-label {
  color: #7c8793;
  font-size: 12px;
  line-height: 1;
}

.search-field input,
.search-field select {
  width: 100%;
  height: 38px;
  padding: 0 11px;
  border: 1px solid #dfe5ea;
  border-radius: 5px;
  outline: none;
  background: #fff;
  color: var(--ink);
  font: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-field input:focus,
.search-field select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(31, 111, 139, 0.11);
}

.input-with-icon {
  position: relative;
  display: block;
}

.input-with-icon svg {
  position: absolute;
  left: 11px;
  top: 11px;
  width: 16px;
  height: 16px;
  fill: none;
  stroke: #99a3ae;
  stroke-width: 1.8;
  pointer-events: none;
}

.input-with-icon input {
  padding-left: 35px;
}

.search-actions {
  display: flex;
  gap: 8px;
}

.button,
.icon-button,
.table-action,
.status-tab,
.modal-close,
.document-link,
.pagination button,
.selection-summary button {
  border: 0;
  cursor: pointer;
  font: inherit;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 5px;
  white-space: nowrap;
  transition: 0.2s ease;
}

.button svg,
.icon-button svg,
.table-action svg,
.modal-document-no svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.button-primary {
  background: var(--accent);
  color: #fff;
}

.button-primary:hover {
  background: var(--accent-dark);
}

.button-secondary {
  background: #edf4f6;
  color: var(--accent-dark);
}

.button-secondary:hover {
  background: #e1edf0;
}

.button-ghost {
  border: 1px solid #dfe5ea;
  background: #fff;
  color: #53606d;
}

.button-ghost:hover {
  border-color: #b7c5cd;
  color: var(--accent-dark);
}

.records-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  padding: 22px 22px 17px;
}

.toolbar-heading {
  display: flex;
  align-items: baseline;
  gap: 11px;
  min-width: 0;
}

.page-kicker,
.modal-kicker {
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

.toolbar-heading h1 {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0;
}

.record-count {
  color: var(--muted);
  font-size: 12px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 36px;
  padding: 0 8px;
  background: transparent;
  color: #6e7b87;
  font-size: 12px;
}

.icon-button:hover {
  color: var(--accent-dark);
}

.status-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 22px;
  border-bottom: 1px solid var(--line);
  overflow-x: auto;
}

.status-tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 43px;
  padding: 0 10px;
  background: transparent;
  color: #73808c;
  font-size: 13px;
  white-space: nowrap;
}

.status-tab::after {
  position: absolute;
  right: 10px;
  bottom: -1px;
  left: 10px;
  height: 2px;
  background: transparent;
  content: '';
}

.status-tab strong {
  min-width: 18px;
  padding: 1px 5px;
  border-radius: 10px;
  background: #f0f3f5;
  color: #7b8791;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}

.status-tab.active {
  color: var(--accent-dark);
  font-weight: 600;
}

.status-tab.active::after {
  background: var(--accent);
}

.status-tab.active strong {
  background: #e5f0f3;
  color: var(--accent-dark);
}

.notice-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 14px 22px 0;
  padding: 9px 12px;
  border: 1px solid #dbe9ed;
  background: #f3f8f9;
  color: var(--accent-dark);
  font-size: 12px;
}

.notice-bar button {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1160px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

.records-table th {
  height: 43px;
  padding: 0 11px;
  border-bottom: 1px solid var(--line);
  background: #fafbfc;
  color: #87929d;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.records-table td {
  height: 70px;
  padding: 10px 11px;
  border-bottom: 1px solid var(--soft-line);
  color: #4e5b67;
  vertical-align: middle;
}

.records-table tbody tr {
  transition: background 0.15s;
}

.records-table tbody tr:not(.skeleton-row):hover {
  background: #fbfcfd;
}

.records-table th:nth-child(1),
.records-table td:nth-child(1) {
  width: 42px;
  padding-left: 22px;
}

.records-table th:nth-child(2),
.records-table td:nth-child(2) {
  width: 145px;
}

.records-table th:nth-child(3),
.records-table td:nth-child(3) {
  width: 100px;
}

.records-table th:nth-child(4),
.records-table td:nth-child(4) {
  width: 150px;
}

.records-table th:nth-child(5),
.records-table td:nth-child(5) {
  width: 180px;
}

.records-table th:nth-child(6),
.records-table td:nth-child(6) {
  width: 132px;
}

.records-table th:nth-child(7),
.records-table td:nth-child(7) {
  width: 112px;
}

.records-table th:nth-child(8),
.records-table td:nth-child(8) {
  width: 105px;
}

.records-table th:nth-child(9),
.records-table td:nth-child(9) {
  width: 103px;
}

.records-table th:nth-child(10),
.records-table td:nth-child(10) {
  width: 155px;
}

.records-table th:nth-child(11),
.records-table td:nth-child(11) {
  width: 92px;
}

.records-table input[type='checkbox'] {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
  cursor: pointer;
}

.document-link {
  padding: 0;
  background: transparent;
  color: var(--accent-dark);
  font-weight: 650;
  text-align: left;
}

.document-link:hover {
  text-decoration: underline;
}

.primary-cell {
  overflow: hidden;
  color: #34414d;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.secondary-cell {
  margin-top: 4px;
  overflow: hidden;
  color: #96a0a9;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-summary {
  font-weight: 500;
}

.date-cell {
  color: #677581;
  white-space: nowrap;
}

.quantity-cell {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: #3f4d59;
}

.quantity-cell strong {
  font-size: 14px;
}

.quantity-cell span {
  color: #99a3ad;
  font-size: 11px;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 7px;
}

.progress-track {
  width: 54px;
  height: 4px;
  overflow: hidden;
  border-radius: 3px;
  background: #e8edf0;
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--green);
}

.progress-cell small {
  color: #7d8993;
  font-size: 10px;
}

.amount-cell {
  color: #34414d !important;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #66737e;
  font-size: 12px;
  white-space: nowrap;
}

.status-tag i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-pending {
  color: var(--amber);
}

.status-confirmed {
  color: #4d7891;
}

.status-processing {
  color: #996f28;
}

.status-completed {
  color: var(--green);
}

.status-rejected {
  color: var(--red);
}

.remark-cell {
  overflow: hidden;
  color: #8c98a2 !important;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-column {
  text-align: right !important;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.table-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 29px;
  height: 29px;
  border-radius: 4px;
  background: transparent;
  color: #81909b;
}

.table-action:hover {
  background: #eef5f6;
  color: var(--accent-dark);
}

.empty-cell {
  height: 310px !important;
  padding: 0 !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 310px;
  color: #8b97a1;
}

.empty-state strong {
  color: #596672;
  font-size: 14px;
}

.empty-state span {
  font-size: 12px;
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin-bottom: 5px;
  border-radius: 50%;
  background: #f2f5f6;
}

.empty-icon svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: #9aa6ae;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
  padding: 0 22px;
  color: #8a96a0;
  font-size: 12px;
}

.selection-summary strong {
  color: var(--accent-dark);
}

.selection-summary button {
  margin-left: 8px;
  padding: 0;
  background: transparent;
  color: var(--accent);
  font-size: 12px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination > span {
  margin-right: 8px;
}

.pagination button {
  min-width: 28px;
  height: 28px;
  padding: 0 7px;
  border-radius: 4px;
  background: transparent;
  color: #7a8791;
  font-size: 12px;
}

.pagination button:hover:not(:disabled),
.pagination button.active {
  background: #eaf2f4;
  color: var(--accent-dark);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.skeleton-row td span {
  display: block;
  width: 70%;
  height: 12px;
  border-radius: 3px;
  background: linear-gradient(90deg, #f0f3f5 25%, #f7f8f9 50%, #f0f3f5 75%);
  background-size: 200% 100%;
  animation: skeleton 1.2s infinite;
}

.detail-modal-layer {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(21, 31, 40, 0.46);
}

.detail-modal {
  display: flex;
  flex-direction: column;
  width: min(1120px, 100%);
  max-height: min(860px, calc(100vh - 48px));
  overflow: hidden;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(22, 39, 53, 0.2);
}

.detail-modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 28px 19px;
  border-bottom: 1px solid var(--line);
}

.detail-modal-header h2 {
  margin: 6px 0 4px;
  color: #1a2732;
  font-size: 21px;
}

.modal-document-no {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0;
  background: transparent;
  color: var(--accent-dark);
  cursor: pointer;
  font-size: 12px;
}

.modal-close {
  align-self: flex-start;
  width: 28px;
  height: 28px;
  background: transparent;
  color: #8a969f;
  font-size: 25px;
  line-height: 1;
}

.modal-close:hover {
  color: #35434f;
}

.detail-modal-body {
  overflow-y: auto;
  padding: 22px 28px 30px;
}

.detail-overview {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 18px;
  padding: 16px 18px;
  border: 1px solid #e4ecef;
  background: #f8fbfb;
}

.detail-overview > div {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-label,
.meta-grid span {
  color: #8b98a2;
  font-size: 11px;
}

.detail-overview strong {
  color: #35434f;
  font-size: 14px;
}

.overview-amount {
  color: var(--accent-dark) !important;
  font-size: 17px !important;
}

.status-tag.large {
  font-size: 13px;
}

.detail-section {
  margin-top: 25px;
}

.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 12px;
}

.section-heading h3 {
  margin: 0;
  color: #34424e;
  font-size: 14px;
}

.section-heading span {
  color: #8c98a2;
  font-size: 11px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-bottom: 4px;
}

.meta-grid div {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.meta-grid strong {
  overflow: hidden;
  color: #465561;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-items-scroll {
  overflow-x: auto;
  border: 1px solid var(--line);
}

.detail-items-table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
  font-size: 12px;
}

.detail-items-table th {
  height: 38px;
  padding: 0 10px;
  background: #fafbfc;
  color: #89959f;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
}

.detail-items-table td {
  height: 43px;
  padding: 0 10px;
  border-top: 1px solid var(--soft-line);
  color: #53616c;
  white-space: nowrap;
}

.remark-section p {
  margin: 0;
  padding: 12px 14px;
  background: #fafbfc;
  color: #65727d;
  font-size: 12px;
  line-height: 1.7;
}

.detail-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 15px 28px;
  border-top: 1px solid var(--line);
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.detail-modal-enter-active,
.detail-modal-leave-active {
  transition: opacity 0.2s ease;
}

.detail-modal-enter-active .detail-modal,
.detail-modal-leave-active .detail-modal {
  transition: transform 0.2s ease;
}

.detail-modal-enter-from,
.detail-modal-leave-to {
  opacity: 0;
}

.detail-modal-enter-from .detail-modal,
.detail-modal-leave-to .detail-modal {
  transform: translateY(12px);
}

@keyframes skeleton {
  to {
    background-position: -200% 0;
  }
}

@media (max-width: 1100px) {
  .search-grid {
    grid-template-columns: repeat(3, minmax(150px, 1fr));
  }

  .keyword-field {
    grid-column: span 2;
  }

  .search-actions {
    grid-column: span 1;
  }
}

@media (max-width: 760px) {
  .purchase-list-page {
    padding: 14px 12px 24px;
  }

  .search-panel {
    padding: 16px;
  }

  .search-grid {
    grid-template-columns: 1fr;
  }

  .keyword-field,
  .search-actions {
    grid-column: auto;
  }

  .search-actions .button {
    flex: 1;
  }

  .records-toolbar {
    align-items: flex-start;
    flex-direction: column;
    padding: 17px 16px 14px;
  }

  .toolbar-heading {
    flex-wrap: wrap;
    gap: 6px 10px;
  }

  .toolbar-actions {
    width: 100%;
  }

  .toolbar-actions .button-primary {
    flex: 1;
  }

  .status-tabs {
    padding: 0 12px;
  }

  .table-footer {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px 16px 16px;
  }

  .detail-modal-layer {
    align-items: flex-end;
    padding: 0;
  }

  .detail-modal {
    max-height: 92vh;
    border-radius: 8px 8px 0 0;
  }

  .detail-modal-header,
  .detail-modal-body,
  .detail-modal-footer {
    padding-right: 18px;
    padding-left: 18px;
  }

  .detail-overview,
  .meta-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* 采购列表统一使用后台紧凑型列表规范 */
.purchase-list-page {
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
  padding: 18px 20px 28px;
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

.purchase-list-page *,
.purchase-list-page *::before,
.purchase-list-page *::after {
  box-sizing: border-box;
}

.purchase-list-page button:focus-visible,
.purchase-list-page input:focus-visible,
.purchase-list-page select:focus-visible,
.purchase-list-page .record-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.purchase-list-page svg {
  stroke-linecap: round;
  stroke-linejoin: round;
}

.search-panel,
.records-panel {
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.search-panel {
  padding: 18px 20px;
  margin-bottom: 14px;
}

.search-grid {
  grid-template-columns: minmax(200px, 1fr) minmax(280px, 1.45fr) minmax(160px, 1fr) auto;
  gap: 14px;
}

.search-field {
  gap: 7px;
}

.field-label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.search-field input,
.search-field select {
  height: 38px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
}

.search-field input::placeholder {
  color: #a2adba;
}

.search-field input:focus,
.search-field select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
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

.button {
  height: 38px;
  min-height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
  box-shadow: 0 2px 5px rgba(var(--accent-rgb), 0.18);
}

.button-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.button-ghost,
.button-secondary,
.button-export {
  color: #445066;
  background: #fff;
  border: 1px solid var(--border-strong);
}

.button-ghost:hover,
.button-secondary:hover,
.button-export:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.records-panel {
  margin-top: 14px;
  overflow: hidden;
  background: var(--panel-bg);
}

.records-toolbar {
  min-height: 62px;
  align-items: center;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-filters {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.toolbar-heading {
  flex: 0 0 auto;
  gap: 8px;
  align-items: baseline;
  padding-right: 8px;
}

.page-kicker {
  color: var(--accent-dark);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.toolbar-heading h1 {
  color: var(--text);
  font-size: 16px;
  font-weight: 650;
}

.status-filter-slider {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.slider-tab {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
  white-space: nowrap;
}

.slider-tab:hover {
  color: var(--accent-dark);
  background: rgba(var(--accent-rgb), 0.1);
}

.slider-tab.active {
  color: #fff;
  background: var(--accent);
  box-shadow: 0 2px 6px rgba(var(--accent-rgb), 0.3);
}

.count-badge {
  display: inline-flex;
  min-width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.slider-tab.active .count-badge {
  color: #fff;
  background: rgba(255, 255, 255, 0.25);
}

.selection-count {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  padding: 0 4px;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.selection-count strong {
  color: var(--accent-dark);
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.toolbar-actions {
  gap: 8px;
}

.toolbar-actions .record-count {
  margin-right: 3px;
  color: var(--text-muted);
  white-space: nowrap;
}

.icon-button {
  width: 36px;
  height: 36px;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
}

.icon-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.status-tabs,
.notice-bar {
  display: none;
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 3000;
  display: flex;
  min-height: 44px;
  max-width: min(520px, calc(100vw - 32px));
  align-items: center;
  gap: 9px;
  padding: 10px 12px 10px 16px;
  color: var(--text);
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.page-notice svg {
  width: 19px;
  height: 19px;
  flex: 0 0 19px;
  color: var(--accent);
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.page-notice button {
  width: 24px;
  height: 24px;
  margin-left: 2px;
  color: var(--text-muted);
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.notice-enter-active,
.notice-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.notice-enter-from,
.notice-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

.records-table {
  min-width: 1320px;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
}

.records-table tbody tr:last-child td {
  border-bottom: 0;
}

.records-table th:nth-child(1),
.records-table td:nth-child(1) {
  width: 50px;
  padding: 0 16px;
  text-align: center;
}

.records-table th:nth-child(2),
.records-table td:nth-child(2) {
  width: 140px;
}

.records-table th:nth-child(3),
.records-table td:nth-child(3) {
  width: 110px;
}

.records-table th:nth-child(4),
.records-table td:nth-child(4) {
  width: 150px;
}

.records-table th:nth-child(5),
.records-table td:nth-child(5) {
  width: 170px;
}

.records-table th:nth-child(6),
.records-table td:nth-child(6) {
  width: 110px;
  text-align: right;
}

.records-table th:nth-child(7),
.records-table td:nth-child(7) {
  width: 120px;
}

.records-table th:nth-child(8),
.records-table td:nth-child(8) {
  width: 110px;
  text-align: right;
}

.records-table th:nth-child(9),
.records-table td:nth-child(9) {
  width: 110px;
}

.records-table th:nth-child(10),
.records-table td:nth-child(10) {
  width: 140px;
}

.records-table th:nth-child(11),
.records-table td:nth-child(11) {
  width: 100px;
  text-align: center !important;
}

.records-table input[type='checkbox'] {
  width: 18px;
  height: 18px;
  margin: 0;
  vertical-align: middle;
  accent-color: var(--accent);
}

.record-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.record-row:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.record-row.selected {
  background: rgba(var(--accent-rgb), 0.12);
}

.document-link {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 4px;
  padding: 3px 0;
  color: var(--accent-dark);
  font-weight: 700;
}

.document-link::after {
  content: '›';
  color: var(--accent);
  font-size: 16px;
  line-height: 1;
}

.primary-cell {
  color: #283548;
  font-size: 13px;
  font-weight: 650;
}

.secondary-cell {
  color: var(--text-muted);
  font-size: 11px;
}

.date-cell,
.remark-cell,
.secondary-cell {
  color: var(--text-secondary);
}

.quantity-cell {
  justify-content: flex-end;
  font-variant-numeric: tabular-nums;
}

.amount-cell {
  color: #182230 !important;
  font-weight: 750;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.status-tag {
  min-height: 25px;
  padding: 3px 9px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
}

.status-pending {
  color: #a4510b;
  background: #fff3df;
  border-color: #f3c887;
}

.status-confirmed {
  color: #16647a;
  background: #e7f5f8;
  border-color: #a9dce5;
}

.status-processing {
  color: #1d4ed8;
  background: #dbeafe;
  border-color: #93c5fd;
}

.status-completed {
  color: #13734f;
  background: #eaf8f1;
  border-color: #a7e2c9;
}

.status-rejected {
  color: #b4232f;
  background: #f1f2f4;
  border-color: #d8dce2;
}

.row-actions {
  justify-content: center;
  gap: 6px;
}

.table-action {
  width: 29px;
  height: 29px;
  color: #667085;
  background: #fff;
  border: 1px solid #d9e0e8;
  border-radius: 4px;
}

.table-action:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.empty-cell {
  height: 290px !important;
  color: var(--text-muted) !important;
}

.empty-state {
  height: 290px;
}

.empty-icon {
  background: #f1f4f7;
}

.table-footer {
  min-height: 58px;
  padding: 10px 16px;
  color: var(--text-secondary);
  background: #fff;
  border-top: 1px solid var(--border);
}

.selection-summary strong {
  color: var(--text);
}

.pagination {
  gap: 8px;
}

.pagination button {
  min-width: 31px;
  height: 31px;
  color: #526074;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
}

.pagination button:hover:not(:disabled),
.pagination button.active {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent);
}

.pagination button:disabled {
  opacity: 0.4;
}

.detail-modal-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --panel-bg: #fff;
  --border: #dfe5ec;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  z-index: 2147482000;
  padding: 24px;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.detail-modal {
  width: min(960px, calc(100vw - 48px));
  max-height: min(880px, calc(100vh - 48px));
  color: var(--text);
  background: #f4f7f9;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
}

.detail-modal-header {
  min-height: 78px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.detail-modal-title-wrap {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.detail-modal-mark {
  display: inline-flex;
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  align-items: center;
  justify-content: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 7px;
}

.detail-modal-mark svg {
  width: 21px;
  height: 21px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.detail-modal-header h2 {
  margin: 3px 0 0;
  color: var(--text);
  font-size: 18px;
  letter-spacing: 0;
}

.modal-kicker {
  color: #758195;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.modal-document-no {
  padding: 0;
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 600;
}

.modal-close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  color: #68758a;
  border-radius: 5px;
  font-size: 0;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-close:hover {
  color: #273245;
  background: #f0f3f6;
}

.detail-modal-body {
  padding: 18px;
  background: #f4f7f9;
}

.detail-overview,
.detail-section {
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.detail-overview {
  padding: 17px;
}

.detail-section {
  margin-top: 15px;
  overflow: hidden;
}

.section-heading {
  min-height: 53px;
  align-items: center;
  padding: 11px 15px;
  border-bottom: 1px solid #e5eaf0;
}

.section-heading h3 {
  color: #263348;
  font-size: 14px;
}

.section-heading span {
  color: #8a96a8;
}

.meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 22px;
  margin: 17px 0;
}

.meta-grid span,
.detail-label {
  color: #8a96a8;
  font-size: 11px;
}

.meta-grid strong,
.detail-overview strong {
  color: #283548;
  font-size: 13px;
}

.overview-amount {
  color: var(--accent-dark) !important;
  font-size: 16px !important;
}

.detail-items-scroll {
  border: 0;
}

.detail-items-table {
  min-width: 820px;
}

.detail-items-table th {
  height: 40px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid #e5eaf0;
  font-size: 12px;
}

.detail-items-table td {
  height: 43px;
  padding: 0 12px;
  border-top: 1px solid #edf1f5;
}

.detail-items-table th:nth-last-child(-n + 3),
.detail-items-table td:nth-last-child(-n + 3) {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.remark-section p {
  padding: 15px;
  color: #374151;
  line-height: 1.6;
}

.detail-modal-footer {
  min-height: 68px;
  padding: 13px 18px;
  background: #fff;
  border-top: 1px solid var(--border);
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .keyword-field {
    grid-column: span 1;
  }

  .search-actions {
    grid-column: span 1;
  }

  .toolbar-heading {
    display: none;
  }
}

@media (max-width: 780px) {
  .purchase-list-page {
    padding: 12px 12px 20px;
  }

  .search-grid {
    grid-template-columns: 1fr;
  }

  .keyword-field,
  .search-actions {
    grid-column: auto;
  }

  .search-actions .button {
    flex: 1;
  }

  .records-toolbar {
    align-items: stretch;
    flex-direction: column;
    padding: 11px 12px;
  }

  .toolbar-filters,
  .toolbar-actions {
    width: 100%;
  }

  .status-filter-slider {
    flex: 1;
    overflow-x: auto;
  }

  .slider-tab {
    flex: 0 0 auto;
    padding: 0 11px;
  }

  .toolbar-actions .record-count {
    margin-right: auto;
  }

  .detail-modal-layer {
    align-items: flex-end;
    padding: 0;
  }

  .detail-modal {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
  }

  .detail-modal-header,
  .detail-modal-body,
  .detail-modal-footer {
    padding-right: 18px;
    padding-left: 18px;
  }

  .detail-modal-footer {
    flex-wrap: wrap;
  }

  .detail-overview,
  .meta-grid {
    grid-template-columns: 1fr 1fr;
  }

  .page-notice {
    top: 12px;
  }
}
</style>
