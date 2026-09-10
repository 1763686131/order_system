<template>
  <div class="unified-order-list-page">
    <!-- 筛选工具栏 - 参考 StockRecordList 风格 -->
    <section class="search-panel" aria-label="订单筛选">
      <form class="search-grid" @submit.prevent="handleFilter">
        <label class="field-group">
          <span>关键词搜索</span>
          <span class="input-with-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            <input
              v-model="filters.keyword"
              type="search"
              :placeholder="searchPlaceholder"
            />
          </span>
        </label>

        <div class="field-group date-field">
          <span>订单日期</span>
          <div class="date-range">
            <input
              v-model="filters.startDate"
              type="date"
              aria-label="开始日期"
              :max="filters.endDate || undefined"
            />
            <span aria-hidden="true">至</span>
            <input
              v-model="filters.endDate"
              type="date"
              aria-label="结束日期"
              :min="filters.startDate || undefined"
            />
          </div>
        </div>

        <div v-if="mode === 'logistics'" class="field-group shipping-method-filter">
          <span>发货方式</span>
          <div class="multi-select-wrapper" @click.stop>
            <div class="multi-select-trigger" @click="shippingDropdownOpen = !shippingDropdownOpen">
              <span class="selected-text">{{ selectedShippingMethodText }}</span>
              <svg class="dropdown-icon" :class="{ open: shippingDropdownOpen }" viewBox="0 0 24 24">
                <path d="m6 9 6 6 6-6"></path>
              </svg>
            </div>
            <div v-if="shippingDropdownOpen" class="multi-select-dropdown">
              <label
                v-for="method in shippingMethods"
                :key="method"
                class="dropdown-option"
                @click.stop
              >
                <input
                  type="checkbox"
                  :checked="filters.shippingMethods.includes(method)"
                  @change="toggleShippingMethod(method)"
                />
                <span>{{ method }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="search-actions">
          <button class="button button-secondary" type="button" @click="handleReset">
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

    <!-- 订单记录面板 -->
    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <!-- 门店分类滑块 -->
          <div class="material-type-slider" role="tablist" aria-label="门店分类筛选">
            <button
              :class="['slider-tab', { active: filters.category === '' }]"
              type="button"
              @click="filters.category = ''"
            >
              全部
            </button>
            <button
              v-for="store in stores"
              :key="store.id"
              :class="['slider-tab', { active: filters.category === store.name + '订单' }]"
              type="button"
              @click="filters.category = store.name + '订单'"
            >
              {{ store.name }}订单
            </button>
          </div>

          <!-- 状态筛选滑块 -->
          <div class="status-filter-slider" role="tablist" aria-label="订单状态筛选">
            <button
              :class="['slider-tab', { active: filters.status === '' }]"
              type="button"
              @click="filters.status = ''"
            >
              全部
              <span class="count-badge">{{ getStatusCount('') }}</span>
            </button>
            <button
              v-if="mode === 'finance'"
              :class="['slider-tab', { active: filters.status === 'pending' }]"
              type="button"
              @click="filters.status = 'pending'"
            >
              未完成
              <span class="count-badge">{{ getStatusCount('pending') }}</span>
            </button>
            <button
              v-if="mode === 'finance'"
              :class="['slider-tab', { active: filters.status === 'completed' }]"
              type="button"
              @click="filters.status = 'completed'"
            >
              已完成
              <span class="count-badge">{{ getStatusCount('completed') }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.status === 'shipped' }]"
              type="button"
              @click="filters.status = 'shipped'"
            >
              已发货
              <span class="count-badge">{{ getStatusCount('shipped') }}</span>
            </button>
          </div>

          <!-- 选中提示 -->
          <div v-if="selectedOrders.length > 0" class="selection-count">
            已选中 <strong>{{ selectedOrders.length }}</strong> 项
          </div>
        </div>

        <div class="toolbar-actions">
          <button
            class="icon-button refresh-button"
            type="button"
            title="刷新列表"
            :disabled="loading"
            @click="fetchOrdersData"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button
            class="button button-export"
            type="button"
            title="导出Excel"
            @click="handleExport"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            导出 Excel
          </button>
          <button
            v-if="mode === 'finance'"
            class="button button-primary create-button"
            type="button"
            @click="handleAdd"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            {{ addButtonText }}
          </button>
          <!-- 批量删除按钮 -->
          <button
            class="button button-delete"
            :class="{ 'has-selection': selectedOrders.length > 0 }"
            type="button"
            :disabled="selectedOrders.length === 0"
            @click="handleBatchDelete"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M3 6h18"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M10 11v6"></path>
              <path d="M14 11v6"></path>
            </svg>
            批量删除
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="col-checkbox">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  :indeterminate="isPagePartiallySelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="document-column">订单编号</th>
              <th>日期</th>
              <th>客户</th>
              <th>收货人</th>
              <th>电话</th>
              <th class="address-column">地址</th>
              <th class="material-column">货物</th>

              <!-- 财务模式列 -->
              <template v-if="mode === 'finance'">
                <th class="number-column">应收金额</th>
                <th class="number-column">已收金额</th>
                <th class="number-column">未收金额</th>
              </template>

              <!-- 物流模式列 -->
              <template v-if="mode === 'logistics'">
                <th>重量</th>
                <th>发货方式</th>
                <th>单号</th>
                <th>回单</th>
              </template>

              <th v-if="mode === 'finance'">状态</th>
              <th v-if="mode === 'logistics'" class="number-column">运费</th>
              <th>备注</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in columnCount" :key="cell"><span></span></td>
              </tr>
            </template>
            <tr v-else-if="pagedRecords.length === 0">
              <td :colspan="columnCount" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>{{ emptyMessage }}</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>
            <tr
              v-for="order in paginatedOrders"
              v-else
              :key="order.id"
              class="record-row"
              :class="{ selected: isSelected(order.id) }"
              :style="{ '--store-bg-color': getStoreColor(order) }"
              tabindex="0"
              @click="openOrderDetail(order)"
              @keydown.enter.self.prevent="openOrderDetail(order)"
            >
              <td class="col-checkbox" @click.stop>
                <input
                  type="checkbox"
                  :checked="isSelected(order.id)"
                  :disabled="isSalesOrderLocked(order)"
                  :title="isSalesOrderLocked(order) ? '已过账单据不可删除，请先反审核' : '选择订单'"
                  @change="toggleSelect(order.id)"
                />
              </td>
              <td>
                <button class="document-link" type="button" @click.stop="openOrderDetail(order)">
                  {{ order.order_number || order.id }}
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="m9 18 6-6-6-6"></path>
                  </svg>
                </button>
              </td>
              <td class="date-cell">{{ formatDate(order) }}</td>
              <td>{{ order.order_client || '-' }}</td>
              <td class="party-cell" :title="getContactPerson(order)">
                {{ getContactPerson(order) }}
              </td>
              <td>{{ getContactPhone(order) }}</td>
              <td class="address-cell" :title="getContactAddress(order)">
                {{ getContactAddress(order).substring(0, 15) }}{{ getContactAddress(order).length > 15 ? '...' : '' }}
              </td>
              <td class="material-cell" :title="getGoodsTooltip(order)">
                <strong>{{ getGoodsDisplay(order).substring(0, 12) }}</strong>
                <span v-if="getGoodsDisplay(order).length > 12">...</span>
              </td>

              <!-- 财务模式列 -->
              <template v-if="mode === 'finance'">
                <td class="number-column numeric">{{ getShouldReceive(order) }}</td>
                <td class="number-column numeric">{{ getCurrentPayment(order) }}</td>
                <td class="number-column numeric">{{ getCurrentDebt(order) }}</td>
              </template>

              <!-- 物流模式列 -->
              <template v-if="mode === 'logistics'">
                <td>{{ getTotalWeight(order) }}</td>
                <td>
                  <span
                    class="shipping-tag clickable can-edit"
                    @click.stop="handleShippingTagClick(order)"
                  >
                    {{ getShippingMethodText(order) }}
                  </span>
                </td>
                <td class="tracking-cell">
                  <span
                    v-if="order.logistics_no"
                    class="tracking-number clickable"
                    @click.stop="copyLogisticsNo(order)"
                    v-html="order.logistics_no.replace(/-/g, '<br>')"
                  >
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span
                    v-if="hasReceipt(order)"
                    class="receipt-status has-receipt clickable"
                    @click.stop="handleReceiptClick(order)"
                  >
                    回单
                  </span>
                </td>
              </template>

              <td v-if="mode === 'finance'">
                <span :class="['status-tag', getStatusClass(order)]">
                  <i aria-hidden="true"></i>
                  {{ getStatusText(order) }}
                </span>
              </td>
              <td v-if="mode === 'logistics'" class="number-column money-value">
                <span v-if="getFreightTotal(order) > 0" class="freight-amount" @click.stop="showFreightDetail(order)">
                  ¥{{ getFreightTotal(order).toFixed(2) }}
                </span>
                <span v-else>-</span>
              </td>
              <td class="remark-cell">
                {{ order.remark && order.remark.length > 4 ? order.remark.substring(0, 4) + '...' : (order.remark || '-') }}
              </td>
              <td class="operation-column" @click.stop>
                <div class="row-actions">
                  <button
                    v-if="mode === 'finance' && isNewOrder(order)"
                    type="button"
                    title="复制为新订单"
                    @click="handleCopySalesOrder(order)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <rect x="8" y="8" width="12" height="12" rx="2"></rect>
                      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path>
                    </svg>
                  </button>
                  <button
                    v-if="mode === 'logistics'"
                    type="button"
                    title="复制物流信息"
                    @click="handleCopyOrderInfo(order)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <rect x="8" y="8" width="12" height="12" rx="2"></rect>
                      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path>
                    </svg>
                  </button>
                  <button
                    v-if="mode === 'finance' && isSalesOrder(order) && !isOrderAudited(order)"
                    type="button"
                    title="编辑订单"
                    @click="handleEditOrder(order)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button
                    v-if="mode === 'finance' && order.status === 'completed'"
                    type="button"
                    title="出库发货"
                    @click="handleShipOrder(order)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <rect x="1" y="3" width="15" height="13"></rect>
                      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
                      <circle cx="5.5" cy="18.5" r="2.5"></circle>
                      <circle cx="18.5" cy="18.5" r="2.5"></circle>
                    </svg>
                  </button>
                  <button
                    v-if="mode === 'logistics'"
                    type="button"
                    :title="hasLogistics(order) ? '修改物流信息' : '录入物流信息'"
                    @click="handleLogisticsAction(order)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredOrders.length === 0 && !loading">
              <td :colspan="columnCount" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>{{ emptyMessage }}</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredOrders.length }}</strong> 条记录
          <template v-if="filteredOrders.length">，当前 {{ pageStart }}-{{ pageEnd }} 条</template>
        </span>
        <div class="pagination" aria-label="分页">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="30">30 条 / 页</option>
            <option :value="50">50 条 / 页</option>
            <option :value="99999">全部</option>
          </select>
          <button
            type="button"
            title="上一页"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"></path></svg>
          </button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button
            type="button"
            title="下一页"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
          </button>
        </div>
      </footer>
    </section>

    <!-- 订单详情居中弹窗 -->
    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="detailModalOpen && selectedOrder" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeDetailModal"></div>
          <section
            class="detail-modal"
            role="dialog"
            aria-modal="true"
            :aria-label="`${mode === 'logistics' ? '物流' : '订单'}详情`"
            tabindex="-1"
            @keydown.esc="closeDetailModal"
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
                  <span>{{ mode === 'logistics' ? '物流详情' : '订单详情' }}</span>
                  <h2>{{ selectedOrder.order_number || selectedOrder.id }}</h2>
                </div>
              </div>
              <button class="detail-modal-close" type="button" title="关闭" @click="closeDetailModal">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <section class="detail-modal-overview">
                <div class="overview-head">
                  <span :class="['status-tag', getStatusClass(selectedOrder)]">
                    <i aria-hidden="true"></i>
                    {{ getStatusText(selectedOrder) }}
                  </span>
                  <span>{{ getCategoryText(selectedOrder) }}</span>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>订单日期</dt>
                    <dd>{{ formatDate(selectedOrder) }}</dd>
                  </div>
                  <div>
                    <dt>客户名称</dt>
                    <dd>{{ selectedOrder.order_client || '-' }}</dd>
                  </div>
                  <div>
                    <dt>收货人</dt>
                    <dd>{{ getContactPerson(selectedOrder) }}</dd>
                  </div>
                  <div>
                    <dt>联系电话</dt>
                    <dd>{{ getContactPhone(selectedOrder) }}</dd>
                  </div>
                  <div v-if="selectedOrder.project_name">
                    <dt>工程项目</dt>
                    <dd>{{ selectedOrder.project_name }}</dd>
                  </div>
                  <div>
                    <dt>收货地址</dt>
                    <dd>{{ getContactAddress(selectedOrder) }}</dd>
                  </div>
                </dl>

              </section>

              <!-- 商品明细 -->
              <section v-if="isNewOrder(selectedOrder)" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>商品明细</h3>
                    <span>共 {{ selectedOrder.order_goods?.length || 0 }} 行</span>
                  </div>
                </div>
                <div class="detail-table-scroll">
                  <table class="detail-table order-goods-table">
                    <thead>
                      <tr>
                        <th>序号</th>
                        <th class="material-detail-column">商品名称</th>
                        <th>规格型号</th>
                        <th>单位</th>
                        <th class="number-column">件数</th>
                        <th class="number-column">数量</th>
                        <th class="number-column">单价</th>
                        <th class="money-column">金额</th>
                        <th class="number-column">税率</th>
                        <th class="money-column">税额</th>
                        <th class="money-column">含税金额</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(item, index) in selectedOrder.order_goods" :key="index">
                        <td>{{ index + 1 }}</td>
                        <td>
                          <strong>{{ getGoodsItemName(item) }}</strong>
                        </td>
                        <td>{{ item.spec || '-' }}</td>
                        <td>{{ item.unit || '-' }}</td>
                        <td class="number-column numeric">{{ item.packages || '-' }}</td>
                        <td class="number-column numeric">{{ item.quantity || '-' }}</td>
                        <td class="number-column numeric">{{ item.price ? `¥${item.price.toFixed(2)}` : '-' }}</td>
                        <td class="money-column item-amount">{{ item.amount ? `¥${item.amount.toFixed(2)}` : '-' }}</td>
                        <td class="number-column numeric">{{ formatItemTaxRate(item) }}</td>
                        <td class="money-column numeric">¥{{ calculateItemTaxAmount(item) }}</td>
                        <td class="money-column item-amount">{{ item.total_amount ? `¥${item.total_amount.toFixed(2)}` : '-' }}</td>
                      </tr>
                      <tr v-if="!selectedOrder.order_goods || selectedOrder.order_goods.length === 0">
                        <td colspan="11" class="detail-modal-empty">暂无商品明细</td>
                      </tr>
                    </tbody>
                    <tfoot v-if="selectedOrder.order_goods && selectedOrder.order_goods.length > 0">
                      <tr class="detail-total-row">
                        <td colspan="4" class="detail-total-label">合计</td>
                        <td class="number-column numeric">{{ calculateTotalPackages(selectedOrder) }}</td>
                        <td class="number-column numeric">{{ calculateTotalQuantity(selectedOrder) }}</td>
                        <td></td>
                        <td class="money-column item-amount">¥{{ calculateSubtotal(selectedOrder) }}</td>
                        <td></td>
                        <td class="money-column item-amount">¥{{ calculateTaxAmount(selectedOrder) }}</td>
                        <td class="money-column item-amount">¥{{ calculateTotalAmount(selectedOrder) }}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </section>

              <!-- 财务信息 -->
              <section v-if="mode === 'finance' && isNewOrder(selectedOrder)" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>财务信息</h3>
                  </div>
                </div>
                <div class="summary-strip financial-summary-strip">
                  <div><span>应收金额</span><strong>{{ getShouldReceive(selectedOrder) }}</strong></div>
                  <div class="received-amount"><span>已收金额</span><strong>{{ getCurrentPayment(selectedOrder) }}</strong></div>
                  <div class="outstanding-amount"><span>未收金额</span><strong>{{ getCurrentDebt(selectedOrder) }}</strong></div>
                </div>
              </section>

              <!-- 物流信息 -->
              <section v-if="mode === 'logistics'" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>物流信息</h3>
                  </div>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>发货方式</dt>
                    <dd>{{ getShippingMethodText(selectedOrder) }}</dd>
                  </div>
                  <div>
                    <dt>物流单号</dt>
                    <dd>{{ selectedOrder.logistics_no || '-' }}</dd>
                  </div>
                  <div>
                    <dt>总重量</dt>
                    <dd>{{ getTotalWeight(selectedOrder) }}</dd>
                  </div>
                  <div v-if="getFreightTotal(selectedOrder) > 0">
                    <dt>运费</dt>
                    <dd>¥{{ getFreightTotal(selectedOrder).toFixed(2) }}</dd>
                  </div>
                </dl>
              </section>

              <!-- 备注信息 -->
              <section v-if="selectedOrder.remark" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>备注信息</h3>
                  </div>
                </div>
                <div style="padding: 15px;">
                  <p style="margin: 0; color: #374151; line-height: 1.6;">{{ selectedOrder.remark }}</p>
                </div>
              </section>
            </div>

            <footer class="detail-modal-footer">
              <div class="detail-modal-left-actions">
                <button
                  v-if="mode === 'finance' && isSalesOrder(selectedOrder) && !isOrderAudited(selectedOrder)"
                  class="button button-edit"
                  type="button"
                  @click="handleEditOrder(selectedOrder)"
                >
                  修改
                </button>
                <button
                  v-if="mode === 'finance' && canDeleteOrder(selectedOrder)"
                  class="button button-danger-light"
                  type="button"
                  :disabled="orderActionLoading !== ''"
                  @click="handleDelete(selectedOrder)"
                >
                  删除
                </button>
              </div>
              <div class="detail-modal-actions">
                <button
                  v-if="mode === 'finance' && canAuditOrder(selectedOrder)"
                  class="button button-audit"
                  type="button"
                  :disabled="orderActionLoading !== ''"
                  @click="handleAuditOrder(selectedOrder)"
                >
                  {{ orderActionLoading === 'audit' ? '审核中...' : '审核' }}
                </button>
                <button
                  v-if="mode === 'finance' && canReverseAuditOrder(selectedOrder)"
                  class="button button-reverse-audit"
                  type="button"
                  :disabled="orderActionLoading !== ''"
                  @click="handleReverseAuditOrder(selectedOrder)"
                >
                  {{ orderActionLoading === 'reverse-audit' ? '反审核中...' : '反审核' }}
                </button>
                <button
                  v-if="mode === 'finance' && selectedOrder.status === 'completed'"
                  class="button button-primary"
                  type="button"
                  @click="handleShipOrder(selectedOrder)"
                >
                  出库发货
                </button>
                <button
                  v-if="mode === 'logistics' && !hasLogistics(selectedOrder)"
                  class="button button-primary"
                  type="button"
                  @click="handleShippingClick(selectedOrder)"
                >
                  录入物流
                </button>
                <button
                  v-if="mode === 'logistics' && hasLogistics(selectedOrder)"
                  class="button button-primary"
                  type="button"
                  @click="handleEdit(selectedOrder)"
                >
                  修改物流
                </button>
                <button
                  v-if="mode === 'logistics'"
                  class="button button-secondary"
                  type="button"
                  @click="handleShippingTagClick(selectedOrder)"
                >
                  {{ hasReceipt(selectedOrder) ? '管理回单' : '上传回单' }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>

    <!-- 展开信息弹窗 -->
    <div v-if="expandModal.visible" class="expand-modal-overlay" @click="closeExpandModal">
      <div class="expand-modal" @click.stop>
        <div class="expand-modal-header">
          <h3>{{ expandModal.title }}</h3>
          <button class="modal-close-btn" @click="closeExpandModal">✕</button>
        </div>
        <div class="expand-modal-body">
          <p>{{ expandModal.content }}</p>
        </div>
      </div>
    </div>

    <!-- 运费明细弹窗 -->
    <div v-if="freightDetailVisible" class="expand-modal-overlay" @click="closeFreightDetail">
      <div class="freight-detail-modal" @click.stop>
        <div class="freight-modal-header">
          <h3>运费明细</h3>
          <button class="modal-close-btn" @click="closeFreightDetail">✕</button>
        </div>
        <div class="freight-modal-body">
          <div class="freight-info">
            <div class="info-row">
              <span class="label">订单编号：</span>
              <span class="value">{{ freightDetailData?.orderId }}</span>
            </div>
            <div class="info-row">
              <span class="label">订单归属：</span>
              <span class="value">{{ freightDetailData?.orderClient }}</span>
            </div>
          </div>
          <div class="freight-items">
            <div
              v-for="(item, index) in freightDetailData?.costs"
              :key="index"
              class="freight-item"
            >
              <div class="item-note">{{ item.note }}</div>
              <div class="item-amount">¥{{ item.amount.toFixed(2) }}</div>
            </div>
          </div>
          <div class="freight-total">
            <span class="total-label">合计：</span>
            <span class="total-amount">¥{{ freightDetailData?.total.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 商品明细弹窗 -->
    <div v-if="orderDetailVisible" class="expand-modal-overlay" @click="closeOrderDetail">
      <div class="order-detail-modal" @click.stop>
        <div class="order-detail-header">
          <h3>订单明细</h3>
          <button class="modal-close-btn" @click="closeOrderDetail">✕</button>
        </div>
        <div class="order-detail-body">
          <!-- 基本信息 -->
          <div class="detail-section">
            <div class="detail-row">
              <span class="detail-label">订单编号：</span>
              <span class="detail-value">{{ currentDetailOrder?.order_number || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">客户名称：</span>
              <span class="detail-value">{{ currentDetailOrder?.order_client || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">订单日期：</span>
              <span class="detail-value">{{ currentDetailOrder?.order_date || currentDetailOrder?.date || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">工程项目：</span>
              <span class="detail-value">{{ currentDetailOrder?.project_name || '-' }}</span>
            </div>
          </div>

          <!-- 商品明细表格 -->
          <div class="detail-section">
            <h4>商品明细</h4>
            <table class="detail-table">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>商品名称</th>
                  <th>规格型号</th>
                  <th>单位</th>
                  <th>件数</th>
                  <th>数量</th>
                  <th>单价</th>
                  <th>金额</th>
                  <th>含税金额</th>
                  <th>备注</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in currentDetailOrder?.order_goods" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ getGoodsItemName(item) }}</td>
                  <td>{{ item.spec || '-' }}</td>
                  <td>{{ item.unit || '-' }}</td>
                  <td>{{ item.packages || '-' }}</td>
                  <td>{{ item.quantity || '-' }}</td>
                  <td>{{ item.price ? `¥${item.price.toFixed(2)}` : '-' }}</td>
                  <td>{{ item.amount ? `¥${item.amount.toFixed(2)}` : '-' }}</td>
                  <td>{{ item.total_amount ? `¥${item.total_amount.toFixed(2)}` : '-' }}</td>
                  <td>{{ item.remark || '-' }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="detail-total-row">
                  <td colspan="4" class="detail-total-label">合计</td>
                  <td>{{ getDetailTotalPackages(currentDetailOrder) }}</td>
                  <td>{{ getDetailTotalQuantity(currentDetailOrder) }}</td>
                  <td colspan="4"></td>
                </tr>
              </tfoot>
            </table>
          </div>

          <!-- 财务汇总 -->
          <div class="detail-section financial-summary">
            <div class="summary-row">
              <span class="summary-label">小计（不含税）：</span>
              <span class="summary-value">{{ currentDetailOrder?.subtotal_amount ? `¥${currentDetailOrder.subtotal_amount.toFixed(2)}` : '-' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">税额：</span>
              <span class="summary-value">{{ currentDetailOrder?.tax_amount ? `¥${currentDetailOrder.tax_amount.toFixed(2)}` : '-' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">价税合计：</span>
              <span class="summary-value">{{ currentDetailOrder?.total_amount ? `¥${currentDetailOrder.total_amount.toFixed(2)}` : '-' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">折扣金额：</span>
              <span class="summary-value">{{ currentDetailOrder?.discount_amount ? `¥${currentDetailOrder.discount_amount.toFixed(2)}` : '¥0.00' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">其他费用：</span>
              <span class="summary-value">{{ currentDetailOrder?.other_fees ? `¥${currentDetailOrder.other_fees.toFixed(2)}` : '¥0.00' }}</span>
            </div>
            <div class="summary-row highlight">
              <span class="summary-label">本单应收：</span>
              <span class="summary-value">{{ currentDetailOrder?.should_receive ? `¥${currentDetailOrder.should_receive.toFixed(2)}` : '-' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">本次收款：</span>
              <span class="summary-value">{{ currentDetailOrder?.current_payment ? `¥${currentDetailOrder.current_payment.toFixed(2)}` : '¥0.00' }}</span>
            </div>
            <div class="summary-row highlight">
              <span class="summary-label">本单欠款：</span>
              <span class="summary-value">{{ currentDetailOrder?.current_debt ? `¥${currentDetailOrder.current_debt.toFixed(2)}` : '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, h, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { useOrderStore } from '@/stores/order'
import { useOrderDraftStore } from '@/stores/orderDraft'
import { formatOrderForCopy } from '@/utils/tools'
import { getStores } from '@/utils/storeHelper'

const router = useRouter()

const props = defineProps({
  mode: {
    type: String,
    required: true,
    validator: (value) => ['finance', 'logistics'].includes(value)
  }
})

const emit = defineEmits(['ship', 'refresh'])

const orderStore = useOrderStore()
const orderDraftStore = useOrderDraftStore()

// 从父组件注入 handleShip 方法
const handleShipFromParent = inject('handleShip', null)

// 注入 Admin 组件提供的方法
const setHeaderActions = inject('setHeaderActions', null)

// 订单数据
const orders = ref([])
const loading = ref(false)
const stores = ref([])
const products = ref([]) // 商品列表，用于反查商品名称

// 详情弹窗状态
const detailModalOpen = ref(false)
const selectedOrder = ref(null)
const orderActionLoading = ref('')

// 发货方式输入
const shippingMethodInput = ref('')

// 排序状态
const sortOrder = ref('desc') // 'desc' = 最近到远, 'asc' = 最远到近
onMounted(() => {
  if (setHeaderActions) {
    // 订单列表只显示导出按钮（新增订单按钮已移到顶部）
    if (props.mode === 'finance') {
      setHeaderActions(() =>
        h('button', {
          class: 'btn-export',
          onClick: handleExport,
          style: 'padding: 10px 20px; background: #fff; color: #6b7280; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;'
        }, [
          h('span', '📥'),
          '导出数据'
        ])
      )
    } else {
      // 物流列表只显示导出按钮
      setHeaderActions(() =>
        h('button', {
          class: 'btn-export',
          onClick: handleExport,
          style: 'padding: 10px 20px; background: #fff; color: #6b7280; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;'
        }, [
          h('span', '📥'),
          '导出数据'
        ])
      )
    }
  }

  // 注册全局刷新回调，当弹窗操作完成后刷新数据
  window.refreshUnifiedOrderList = () => {
    fetchOrdersData()
  }

  // 添加点击外部关闭下拉框的监听
  document.addEventListener('click', handleClickOutside)

  fetchOrdersData()
})

onUnmounted(() => {
  // 清理事件监听
  document.removeEventListener('click', handleClickOutside)
  if (setHeaderActions) {
    setHeaderActions(null)
  }
})

// 监听 mode 变化，重新获取数据
watch(() => props.mode, () => {
  fetchOrdersData()
})


// 根据 store_id 或 type 获取门店名称
const getStoreName = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store ? store.name : '未知门店'
}

// 根据 store_id 或 type 获取门店背景颜色
const getStoreColor = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store?.color || '#f5f5f5'
}

// 根据 store_id 或 type 获取门店字体颜色
const getStoreTextColor = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  const store = stores.value.find(s => s.id === storeId)
  return store?.textColor || '#333333'
}

// 根据 store_id 或 type 判断是否为绝缘（用于样式，已废弃）
const isInsulationStore = (order) => {
  const storeId = order.store_id || (order.type === 1 ? 1 : 2)
  return storeId === 1
}

// 筛选条件
const filters = ref({
  keyword: '',
  category: '',
  status: '', // 新增状态筛选
  shippingMethods: [], // 改为数组以支持多选
  startDate: '',
  endDate: ''
})

// 发货方式选项
const shippingMethods = ['物流', '零担快运', '快递', '专车', '其它']
const shippingDropdownOpen = ref(false)

// 切换发货方式选中状态
const toggleShippingMethod = (method) => {
  const index = filters.value.shippingMethods.indexOf(method)
  if (index > -1) {
    filters.value.shippingMethods.splice(index, 1)
  } else {
    filters.value.shippingMethods.push(method)
  }
}

// 计算选中的发货方式显示文本
const selectedShippingMethodText = computed(() => {
  if (filters.value.shippingMethods.length === 0) {
    return '全部发货方式'
  } else if (filters.value.shippingMethods.length === shippingMethods.length) {
    return '全部发货方式'
  } else {
    return `已选 ${filters.value.shippingMethods.length} 项`
  }
})

// 选中的订单
const selectedOrders = ref([])

// 展开弹窗状态
const expandModal = ref({
  visible: false,
  title: '',
  content: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(30)
const showAll = ref(false) // 是否显示全部

// 计算属性
const pageTitle = computed(() => {
  return props.mode === 'logistics' ? '物流订单列表' : '订单列表'
})

const addButtonText = computed(() => {
  return props.mode === 'logistics' ? '新增物流单' : '新增订单'
})

const searchPlaceholder = computed(() => {
  return props.mode === 'logistics'
    ? '搜索物流单ID、客户、收货人、单号...'
    : '搜索订单ID、客户、收货人...'
})

const emptyMessage = computed(() => {
  return props.mode === 'logistics' ? '暂无物流订单数据' : '暂无订单数据'
})

const columnCount = computed(() => {
  return props.mode === 'logistics' ? 14 : 14
})

// 获取订单数据
const fetchOrdersData = async () => {
  loading.value = true
  try {
    // 并行加载订单、门店和商品数据
    const [ordersResponse, storesData, productsData] = await Promise.all([
      request({
        url: '/orders',
        method: 'GET'
      }),
      getStores(),
      request({
        url: '/products/inventory',
        method: 'GET'
      })
    ])

    // 只显示状态为 active 的门店
    stores.value = storesData.filter(store => store.status === 'active')

    // 保存商品列表
    if (productsData && Array.isArray(productsData)) {
      products.value = productsData
    }

    if (ordersResponse && Array.isArray(ordersResponse)) {
      // 更新 orderStore 的所有订单数据
      orderStore.setOrders(ordersResponse)

      // 物流模式只显示已出库订单
      if (props.mode === 'logistics') {
        orders.value = ordersResponse.filter(order => order.status === 'shipped')
      } else {
        orders.value = ordersResponse
      }
    } else {
      orders.value = []
    }
  } catch (error) {
    console.error('获取订单失败:', error)
    orders.value = []
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (order) => {
  const date = props.mode === 'logistics'
    ? (order.shipped_date || order.completed_date || order.date || '')
    : (order.date || '')
  return date ? date.substring(0, 10) : '-'
}

// 获取分类文本
const getCategoryText = (order) => {
  return getStoreName(order) + '订单'
}

// 获取发货方式文本
const getShippingMethodText = (order) => {
  const methodMap = { 0: '物流', 1: '零担快运', 2: '快递', 3: '专车', 4: '其它' }

  if (order.shipping_method !== undefined && order.shipping_method !== '') {
    let method = methodMap[order.shipping_method] || '其它'
    if (order.shipping_method === 4 && order.shipping_custom) {
      method = order.shipping_custom
    }
    return method
  } else if (order.logistics_type) {
    return order.logistics_type
  }
  return '其它'
}

// 检查是否有回单
const hasReceipt = (order) => {
  return order.receipt_img_url && String(order.receipt_img_url).trim() !== ''
}

// 计算过滤后的订单
const filteredOrders = computed(() => {
  let result = [...orders.value]

  // 关键词搜索（扩展支持新字段）
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(order => {
      // 订单ID
      if (String(order.id).toLowerCase().includes(keyword)) return true

      // 订单编号（新订单）
      if (order.order_number && order.order_number.toLowerCase().includes(keyword)) return true

      // 客户名称
      if ((order.order_client || '').toLowerCase().includes(keyword)) return true

      // 联系人（新旧字段）
      if ((order.contact_person || '').toLowerCase().includes(keyword)) return true
      if ((order.receiver_name || '').toLowerCase().includes(keyword)) return true

      // 联系地址（新旧字段）
      if ((order.contact_address || '').toLowerCase().includes(keyword)) return true
      if ((order.receiver_address || '').toLowerCase().includes(keyword)) return true

      // 工程项目（新订单）
      if (order.project_name && order.project_name.toLowerCase().includes(keyword)) return true

      // 商品名称（旧字段）
      if ((order.goods_name || '').toLowerCase().includes(keyword)) return true

      // 商品明细（新字段）
      if (order.order_goods && order.order_goods.length > 0) {
        const hasMatch = order.order_goods.some(item =>
          (item.goods_name || '').toLowerCase().includes(keyword)
        )
        if (hasMatch) return true
      }

      // 物流单号（物流模式）
      if (props.mode === 'logistics' && (order.logistics_no || '').toLowerCase().includes(keyword)) {
        return true
      }

      return false
    })
  }

  // 分类筛选
  if (filters.value.category) {
    result = result.filter(order => {
      const orderCategory = getCategoryText(order)
      return orderCategory === filters.value.category
    })
  }

  // 状态筛选
  if (filters.value.status) {
    result = result.filter(order => {
      return order.status === filters.value.status
    })
  }

  // 发货方式筛选（仅物流模式）
  if (props.mode === 'logistics' && filters.value.shippingMethods.length > 0) {
    result = result.filter(order => {
      const method = getShippingMethodText(order)
      return filters.value.shippingMethods.includes(method)
    })
  }

  // 日期筛选
  if (filters.value.startDate || filters.value.endDate) {
    result = result.filter(order => {
      const orderDate = formatDate(order)
      if (filters.value.startDate && orderDate < filters.value.startDate) return false
      if (filters.value.endDate && orderDate > filters.value.endDate) return false
      return true
    })
  }

  // 日期排序
  result.sort((a, b) => {
    const dateA = props.mode === 'logistics'
      ? (a.shipped_date || a.completed_date || a.date || '')
      : (a.date || '')
    const dateB = props.mode === 'logistics'
      ? (b.shipped_date || b.completed_date || b.date || '')
      : (b.date || '')

    if (sortOrder.value === 'desc') {
      return dateB.localeCompare(dateA) // 最近到远
    } else {
      return dateA.localeCompare(dateB) // 最远到近
    }
  })

  return result
})

const totalOrders = computed(() => filteredOrders.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalOrders.value / pageSize.value)))

// 分页后的订单数据
const paginatedOrders = computed(() => {
  if (showAll.value) {
    return filteredOrders.value
  }
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredOrders.value.slice(start, end)
})

const pagedRecords = computed(() => paginatedOrders.value)

const pageStart = computed(() => filteredOrders.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredOrders.value.length))

const isAllSelected = computed(() => {
  const deletableOrders = paginatedOrders.value.filter(canDeleteOrder)
  return deletableOrders.length > 0 &&
    deletableOrders.every(order => selectedOrders.value.includes(order.id))
})

const isPagePartiallySelected = computed(() => {
  const deletableOrders = paginatedOrders.value.filter(canDeleteOrder)
  const selectedCount = deletableOrders.filter(order =>
    selectedOrders.value.includes(order.id)
  ).length
  return selectedCount > 0 && selectedCount < deletableOrders.length
})

// 计算当前页运费总额
const currentPageFreightTotal = computed(() => {
  return paginatedOrders.value.reduce((sum, order) => {
    return sum + getFreightTotal(order)
  }, 0)
})

// 方法
const isSelected = (orderId) => {
  return selectedOrders.value.includes(orderId)
}

// ========== 新旧字段兼容辅助函数 ==========

// 获取联系人
const getContactPerson = (order) => {
  return order.contact_person || order.receiver_name || '-'
}

// 获取联系电话
const getContactPhone = (order) => {
  return order.contact_phone || order.receiver_phone || '-'
}

// 获取联系地址
const getContactAddress = (order) => {
  return order.contact_address || order.receiver_address || '-'
}

// 获取商品信息显示
const getGoodsDisplay = (order) => {
  // 1. 如果有 order_goods 数组（新订单）
  if (order.order_goods && order.order_goods.length > 0) {
    const first = order.order_goods[0]
    const count = order.order_goods.length
    if (count > 1) {
      return `${first.goods_name} 等${count}件商品`
    }
    return `${first.goods_name} ${first.spec || ''}`
  }
  // 2. 回退到旧字段
  return order.goods_name || '-'
}

// 获取商品信息悬停提示
const getGoodsTooltip = (order) => {
  if (!order.order_goods || order.order_goods.length === 0) {
    return order.goods_name || '-'
  }
  return order.order_goods.map(item =>
    `${item.goods_name} ${item.spec || ''} x${item.quantity}`
  ).join('\n')
}

// 获取总重量
const getTotalWeight = (order) => {
  // 1. 如果有 order_goods 数组
  if (order.order_goods && order.order_goods.length > 0) {
    const total = order.order_goods.reduce((sum, item) => sum + (item.quantity || 0), 0)
    const unit = order.order_goods[0]?.unit || 'kg'
    return `${total}${unit}`
  }
  // 2. 回退到旧字段
  return order.goods_weight || '-'
}

// 获取件数
const getPackageCount = (order) => {
  // 1. 如果有 order_goods 数组
  if (order.order_goods && order.order_goods.length > 0) {
    const total = order.order_goods.reduce((sum, item) => sum + (item.packages || 0), 0)
    return `${total}件`
  }
  // 2. 回退到旧字段
  return order.goods_quantity || '-'
}

// 获取应收金额
const getShouldReceive = (order) => {
  if (order.should_receive !== undefined && order.should_receive !== null) {
    return `¥${order.should_receive.toFixed(2)}`
  }
  if (order.total_amount !== undefined && order.total_amount !== null) {
    return `¥${order.total_amount.toFixed(2)}`
  }
  return '-'
}

// 获取已收金额
const getCurrentPayment = (order) => {
  if (order.current_payment !== undefined && order.current_payment !== null) {
    return `¥${order.current_payment.toFixed(2)}`
  }
  return '-'
}

// 获取未收金额
const getCurrentDebt = (order) => {
  if (order.current_debt !== undefined && order.current_debt !== null) {
    return `¥${order.current_debt.toFixed(2)}`
  }
  // 如果没有 current_debt，尝试计算
  if (order.should_receive !== undefined && order.current_payment !== undefined) {
    const debt = order.should_receive - order.current_payment
    return `¥${debt.toFixed(2)}`
  }
  return '-'
}

// 判断是否为新订单（有商品明细）
const isNewOrder = (order) => {
  return Array.isArray(order?.order_goods) && order.order_goods.length > 0
}

// 新销售订单同时具备规范订单编号和商品明细，旧兼容数据不进入审核流程。
const isSalesOrder = (order) => {
  return Boolean(String(order?.order_number || '').trim()) && isNewOrder(order)
}

const isOrderAudited = (order) => Number(order?.audit_state) === 1
const isSalesOrderLocked = (order) => isSalesOrder(order) && isOrderAudited(order)
const canDeleteOrder = (order) => !isSalesOrderLocked(order)

// 根据 product_id 查找商品名称
const getProductNameById = (productId) => {
  if (!productId) return '-'
  const product = products.value.find(p => p.id === productId)
  return product ? product.name : `商品#${productId}`
}

// 获取商品明细的商品名称（兼容空 goods_name）
const getGoodsItemName = (item) => {
  // 1. 优先使用 goods_name
  if (item.goods_name && item.goods_name.trim()) {
    return item.goods_name
  }
  // 2. 回退到通过 product_id 查找
  if (item.product_id) {
    return getProductNameById(item.product_id)
  }
  // 3. 都没有，返回默认值
  return '-'
}

// 计算合计件数
const calculateTotalPackages = (order) => {
  if (!order || !Array.isArray(order.order_goods)) return 0
  return order.order_goods.reduce((total, item) => {
    return total + (Number(item.packages) || 0)
  }, 0)
}

// 计算合计数量
const calculateTotalQuantity = (order) => {
  if (!order || !Array.isArray(order.order_goods)) return '0'
  const total = order.order_goods.reduce((sum, item) => {
    return sum + (Number(item.quantity) || 0)
  }, 0)
  return Number.isInteger(total) ? total.toString() : total.toFixed(2)
}

// 计算小计（不含税）
const calculateSubtotal = (order) => {
  if (!order || !Array.isArray(order.order_goods)) return '0.00'
  const subtotal = order.order_goods.reduce((sum, item) => {
    return sum + (Number(item.amount) || 0)
  }, 0)
  return subtotal.toFixed(2)
}

// 计算含税总额
const calculateTotalAmount = (order) => {
  if (!order || !Array.isArray(order.order_goods)) return '0.00'
  const total = order.order_goods.reduce((sum, item) => {
    return sum + (Number(item.total_amount) || 0)
  }, 0)
  return total.toFixed(2)
}

const getItemTaxAmount = (item) => {
  const totalAmount = Number(item?.total_amount) || 0
  if (totalAmount === 0) return 0

  return totalAmount - (Number(item?.amount) || 0)
}

const calculateItemTaxAmount = (item) => getItemTaxAmount(item).toFixed(2)

const formatItemTaxRate = (item) => {
  const taxRate = Number(item?.tax_rate) || 0
  return `${Number.isInteger(taxRate) ? taxRate : taxRate.toFixed(2)}%`
}

// 计算税额
const calculateTaxAmount = (order) => {
  if (!order || !Array.isArray(order.order_goods)) return '0.00'
  const tax = order.order_goods.reduce((sum, item) => {
    return sum + getItemTaxAmount(item)
  }, 0)
  return tax.toFixed(2)
}

// 商品明细弹窗状态
const orderDetailVisible = ref(false)
const currentDetailOrder = ref(null)

// 打开订单详情弹窗
const openOrderDetail = (order) => {
  selectedOrder.value = order
  detailModalOpen.value = true
}

// 关闭详情弹窗
const closeDetailModal = () => {
  detailModalOpen.value = false
  selectedOrder.value = null
  orderActionLoading.value = ''
}

// 显示商品明细弹窗
const showOrderDetail = (order) => {
  console.log('打开订单明细弹窗', order)
  console.log('订单编号:', order.order_number)
  console.log('商品明细:', order.order_goods)
  currentDetailOrder.value = order
  orderDetailVisible.value = true
  console.log('弹窗状态:', orderDetailVisible.value)
}

// 关闭商品明细弹窗
const closeOrderDetail = () => {
  console.log('关闭订单明细弹窗')
  orderDetailVisible.value = false
  currentDetailOrder.value = null
}

// ========== 原有方法 ==========

const toggleSelect = (orderId) => {
  const order = orders.value.find(item => item.id === orderId)
  if (isSalesOrderLocked(order)) {
    window.alert('已过账单据不可删除，请先反审核')
    return
  }

  const index = selectedOrders.value.indexOf(orderId)
  if (index > -1) {
    selectedOrders.value.splice(index, 1)
  } else {
    selectedOrders.value.push(orderId)
  }
}

const toggleSelectAll = () => {
  const currentPageIds = paginatedOrders.value
    .filter(canDeleteOrder)
    .map(order => order.id)

  if (isAllSelected.value) {
    selectedOrders.value = selectedOrders.value.filter(
      orderId => !currentPageIds.includes(orderId)
    )
  } else {
    selectedOrders.value = [
      ...new Set([...selectedOrders.value, ...currentPageIds])
    ]
  }
}

const getCategoryColor = (category) => {
  const colors = {
    '绝缘订单': '#e3f2fd',
    '中固订单': '#fff3e0'
  }
  return colors[category] || '#f5f5f5'
}

const getShippingColor = (method) => {
  const colors = {
    '快递': '#e8f5e9',
    '物流': '#e3f2fd',
    '零担快运': '#e3f2fd',
    '专车': '#f3e5f5',
    '其它': '#f5f5f5'
  }
  return colors[method] || '#f5f5f5'
}

const handleFilter = () => {
  console.log('筛选订单', filters.value)
}

const handleReset = () => {
  filters.value = {
    keyword: '',
    category: '',
    status: '', // 重置状态筛选
    shippingMethods: [], // 改为数组
    startDate: '',
    endDate: ''
  }
}

// 获取各状态的订单数量（基于当前所有筛选后的订单）
const getStatusCount = (status) => {
  if (!status) {
    // 全部：返回应用了除状态外所有筛选条件的订单数
    return filteredOrders.value.length
  }

  // 特定状态：在当前筛选结果基础上再按状态过滤
  return filteredOrders.value.filter(order => order.status === status).length
}

const handleAdd = () => {
  openOrderTask({ name: 'admin-orders-create' })
}

const handleEdit = (order) => {
  // 物流模式：沿用原有物流修改功能
  orderStore.allOrders = orders.value
  closeDetailModal()
  window.dispatchEvent(new CustomEvent('open-shipped-action-modal', {
    detail: { orderId: order.id, mode: 'edit' }
  }))
}

// 编辑订单（跳转到编辑页面）
const handleEditOrder = (order) => {
  closeDetailModal()
  openOrderTask({ name: 'admin-orders-edit', params: { id: order.id } })
}

// 复制新格式销售订单：进入新增页并由表单重新生成订单编号
const handleCopySalesOrder = (order) => {
  openOrderTask(
    {
      name: 'admin-orders-create',
      query: { copyFrom: String(order.id) }
    }
  )
}

const openOrderTask = (location) => {
  // 新增和修改只保留一个任务，后打开的页面替换原草稿。
  orderDraftStore.clearDraft()
  router.push(location)
}

// 计算运费总额
const getFreightTotal = (order) => {
  if (!order.freight_costs || !Array.isArray(order.freight_costs)) {
    return 0
  }
  return order.freight_costs.reduce((sum, item) => {
    return sum + (Number(item.amount) || 0)
  }, 0)
}

// 显示运费明细
const freightDetailVisible = ref(false)
const freightDetailData = ref(null)

const showFreightDetail = (order) => {
  if (!order.freight_costs || order.freight_costs.length === 0) {
    return
  }
  freightDetailData.value = {
    orderId: order.id,
    orderClient: order.order_client,
    costs: order.freight_costs,
    total: getFreightTotal(order)
  }
  freightDetailVisible.value = true
}

const closeFreightDetail = () => {
  freightDetailVisible.value = false
  freightDetailData.value = null
}

// 判断订单是否已录入物流单号
const hasLogistics = (order) => {
  const logistics = order.logistics_no || ''
  return logistics &&
         logistics !== '暂未录入单号' &&
         logistics !== '无单号记录' &&
         logistics !== '暂无记录'
}

// 复制物流极简信息
const handleCopyOrderInfo = async (order) => {
  try {
    const textToCopy = formatOrderForCopy(order, false, {
      storeName: getStoreName(order)
    })

    // 优先使用 Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(textToCopy)
      showCopyMessage('复制成功')
    } else {
      // 降级方案：使用传统的 execCommand 方法
      const textarea = document.createElement('textarea')
      textarea.value = textToCopy
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      textarea.style.top = '0'
      textarea.style.left = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()

      try {
        const successful = document.execCommand('copy')
        if (successful) {
          showCopyMessage('复制成功')
        } else {
          throw new Error('execCommand failed')
        }
      } catch (err) {
        console.error('复制失败:', err)
        alert('复制失败，请手动复制')
      } finally {
        document.body.removeChild(textarea)
      }
    }
  } catch (error) {
    console.error('复制失败:', error)
    alert('复制失败，请手动复制')
  }
}

const handleUploadReceipt = (order) => {
  console.log('上传回单', order)
}

const handleReceiptClick = (order) => {
  // 只有已上传回单才能查看
  if (!hasReceipt(order)) {
    return
  }

  // 更新 orderStore 数据，确保弹窗可以获取到订单信息
  orderStore.allOrders = orders.value

  // 已上传回单 - 查看回单
  window.triggerShippedActionModal(order.id, 'view_receipt')
}

const handleShippingClick = (order) => {
  // 更新 orderStore 数据
  orderStore.allOrders = orders.value
  closeDetailModal()

  // 物流录入与订单审核相互独立
  window.triggerShippedActionModal(order.id, 'entry')
}

const handleLogisticsAction = (order) => {
  if (hasLogistics(order)) {
    handleEdit(order)
    return
  }
  handleShippingClick(order)
}

const canAuditOrder = (order) => {
  return isSalesOrder(order) &&
    order?.status === 'shipped' &&
    !isOrderAudited(order)
}

const canReverseAuditOrder = (order) => {
  return isSalesOrder(order) &&
    order?.status === 'shipped' &&
    isOrderAudited(order)
}

const updateOrderAuditState = async (order, audited) => {
  if (!isSalesOrder(order) || order.status !== 'shipped') return

  const actionLabel = audited ? '审核' : '反审核'
  const nextStatusLabel = audited ? '已过帐' : getStatusText({ ...order, audit_state: 0 })
  if (!window.confirm(`确定要${actionLabel}订单 ${order.order_number || order.id} 吗？`)) {
    return
  }

  orderActionLoading.value = audited ? 'audit' : 'reverse-audit'
  try {
    await request({
      url: `/orders/${order.id}`,
      method: 'PUT',
      data: {
        audit_state: audited ? 1 : 0
      }
    })

    await fetchOrdersData()
    selectedOrder.value = orders.value.find(item => item.id === order.id) || {
      ...order,
      audit_state: audited ? 1 : 0
    }
    if (audited) {
      selectedOrders.value = selectedOrders.value.filter(id => id !== order.id)
    }
    window.alert(`${actionLabel}成功，订单状态已更新为${nextStatusLabel}`)
  } catch (error) {
    console.error(`${actionLabel}订单失败:`, error)
    window.alert(error?.response?.data?.message || `${actionLabel}失败，请稍后重试`)
  } finally {
    orderActionLoading.value = ''
  }
}

const handleAuditOrder = (order) => updateOrderAuditState(order, true)
const handleReverseAuditOrder = (order) => updateOrderAuditState(order, false)

// 点击发货方式标签 - 回单随时可上传或管理
const handleShippingTagClick = (order) => {
  orderStore.allOrders = orders.value
  closeDetailModal()
  window.triggerShippedActionModal(order.id, 'receipt')
}

const handleLogisticsClick = (order) => {
  orderStore.allOrders = orders.value
  closeDetailModal()
  window.triggerShippedActionModal(order.id, 'receipt')
}

// 复制单号
const copyLogisticsNo = async (order) => {
  if (!order.logistics_no) return

  try {
    await navigator.clipboard.writeText(order.logistics_no)
    showCopyMessage('复制成功')
  } catch (err) {
    // 如果 clipboard API 不可用，使用备用方法
    const textarea = document.createElement('textarea')
    textarea.value = order.logistics_no
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      showCopyMessage('复制成功')
    } catch (e) {
      showCopyMessage('复制失败', 'error')
    }
    document.body.removeChild(textarea)
  }
}

// 显示复制消息
const showCopyMessage = (text, type = 'success') => {
  const message = document.createElement('div')
  message.className = `copy-message copy-message-${type}`
  message.innerHTML = `
    <span class="copy-message-icon">${type === 'success' ? '✓' : '✕'}</span>
    <span>${text}</span>
  `
  message.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 12px 24px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
    z-index: 100002;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    background: ${type === 'success' ? '#f0f9ff' : '#fef2f2'};
    color: ${type === 'success' ? '#0369a1' : '#dc2626'};
    border: 1px solid ${type === 'success' ? '#bae6fd' : '#fecaca'};
    animation: slideDown 0.3s ease;
  `

  document.body.appendChild(message)

  setTimeout(() => {
    message.style.opacity = '0'
    message.style.transform = 'translateX(-50%) translateY(-20px)'
    message.style.transition = 'all 0.3s ease'
    setTimeout(() => {
      document.body.removeChild(message)
    }, 300)
  }, 2000)
}

// 切换排序
const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

// 获取订单状态文本
const getStatusText = (order) => {
  if (isNewOrder(order) && isOrderAudited(order)) {
    return '已过帐'
  } else if (order.status === 'shipped') {
    return '已发货'
  } else if (order.status === 'completed') {
    return '已完成'
  } else {
    return '未完成'
  }
}

// 获取订单状态样式类
const getStatusClass = (order) => {
  if (isNewOrder(order) && isOrderAudited(order)) {
    return 'status-posted'
  } else if (order.status === 'shipped') {
    return 'status-shipped'
  } else if (order.status === 'completed') {
    return 'status-completed'
  } else {
    return 'status-pending'
  }
}

// 点击外部关闭下拉框
const handleClickOutside = (event) => {
  const target = event.target
  if (!target.closest('.shipping-method-filter')) {
    shippingDropdownOpen.value = false
  }
}

// 处理出库发货
const handleShipOrder = (order) => {
  // 更新 orderStore 数据
  orderStore.allOrders = orders.value

  // 使用注入的方法或者 emit
  if (handleShipFromParent) {
    handleShipFromParent(order.id)
  } else {
    emit('ship', order.id)
  }
}

const handleViewReceipt = (order) => {
  if (hasReceipt(order)) {
    console.log('查看回单', order)
  }
}

const handleDelete = async (order) => {
  if (isSalesOrderLocked(order)) {
    window.alert('已过账单据不可删除，请先反审核')
    return
  }

  // 判断是否为新订单
  const isNew = isNewOrder(order)

  // 显示提示信息
  let confirmMsg = `确定要删除订单 ${order.id} 吗？`
  if (isNew) {
    confirmMsg = `确定要删除订单 ${order.order_number || order.id} 吗？\n\n此订单包含 ${order.order_goods.length} 种商品，删除后将恢复库存。`
  }

  if (confirm(confirmMsg)) {
    try {
      await request({
        url: `/orders/${order.id}`,
        method: 'DELETE'
      })
      alert('删除成功' + (isNew ? '，库存已恢复' : ''))
      closeDetailModal()
      selectedOrders.value = selectedOrders.value.filter(id => id !== order.id)
      await fetchOrdersData()
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败：' + (error?.response?.data?.message || error.message || '未知错误'))
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedOrders.value.length === 0) {
    alert('请先选择要删除的订单')
    return
  }

  // 统计新旧订单数量
  const selectedOrdersData = orders.value.filter(o => selectedOrders.value.includes(o.id))
  const lockedOrders = selectedOrdersData.filter(isSalesOrderLocked)
  if (lockedOrders.length > 0) {
    alert(`选中的订单中有 ${lockedOrders.length} 个已过账单据，请先反审核`)
    return
  }

  const newOrdersCount = selectedOrdersData.filter(o => o.order_goods && o.order_goods.length > 0).length
  const oldOrdersCount = selectedOrders.value.length - newOrdersCount

  // 构建提示信息
  let confirmMsg = `确定要删除选中的 ${selectedOrders.value.length} 个订单吗？\n\n`
  if (newOrdersCount > 0) {
    confirmMsg += `其中包含 ${newOrdersCount} 个销售单（将恢复库存）\n`
  }
  if (oldOrdersCount > 0) {
    confirmMsg += `其中包含 ${oldOrdersCount} 个普通订单`
  }

  if (confirm(confirmMsg)) {
    try {
      console.log('开始批量删除订单:', selectedOrders.value)

      const results = await Promise.allSettled(
        selectedOrders.value.map(id =>
          request({ url: `/orders/${id}`, method: 'DELETE' })
        )
      )

      const failed = results.filter(r => r.status === 'rejected')

      if (failed.length > 0) {
        console.error('部分删除失败:', failed)
        alert(`删除完成，但有 ${failed.length} 个订单删除失败`)
      } else {
        alert('删除成功' + (newOrdersCount > 0 ? '，库存已恢复' : ''))
      }

      selectedOrders.value = []
      await fetchOrdersData()
    } catch (error) {
      console.error('批量删除失败:', error)
      alert('批量删除失败: ' + (error.message || '未知错误'))
    }
  }
}

const handleExport = () => {
  console.log('导出数据')
}

const showExpandModal = (content, title) => {
  expandModal.value = {
    visible: true,
    title: title,
    content: content
  }
}

const closeExpandModal = () => {
  expandModal.value.visible = false
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const changePageSize = (size) => {
  if (size === 'all') {
    showAll.value = true
    pageSize.value = totalOrders.value || 9999 // 设置一个足够大的数字
  } else {
    showAll.value = false
    pageSize.value = size
  }
  currentPage.value = 1 // 切换每页显示数量时重置到第一页
}
</script>

<style scoped>
.unified-order-list-page {
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

/* 搜索面板 */
.search-panel {
  padding: 18px 20px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(280px, 1.45fr) minmax(160px, 1fr) auto;
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
.field-group select {
  width: 100%;
  height: 38px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  padding: 0 11px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
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

/* 多选下拉框样式 */
.multi-select-wrapper {
  position: relative;
}

.multi-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.multi-select-trigger:hover {
  border-color: var(--accent);
}

.multi-select-trigger .selected-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.multi-select-trigger .dropdown-icon {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  transition: transform 0.2s ease;
}

.multi-select-trigger .dropdown-icon.open {
  transform: rotate(180deg);
}

.multi-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 100;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.dropdown-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dropdown-option:hover {
  background: var(--accent-soft);
}

.dropdown-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
}

.dropdown-option span {
  flex: 1;
  font-size: 14px;
  color: var(--text);
}

.search-actions {
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

.button:disabled {
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

/* 导出按钮 */
.button-export {
  color: #374151;
  background: #fff;
  border-color: #d1d5db;
}

.button-export:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

/* 批量删除按钮 */
.button-delete {
  color: #9ca3af;
  background: #f9fafb;
  border-color: #e5e7eb;
  cursor: not-allowed;
  transition: all 0.2s ease;
}

.button-delete.has-selection {
  color: #fff;
  background: #ef4444;
  border-color: #dc2626;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(239, 68, 68, 0.25);
}

.button-delete.has-selection:hover:not(:disabled) {
  background: #dc2626;
  border-color: #b91c1c;
  box-shadow: 0 3px 8px rgba(239, 68, 68, 0.35);
}

/* 记录面板 */
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

.material-type-slider {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.status-filter-slider {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
  margin-left: 16px;
}

.slider-tab {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 16px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  position: relative;
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
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.slider-tab.active .count-badge {
  background: rgba(255, 255, 255, 0.25);
}

.selection-count {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  margin-left: auto;
}

.selection-count strong {
  color: var(--accent-dark);
  font-size: 15px;
  font-weight: 700;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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

/* 表格 */
.table-scroll {
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
  vertical-align: middle;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.records-table tbody tr:last-child td {
  border-bottom: 0;
}

.record-row {
  cursor: pointer;
  transition: background 0.15s ease;
  background: var(--store-bg-color, #fff);
}

.record-row:hover {
  background: rgba(var(--accent-rgb), 0.18) !important;
}

.record-row.selected {
  background: rgba(var(--accent-rgb), 0.12) !important;
}

/* 增大复选框尺寸并对齐 */
.col-checkbox {
  width: 50px !important;
  text-align: center !important;
  vertical-align: middle !important;
  padding: 0 16px !important;
  line-height: 1 !important;
}

.records-table th.col-checkbox {
  padding: 0 16px !important;
  vertical-align: middle !important;
  line-height: 45px !important;
}

.records-table td.col-checkbox {
  padding: 0 16px !important;
  vertical-align: middle !important;
  line-height: 57px !important;
}

.records-table input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent);
  margin: 0;
  padding: 0;
  vertical-align: middle;
  position: relative;
  top: 0;
}

.records-table thead th.col-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  padding: 0;
  vertical-align: middle;
  position: relative;
  top: 0;
}

.records-table tbody td.col-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  padding: 0;
  vertical-align: middle;
  position: relative;
  top: 0;
}
.document-column { width: 140px; }
.records-table th:nth-child(3) { width: 110px; }
.records-table th:nth-child(4) { width: 140px; }
.records-table th:nth-child(5) { width: 100px; }
.records-table th:nth-child(6) { width: 120px; }
.address-column { width: 140px; }
.material-column { width: 150px; }
.number-column { width: 100px; text-align: right !important; }
.money-column { width: 120px; text-align: right !important; }
.operation-column { width: 100px; text-align: center; }

.numeric,
.money-value {
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

.date-cell,
.party-cell {
  color: var(--text-secondary);
}

.address-cell,
.remark-cell {
  color: var(--text-secondary);
  font-size: 13px;
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
  color: #1d4ed8;
  background: #dbeafe;
  border: 1px solid #93c5fd;
}

.status-shipped {
  color: #13734f;
  background: #eaf8f1;
  border: 1px solid #a7e2c9;
}

.status-reviewed,
.status-completed {
  color: #16647a;
  background: #e7f5f8;
}

.status-pending,
.status-out {
  color: #a4510b;
  background: #fff3df;
}

.status-cancelled {
  color: #b4232f;
  background: #f1f2f4;
}

.shipping-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  background: #f3f4f6;
  color: #6b7280;
}

.shipping-tag.clickable.can-edit {
  background: #e6f4ff;
  color: #1677ff;
  cursor: pointer;
}

.shipping-tag.clickable.can-edit:hover {
  background: #bae0ff;
}

.tracking-cell {
  text-align: center;
  font-size: 12px;
}

.tracking-number {
  color: #374151;
  cursor: pointer;
  transition: color 0.2s;
}

.tracking-number:hover {
  color: #2563eb;
}

.receipt-status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.has-receipt {
  color: #10b981;
  background: #d1fae5;
  cursor: pointer;
}

.has-receipt:hover {
  background: #a7f3d0;
}

.freight-amount {
  color: #1890ff;
  font-weight: 650;
  cursor: pointer;
}

.freight-amount:hover {
  text-decoration: underline;
}

.row-actions {
  display: flex;
  justify-content: center;
  gap: 6px;
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

/* 页脚 */
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
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 12px;
  outline: none;
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

/* 订单详情居中弹窗 */
.detail-modal-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --border-strong: #cbd5e1;
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 2147482000;
}

.detail-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.detail-modal {
  position: relative;
  display: flex;
  width: min(960px, calc(100vw - 48px));
  max-height: min(880px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  color: #172033;
  background: #f4f7f9;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
  outline: none;
}

.detail-modal-header {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #dfe5ec;
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
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 7px;
}

.detail-modal-mark svg {
  width: 21px;
  height: 21px;
}

.detail-modal-title-wrap > div {
  min-width: 0;
}

.detail-modal-title-wrap span:not(.detail-modal-mark) {
  color: #758195;
  font-size: 11px;
  font-weight: 600;
}

.detail-modal-title-wrap h2 {
  margin: 3px 0 0;
  overflow: hidden;
  color: #172033;
  font-size: 18px;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-modal-close {
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

.detail-modal-close:hover {
  color: #273245;
  background: #f0f3f6;
}

.detail-modal-close svg {
  width: 20px;
  height: 20px;
}

.detail-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
}

.detail-modal-overview,
.detail-section {
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.detail-modal-overview {
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

.financial-summary-strip .received-amount strong {
  color: #07805f;
}

.financial-summary-strip .outstanding-amount strong {
  color: #dc3545;
}

.financial-summary-strip {
  margin: 15px;
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

.detail-table-scroll {
  overflow-x: auto;
  padding-right: 12px;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.detail-table th {
  height: 39px;
  padding: 0 8px;
  color: #647086;
  background: #f8fafb;
  border-bottom: 1px solid #e5eaf0;
  font-size: 11px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.detail-table td {
  height: 50px;
  padding: 6px 8px;
  color: #3c485b;
  border-bottom: 1px solid #edf1f5;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-table tr:last-child td {
  border-bottom: 0;
}

.detail-table th:nth-child(1) { width: 45px; text-align: center; }
.detail-table .material-detail-column { width: auto; min-width: 120px; }
.detail-table th:nth-child(3) { width: 90px; }
.detail-table th:nth-child(4) { width: 50px; text-align: center; }
.detail-table th:nth-child(5) { width: 55px; }
.detail-table th:nth-child(6) { width: 65px; }
.detail-table th:nth-child(7) { width: 75px; }
.detail-table th:nth-child(8) { width: 85px; }
.detail-table th:nth-child(9) { width: 95px; }

.order-goods-table {
  min-width: 880px;
}

.order-goods-table th:nth-child(1) { width: 45px; text-align: center; }
.order-goods-table .material-detail-column { width: auto; min-width: 130px; }
.order-goods-table th:nth-child(3) { width: 90px; }
.order-goods-table th:nth-child(4) { width: 50px; text-align: center; }
.order-goods-table th:nth-child(5) { width: 55px; }
.order-goods-table th:nth-child(6) { width: 65px; }
.order-goods-table th:nth-child(7) { width: 75px; }
.order-goods-table th:nth-child(8) { width: 88px; }
.order-goods-table th:nth-child(9) { width: 62px; }
.order-goods-table th:nth-child(10) { width: 85px; }
.order-goods-table th:nth-child(11) { width: 95px; }

.order-goods-table th:last-child,
.order-goods-table td:last-child {
  padding-right: 14px;
}

.detail-table td:first-child {
  text-align: center;
}

.detail-table td strong {
  display: block;
  overflow: hidden;
  color: #283548;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-table tfoot {
  background: #f8fafb;
  font-weight: 600;
}

.detail-total-row td {
  color: #111827;
  border-top: 2px solid #e5eaf0;
  border-bottom: none;
  font-weight: 650;
}

.detail-total-label {
  text-align: right !important;
  color: #374151 !important;
}

.order-goods-table .detail-total-label {
  padding-left: 20px !important;
  text-align: left !important;
}

.item-amount {
  color: #263348 !important;
  font-weight: 700;
}

.detail-modal-empty {
  height: 150px !important;
  color: #8a96a8 !important;
  text-align: center;
}

.detail-modal-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  background: #fff;
  border-top: 1px solid #dfe5ec;
}

.detail-modal-left-actions,
.detail-modal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-modal-left-actions {
  justify-content: flex-start;
}

.detail-modal-actions {
  justify-content: flex-end;
  margin-left: auto;
}

.button-edit {
  color: #fff;
  background: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 2px 5px rgba(37, 99, 235, 0.2);
}

.button-edit:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.detail-modal-actions .button-primary {
  color: #fff;
  background: var(--accent, #0f9f78);
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 2px 5px rgba(15, 159, 120, 0.18);
}

.detail-modal-actions .button-primary:hover:not(:disabled) {
  background: var(--accent-dark, #08745a);
  border-color: var(--accent-dark, #08745a);
}

.button-audit {
  color: #fff;
  background: var(--accent, #0f9f78);
  border-color: var(--accent, #0f9f78);
  box-shadow: 0 2px 5px rgba(15, 159, 120, 0.18);
}

.button-audit:hover:not(:disabled) {
  background: var(--accent-dark, #08745a);
  border-color: var(--accent-dark, #08745a);
}

.button-reverse-audit {
  color: #b45309;
  background: #fffbeb;
  border-color: #f5cf83;
}

.button-reverse-audit:hover:not(:disabled) {
  color: #92400e;
  background: #fef3c7;
  border-color: #e7b95a;
}

.button-danger-light {
  color: #b4232f;
  background: #fff;
  border-color: #efb5ba;
}

.button-danger-light:hover:not(:disabled) {
  color: #fff;
  background: #dc3545;
  border-color: #c92f3e;
}

.detail-modal-enter-active,
.detail-modal-leave-active {
  transition: opacity 0.2s ease;
}

.detail-modal-enter-active .detail-modal,
.detail-modal-leave-active .detail-modal {
  transition: transform 0.22s ease, opacity 0.2s ease;
}

.detail-modal-enter-from,
.detail-modal-leave-to {
  opacity: 0;
}

.detail-modal-enter-from .detail-modal,
.detail-modal-leave-to .detail-modal {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}

/* 运费明细弹窗 */
.expand-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

.freight-detail-modal {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 500px;
  max-width: 90vw;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.freight-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.freight-modal-header h3 {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.freight-modal-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.freight-info {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-weight: bold;
  color: #666;
  min-width: 100px;
}

.info-row .value {
  color: #333;
}

.freight-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.freight-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 4px solid #1890ff;
}

.item-note {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.item-amount {
  font-size: 16px;
  color: #1890ff;
  font-weight: bold;
}

.freight-total {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 2px solid #e5e7eb;
}

.total-label {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.total-amount {
  font-size: 20px;
  font-weight: bold;
  color: #1890ff;
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .search-grid {
    grid-template-columns: 1fr;
  }

  .detail-modal-layer {
    padding: 0;
  }

  .detail-modal {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
  }

  .detail-modal-footer {
    align-items: center;
    flex-wrap: wrap;
  }

  .detail-modal-left-actions,
  .detail-modal-actions {
    width: auto;
  }
}
</style>
