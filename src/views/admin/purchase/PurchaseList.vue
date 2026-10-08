<template>
  <div class="purchase-list-page" :class="{ 'is-inbound': isInbound, 'is-return': isReturn }">
    <template v-if="isReturn">
      <section class="search-panel">
        <div class="search-grid return-search-grid">
          <label class="search-field keyword-field">
            <span class="field-label">单号 / 供应商</span>
            <span class="input-with-icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4.5 4.5"></path>
              </svg>
              <input v-model.trim="returnFilters.keyword" type="search" placeholder="单号、供应商、门店" @keyup.enter="applyReturnFilters" />
            </span>
          </label>
          <label class="search-field">
            <span class="field-label">门店</span>
            <select v-model="returnFilters.storeId" @change="onReturnStoreChange">
              <option value="">全部授权门店</option>
              <option v-for="store in returnOptions.stores" :key="store.id" :value="String(store.id)">{{ store.name }}</option>
            </select>
          </label>
          <label class="search-field">
            <span class="field-label">供应商</span>
            <select v-model="returnFilters.supplierId">
              <option value="">全部供应商</option>
              <option v-for="supplier in returnSuppliersForFilter" :key="supplier.id" :value="String(supplier.id)">{{ supplier.supplierName }}</option>
            </select>
          </label>
          <div class="search-field date-field">
            <span class="field-label">业务日期</span>
            <div class="date-range">
              <input v-model="returnFilters.startDate" type="date" :max="returnFilters.endDate || undefined" aria-label="开始日期" />
              <span aria-hidden="true">至</span>
              <input v-model="returnFilters.endDate" type="date" :min="returnFilters.startDate || undefined" aria-label="结束日期" />
            </div>
          </div>
          <label class="search-field">
            <span class="field-label">状态</span>
            <select v-model="returnFilters.status">
              <option value="all">全部状态</option>
              <option v-for="option in returnStatusOptions" :key="option.key" :value="option.key">{{ option.label }}</option>
            </select>
          </label>
          <div class="search-actions">
            <button class="button button-primary" type="button" @click="applyReturnFilters">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="11" cy="11" r="6.5"></circle>
                <path d="m16 16 4.5 4.5"></path>
              </svg>
              查询
            </button>
            <button class="button button-ghost" type="button" @click="resetReturnFilters">
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
              <div class="page-kicker">采购执行</div>
              <h1>采购退货</h1>
            </div>
            <div class="status-filter-slider" role="tablist" aria-label="采购退货状态筛选">
              <button
                v-for="tab in returnStatusTabs"
                :key="tab.key"
                :class="['slider-tab', { active: returnFilters.status === tab.key }]"
                type="button"
                role="tab"
                :aria-selected="returnFilters.status === tab.key"
                @click="setReturnStatusFilter(tab.key)"
              >
                {{ tab.label }}
                <span class="count-badge">{{ tab.count }}</span>
              </button>
            </div>
          </div>
          <div class="toolbar-actions">
            <span class="record-count">共 {{ returnFilteredRecords.length }} 条记录</span>
            <button class="icon-button refresh-button" type="button" title="刷新列表" @click="refreshData">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M20 11a8.1 8.1 0 0 0-14.8-4L3 10"></path>
                <path d="M3 4v6h6"></path>
                <path d="M4 13a8.1 8.1 0 0 0 14.8 4L21 14"></path>
                <path d="M21 20v-6h-6"></path>
              </svg>
            </button>
            <button v-if="canReturn('create')" class="button button-primary" type="button" @click="createReturn">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 5v14"></path>
                <path d="M5 12h14"></path>
              </svg>
              新增采购退货
            </button>
          </div>
        </header>

        <div v-if="returnError" class="notice-bar return-error" role="alert">{{ returnError }}</div>
        <div class="return-summary">
          <span>单据数<strong>{{ returnFilteredRecords.length }}</strong></span>
          <span>已审核退货金额<strong>{{ formatMoney(returnAuditedTotal) }}</strong></span>
          <span>已审核单据<strong>{{ returnAuditedCount }}</strong></span>
        </div>
        <div class="table-scroll">
          <table class="records-table return-records-table">
            <thead>
              <tr>
                <th>退货单号</th>
                <th>供应商 / 门店</th>
                <th>业务日期</th>
                <th>明细数</th>
                <th>退货数量</th>
                <th>原成本</th>
                <th>确认退货金额</th>
                <th>状态</th>
                <th>制单 / 审核</th>
                <th class="action-column">操作</th>
              </tr>
            </thead>
            <tbody v-if="loading">
              <tr v-for="index in 6" :key="`return-skeleton-${index}`" class="skeleton-row">
                <td v-for="column in 10" :key="column"><span></span></td>
              </tr>
            </tbody>
            <tbody v-else-if="returnPaginatedRecords.length">
              <tr v-for="record in returnPaginatedRecords" :key="record.id" class="record-row">
                <td>
                  <button class="document-link" type="button" @click="openReturnDetail(record)">
                    {{ record.documentNo }}
                  </button>
                </td>
                <td>
                  <div class="primary-cell">{{ record.supplierName }}</div>
                  <div class="secondary-cell">{{ record.storeName }}</div>
                </td>
                <td class="date-cell">{{ formatDate(record.businessDate) }}</td>
                <td>{{ record.items?.length || 0 }}</td>
                <td class="quantity-cell">{{ returnQuantityLabel(record) }}</td>
                <td class="amount-cell">¥ {{ formatMoney(record.originalCost) }}</td>
                <td class="amount-cell">¥ {{ formatMoney(record.returnAmount) }}</td>
                <td>
                  <span class="status-tag" :class="`status-${returnStatusClass(record.status)}`">
                    <i></i>{{ returnStatusLabels[record.status] || record.status }}
                  </span>
                  <div v-if="record.lockedAt" class="secondary-cell">已锁期</div>
                </td>
                <td>
                  <div class="primary-cell">{{ record.createdBy || '-' }}</div>
                  <div class="secondary-cell">{{ record.auditedBy || '-' }}</div>
                </td>
                <td class="action-column" @click.stop>
                  <div class="row-actions">
                    <button class="table-action" type="button" title="查看详情" @click="openReturnDetail(record)">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                        <circle cx="12" cy="12" r="2.5"></circle>
                      </svg>
                    </button>
                    <button v-if="record.status === 'draft' && !record.lockedAt && canReturn('edit')" class="table-action" type="button" title="编辑草稿" @click="editReturn(record)">
                      <Pencil :size="15" aria-hidden="true" />
                    </button>
                    <button v-if="['draft', 'reversed'].includes(record.status) && !record.lockedAt && canReturn('audit')" class="table-action audit-action" type="button" title="审核退货" @click="confirmReturnAction(record, 'audit')">
                      <Check :size="15" aria-hidden="true" />
                    </button>
                    <button v-if="record.status === 'audited' && !record.lockedAt && canReturn('reverse_audit')" class="table-action" type="button" title="反审核" @click="confirmReturnAction(record, 'reverse-audit')">
                      <RotateCcw :size="15" aria-hidden="true" />
                    </button>
                    <button v-if="record.status === 'draft' && !record.lockedAt && canReturn('delete')" class="table-action danger" type="button" title="删除草稿" @click="confirmReturnAction(record, 'delete')">
                      <Trash2 :size="15" aria-hidden="true" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="10" class="empty-cell">
                  <div class="empty-state">
                    <div class="empty-icon">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11l2.5 2.5v13a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 18.5Z"></path>
                        <path d="M8 8h8M8 12h8M8 16h5"></path>
                      </svg>
                    </div>
                    <strong>暂无采购退货记录</strong>
                    <span>调整筛选条件，或创建一张新的采购退货单</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="table-footer">
          <div class="selection-summary">共 {{ returnFilteredRecords.length }} 条</div>
          <div class="pagination">
            <span>共 {{ returnFilteredRecords.length }} 条</span>
            <button type="button" :disabled="returnCurrentPage === 1" @click="returnCurrentPage -= 1">上一页</button>
            <button
              v-for="page in returnPageNumbers"
              :key="page"
              type="button"
              :class="{ active: page === returnCurrentPage }"
              @click="returnCurrentPage = page"
            >
              {{ page }}
            </button>
            <button type="button" :disabled="returnCurrentPage === returnTotalPages" @click="returnCurrentPage += 1">下一页</button>
          </div>
        </div>
      </section>
      <CustomModal
        :visible="Boolean(returnPendingAction)"
        :title="returnActionTitle"
        :message="returnActionMessage"
        @confirm="actReturn"
        @cancel="returnPendingAction = null"
      />
    </template>
    <template v-else>
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
          <span class="field-label">{{ isInbound ? '入库日期' : '申请日期' }}</span>
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

        <label v-if="!isInbound" class="search-field">
          <span class="field-label">开票状态</span>
          <select v-model="filters.invoiceStatus">
            <option value="">全部</option>
            <option v-for="(label, key) in invoiceLabels" :key="key" :value="key">{{ label }}</option>
          </select>
        </label>
        <label v-if="!isInbound" class="search-field">
          <span class="field-label">付款状态</span>
          <select v-model="filters.paymentStatus">
            <option value="">全部</option>
            <option v-for="(label, key) in paymentFilterLabels" :key="key" :value="key">{{ label }}</option>
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
            <h1>{{ isInbound ? '采购入库申请' : '采购订单' }}</h1>
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
          <button v-if="isInbound" class="button button-ghost" type="button" @click="router.push({ name: 'admin-purchase-inbound-application-create' })">
            <Plus :size="16" aria-hidden="true" />申请采购
          </button>
          <button class="button button-primary" type="button" @click="createRecord">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            {{ isInbound ? '新增入库单' : '新增采购单' }}
          </button>
          <button
            v-if="isInbound && canDelete"
            class="button button-danger"
            type="button"
            :disabled="!selectedIds.size || loading || deleting"
            @click="confirmDeleteSelected"
          >
            <Trash2 :size="16" aria-hidden="true" />
            {{ deleting ? '删除中...' : '批量删除' }}
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <colgroup v-if="isInbound">
            <col style="width: 38px">
            <col style="width: 150px">
            <col style="width: 110px">
            <col style="width: 120px">
            <col style="width: 140px">
            <col style="width: 170px">
            <col style="width: 140px">
            <col style="width: 90px">
            <col style="width: 115px">
            <col>
            <col style="width: 170px">
          </colgroup>
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
              <th>{{ isInbound ? '入库日期' : '申请日期' }}</th>
              <th v-if="isInbound">仓库</th>
              <th v-else>门店</th>
              <th>供应商</th>
              <th>{{ isInbound ? '商品物品名称' : '物料摘要' }}</th>
              <th>{{ isInbound ? '入库数量/总数量' : '计划采购数量' }}</th>
              <th v-if="isInbound">进度</th>
              <th v-if="!isInbound">应付金额</th>
              <template v-if="!isInbound">
                <th class="finance-column amount-cell">付款金额</th>
                <th class="finance-column payment-status-cell">付款状态</th>
              </template>
              <th>{{ isInbound ? '入库状态' : '履约状态' }}</th>
              <th v-if="!isInbound" class="finance-column">开票状态</th>
              <th>备注</th>
              <th class="action-column">操作</th>
            </tr>
          </thead>
          <tbody v-if="loading">
            <tr v-for="index in 6" :key="`skeleton-${index}`" class="skeleton-row">
              <td v-for="column in recordTableColumnCount" :key="column"><span></span></td>
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
                  :disabled="isInbound && record.sourceType === 'inbound-application' && ['draft', 'pending_review'].includes(record.status)"
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
              <td v-if="isInbound">{{ record.warehouseName }}</td>
              <td v-else>{{ record.storeName || '—' }}</td>
              <td>
                <div v-if="supplierNamesFor(record).length > 1" class="summary-with-count" :title="supplierNamesFor(record).join('、')">
                  <span class="primary-cell summary-name">{{ supplierNamesFor(record)[0] }}</span>
                  <span class="summary-pill">供应商+{{ supplierNamesFor(record).length }}</span>
                </div>
                <div v-else class="primary-cell">{{ supplierNamesFor(record)[0] || record.supplierName || '—' }}</div>
                <div v-if="isInbound" class="secondary-cell">{{ record.inspector }}</div>
              </td>
              <td>
                <div v-if="itemNamesFor(record).length > 1" class="summary-with-count item-summary-count" :title="itemNamesFor(record).join('、')">
                  <span class="primary-cell summary-name">{{ itemNamesFor(record)[0] }}</span>
                  <span class="summary-pill">商品+{{ itemNamesFor(record).length }}</span>
                </div>
                <div v-else class="primary-cell item-summary">{{ itemNamesFor(record)[0] || '—' }}</div>
              </td>
              <td>
                <div class="quantity-cell">
                  <strong>{{ isInbound ? receiptLabel(record) : plannedQuantityLabel(record) }}</strong>
                </div>
              </td>
              <td v-if="isInbound" class="progress-column">
                <div class="progress-cell">
                  <template v-if="record.purchaseOrderId">
                    <span class="progress-track"><i :style="{ width: `${recordProgress(record)}%` }"></i></span>
                    <small>{{ recordProgress(record) }}%</small>
                  </template>
                  <span v-else>—</span>
                </div>
              </td>
              <td v-if="!isInbound" class="amount-cell">
                <div>¥ {{ formatMoney(isInbound ? (record.estimatedAmount ?? record.totalAmount) : record.estimatedAmount) }}</div>
              </td>
              <template v-if="!isInbound">
                <td class="finance-column amount-cell">¥ {{ formatMoney(record.currentPayment) }}</td>
                <td class="finance-column payment-status-cell">{{ purchasePaymentLabel(record) }}</td>
              </template>
              <td>
                <span class="status-tag" :class="`status-${getStatusClass(record.status)}`">
                  <i></i>{{ getStatusLabel(record.status) }}
                </span>
                <div v-if="isInbound && !record.purchaseOrderId && record.settlementType === 'pending_supplier'" class="secondary-cell">{{ settlementLabels[record.financialStatus] }}</div>
              </td>
              <td v-if="!isInbound" class="finance-column">{{ invoiceLabels[record.invoiceStatus] || '无需开票' }}</td>
              <td class="remark-cell" :title="record.remark || ''">{{ record.remark || '—' }}</td>
              <td class="action-column" @click.stop>
                <div class="row-actions">
                  <button class="table-action" type="button" title="查看详情" @click="openDetail(record)">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="2.5"></circle>
                    </svg>
                  </button>
                  <button v-if="canReviewInbound(record)" class="table-action audit-action" type="button" title="采购审核" aria-label="采购审核" @click="openSettlement(record)">
                    <Check :size="15" aria-hidden="true" />
                  </button>
                  <button
                    v-if="isInbound && canDeleteApplication && record.sourceType === 'inbound-application' && ['draft', 'pending_review'].includes(record.status)"
                    class="table-action danger"
                    type="button"
                    title="删除未审核采购申请"
                    @click="confirmDeleteApplication(record)"
                  >
                    <Trash2 :size="15" aria-hidden="true" />
                  </button>
                  <button
                    v-if="isInbound && record.inboundId"
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
                    v-if="canSupplement(record)"
                    class="table-action supplement-action"
                    type="button"
                    title="补充入库"
                    @click="supplementRecord(record)"
                  >
                    <Plus :size="15" aria-hidden="true" />
                    补充入库
                  </button>
                  <button
                    v-if="!isInbound && record.status === 'pending' && canAudit"
                    class="table-action audit-action"
                    type="button"
                    title="补充采购信息并审核"
                    @click="auditRecord(record)"
                  >
                    ✓
                  </button>
                  <button
                    v-if="canReverseAudit(record)"
                    class="table-action"
                    type="button"
                    title="反审核采购订单"
                    @click="confirmOrderReverseAudit(record)"
                  >
                    <RotateCcw :size="15" aria-hidden="true" />
                  </button>
                  <button
                    v-if="canEdit(record)"
                    class="table-action"
                    type="button"
                    :title="isInbound ? '编辑入库单' : '编辑采购申请'"
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
              <td :colspan="recordTableColumnCount" class="empty-cell">
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
            :class="{ 'is-inbound': isInbound }"
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
                  <h2>{{ isInbound ? '采购入库申请详情' : '采购订单详情' }}</h2>
                  <div class="modal-document-no">{{ getRecordNo(selectedRecord) }}</div>
                </div>
              </div>
              <button class="modal-close" type="button" title="关闭" aria-label="关闭详情" @click="closeDetail">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <div v-if="isInbound" class="detail-overview inbound-detail-overview">
                <div>
                  <span class="detail-label">{{ selectedRecord.purchaseOrderId ? '申请日期' : '入库日期' }}</span>
                  <strong>{{ formatDate(recordDate(selectedRecord)) }}</strong>
                </div>
                <div>
                  <span class="detail-label">申请总数量</span>
                  <strong>{{ detailQuantityLabel(selectedRecord, 'orderedQty') }}</strong>
                </div>
                <div>
                  <span class="detail-label">采购数量</span>
                  <strong>{{ !selectedRecord.purchaseOrderId ? '—' : selectedRecord.actualTotalQuantity == null ? '待补充' : detailQuantityLabel(selectedRecord, 'actualPurchaseQty') }}</strong>
                </div>
                <div>
                  <span class="detail-label">实收数量</span>
                  <strong>{{ detailQuantityLabel(selectedRecord, 'receivedQty') }}</strong>
                </div>
                <div>
                  <span class="detail-label">当前状态</span>
                  <span class="status-tag large" :class="`status-${getStatusClass(selectedRecord.status)}`">
                    <i></i>{{ getStatusLabel(selectedRecord.status) }}
                  </span>
                </div>
              </div>
              <div v-else class="detail-overview">
                <div>
                  <span class="detail-label">当前状态</span>
                  <span class="status-tag large" :class="`status-${getStatusClass(selectedRecord.status)}`">
                    <i></i>{{ getStatusLabel(selectedRecord.status) }}
                  </span>
                </div>
                <div>
                  <span class="detail-label">申请日期</span>
                  <strong>{{ formatDate(recordDate(selectedRecord)) }}</strong>
                </div>
                <div>
                  <span class="detail-label">采购金额</span>
                  <strong class="overview-amount">¥ {{ formatMoney(selectedRecord.totalAmount) }}</strong>
                </div>
              </div>

              <section v-if="!isInbound" class="detail-section">
                <div class="section-heading"><h3>采购结算</h3><span>{{ receiptLabel(selectedRecord) }}</span></div>
                <div class="meta-grid">
                  <div><span>已确认应付</span><strong>¥ {{ formatMoney(selectedRecord.confirmedPayable) }}</strong></div>
                  <div><span>已核销 / 未付</span><strong>¥ {{ formatMoney(selectedRecord.allocatedAmount) }} / ¥ {{ formatMoney(selectedRecord.unpaidAmount) }}</strong></div>
                  <div><span>开票状态</span><strong>{{ invoiceLabels[selectedRecord.invoiceStatus] || '无需开票' }}</strong></div>
                  <div><span>付款状态</span><strong>{{ paymentLabels[selectedRecord.paymentStatus] || '未确认应付' }}</strong></div>
                  <div><span>已开票 / 未开票</span><strong>¥ {{ formatMoney(selectedRecord.billedAmount) }} / ¥ {{ formatMoney(selectedRecord.unbilledAmount) }}</strong></div>
                </div>
              </section>

              <section v-if="!isInbound" class="detail-section">
                <div class="section-heading">
                  <h3>基础信息</h3>
                  <span>共 {{ selectedRecord.itemCount }} 项物料</span>
                </div>
                <div class="meta-grid">
                  <div><span>供应商</span><strong>{{ selectedRecord.supplierName }}</strong></div>
                  <div><span>收货仓库</span><strong>{{ selectedRecord.warehouseName }}</strong></div>
                  <div><span>{{ isInbound ? '验收人员' : '申请人员' }}</span><strong>{{ isInbound ? selectedRecord.inspector : selectedRecord.contact }}</strong></div>
                  <div><span>{{ isInbound ? '质检单号' : '预计到货' }}</span><strong>{{ isInbound ? selectedRecord.qualityNo || '—' : selectedRecord.expectedDate || '—' }}</strong></div>
                </div>
              </section>

              <section class="detail-section">
                <div class="section-heading">
                  <h3>采购物料明细</h3>
                  <span>{{ isInbound ? `共 ${selectedRecord.itemCount} 项物料` : receiptLabel(selectedRecord) }}</span>
                </div>
                <div class="detail-items-scroll">
                  <table class="detail-items-table" :class="{ 'inbound-items-table': isInbound }">
                    <colgroup v-if="isInbound">
                      <col style="width: 115px">
                      <col style="width: 130px">
                      <col style="width: 130px">
                      <col style="width: 75px">
                      <col style="width: 160px">
                      <col style="width: 160px">
                      <col style="width: 140px">
                      <col style="width: 115px">
                      <col>
                    </colgroup>
                    <thead>
                      <tr>
                        <th>物料编码</th>
                        <th>物料名称</th>
                        <th>规格型号</th>
                        <th>单位</th>
                        <th v-if="!isInbound">采购供应商</th>
                        <th v-if="isInbound">申请数量</th>
                        <th>{{ isInbound ? '应收数量' : '申请数量' }}</th>
                        <th v-if="!isInbound">实际采购数量</th>
                        <th>累计实收</th>
                        <th>履约进度</th>
                        <th v-if="isInbound">备注</th>
                        <th v-if="!isInbound">采购单价</th>
                        <th v-if="!isInbound">金额</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in selectedRecord.items" :key="`${selectedRecord.id}-${index}`">
                        <td>{{ item.productCode }}</td>
                        <td>{{ item.goodsName }}</td>
                        <td>{{ item.specification || '—' }}</td>
                        <td>{{ item.unit }}</td>
                        <td v-if="!isInbound" :title="item.supplierName || selectedRecord.supplierName">{{ item.supplierName || '待补充' }}</td>
                        <td v-if="isInbound">{{ item.orderedQty == null ? '—' : formatNumber(item.orderedQty) }}</td>
                        <td>{{ formatNumber(isInbound ? item.expectedQty : item.quantity) }}</td>
                        <td v-if="!isInbound">{{ item.actualPurchaseQty == null ? '待补充' : formatNumber(item.actualPurchaseQty) }}</td>
                        <td>
                          {{ formatNumber(item.receivedQty ?? 0) }}
                          <small v-if="Number(item.receivedQty) > Number(item.expectedQty ?? item.quantity)" class="secondary-cell">超收 {{ formatNumber(Number(item.receivedQty) - Number(item.expectedQty ?? item.quantity)) }}</small>
                        </td>
                        <td>
                          <div class="detail-item-progress">
                            <span class="progress-track">
                              <i :style="{ width: `${Math.min(100, itemProgress(item))}%` }"></i>
                            </span>
                            <small>{{ itemProgress(item) }}%</small>
                          </div>
                        </td>
                        <td v-if="isInbound" class="item-remark-cell" :title="item.remark || ''">{{ item.remark || '—' }}</td>
                        <td v-if="!isInbound">{{ item.price == null ? '待补充' : `¥ ${formatMoney(item.price)}` }}</td>
                        <td v-if="!isInbound">{{ item.amount == null ? '待补充' : `¥ ${formatMoney(item.amount)}` }}</td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr>
                        <template v-if="isInbound">
                          <td colspan="4" class="detail-total-label">合计</td>
                          <td>{{ detailQuantityLabel(selectedRecord, 'orderedQty') }}</td>
                          <td>{{ detailQuantityLabel(selectedRecord, 'expectedQty') }}</td>
                          <td>{{ detailQuantityLabel(selectedRecord, 'receivedQty') }}</td>
                          <td class="detail-progress-total">—</td>
                          <td></td>
                        </template>
                        <template v-else>
                          <td colspan="4" class="detail-total-label">合计</td>
                          <td>—</td>
                          <td>{{ hasMixedUnits(selectedRecord) ? '—' : formatNumber(detailTotals.plannedQuantity) }}</td>
                          <td>{{ selectedRecord.actualTotalQuantity == null || hasMixedUnits(selectedRecord) ? '—' : formatNumber(selectedRecord.actualTotalQuantity) }}</td>
                          <td>{{ hasMixedUnits(selectedRecord) ? '—' : formatNumber(detailTotals.receivedQuantity) }}</td>
                          <td class="detail-progress-total">—</td>
                          <td>—</td>
                          <td>¥ {{ formatMoney(detailTotals.amount) }}</td>
                        </template>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </section>

              <section v-if="!isInbound && selectedRecord.batches?.length" class="detail-section">
                <div class="section-heading">
                  <h3>入库批次</h3>
                  <span>共 {{ selectedRecord.batches.length }} 批</span>
                </div>
                <div class="detail-items-scroll">
                  <table class="detail-items-table batch-items-table">
                    <thead><tr><th>入库日期</th><th>商品名称</th><th>规格型号</th><th>单位</th><th>类型</th><th>本批数量</th><th>仓库</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody v-for="batch in selectedRecord.batches" :key="batch.id">
                      <tr
                        v-for="(item, itemIndex) in (batch.items?.length ? batch.items : [null])"
                        :key="`${batch.id}-${item?.id ?? itemIndex}`"
                      >
                        <td v-if="itemIndex === 0" :rowspan="batch.items?.length || 1">{{ formatDate(batch.documentDate) }}</td>
                        <td :title="item?.goodsName || item?.productName || '—'">{{ item?.goodsName || item?.productName || '—' }}</td>
                        <td :title="item?.specification || '—'">{{ item?.specification || '—' }}</td>
                        <td>{{ item?.unit || '—' }}</td>
                        <td>{{ getInboundTypeLabel(item?.productType || batch.type) }}</td>
                        <td class="batch-quantity">{{ formatNumber(item?.receivedQty ?? item?.quantity ?? batch.receivedQuantity ?? 0) }}</td>
                        <td v-if="itemIndex === 0" :rowspan="batch.items?.length || 1">{{ batch.warehouseName || '—' }}</td>
                        <td v-if="itemIndex === 0" :rowspan="batch.items?.length || 1">{{ getStatusLabel(batch.status) }}</td>
                        <td v-if="itemIndex === 0" :rowspan="batch.items?.length || 1">
                          <button class="document-link" type="button" @click="viewBatch(batch)">查看</button>
                        </td>
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
              <div class="footer-actions">
                <button v-if="!isInbound && canOpenExpenses(selectedRecord)" class="button button-secondary" type="button" @click="openExpenses(selectedRecord)">
                  <ReceiptText :size="16" aria-hidden="true" />采购费用
                </button>
                <button v-if="canReviewInbound(selectedRecord)" class="button button-secondary" type="button" @click="openSettlement(selectedRecord)">
                  <Wallet :size="16" aria-hidden="true" />采购审核
                </button>
                <button v-if="!isInbound && selectedRecord.status === 'pending' && canAudit" class="button button-primary" type="button" @click="auditRecord(selectedRecord)">
                  补充采购信息并审核
                </button>
                <button v-if="canReverseAudit(selectedRecord)" class="button button-secondary" type="button" @click="confirmOrderReverseAudit(selectedRecord)">
                  <RotateCcw :size="16" aria-hidden="true" />反审核采购订单
                </button>
                <button v-if="!isInbound && ['approved', 'partial'].includes(selectedRecord.status)" class="button button-secondary" type="button" @click="router.push({ name: 'admin-purchase-inbound-create', query: { purchaseOrderId: selectedRecord.id } })">
                  创建采购入库单
                </button>
                <button v-if="isInbound && selectedRecord.inboundId" class="button button-secondary" type="button" @click="printRecord(selectedRecord)">
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 9V3h12v6"></path>
                    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                    <path d="M6 14h12v7H6z"></path>
                  </svg>
                  打印入库单
                </button>
                <button v-if="isInbound && canDeleteApplication && selectedRecord.sourceType === 'inbound-application' && ['draft', 'pending_review'].includes(selectedRecord.status)" class="button button-danger" type="button" @click="confirmDeleteApplication(selectedRecord)">
                  <Trash2 :size="16" aria-hidden="true" />删除申请
                </button>
                <button v-if="isInbound && selectedRecord.status === 'pending'" class="button button-primary" type="button" @click="editRecord(selectedRecord)">
                  创建采购入库单
                </button>
                <button v-if="canSupplement(selectedRecord)" class="button button-primary" type="button" @click="supplementRecord(selectedRecord)">
                  <Plus :size="16" aria-hidden="true" />补充入库
                </button>
                <button v-if="canEdit(selectedRecord) && !(isInbound && selectedRecord.status === 'pending')" class="button button-primary" type="button" @click="editRecord(selectedRecord)">
                  {{ isInbound ? (selectedRecord.sourceType === 'inbound-application' ? '编辑采购申请' : '编辑入库单') : '编辑采购申请' }}
                </button>
              </div>
            </footer>
          </article>
        </div>
      </Transition>
    </Teleport>
    <PurchaseExpenseDialog v-if="expenseOrderId" :order-id="expenseOrderId" @close="expenseOrderId = null" @updated="refreshData(false)" />
    <SupplierAssignmentDialog v-if="settlementInboundId" :inbound-id="settlementInboundId" @close="settlementInboundId = null" @updated="refreshData(false)" />
    <CustomModal
      :visible="deleteConfirmOpen"
      :title="applicationDeleteTarget ? '确认删除采购申请' : '确认批量删除'"
      :message="deleteConfirmMessage"
      confirm-text="删除"
      :danger="true"
      @confirm="deleteSelected"
      @cancel="deleteConfirmOpen = false"
    />
    <CustomModal
      :visible="Boolean(orderReverseAuditTarget)"
      title="反审核采购订单"
      message="确认反审核该采购订单？已有入库或费用引用的订单不能反审核。"
      @confirm="reverseAuditOrder"
      @cancel="orderReverseAuditTarget = null"
    />
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Check, Pencil, Plus, ReceiptText, RotateCcw, Trash2, Wallet } from '@lucide/vue'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'
import { useUserStore } from '@/stores/user'
import { ADMIN_PURCHASE_ORDER_PERMISSIONS } from '@/utils/accessControl'
import PurchaseExpenseDialog from '@/components/admin/purchase/PurchaseExpenseDialog.vue'
import SupplierAssignmentDialog from '@/components/admin/purchase/SupplierAssignmentDialog.vue'
import { purchaseReturnStatusLabels } from '@/composables/documents/documentModels'
import { invoiceLabels, operationKey, paymentLabels, fulfillmentLabel, settlementLabels } from '@/utils/supplierFinance'

