<template>
  <div class="return-order-list-page">
    <!-- 筛选工具栏 -->
    <section class="search-panel" aria-label="退货单筛选">
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
              placeholder="搜索退货单号、客户、原订单号..."
            />
          </span>
        </label>

        <div class="field-group date-field">
          <span>退货日期</span>
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

        <div class="field-group">
          <span>处理状态</span>
          <select v-model="filters.status">
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="processing">处理中</option>
            <option value="completed">已完成</option>
            <option value="rejected">已拒绝</option>
          </select>
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

    <!-- 退货记录面板 -->
    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <!-- 状态筛选滑块 -->
          <div class="status-filter-slider" role="tablist" aria-label="处理状态筛选">
            <button
              :class="['slider-tab', { active: filters.status === '' }]"
              type="button"
              @click="filters.status = ''"
            >
              全部
              <span class="count-badge">{{ getStatusCount('') }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.status === 'pending' }]"
              type="button"
              @click="filters.status = 'pending'"
            >
              待处理
              <span class="count-badge">{{ getStatusCount('pending') }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.status === 'processing' }]"
              type="button"
              @click="filters.status = 'processing'"
            >
              处理中
              <span class="count-badge">{{ getStatusCount('processing') }}</span>
            </button>
            <button
              :class="['slider-tab', { active: filters.status === 'completed' }]"
              type="button"
              @click="filters.status = 'completed'"
            >
              已完成
              <span class="count-badge">{{ getStatusCount('completed') }}</span>
            </button>
          </div>

          <!-- 选中提示 -->
          <div v-if="selectedReturns.length > 0" class="selection-count">
            已选中 <strong>{{ selectedReturns.length }}</strong> 项
          </div>
        </div>

        <div class="toolbar-actions">
          <button
            class="icon-button refresh-button"
            type="button"
            title="刷新列表"
            :disabled="loading"
            @click="fetchData"
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
            class="button button-primary create-button"
            type="button"
            @click="openCreateModal"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            录入退货单
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
                  :indeterminate="isPartiallySelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="document-column">退货单号</th>
              <th class="document-column">原订单号</th>
              <th>退货日期</th>
              <th>客户名称</th>
              <th class="material-column">退货商品</th>
              <th class="number-column">退货数量</th>
              <th class="number-column">退货金额</th>
              <th class="reason-column">退货原因</th>
              <th>处理状态</th>
              <th class="remark-column">备注</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 12" :key="cell"><span></span></td>
              </tr>
            </template>
            <tr v-else-if="filteredReturns.length === 0">
              <td colspan="12" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M4 6h16v14H4z"></path>
                    <path d="M8 3h8v3H8z"></path>
                    <path d="M8 11h8M8 15h5"></path>
                  </svg>
                </div>
                <strong>暂无退货数据</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>
            <tr
              v-for="item in paginatedReturns"
              v-else
              :key="item.id"
              class="record-row"
              :class="{ selected: isSelected(item.id) }"
              tabindex="0"
              @click="openDetailModal(item)"
              @keydown.enter.self.prevent="openDetailModal(item)"
            >
              <td class="col-checkbox" @click.stop>
                <input
                  type="checkbox"
                  :checked="isSelected(item.id)"
                  @change="toggleSelect(item.id)"
                />
              </td>
              <td>
                <button class="document-link" type="button" @click.stop="openDetailModal(item)">
                  {{ item.return_number }}
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="m9 18 6-6-6-6"></path>
                  </svg>
                </button>
              </td>
              <td class="date-cell">{{ item.original_order_number }}</td>
              <td class="date-cell">{{ item.return_date }}</td>
              <td>{{ item.customer_name }}</td>
              <td class="material-cell" :title="item.goods_name">
                <strong>{{ item.goods_name.substring(0, 12) }}</strong>
                <span v-if="item.goods_name.length > 12">...</span>
              </td>
              <td class="number-column numeric">{{ item.quantity }}</td>
              <td class="number-column numeric money-value">¥{{ item.amount.toFixed(2) }}</td>
              <td class="reason-cell" :title="item.reason">
                {{ item.reason.length > 10 ? item.reason.substring(0, 10) + '...' : item.reason }}
              </td>
              <td>
                <span :class="['status-tag', getStatusClass(item.status)]">
                  <i aria-hidden="true"></i>
                  {{ getStatusText(item.status) }}
                </span>
              </td>
              <td class="remark-cell">
                {{ item.remark && item.remark.length > 4 ? item.remark.substring(0, 4) + '...' : (item.remark || '-') }}
              </td>
              <td class="operation-column" @click.stop>
                <div class="row-actions">
                  <button
                    v-if="item.status === 'pending'"
                    type="button"
                    title="处理退货"
                    @click="handleProcess(item)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button
                    type="button"
                    title="查看详情"
                    @click="openDetailModal(item)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
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
          共 <strong>{{ filteredReturns.length }}</strong> 条记录
          <template v-if="filteredReturns.length">，当前 {{ pageStart }}-{{ pageEnd }} 条</template>
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

    <!-- 录入退货单弹窗 -->
    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="createModalOpen" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeCreateModal"></div>
          <section
            class="detail-modal create-modal"
            role="dialog"
            aria-modal="true"
            aria-label="录入退货单"
            tabindex="-1"
            @keydown.esc="closeCreateModal"
          >
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                </span>
                <div>
                  <span>退货管理</span>
                  <h2>录入退货单</h2>
                </div>
              </div>
              <button class="detail-modal-close" type="button" title="关闭" @click="closeCreateModal">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <form class="return-form" @submit.prevent="handleSubmit">
                <div class="form-section">
                  <h3>基本信息</h3>
                  <div class="form-grid">
                    <label class="form-field">
                      <span class="field-label">原订单号 <em>*</em></span>
                      <input
                        v-model="formData.original_order_number"
                        type="text"
                        placeholder="请输入原订单号"
                        required
                      />
                    </label>

                    <label class="form-field">
                      <span class="field-label">退货日期 <em>*</em></span>
                      <input
                        v-model="formData.return_date"
                        type="date"
                        required
                      />
                    </label>

                    <label class="form-field">
                      <span class="field-label">客户名称 <em>*</em></span>
                      <input
                        v-model="formData.customer_name"
                        type="text"
                        placeholder="请输入客户名称"
                        required
                      />
                    </label>

                    <label class="form-field">
                      <span class="field-label">联系电话</span>
                      <input
                        v-model="formData.contact_phone"
                        type="tel"
                        placeholder="请输入联系电话"
                      />
                    </label>
                  </div>
                </div>

                <div class="form-section">
                  <h3>退货商品信息</h3>
                  <div class="form-grid">
                    <label class="form-field full-width">
                      <span class="field-label">商品名称 <em>*</em></span>
                      <input
                        v-model="formData.goods_name"
                        type="text"
                        placeholder="请输入商品名称"
                        required
                      />
                    </label>

                    <label class="form-field">
                      <span class="field-label">退货数量 <em>*</em></span>
                      <input
                        v-model.number="formData.quantity"
                        type="number"
                        min="1"
                        placeholder="请输入数量"
                        required
                      />
                    </label>

                    <label class="form-field">
                      <span class="field-label">退货金额 <em>*</em></span>
                      <input
                        v-model.number="formData.amount"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="请输入金额"
                        required
                      />
                    </label>
                  </div>
                </div>

                <div class="form-section">
                  <h3>退货原因及备注</h3>
                  <div class="form-grid">
                    <label class="form-field full-width">
                      <span class="field-label">退货原因 <em>*</em></span>
                      <select v-model="formData.reason" required>
                        <option value="">请选择退货原因</option>
                        <option value="质量问题">质量问题</option>
                        <option value="发错货">发错货</option>
                        <option value="规格不符">规格不符</option>
                        <option value="客户取消">客户取消</option>
                        <option value="其他原因">其他原因</option>
                      </select>
                    </label>

                    <label class="form-field full-width">
                      <span class="field-label">备注</span>
                      <textarea
                        v-model="formData.remark"
                        rows="3"
                        placeholder="请输入备注信息"
                      ></textarea>
                    </label>
                  </div>
                </div>
              </form>
            </div>

            <footer class="detail-modal-footer">
              <div class="detail-modal-left-actions"></div>
              <div class="detail-modal-actions">
                <button
                  class="button button-secondary"
                  type="button"
                  @click="closeCreateModal"
                >
                  取消
                </button>
                <button
                  class="button button-primary"
                  type="button"
                  :disabled="submitting"
                  @click="handleSubmit"
                >
                  {{ submitting ? '提交中...' : '提交' }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>

    <!-- 退货详情弹窗 -->
    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="detailModalOpen && selectedReturn" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeDetailModal"></div>
          <section
            class="detail-modal"
            role="dialog"
            aria-modal="true"
            aria-label="退货详情"
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
                  <span>退货详情</span>
                  <h2>{{ selectedReturn.return_number }}</h2>
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
                  <span :class="['status-tag', getStatusClass(selectedReturn.status)]">
                    <i aria-hidden="true"></i>
                    {{ getStatusText(selectedReturn.status) }}
                  </span>
                  <span>{{ selectedReturn.return_date }}</span>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>退货单号</dt>
                    <dd>{{ selectedReturn.return_number }}</dd>
                  </div>
                  <div>
                    <dt>原订单号</dt>
                    <dd>{{ selectedReturn.original_order_number }}</dd>
                  </div>
                  <div>
                    <dt>客户名称</dt>
                    <dd>{{ selectedReturn.customer_name }}</dd>
                  </div>
                  <div>
                    <dt>联系电话</dt>
                    <dd>{{ selectedReturn.contact_phone || '-' }}</dd>
                  </div>
                  <div>
                    <dt>退货日期</dt>
                    <dd>{{ selectedReturn.return_date }}</dd>
                  </div>
                  <div>
                    <dt>退货原因</dt>
                    <dd>{{ selectedReturn.reason }}</dd>
                  </div>
                </dl>
              </section>

              <!-- 退货商品信息 -->
              <section class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>退货商品信息</h3>
                  </div>
                </div>
                <div class="summary-strip">
                  <div>
                    <span>商品名称</span>
                    <strong>{{ selectedReturn.goods_name }}</strong>
                  </div>
                  <div>
                    <span>退货数量</span>
                    <strong>{{ selectedReturn.quantity }}</strong>
                  </div>
                  <div>
                    <span>退货金额</span>
                    <strong class="amount-text">¥{{ selectedReturn.amount.toFixed(2) }}</strong>
                  </div>
                </div>
              </section>

              <!-- 备注信息 -->
              <section v-if="selectedReturn.remark" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>备注信息</h3>
                  </div>
                </div>
                <div style="padding: 15px;">
                  <p style="margin: 0; color: #374151; line-height: 1.6;">{{ selectedReturn.remark }}</p>
                </div>
              </section>
            </div>

            <footer class="detail-modal-footer">
              <div class="detail-modal-left-actions"></div>
              <div class="detail-modal-actions">
                <button
                  v-if="selectedReturn.status === 'pending'"
                  class="button button-primary"
                  type="button"
                  @click="handleProcess(selectedReturn)"
                >
                  处理退货
                </button>
                <button
                  class="button button-secondary"
                  type="button"
                  @click="closeDetailModal"
                >
                  关闭
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// 筛选条件
const filters = ref({
  keyword: '',
  status: '',
  startDate: '',
  endDate: ''
})

// 数据状态
const loading = ref(false)
const selectedReturns = ref([])
const createModalOpen = ref(false)
const detailModalOpen = ref(false)
const selectedReturn = ref(null)
const submitting = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(30)

// 表单数据
const formData = ref({
  original_order_number: '',
  return_date: new Date().toISOString().split('T')[0],
  customer_name: '',
  contact_phone: '',
  goods_name: '',
  quantity: 1,
  amount: 0,
  reason: '',
  remark: ''
})

// 模拟退货数据
const returnOrders = ref([
  {
    id: 1,
    return_number: 'RT202609110001',
    original_order_number: 'ZG20260901001',
    return_date: '2026-09-11',
    customer_name: '北京建设工程有限公司',
    contact_phone: '13800138000',
    goods_name: 'M24螺栓 304不锈钢',
    quantity: 100,
    amount: 2500.00,
    reason: '质量问题',
    status: 'pending',
    remark: '表面有划痕，需要退换货'
  },
  {
    id: 2,
    return_number: 'RT202609100001',
    original_order_number: 'JY20260815002',
    return_date: '2026-09-10',
    customer_name: '上海电力设备公司',
    contact_phone: '13900139000',
    goods_name: '绝缘子 110KV',
    quantity: 50,
    amount: 8500.00,
    reason: '发错货',
    status: 'processing',
    remark: '应该发220KV规格'
  },
  {
    id: 3,
    return_number: 'RT202609090001',
    original_order_number: 'ZG20260820003',
    return_date: '2026-09-09',
    customer_name: '天津钢铁制造厂',
    contact_phone: '13700137000',
    goods_name: '角钢 L50x5',
    quantity: 200,
    amount: 6800.00,
    reason: '规格不符',
    status: 'completed',
    remark: '已协商换货完成'
  },
  {
    id: 4,
    return_number: 'RT202609080001',
    original_order_number: 'JY20260805004',
    return_date: '2026-09-08',
    customer_name: '深圳科技园区管委会',
    contact_phone: '13600136000',
    goods_name: '电缆桥架 200x100',
    quantity: 80,
    amount: 4200.00,
    reason: '客户取消',
    status: 'rejected',
    remark: '订单取消超出退货期限'
  },
  {
    id: 5,
    return_number: 'RT202609070001',
    original_order_number: 'ZG20260710005',
    return_date: '2026-09-07',
    customer_name: '广州建筑集团',
    contact_phone: '13500135000',
    goods_name: 'H型钢 HN400x200x8x13',
    quantity: 30,
    amount: 15600.00,
    reason: '质量问题',
    status: 'completed',
    remark: '钢材表面锈蚀，已退款处理'
  }
])

// 计算属性
const filteredReturns = computed(() => {
  let result = [...returnOrders.value]

  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(item =>
      item.return_number.toLowerCase().includes(keyword) ||
      item.original_order_number.toLowerCase().includes(keyword) ||
      item.customer_name.toLowerCase().includes(keyword) ||
      item.goods_name.toLowerCase().includes(keyword)
    )
  }

  // 状态筛选
  if (filters.value.status) {
    result = result.filter(item => item.status === filters.value.status)
  }

  // 日期筛选
  if (filters.value.startDate) {
    result = result.filter(item => item.return_date >= filters.value.startDate)
  }
  if (filters.value.endDate) {
    result = result.filter(item => item.return_date <= filters.value.endDate)
  }

  // 按日期倒序排序
  result.sort((a, b) => b.return_date.localeCompare(a.return_date))

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredReturns.value.length / pageSize.value)))