const props = defineProps({
  mode: {
    type: String,
    default: 'orders',
    validator: value => ['orders', 'inbound', 'returns'].includes(value)
  }
})

const router = useRouter()
const userStore = useUserStore()
const isInbound = computed(() => props.mode === 'inbound')
const isReturn = computed(() => props.mode === 'returns')
const paymentFilterLabels = computed(() => isInbound.value ? paymentLabels : {
  unpaid: '未付款', partial: '部分付款', paid: '已结清', prepaid: '增加预付'
})
const canAudit = computed(() => userStore.hasPerm(ADMIN_PURCHASE_ORDER_PERMISSIONS.AUDIT))
const canDelete = computed(() => userStore.hasPerm(ADMIN_PURCHASE_ORDER_PERMISSIONS.DELETE))
const canDeleteApplication = computed(() => userStore.hasPerm('admin.route.purchase.inbound'))
const canReverseAuditPermission = computed(() => userStore.hasPerm(ADMIN_PURCHASE_ORDER_PERMISSIONS.REVERSE_AUDIT))
const canReturn = action => userStore.hasPerm(`admin.purchase.return.${action}`)
const returnStatusLabels = purchaseReturnStatusLabels

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
const emptyFilters = () => ({ keyword: '', status: 'all', startDate: '', endDate: '', invoiceStatus: '', paymentStatus: '' })
const filters = ref(emptyFilters())
const returnOptions = ref({ stores: [], suppliers: [] })
const returnRecords = ref([])
const returnError = ref('')
const returnPendingAction = ref(null)
const returnFilters = ref({ keyword: '', storeId: '', supplierId: '', status: 'all', startDate: '', endDate: '' })
const returnCurrentPage = ref(1)
const returnPageSize = 30
const returnSuppliersForFilter = computed(() => returnOptions.value.suppliers.filter(row =>
  !returnFilters.value.storeId || !row.storeId || Number(row.storeId) === Number(returnFilters.value.storeId)
))
const returnStatusTabs = computed(() => {
  const statuses = [
    { key: 'all', label: '全部' },
    { key: 'draft', label: returnStatusLabels.draft },
    { key: 'audited', label: returnStatusLabels.audited },
    { key: 'reversed', label: returnStatusLabels.reversed },
    { key: 'cancelled', label: returnStatusLabels.cancelled }
  ]
  return statuses.map(tab => ({
    ...tab,
    count: tab.key === 'all'
      ? returnRecords.value.length
      : returnRecords.value.filter(record => record.status === tab.key).length
  }))
})
const returnStatusOptions = computed(() => returnStatusTabs.value.filter(tab => tab.key !== 'all'))
const returnFilteredRecords = computed(() => {
  const filters = returnFilters.value
  const keyword = filters.keyword.toLowerCase()
  return returnRecords.value
    .filter(record => {
      const searchable = [record.documentNo, record.supplierName, record.storeName, record.remark].join(' ').toLowerCase()
      const date = record.businessDate || ''
      return (!keyword || searchable.includes(keyword))
        && (filters.status === 'all' || record.status === filters.status)
        && (!filters.storeId || String(record.storeId) === String(filters.storeId))
        && (!filters.supplierId || String(record.supplierId) === String(filters.supplierId))
        && (!filters.startDate || date >= filters.startDate)
        && (!filters.endDate || date <= filters.endDate)
    })
    .sort((a, b) => String(b.businessDate || '').localeCompare(String(a.businessDate || '')))
})
const returnTotalPages = computed(() => Math.max(1, Math.ceil(returnFilteredRecords.value.length / returnPageSize)))
const returnPaginatedRecords = computed(() => {
  const start = (returnCurrentPage.value - 1) * returnPageSize
  return returnFilteredRecords.value.slice(start, start + returnPageSize)
})
const returnPageNumbers = computed(() => Array.from({ length: returnTotalPages.value }, (_, index) => index + 1))
const returnAudited = computed(() => returnRecords.value.filter(record => record.status === 'audited'))
const returnAuditedCount = computed(() => returnAudited.value.length)
const returnAuditedTotal = computed(() => returnAudited.value.reduce((sum, record) => sum + Number(record.returnAmount || 0), 0))
const returnActionTitle = computed(() => ({
  audit: '审核采购退货',
  'reverse-audit': '反审核采购退货',
  delete: '删除采购退货'
}[returnPendingAction.value?.action] || '确认操作'))
const returnActionMessage = computed(() => ({
  audit: '确认审核该采购退货？审核后将扣减对应批次库存，并冲减应付或形成供应商贷项。',
  'reverse-audit': '确认反审核该采购退货？系统将冲销对应账务并恢复库存。',
  delete: '确定删除该采购退货草稿？'
}[returnPendingAction.value?.action] || ''))
const expenseOrderId = ref(null)
const settlementInboundId = ref(null)
const canReadSettlement = computed(() => userStore.hasPerm('admin.purchase.inbound.settlement.read'))
const loading = ref(true)
const recordTableColumnCount = computed(() => isInbound.value ? 11 : 14)
const currentPage = ref(1)
const pageSize = 30
const selectedIds = ref(new Set())
const selectedRecord = ref(null)
const detailTotals = computed(() => (selectedRecord.value?.items || []).reduce((totals, item) => ({
  plannedQuantity: totals.plannedQuantity + Number(isInbound.value ? item.expectedQty : item.quantity),
  receivedQuantity: totals.receivedQuantity + Number(item.receivedQty ?? item.quantity ?? 0),
  amount: totals.amount + Number(item.amount ?? item.totalAmount ?? 0)
}), { plannedQuantity: 0, receivedQuantity: 0, amount: 0 }))
const detailModalOpen = ref(false)
const notice = ref('')
const deleting = ref(false)
const applicationDeleteTarget = ref(null)
const orderReverseAuditTarget = ref(null)
const deleteConfirmOpen = ref(false)
const deleteTargets = ref([])
const deleteConfirmMessage = computed(() => applicationDeleteTarget.value
  ? `确定删除未审核采购申请 ${getRecordNo(applicationDeleteTarget.value)}？删除后不能恢复。`
  : `确定删除选中的 ${deleteTargets.value.length} 条采购入库及全部批次吗？已审核批次将回退库存和累计入库数量，采购订单保留。`)