const paginatedReturns = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredReturns.value.slice(start, end)
})

const pageStart = computed(() => filteredReturns.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredReturns.value.length))

const isAllSelected = computed(() => {
  return paginatedReturns.value.length > 0 &&
    paginatedReturns.value.every(item => selectedReturns.value.includes(item.id))
})

const isPartiallySelected = computed(() => {
  const selectedCount = paginatedReturns.value.filter(item =>
    selectedReturns.value.includes(item.id)
  ).length
  return selectedCount > 0 && selectedCount < paginatedReturns.value.length
})

// 方法
const fetchData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleReset = () => {
  filters.value = {
    keyword: '',
    status: '',
    startDate: '',
    endDate: ''
  }
  currentPage.value = 1
}

const getStatusCount = (status) => {
  if (!status) return returnOrders.value.length
  return returnOrders.value.filter(item => item.status === status).length
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const classMap = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    rejected: 'status-rejected'
  }
  return classMap[status] || ''
}

const isSelected = (id) => {
  return selectedReturns.value.includes(id)
}

const toggleSelect = (id) => {
  const index = selectedReturns.value.indexOf(id)
  if (index > -1) {
    selectedReturns.value.splice(index, 1)
  } else {
    selectedReturns.value.push(id)
  }
}

const toggleSelectAll = () => {
  const currentPageIds = paginatedReturns.value.map(item => item.id)

  if (isAllSelected.value) {
    selectedReturns.value = selectedReturns.value.filter(
      id => !currentPageIds.includes(id)
    )
  } else {
    selectedReturns.value = [
      ...new Set([...selectedReturns.value, ...currentPageIds])
    ]
  }
}

const openCreateModal = () => {
  formData.value = {
    original_order_number: '',
    return_date: new Date().toISOString().split('T')[0],
    customer_name: '',
    contact_phone: '',
    goods_name: '',
    quantity: 1,
    amount: 0,
    reason: '',
    remark: ''
  }
  createModalOpen.value = true
}

const closeCreateModal = () => {
  createModalOpen.value = false
}

const handleSubmit = () => {
  // 验证表单
  if (!formData.value.original_order_number || !formData.value.customer_name ||
      !formData.value.goods_name || !formData.value.reason) {
    alert('请填写必填项')
    return
  }

  submitting.value = true

  // 模拟提交
  setTimeout(() => {
    // 生成新的退货单号
    const today = new Date().toISOString().split('T')[0].replace(/-/g, '')
    const count = returnOrders.value.filter(item =>
      item.return_number.includes(today)
    ).length + 1
    const newReturnNumber = `RT${today}${String(count).padStart(4, '0')}`

    // 添加到列表
    returnOrders.value.unshift({
      id: Date.now(),
      return_number: newReturnNumber,
      ...formData.value,
      status: 'pending'
    })

    submitting.value = false
    closeCreateModal()
    alert('退货单录入成功！\n退货单号：' + newReturnNumber)
  }, 1000)
}