const sourceRecords = computed(() => (isInbound.value ? inboundRecords.value : orderRecords.value))

const statusTabs = computed(() => {
  const statuses = isInbound.value
    ? [
        { key: 'all', label: '全部' },
        { key: 'pending_review', label: '待审核' },
        { key: 'pending', label: '待入库' },
        { key: 'draft', label: '草稿' },
        { key: 'partial', label: '部分入库' },
        { key: 'reviewed', label: '已审核' },
        { key: 'posted', label: '已入库' },
        { key: 'cancelled', label: '已作废' }
      ]
    : [
        { key: 'all', label: '全部' },
        { key: 'draft', label: '草稿' },
        { key: 'pending', label: '待审核' },
        { key: 'approved', label: '已审核' },
        { key: 'partial', label: '部分入库' },
        { key: 'completed', label: '已完成' },
        { key: 'cancelled', label: '已取消' },
        { key: 'rejected', label: '已驳回' }
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
  const { status, startDate, endDate, invoiceStatus, paymentStatus } = filters.value

  return sourceRecords.value
    .filter(record => {
      const searchable = [
        isInbound.value ? record.inboundNo : record.orderNo,
        record.supplierName,
        record.storeName,
        record.warehouseName,
        record.itemSummary
      ].join(' ').toLowerCase()
      const date = recordDate(record)
      return (!keyword || searchable.includes(keyword))
        && (status === 'all' || record.status === status)
        && (!invoiceStatus || record.invoiceStatus === invoiceStatus)
        && (!paymentStatus || (isInbound.value ? record.paymentStatus : record.purchasePaymentStatus) === paymentStatus)
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
const currentPageIds = computed(() => paginatedRecords.value
  .filter(record => !isInbound.value || !(
    record.sourceType === 'inbound-application' && ['draft', 'pending_review'].includes(record.status)
  ))
  .map(record => record.id))
const isAllPageSelected = computed(() => currentPageIds.value.length > 0 && currentPageIds.value.every(id => selectedIds.value.has(id)))
const isSomePageSelected = computed(() => currentPageIds.value.some(id => selectedIds.value.has(id)) && !isAllPageSelected.value)

watch(
  () => props.mode,
  () => {
    filters.value = emptyFilters()
    returnFilters.value = { keyword: '', storeId: '', supplierId: '', status: 'all', startDate: '', endDate: '' }
    currentPage.value = 1
    returnCurrentPage.value = 1
    selectedIds.value = new Set()
    returnPendingAction.value = null
    returnError.value = ''
    closeDetail()
    refreshData(false)
  }
)

watch(
  () => Object.values(filters.value),
  () => {
    currentPage.value = 1
    selectedIds.value = new Set()
  }
)

watch(totalPages, value => {
  if (currentPage.value > value) currentPage.value = value
})

watch(returnTotalPages, value => {
  if (returnCurrentPage.value > value) returnCurrentPage.value = value
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

function detailQuantityLabel(record, field) {
  const totals = new Map()
  for (const item of record.items || []) {
    const value = field === 'orderedQty'
      ? item.orderedQty ?? item.expectedQty
      : item[field]
    if (value == null || value === '') continue
    const unit = String(item.unit || '').trim()
    totals.set(unit, (totals.get(unit) || 0) + Number(value || 0))
  }
  return [...totals]
    .map(([unit, value]) => `${formatNumber(value)}${unit ? ` ${unit}` : ''}`)
    .join(' / ') || '—'
}

function itemProgress(item) {
  const planned = Number(item.expectedQty ?? item.quantity ?? 0)
  const received = Number(item.receivedQty ?? 0)
  return planned > 0 ? Math.min(100, Math.round((received / planned) * 100)) : 0
}

function hasMixedUnits(record) {
  return new Set((record.items || []).map(item => item.unit)).size > 1
}
function receiptLabel(record) {
  if (isInbound.value && !record.purchaseOrderId) {
    return hasMixedUnits(record) ? `${record.items.length} 行` : `${formatNumber(record.receivedQuantity)} ${record.items?.[0]?.unit || ''}`
  }
  return fulfillmentLabel(record)
}
function plannedQuantityLabel(record) {
  if (record.progressBasis === 'lines' || hasMixedUnits(record)) {
    return `${record.totalLineCount || record.itemCount || 0} 行`
  }
  return `${formatNumber(record.requestedTotalQuantity)} ${record.items?.[0]?.unit || ''}`.trim()
}
function purchasePaymentLabel(record) {
  if (record.purchasePaymentStatus === 'prepaid') return `增加预付 ¥ ${formatMoney(record.prepaidAmount)}`
  if (record.purchasePaymentStatus !== 'paid') return `未付 ¥ ${formatMoney(record.estimatedUnpaidAmount)}`
  return '已结清'
}
function canOpenExpenses(record) {
  return userStore.hasPerm('admin.route.purchase.orders') &&
    Boolean(record.purchaseOrderId || (!isInbound.value && ['approved', 'partial', 'completed'].includes(record.status)))
}
function openExpenses(record) {
  const id = Number(record.purchaseOrderId || record.id)
  closeDetail()
  expenseOrderId.value = id
}
function openSettlement(record) {
  const id = record.inboundId
  closeDetail()
  settlementInboundId.value = id
}
function canReviewInbound(record) {
  return isInbound.value && !record.purchaseOrderId && record.documentSource === 'other'
    && ['reviewed', 'posted'].includes(record.status) && canReadSettlement.value
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function getInboundTypeLabel(type) {
  if (type === 'finished-product') return '成品'
  if (type === 'raw-material') return '原材料'
  return '—'
}

function quantityValue(record) {
  return isInbound.value ? record.receivedQuantity : record.totalQuantity
}

function recordProgress(record) {
  return Math.min(100, Number(record.fulfillmentProgress || 0))
}

function getStatusLabel(status) {
  const tab = statusTabs.value.find(item => item.key === status)
  return tab?.label || status
}

function getStatusClass(status) {
  if (status === 'pending' || status === 'pending_review' || status === 'draft') return 'pending'
  if (status === 'approved' || status === 'reviewed') return 'confirmed'
  if (status === 'partial') return 'processing'
  if (status === 'completed' || status === 'posted') return 'completed'
  return 'rejected'
}

function returnStatusClass(status) {
  if (status === 'draft' || status === 'reversed') return 'pending'
  if (status === 'audited') return 'completed'
  return 'rejected'
}

function returnQuantityLabel(record) {
  const items = record.items || []
  const quantitiesByUnit = new Map()
  items.forEach(item => {
    const unit = String(item.unit || '').trim()
    quantitiesByUnit.set(unit, (quantitiesByUnit.get(unit) || 0) + Number(item.quantity || 0))
  })
  return [...quantitiesByUnit.entries()]
    .map(([unit, quantity]) => `${Number(quantity).toLocaleString('zh-CN', { maximumFractionDigits: 4 })}${unit ? ` ${unit}` : ''}`)
    .join(' / ') || '0'
}

function applyReturnFilters() {
  returnCurrentPage.value = 1
}

function resetReturnFilters() {
  returnFilters.value = { keyword: '', storeId: '', supplierId: '', status: 'all', startDate: '', endDate: '' }
}

function setReturnStatusFilter(status) {
  returnFilters.value.status = status
  returnCurrentPage.value = 1
}

function onReturnStoreChange() {
  if (!returnSuppliersForFilter.value.some(row => String(row.id) === String(returnFilters.value.supplierId))) {
    returnFilters.value.supplierId = ''
  }
}

function createReturn() {
  router.push({ name: 'admin-purchase-return-create' })
}

function openReturnDetail(record) {
  router.push({ name: 'admin-purchase-return-view', params: { id: record.id } })
}

function editReturn(record) {
  router.push({ name: 'admin-purchase-return-edit', params: { id: record.id } })
}

function confirmReturnAction(record, action) {
  if (!loading.value) returnPendingAction.value = { row: record, action }
}

async function actReturn() {
  if (!returnPendingAction.value || loading.value) return
  const { row, action } = returnPendingAction.value
  returnPendingAction.value = null
  loading.value = true
  returnError.value = ''
  try {
    const suffix = action === 'delete' ? '' : `/${action}`
    const response = await request({
      url: `/purchase-returns/${row.id}${suffix}`,
      method: action === 'delete' ? 'DELETE' : 'POST',
      data: { version: row.version, idempotencyKey: operationKey() }
    })
    if (response?.success === false) throw new Error(response.message || '操作失败')
    await refreshData(false)
  } catch (error) {
    returnError.value = error?.response?.data?.message || error.message || '操作失败'
  } finally {
    loading.value = false
  }
}

function canEdit(record) {
  return isInbound.value
    ? (record.sourceType === 'inbound-application' && record.status === 'draft')
      || record.status === 'pending'
      || Boolean(record.editableInboundId)
    : userStore.hasPerm(ADMIN_PURCHASE_ORDER_PERMISSIONS.EDIT) && ['draft', 'pending'].includes(record.status)
}

function canReverseAudit(record) {
  return !isInbound.value
    && canReverseAuditPermission.value
    && record.status === 'approved'
    && !record.hasInbound
    && Number(record.inboundCount || 0) === 0
    && Number(record.receivedQuantity || 0) <= 0
}

function confirmOrderReverseAudit(record) {
  if (!loading.value && canReverseAudit(record)) orderReverseAuditTarget.value = record
}

async function reverseAuditOrder() {
  const record = orderReverseAuditTarget.value
  if (!record || loading.value) return
  orderReverseAuditTarget.value = null
  loading.value = true
  try {
    const response = await request({
      url: `/purchase-orders/${record.id}/audit`,
      method: 'DELETE',
      data: { version: record.version }
    })
    if (response?.success === false) throw new Error(response.message || '反审核失败')
    closeDetail()
    await refreshData(false)
    showNotice('采购订单已反审核')
  } catch (error) {
    showNotice(error?.response?.data?.message || error.message || '反审核失败')
  } finally {
    loading.value = false
  }
}

function canSupplement(record) {
  return isInbound.value && Boolean(record.purchaseOrderId)
    && record.remainingQuantity > 0.0000001
    && !record.editableInboundId
    && record.batches?.some(batch => ['reviewed', 'posted'].includes(batch.status))
}

function supplementRecord(record) {
  if (!canSupplement(record)) return
  router.push({
    name: 'admin-purchase-inbound-create',
    query: { purchaseOrderId: record.purchaseOrderId, productType: record.remainingTypes[0], supplement: '1' }
  })
}

function viewBatch(batch) {
  router.push({
    name: batch.status === 'draft' ? 'admin-purchase-inbound-edit' : 'admin-purchase-inbound-view',
    params: { id: batch.id }
  })
}

function applyFilters() {
  currentPage.value = 1
}

function resetFilters() {
  filters.value = emptyFilters()
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

function confirmDeleteApplication(record) {
  if (!canDeleteApplication.value || !isInbound.value || deleting.value || loading.value ||
    record?.sourceType !== 'inbound-application' ||
    !['draft', 'pending_review'].includes(record.status) ||
    !record.purchaseOrderId) return
  applicationDeleteTarget.value = record
  deleteTargets.value = []
  deleteConfirmOpen.value = true
}

function confirmDeleteSelected() {
  if (!canDelete.value || deleting.value || loading.value) return
  applicationDeleteTarget.value = null
  deleteTargets.value = inboundRecords.value.filter(record => selectedIds.value.has(record.id))
  if (deleteTargets.value.length) deleteConfirmOpen.value = true
}

async function deleteSelected() {
  if (deleting.value || (!applicationDeleteTarget.value && !deleteTargets.value.length)) return
  deleteConfirmOpen.value = false
  deleting.value = true
  try {
    if (applicationDeleteTarget.value) {
      const record = applicationDeleteTarget.value
      const response = await request({
        url: `/purchase-inbound-applications/${record.purchaseOrderId}`,
        method: 'DELETE',
        data: { version: record.version }
      })
      if (!response?.success) throw new Error(response?.message || '删除采购申请失败')
      clearSelection()
      closeDetail()
      await refreshData(false)
      showNotice('采购申请已删除')
      return
    }
    const response = await request({
      url: '/purchase-inbounds/bulk-delete',
      method: 'POST',
      data: {
        purchaseOrderIds: deleteTargets.value.filter(record => record.purchaseOrderId).map(record => record.purchaseOrderId),
        inboundIds: deleteTargets.value.filter(record => !record.purchaseOrderId).map(record => record.inboundId)
      }
    })
    if (!response?.success) throw new Error(response?.message || '删除失败')
    clearSelection()
    closeDetail()
    await refreshData(false)
    showNotice('所选采购入库记录已删除')
  } catch (error) {
    showNotice(error?.response?.data?.message || error.message || '删除失败')
  } finally {
    deleting.value = false
    deleteTargets.value = []
    applicationDeleteTarget.value = null
  }
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

async function createRecord() {
  if (!isInbound.value) {
    router.push({ name: 'admin-purchase-order-create' })
    return
  }
  router.push({ name: 'admin-purchase-inbound-create' })
}

function editRecord(record) {
  if (!isInbound.value) {
    if (canEdit(record)) router.push({ name: 'admin-purchase-order-edit', params: { id: record.id } })
    else router.push({ name: 'admin-purchase-order-view', params: { id: record.id } })
    return
  }
  if (record.sourceType === 'inbound-application' && record.status === 'draft') {
    router.push({ name: 'admin-purchase-inbound-application-edit', params: { id: record.purchaseOrderId } })
    return
  }
  if (record.status === 'pending' && record.purchaseOrderId) {
    router.push({ name: 'admin-purchase-inbound-create', query: { purchaseOrderId: record.purchaseOrderId, productType: record.remainingTypes[0] } })
    return
  }
  router.push({ name: 'admin-purchase-inbound-edit', params: { id: record.editableInboundId || record.inboundId } })
}

function auditRecord(record) {
  if (isInbound.value || record.status !== 'pending' || !canAudit.value) return
  closeDetail()
  router.push({ name: 'admin-purchase-order-audit', params: { id: record.id } })
}

function printRecord(record) {
  if (!isInbound.value) return
  router.push({ path: `/admin/purchase/inbound/${record.inboundId}`, query: { print: '1' } })
}

function exportRecords() {
  const rows = filteredRecords.value
  if (!rows.length) { showNotice('当前没有可导出的记录'); return }
  const headers = isInbound.value
    ? ['入库单号', '日期', '供应商', '实收数量', '金额', '状态']
    : ['采购单号', '申请日期', '门店', '供应商', '计划采购数量', '应付金额', '付款金额', '付款状态', '履约状态']
  const lines = isInbound.value
    ? rows.map(record => [getRecordNo(record), recordDate(record), record.supplierName, quantityValue(record), record.totalAmount, getStatusLabel(record.status)])
    : rows.map(record => [
        getRecordNo(record),
        recordDate(record),
        record.storeName,
        record.supplierName,
        plannedQuantityLabel(record),
        record.estimatedAmount,
        record.currentPayment,
        purchasePaymentLabel(record),
        getStatusLabel(record.status)
      ])
  const csv = [headers, ...lines].map(line => line.map(value => `"${String(value ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${isInbound.value ? '采购入库' : '采购订单'}.csv`; link.click(); URL.revokeObjectURL(link.href)
}

function supplierNamesFor(record) {
  const itemNames = [...new Set((record.items || [])
    .map(item => String(item.supplierName || '').trim())
    .filter(Boolean))]
  if (itemNames.length) return itemNames
  const names = Array.isArray(record.supplierNames) && record.supplierNames.length
    ? record.supplierNames
    : String(record.supplierName || '').split('、')
  return [...new Set(names.map(name => String(name || '').trim()).filter(Boolean))]
}

function warehouseNamesFor(record) {
  const itemNames = [...new Set((record.items || [])
    .map(item => String(item.warehouseName || item.warehouse_name || '').trim())
    .filter(Boolean))]
  if (itemNames.length) return itemNames
  const names = Array.isArray(record.warehouseNames) && record.warehouseNames.length
    ? record.warehouseNames
    : String(record.warehouseName || record.warehouse_name || '').split('、')
  return [...new Set(names.map(name => String(name || '').trim()).filter(Boolean))]
}

function itemNamesFor(record) {
  const names = (record.items || [])
    .map(item => String(item.goodsName || item.productName || '').trim())
    .filter(Boolean)
  return names.length
    ? [...new Set(names)]
    : (record.itemSummary ? [record.itemSummary] : [])
}

function normalizeOrder(record) {
  const items = (record.items || record.orderItems || []).map(item => ({
    ...item,
    goodsName: item.productName || item.goodsName || '',
    quantity: item.orderedQty || 0,
    expectedQty: item.effectivePurchaseQty,
    price: item.unitPrice,
    amount: item.amount
  }))
  const lineSupplierNames = [...new Set(items
    .map(item => String(item.supplierName || '').trim())
    .filter(Boolean))]
  const lineWarehouseNames = [...new Set(items
    .map(item => String(item.warehouseName || item.warehouse_name || '').trim())
    .filter(Boolean))]
  return {
    ...record, id: record.orderId || record.id, orderNo: record.orderNo || '', purchaseDate: record.orderDate || '',
    status: record.status === 'confirmed' ? 'approved' : (record.status || 'draft'),
    supplierName: record.supplierName || lineSupplierNames.join('、') || '待采购审核', supplierNames: lineSupplierNames,
    storeName: record.storeName || '',
    warehouseName: record.warehouseName || record.warehouse_name || lineWarehouseNames.join('、'), warehouseNames: lineWarehouseNames,
    contact: record.createdBy || '',
    itemSummary: items.map(item => item.goodsName).filter(Boolean).slice(0, 2).join('、') + (items.length > 2 ? ' 等' : ''),
    itemCount: items.length, totalQuantity: Number(record.totalQuantity || 0), receivedQuantity: items.reduce((sum, item) => sum + Number(item.receivedQty || 0), 0),
    totalAmount: Number(record.totalAmount || 0), items
  }
}

function normalizeInbound(record) {
  const items = (record.items || []).map(item => ({ ...item, goodsName: item.productName || item.goodsName || '', quantity: item.receivedQty || 0, price: item.unitPrice, amount: item.totalAmount }))
  const supplierNames = [...new Set(items.map(item => String(item.supplierName || '').trim()).filter(Boolean))]
  return {
    ...record, id: record.id, inboundId: record.id, editableInboundId: record.status === 'draft' ? record.id : null, inboundNo: record.documentNo || '', documentDate: record.documentDate || '', supplierName: record.supplierName || supplierNames.join('、'), supplierNames,
    warehouseName: record.warehouseName || '', inspector: record.inspector || '', qualityNo: record.qualityNo || '', itemSummary: items.map(item => item.goodsName).filter(Boolean).slice(0, 2).join('、') + (items.length > 2 ? ' 等' : ''), itemCount: items.length,
    expectedQuantity: items.reduce((sum, item) => sum + Number(item.expectedQty || 0), 0), receivedQuantity: items.reduce((sum, item) => sum + Number(item.receivedQty || 0), 0), totalAmount: Number(record.totalAmount || 0), items
  }
}

function normalizePurchaseInbound(record, batches) {
  const activeBatches = batches.filter(batch => batch.status !== 'cancelled')
  const auditedBatches = activeBatches.filter(batch => ['reviewed', 'posted'].includes(batch.status))
  const draft = activeBatches.find(batch => batch.status === 'draft')
  const latest = activeBatches[0] || batches[0]
  const order = normalizeOrder(record)
  const items = (record.items || record.orderItems || [])
    .map(item => ({
      ...item,
      goodsName: item.productName || item.goodsName || '',
      expectedQty: Number(item.effectivePurchaseQty),
      receivedQty: Number(item.receivedQty || 0),
      remainingQty: Number(item.remainingQty),
      quantity: Number(item.receivedQty || 0),
      price: item.unitPrice,
      amount: item.unitPrice == null ? null : Number((Number(item.receivedQty || 0) * Number(item.unitPrice)).toFixed(2))
    }))
  const remainingQuantity = items.reduce((sum, item) => sum + item.remainingQty, 0)
  const remainingTypes = [...new Set(items.filter(item => item.remainingQty > 0.0000001).map(item => item.productType))]
  const supplierNames = [...new Set(items.map(item => String(item.supplierName || '').trim()).filter(Boolean))]
  const warehouseNames = [...new Set(activeBatches.map(batch => batch.warehouseName).filter(Boolean))]
  return {
    ...order,
    id: `purchase-order-${order.id}`,
    inboundId: latest?.id || null,
    editableInboundId: draft?.id || null,
    purchaseOrderId: order.id,
    inboundNo: latest?.inboundNo || record.orderNo || '',
    documentDate: latest?.documentDate || record.orderDate || '',
    warehouseName: warehouseNames.join('、') || order.warehouseName || '待选择入库仓库',
    inspector: latest?.inspector || '',
    qualityNo: latest?.qualityNo || '',
    itemSummary: items.map(item => item.goodsName).filter(Boolean).slice(0, 2).join('、') + (items.length > 2 ? ' 等' : ''),
    itemCount: items.length,
    supplierNames,
    expectedQuantity: items.reduce((sum, item) => sum + item.expectedQty, 0),
    receivedQuantity: items.reduce((sum, item) => sum + item.receivedQty, 0),
    remainingQuantity,
    remainingTypes,
    totalAmount: auditedBatches.length ? auditedBatches.reduce((sum, batch) => sum + batch.totalAmount, 0) : order.totalAmount,
    status: record.status === 'pending'
      ? 'pending_review'
      : record.sourceType === 'inbound-application' && record.status === 'draft'
        ? 'draft'
        : draft ? 'draft' : auditedBatches.length ? (remainingQuantity > 0.0000001 ? 'partial' : 'reviewed') : 'pending',
    remark: record.remark || (
      record.status === 'pending' ? '采购申请待审核'
        : record.status === 'draft' ? '采购申请草稿'
          : '采购订单已审核，等待选择仓库入库'
    ),
    items,
    batches
  }
}

async function refreshData(showMessage = true) {
  loading.value = true
  try {
    if (isReturn.value) {
      const [options, result] = await Promise.all([
        request.get('/purchase-returns/options'),
        request.get('/purchase-returns')
      ])
      returnOptions.value = options || { stores: [], suppliers: [] }
      returnRecords.value = result?.items || []
      returnError.value = ''
      if (showMessage) showNotice('采购退货列表已刷新')
      return
    }
    if (isInbound.value) {
      const [inboundData, orderData] = await Promise.all([
        request({ url: '/stock-inbounds', method: 'GET', params: { businessType: 'purchase' } }),
        request({ url: '/purchase-orders', method: 'GET' })
      ])
      const actualRecords = (Array.isArray(inboundData) ? inboundData : []).map(normalizeInbound)
      const batchesByOrder = new Map()
      actualRecords.filter(record => record.purchaseOrderId).forEach(record => {
        const key = String(record.purchaseOrderId)
        if (!batchesByOrder.has(key)) batchesByOrder.set(key, [])
        batchesByOrder.get(key).push(record)
      })
      const purchaseRecords = (Array.isArray(orderData) ? orderData : [])
        .filter(order => !order.inboundDeletedAt && (
          ['approved', 'partial', 'completed'].includes(order.status) ||
          (order.sourceType === 'inbound-application' && ['draft', 'pending'].includes(order.status)) ||
          batchesByOrder.has(String(order.orderId || order.id))
        ))
        .map(order => normalizePurchaseInbound(order, batchesByOrder.get(String(order.orderId || order.id)) || []))
        .filter(record => record.items.length)
      inboundRecords.value = [...purchaseRecords, ...actualRecords.filter(record => !record.purchaseOrderId)]
    } else {
      const data = await request({ url: '/purchase-orders', method: 'GET' })
      orderRecords.value = (Array.isArray(data) ? data : [])
        .filter(order => !(order.sourceType === 'inbound-application' && order.status === 'draft'))
        .map(normalizeOrder)
    }
    const availableIds = new Set(sourceRecords.value.map(record => record.id))
    selectedIds.value = new Set([...selectedIds.value].filter(id => availableIds.has(id)))
    if (showMessage) showNotice('列表已刷新')
  } catch (error) {
    const message = error?.response?.data?.message || error.message || '列表加载失败'
    if (isReturn.value) returnError.value = message
    else showNotice(message)
  } finally { loading.value = false }
}

onMounted(() => refreshData(false))
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

.search-grid {
  grid-template-columns: minmax(180px, 1fr) minmax(250px, 1.3fr) repeat(3, minmax(110px, .6fr)) auto !important;
}
.records-table {
  min-width: 1610px !important;
}
.is-inbound .records-table {
  min-width: 1720px !important;
}
.records-table .finance-column {
  width: 130px !important;
  text-align: left !important;
}
.records-table .action-column {
  width: 170px !important;
}
@media (max-width: 1200px) {
  .search-grid { grid-template-columns: repeat(3, minmax(140px, 1fr)) !important; }
}
@media (max-width: 600px) {
  .search-grid { grid-template-columns: 1fr !important; }
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
.table-action svg {
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
  justify-content: center;
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

.detail-item-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.detail-item-progress .progress-track {
  width: 36px;
  flex: 0 1 36px;
}

.detail-item-progress .progress-track i {
  background: #0f9f78;
}

.detail-item-progress small {
  min-width: 26px;
  color: #7d8993;
  font-size: 10px;
  text-align: right;
  white-space: nowrap;
}

.detail-progress-total {
  text-align: center !important;
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
  padding: 16px;
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
  position: relative;
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
  display: block;
  width: fit-content;
  padding: 0;
  color: var(--accent-dark);
  cursor: default;
  font-size: 12px;
}

.modal-close {
  position: absolute;
  top: 14px;
  right: 20px;
  display: inline-flex;
  align-self: flex-start;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #d7e0e8;
  border-radius: 5px;
  color: #536176;
  cursor: pointer;
}

.modal-close svg {
  display: block;
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-width: 1.8;
}

.modal-close:hover {
  color: #273245;
  background: #f0f3f6;
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

.button-danger {
  color: #b4232f;
  background: #fff;
  border-color: #efc4c8;
}

.button-danger:hover:not(:disabled) {
  background: #fff1f2;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
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
  background: rgba(var(--accent-rgb), 0.18) !important;
}

.record-row.selected {
  background: rgba(var(--accent-rgb), 0.12) !important;
}

.record-row.selected:hover {
  background: rgba(var(--accent-rgb), 0.18) !important;
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

.summary-with-count {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  min-width: 0;
}

.summary-name {
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-pill {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  padding: 4px 7px;
  color: #536a83;
  background: #f1f4f7;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 650;
  line-height: 1.3;
  white-space: nowrap;
}

.item-summary-count {
  max-width: 100%;
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

.table-action.danger { color: #b4232f; }
.table-action.danger:hover { color: #9f1c27; background: #fff1f2; border-color: #f0b9bf; }

.is-inbound .records-table {
  width: 100%;
  min-width: 1420px !important;
  table-layout: fixed;
}

.is-inbound .records-table th {
  height: 42px;
  text-align: left;
}

.is-inbound .records-table td {
  height: 54px;
  text-align: left;
}

.is-inbound .records-table th:nth-child(10),
.is-inbound .records-table td:nth-child(10) {
  width: auto !important;
}

.is-inbound .records-table .checkbox-column,
.is-inbound .records-table .action-column {
  text-align: center !important;
}

.is-inbound .records-table .quantity-cell {
  justify-content: flex-start;
}

.is-inbound .records-table .progress-column {
  text-align: left;
}

.is-inbound .records-table .progress-cell {
  justify-content: flex-start;
}

.is-inbound .detail-overview { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.is-inbound .inbound-detail-overview > div:last-child {
  width: max-content;
  align-items: flex-start;
  justify-self: start;
}
.is-inbound .inbound-detail-overview .status-tag {
  align-self: flex-start;
  flex: 0 0 auto;
  width: max-content;
  max-width: max-content;
  white-space: nowrap;
}

.is-inbound .quantity-cell {
  gap: 3px;
  white-space: nowrap;
}

.is-inbound .quantity-cell span {
  white-space: nowrap;
}

.is-inbound .progress-column {
  text-align: center;
}

.is-inbound .progress-cell {
  justify-content: center;
  margin-top: 0;
}

.supplement-action {
  width: auto;
  min-width: 88px;
  padding: 0 7px;
  gap: 3px;
  color: var(--accent-dark);
  white-space: nowrap;
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
  padding: 16px;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.detail-modal {
  width: min(1200px, calc(100vw - 32px));
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
  margin: 0;
  padding: 18px 16px;
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

.inbound-items-table {
  width: 100%;
  min-width: 1160px;
  table-layout: fixed;
}

.is-inbound .detail-items-table.inbound-items-table th,
.is-inbound .detail-items-table.inbound-items-table td {
  text-align: left;
  font-variant-numeric: tabular-nums;
}

.inbound-items-table .item-remark-cell {
  overflow: hidden;
  text-overflow: ellipsis;
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

.detail-items-table tfoot td {
  height: 45px;
  background: #f8fafc;
  border-top: 1px solid #dfe5ec;
  color: #283548;
  font-weight: 650;
}

.detail-items-table tfoot .detail-total-label,
.detail-items-table tfoot td:nth-child(3) {
  text-align: left;
}

.batch-items-table {
  width: 100%;
  min-width: 0;
  table-layout: fixed;
}

.batch-items-table th,
.batch-items-table td {
  overflow: hidden;
  padding-right: 7px;
  padding-left: 7px;
  text-overflow: ellipsis;
}

.batch-items-table tbody td {
  border-top: 0;
  border-bottom: 1px solid #edf1f5;
  vertical-align: middle;
}

.detail-items-table.batch-items-table thead th,
.detail-items-table.batch-items-table tbody td {
  text-align: left;
}

.detail-items-table.batch-items-table tbody td.batch-quantity {
  text-align: right;
}

.batch-items-table th:nth-child(1) {
  width: 10%;
}

.batch-items-table th:nth-child(2) {
  width: 18%;
}

.batch-items-table th:nth-child(3) {
  width: 17%;
}

.batch-items-table th:nth-child(4) {
  width: 7%;
}

.batch-items-table th:nth-child(5) {
  width: 8%;
}

.batch-items-table th:nth-child(6) {
  width: 11%;
}

.batch-items-table th:nth-child(7) {
  width: 12%;
}

.batch-items-table th:nth-child(8) {
  width: 8%;
}

.batch-items-table th:nth-child(9) {
  width: 9%;
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

.detail-modal-footer .footer-actions {
  margin-left: auto;
}

.is-return .return-search-grid {
  grid-template-columns: minmax(210px, 1.2fr) minmax(120px, 0.6fr) minmax(110px, 0.55fr) minmax(220px, 1.1fr) minmax(120px, 0.6fr) auto !important;
  gap: 10px;
}

.is-return .search-panel {
  padding: 14px 16px;
  margin-bottom: 12px;
}

.is-return .search-field {
  gap: 5px;
}

.is-return .search-field input,
.is-return .search-field select {
  height: 36px;
}

.is-return .date-range {
  grid-template-columns: minmax(104px, 1fr) auto minmax(104px, 1fr);
  gap: 5px;
}

.is-return .search-actions {
  gap: 7px;
}

.is-return .search-actions .button {
  height: 36px;
  min-height: 36px;
  padding: 0 12px;
}

.is-return .records-toolbar {
  min-height: 56px;
  padding: 8px 14px;
}

.is-return .toolbar-filters {
  gap: 8px;
}

.is-return .toolbar-heading {
  gap: 5px;
  padding-right: 2px;
}

.is-return .toolbar-heading h1 {
  font-size: 15px;
}

.is-return .status-filter-slider {
  gap: 3px;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  padding: 3px;
  border-radius: 6px;
}

.is-return .slider-tab {
  flex: 0 0 auto;
  height: 32px;
  gap: 5px;
  padding: 0 10px;
  border-radius: 5px;
  font-size: 12px;
}

.is-return .count-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 10px;
}

.is-return .toolbar-actions {
  gap: 6px;
}

.is-return .toolbar-actions .button {
  height: 34px;
  min-height: 34px;
  padding: 0 11px;
}

.is-return .toolbar-actions .icon-button {
  width: 34px;
  height: 34px;
}

.is-return .return-summary {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 9px 14px;
  color: var(--text-secondary);
  background: #fbfcfd;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}

.is-return .return-summary span {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}

.is-return .return-summary strong {
  color: var(--accent-dark);
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}

.is-return .return-error {
  display: flex;
  margin: 14px 16px 0;
}

.is-return .return-records-table {
  width: 100%;
  min-width: 1120px !important;
  table-layout: fixed;
}

.is-return .return-records-table th,
.is-return .return-records-table td {
  padding-right: 8px;
  padding-left: 8px;
}

.is-return .return-records-table th:nth-child(1),
.is-return .return-records-table td:nth-child(1) {
  width: 9%;
}

.is-return .return-records-table th:nth-child(2),
.is-return .return-records-table td:nth-child(2) {
  width: 15%;
}

.is-return .return-records-table th:nth-child(3),
.is-return .return-records-table td:nth-child(3) {
  width: 9%;
}

.is-return .return-records-table th:nth-child(4),
.is-return .return-records-table td:nth-child(4) {
  width: 6%;
  text-align: center;
}

.is-return .return-records-table th:nth-child(5),
.is-return .return-records-table td:nth-child(5) {
  width: 10%;
  display: table-cell;
  text-align: center;
  white-space: nowrap;
}

.is-return .return-records-table th:nth-child(6),
.is-return .return-records-table td:nth-child(6),
.is-return .return-records-table th:nth-child(7),
.is-return .return-records-table td:nth-child(7) {
  width: 11.5%;
  text-align: right;
}

.is-return .return-records-table th:nth-child(8),
.is-return .return-records-table td:nth-child(8) {
  width: 8%;
}

.is-return .return-records-table th:nth-child(9),
.is-return .return-records-table td:nth-child(9) {
  width: 10%;
}

.is-return .return-records-table th:nth-child(10),
.is-return .return-records-table td:nth-child(10) {
  width: 10%;
}

.is-return .return-records-table .action-column {
  width: 10% !important;
  text-align: center;
}

.is-return .return-records-table .primary-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.is-return .return-records-table .audit-action {
  color: var(--accent-dark);
}

.records-table th.action-column,
.records-table td.action-column,
.records-table .skeleton-row td:last-child {
  position: sticky;
  right: 0;
  background-clip: padding-box;
  box-shadow: -8px 0 12px -10px rgba(15, 23, 42, 0.42);
}

.records-table th.action-column {
  z-index: 4;
  background-color: #f8fafc;
}

.records-table td.action-column,
.records-table .skeleton-row td:last-child {
  z-index: 2;
}

.records-table td.action-column {
  background-color: transparent !important;
}

.records-table .skeleton-row td:last-child {
  background-color: #fff;
}

/* Keep the three purchase tables dense horizontally without changing row height. */
.purchase-list-page .search-grid {
  column-gap: 5px;
}

.purchase-list-page .search-field {
  gap: 7px;
}

.purchase-list-page .date-range {
  gap: 5px;
}

.purchase-list-page .button {
  padding-right: 10px;
  padding-left: 10px;
}

.purchase-list-page .records-toolbar {
  gap: 10px;
}

.purchase-list-page .toolbar-filters,
.purchase-list-page .toolbar-actions {
  gap: 6px;
}

.purchase-list-page .status-filter-slider {
  gap: 3px;
}

.purchase-list-page .slider-tab {
  gap: 4px;
  padding-right: 8px;
  padding-left: 8px;
}

.purchase-list-page .records-table th,
.purchase-list-page .records-table td {
  padding-right: 5px;
  padding-left: 5px;
}

.purchase-list-page .records-table th:nth-child(1),
.purchase-list-page .records-table td:nth-child(1) {
  width: 38px;
  padding-right: 5px;
  padding-left: 5px;
}

.purchase-list-page .row-actions {
  gap: 3px;
}

.purchase-list-page .table-action {
  width: 27px;
}

.purchase-list-page .supplement-action {
  min-width: 80px;
  padding-right: 5px;
  padding-left: 5px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table {
  min-width: 1540px !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th,
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td {
  text-align: left !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table .checkbox-column,
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table .action-column {
  text-align: center !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table .amount-cell,
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(7),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(8) {
  text-align: right !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table .payment-status-cell {
  white-space: nowrap;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(2),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(2) {
  width: 138px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(3),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(3) {
  width: 96px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(4),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(4) {
  width: 112px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(5),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(5) {
  width: 145px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(6),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(6) {
  width: 174px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(7),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(7) {
  width: 128px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(8),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(8) {
  width: 124px;
  text-align: right;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(9),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(9) {
  width: 116px !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(10),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(10) {
  width: 180px !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(11),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(11) {
  width: 102px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(12),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(12) {
  width: 98px !important;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(13),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(13) {
  width: 90px;
}

.purchase-list-page:not(.is-inbound):not(.is-return) .records-table th:nth-child(14),
.purchase-list-page:not(.is-inbound):not(.is-return) .records-table td:nth-child(14) {
  width: 96px !important;
}

@media (max-width: 1280px) {
  .is-return .return-search-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  }

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

  .toolbar-actions {
    flex-wrap: wrap;
  }

  .toolbar-actions .record-count {
    flex-basis: 100%;
  }

  .toolbar-actions .button-danger {
    flex: 1;
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

.is-inbound .detail-overview { grid-template-columns: 1fr 1fr; }
.is-inbound .inbound-detail-overview > div:last-child { grid-column: 1 / -1; }

  .page-notice {
    top: 12px;
  }

  .is-return .return-search-grid {
    grid-template-columns: 1fr !important;
  }

  .is-return .return-summary {
    flex-wrap: wrap;
    gap: 10px 18px;
  }
}
</style>