const openDetailModal = (item) => {
  selectedReturn.value = item
  detailModalOpen.value = true
}

const closeDetailModal = () => {
  detailModalOpen.value = false
  selectedReturn.value = null
}

const handleProcess = (item) => {
  closeDetailModal()
  alert(`处理退货单：${item.return_number}\n\n此功能需要在实际业务中实现具体处理流程`)
}

const handleExport = () => {
  alert('导出功能待实现')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.return-order-list-page {
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
select,
textarea {
  font: inherit;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
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
  min-width: 1400px;
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
}

.record-row:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.record-row.selected {
  background: rgba(var(--accent-rgb), 0.12);
}

.col-checkbox {
  width: 50px !important;
  text-align: center !important;
  vertical-align: middle !important;
  padding: 0 16px !important;
}

.records-table input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent);
  margin: 0;
  vertical-align: middle;
}

.document-column { width: 140px; }
.number-column { width: 100px; text-align: right !important; }
.material-column { width: 150px; }
.reason-column { width: 120px; }
.remark-column { width: 100px; }
.operation-column { width: 100px; text-align: center; }

.numeric,
.money-value {
  font-variant-numeric: tabular-nums;
}

.money-value {
  color: #182230 !important;
  font-weight: 750;
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

.date-cell {
  color: var(--text-secondary);
}

.material-cell,
.reason-cell,
.remark-cell {
  color: var(--text-secondary);
  font-size: 13px;
}

.material-cell strong {
  display: block;
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.status-pending {
  color: #a4510b;
  background: #fff3df;
  border: 1px solid #f3c887;
}

.status-processing {
  color: #1d4ed8;
  background: #dbeafe;
  border: 1px solid #93c5fd;
}

.status-completed {
  color: #13734f;
  background: #eaf8f1;
  border: 1px solid #a7e2c9;
}

.status-rejected {
  color: #b4232f;
  background: #fff1f2;
  border: 1px solid #fecaca;
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

/* 弹窗 */
.detail-modal-layer {
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

.create-modal {
  width: min(720px, calc(100vw - 48px));
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
  padding: 15px;
}

.summary-strip > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  padding: 0 15px;
  border-right: 1px solid #e5eaf0;
}

.summary-strip > div:first-child {
  padding-left: 0;
}

.summary-strip > div:last-child {
  border-right: 0;
  padding-right: 0;
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

.summary-strip .amount-text {
  color: #07805f;
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

.detail-modal-actions {
  justify-content: flex-end;
  margin-left: auto;
}

/* 表单样式 */
.return-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  padding: 18px;
}

.form-section h3 {
  margin: 0 0 14px;
  color: #263348;
  font-size: 14px;
  font-weight: 650;
  padding-bottom: 12px;
  border-bottom: 1px solid #edf1f5;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-field.full-width {
  grid-column: 1 / -1;
}

.field-label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-label em {
  color: #ef4444;
  font-style: normal;
}

.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  min-height: 38px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  padding: 9px 11px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.form-field textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
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

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid {
    grid-template-columns: 1fr;
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
    flex-wrap: wrap;
  }
}
</style>
