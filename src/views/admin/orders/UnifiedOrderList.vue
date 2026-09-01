<template>
  <div class="unified-order-list-page">
    <!-- 筛选工具栏 -->
    <div class="filter-bar">
      <div class="filter-group">
        <!-- 分类滑块 -->
        <div class="category-tabs">
          <div
            :class="['category-tab', { active: filters.category === '' }]"
            @click="filters.category = ''"
          >
            全部
          </div>
          <div
            v-for="store in stores"
            :key="store.id"
            :class="['category-tab', { active: filters.category === store.name + '订单' }]"
            @click="filters.category = store.name + '订单'"
          >
            {{ store.name }}订单
          </div>
        </div>

        <input
          v-model="filters.keyword"
          type="text"
          :placeholder="searchPlaceholder"
          class="search-input"
        />
        <div v-if="mode === 'logistics'" class="shipping-method-filter">
          <div class="filter-label" @click="toggleShippingDropdown">
            <span>{{ selectedShippingMethodText }}</span>
            <span class="dropdown-arrow" :class="{ open: shippingDropdownOpen }">▼</span>
          </div>
          <div v-if="shippingDropdownOpen" class="shipping-dropdown">
            <label
              v-for="method in shippingMethods"
              :key="method"
              class="shipping-option"
            >
              <input
                type="checkbox"
                :value="method"
                :checked="filters.shippingMethods.includes(method)"
                @change="toggleShippingMethod(method)"
              />
              <span>{{ method }}</span>
            </label>
          </div>
        </div>
        <input
          v-model="filters.startDate"
          type="date"
          class="filter-date"
          placeholder="开始日期"
        />
        <input
          v-model="filters.endDate"
          type="date"
          class="filter-date"
          placeholder="结束日期"
        />
        <button class="btn-filter" @click="handleFilter">筛选</button>
        <button class="btn-reset" @click="handleReset">重置</button>
      </div>
      <div class="batch-actions">
        <span class="selected-count">已选 {{ selectedOrders.length }} 项</span>
        <button
          class="btn-batch"
          :disabled="selectedOrders.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </button>
      </div>
    </div>

    <!-- 订单表格 -->
    <div class="table-container">
      <table class="order-table">
        <thead>
          <tr>
            <th class="col-checkbox">
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th class="col-id">订单ID</th>
            <th class="col-date">
              <div class="date-header">
                <span>日期</span>
                <div class="sort-arrows" @click="toggleSort">
                  <span class="arrow arrow-up" :class="{ active: sortOrder === 'asc' }">▲</span>
                  <span class="arrow arrow-down" :class="{ active: sortOrder === 'desc' }">▼</span>
                </div>
              </div>
            </th>
            <th class="col-customer">客户</th>
            <th class="col-receiver">收货人</th>
            <th class="col-phone">电话</th>
            <th class="col-address">地址</th>
            <th class="col-goods">货物</th>

            <!-- 财务模式列 -->
            <template v-if="mode === 'finance'">
              <th class="col-amount">应收金额</th>
              <th class="col-amount">已收金额</th>
              <th class="col-amount">未收金额</th>
            </template>

            <!-- 物流模式列 -->
            <template v-if="mode === 'logistics'">
              <th class="col-weight">重量</th>
              <th class="col-shipping">发货方式</th>
              <th class="col-tracking">单号</th>
              <th class="col-receipt">回单</th>
            </template>

            <th v-if="mode === 'finance'" class="col-status">状态</th>
            <th v-if="mode === 'logistics'" class="col-freight">运费</th>
            <th class="col-remark">备注</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="order in paginatedOrders"
            :key="order.id"
            :class="{
              selected: isSelected(order.id)
            }"
            :style="{ backgroundColor: getStoreColor(order), color: getStoreTextColor(order) }"
          >
            <td class="col-checkbox">
              <input
                type="checkbox"
                :checked="isSelected(order.id)"
                @change="toggleSelect(order.id)"
              />
            </td>
            <td class="col-id">
              <span :class="mode === 'logistics' ? 'logistics-id' : 'order-id'">
                {{ order.id }}
              </span>
            </td>
            <td class="col-date">{{ formatDate(order) }}</td>
            <td class="col-customer">{{ order.order_client || '-' }}</td>
            <td class="col-receiver">{{ order.receiver_name || '-' }}</td>
            <td class="col-phone">{{ order.receiver_phone || '-' }}</td>
            <td class="col-address">
              <div class="expandable-cell">
                <span class="cell-text">{{ (order.receiver_address || '-').substring(0, 6) }}</span>
                <span
                  v-if="order.receiver_address && order.receiver_address.length > 6"
                  class="expand-icon"
                  @click="showExpandModal(order.receiver_address, '收货地址')"
                >
                  ▼
                </span>
              </div>
            </td>
            <td class="col-goods">
              <div class="expandable-cell">
                <span class="cell-text">{{ (order.goods_name || '-').substring(0, 10) }}</span>
                <span
                  v-if="order.goods_name && order.goods_name.length > 10"
                  class="expand-icon"
                  @click="showExpandModal(order.goods_name, '货物信息')"
                >
                  ▼
                </span>
              </div>
            </td>

            <!-- 财务模式列 -->
            <template v-if="mode === 'finance'">
              <td class="col-amount amount-receivable">-</td>
              <td class="col-amount amount-received">-</td>
              <td class="col-amount amount-unpaid">
                <span>-</span>
              </td>
            </template>

            <!-- 物流模式列 -->
            <template v-if="mode === 'logistics'">
              <td class="col-weight">
                <span class="weight-text">{{ order.goods_weight || '-' }}</span>
              </td>
              <td class="col-shipping">
                <span
                  class="shipping-tag clickable"
                  :class="{ 'can-edit': order.audit_state === 1 }"
                  :title="order.audit_state === 1 ? '点击上传回单' : '已审核订单才能上传回单'"
                  @click="handleShippingTagClick(order)"
                >
                  {{ getShippingMethodText(order) }}
                </span>
              </td>
              <td class="col-tracking">
                <span
                  v-if="order.logistics_no"
                  class="tracking-number clickable"
                  :title="'点击复制单号'"
                  @click="copyLogisticsNo(order)"
                  v-html="order.logistics_no.replace(/-/g, '<br>')"
                >
                </span>
                <span class="no-tracking" v-else>-</span>
              </td>
              <td class="col-receipt">
                <span
                  v-if="hasReceipt(order)"
                  class="receipt-status has-receipt clickable"
                  :title="'点击查看回单'"
                  @click="handleReceiptClick(order)"
                >
                  回单
                </span>
              </td>
            </template>

            <td v-if="mode === 'finance'" class="col-status">
              <span :class="['status-tag', getStatusClass(order)]">
                {{ getStatusText(order) }}
              </span>
            </td>
            <td v-if="mode === 'logistics'" class="col-freight">
              <span
                v-if="getFreightTotal(order) > 0"
                class="freight-amount"
                @click="showFreightDetail(order)"
                :title="'点击查看运费明细'"
              >
                ¥{{ getFreightTotal(order).toFixed(2) }}
              </span>
              <span v-else class="freight-empty">-</span>
            </td>
            <td class="col-remark">
              <span
                v-if="order.remark && order.remark.length > 2"
                class="remark-text clickable"
                @click="showExpandModal('备注信息', order.remark)"
                :title="'点击查看完整备注'"
              >
                {{ order.remark.substring(0, 2) }}...
              </span>
              <span v-else class="remark-text">{{ order.remark || '-' }}</span>
            </td>
            <td class="col-actions">
              <div class="action-buttons">
                <button
                  v-if="mode === 'finance' && order.status === 'completed'"
                  class="btn-action btn-ship"
                  @click="handleShipOrder(order)"
                  title="出库发货"
                >
                  出库
                </button>
                <button
                  v-if="mode === 'logistics' && order.audit_state !== 1"
                  class="btn-action btn-logistics"
                  @click="handleShippingClick(order)"
                  title="录入物流信息"
                >
                  录入
                </button>
                <button
                  v-if="mode === 'logistics'"
                  class="btn-action btn-copy"
                  @click="handleCopyOrderInfo(order)"
                  title="复制物流信息"
                >
                  复制
                </button>
                <button
                  v-if="mode === 'logistics' && order.audit_state === 1"
                  class="btn-action btn-edit"
                  @click="handleEdit(order)"
                  title="修改信息"
                >
                  修改
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredOrders.length === 0">
            <td :colspan="columnCount" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">{{ mode === 'logistics' ? '🚚' : '📦' }}</span>
                <p>{{ emptyMessage }}</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <div class="pagination-info">
        <span>共 {{ totalOrders }} 条记录</span>
        <div class="page-size-selector">
          <span>每页显示</span>
          <div class="page-size-tabs">
            <button
              :class="['page-size-tab', { active: !showAll && pageSize === 20 }]"
              @click="changePageSize(20)"
            >
              20条
            </button>
            <button
              :class="['page-size-tab', { active: !showAll && pageSize === 50 }]"
              @click="changePageSize(50)"
            >
              50条
            </button>
            <button
              :class="['page-size-tab', { active: showAll }]"
              @click="changePageSize('all')"
            >
              全部
            </button>
          </div>
        </div>
      </div>
      <div v-if="mode === 'logistics'" class="freight-summary">
        <span class="freight-label">当前页运费合计：</span>
        <span class="freight-total">¥{{ currentPageFreightTotal.toFixed(2) }}</span>
      </div>
      <div class="pagination-controls">
        <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">
          下一页
        </button>
      </div>
    </div>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, h, watch } from 'vue'
import request from '@/api/request'
import { useOrderStore } from '@/stores/order'
import { formatOrderForCopy } from '@/utils/tools'
import { getStores } from '@/utils/storeHelper'

const props = defineProps({
  mode: {
    type: String,
    required: true,
    validator: (value) => ['finance', 'logistics'].includes(value)
  }
})

const emit = defineEmits(['ship', 'refresh'])

const orderStore = useOrderStore()

// 从父组件注入 handleShip 方法
const handleShipFromParent = inject('handleShip', null)

// 注入 Admin 组件提供的方法
const setHeaderActions = inject('setHeaderActions', null)

// 在组件挂载时设置顶部栏按钮
onMounted(() => {
  if (setHeaderActions) {
    // 订单列表显示两个按钮，物流列表只显示导出按钮
    if (props.mode === 'finance') {
      setHeaderActions(() =>
        h('div', { style: 'display: flex; gap: 12px;' }, [
          h('button', {
            class: 'btn-primary',
            onClick: handleAdd,
            style: 'padding: 10px 20px; background: #34d399; color: #fff; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;'
          }, [
            h('span', '➕'),
            '新增订单'
          ]),
          h('button', {
            class: 'btn-export',
            onClick: handleExport,
            style: 'padding: 10px 20px; background: #fff; color: #6b7280; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px;'
          }, [
            h('span', '📥'),
            '导出数据'
          ])
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
})

// 监听 mode 变化，重新获取数据
watch(() => props.mode, () => {
  fetchOrdersData()
})

// 订单数据
const orders = ref([])
const loading = ref(false)
const stores = ref([])

// 排序状态
const sortOrder = ref('desc') // 'desc' = 最近到远, 'asc' = 最远到近

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
  shippingMethods: [], // 改为数组以支持多选
  startDate: '',
  endDate: ''
})

// 发货方式选项
const shippingMethods = ['物流', '零担快运', '快递', '专车', '其它']
const shippingDropdownOpen = ref(false)

// 切换发货方式下拉框
const toggleShippingDropdown = () => {
  shippingDropdownOpen.value = !shippingDropdownOpen.value
}

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
const pageSize = ref(20)
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
    // 并行加载订单和门店数据
    const [ordersResponse, storesData] = await Promise.all([
      request({
        url: '/orders',
        method: 'GET'
      }),
      getStores()
    ])

    // 只显示状态为 active 的门店
    stores.value = storesData.filter(store => store.status === 'active')

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

  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(order =>
      String(order.id).toLowerCase().includes(keyword) ||
      (order.order_client || '').toLowerCase().includes(keyword) ||
      (order.receiver_name || '').toLowerCase().includes(keyword) ||
      (props.mode === 'logistics' && (order.logistics_no || '').toLowerCase().includes(keyword))
    )
  }

  // 分类筛选
  if (filters.value.category) {
    result = result.filter(order => {
      const orderCategory = getCategoryText(order)
      return orderCategory === filters.value.category
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
const totalPages = computed(() => Math.ceil(totalOrders.value / pageSize.value))

// 分页后的订单数据
const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredOrders.value.slice(start, end)
})

const isAllSelected = computed(() => {
  return paginatedOrders.value.length > 0 &&
    paginatedOrders.value.every(order => selectedOrders.value.includes(order.id))
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

const toggleSelect = (orderId) => {
  const index = selectedOrders.value.indexOf(orderId)
  if (index > -1) {
    selectedOrders.value.splice(index, 1)
  } else {
    selectedOrders.value.push(orderId)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedOrders.value = []
  } else {
    selectedOrders.value = filteredOrders.value.map(order => order.id)
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
    shippingMethods: [], // 改为数组
    startDate: '',
    endDate: ''
  }
}

const handleAdd = () => {
  console.log(props.mode === 'logistics' ? '新增物流单' : '新增订单')
}

const handleEdit = (order) => {
  // 触发打开已出库订单管理弹窗，模式为编辑
  window.dispatchEvent(new CustomEvent('open-shipped-action-modal', {
    detail: { orderId: order.id, mode: 'edit' }
  }))
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
    const textToCopy = formatOrderForCopy(order)

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

  // 打开审核弹窗（填写物流单号）
  window.triggerShippedActionModal(order.id, 'audit')
}

// 点击发货方式标签 - 上传回单
const handleShippingTagClick = (order) => {
  // 更新 orderStore 数据
  orderStore.allOrders = orders.value

  if (order.audit_state === 1) {
    // 已审核的订单，打开回单上传窗口
    window.triggerShippedActionModal(order.id, 'receipt')
  }
}

const handleLogisticsClick = (order) => {
  // 更新 orderStore 数据
  orderStore.allOrders = orders.value

  if (order.audit_state === 1) {
    // 已审核的订单，打开填写单号弹窗
    window.triggerShippedActionModal(order.id, 'receipt')
  }
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
  if (order.status === 'shipped' && order.audit_state === 1) {
    return '已发货'
  } else if (order.status === 'shipped') {
    return '已出库'
  } else if (order.status === 'completed') {
    return '已完成'
  } else {
    return '未完成'
  }
}

// 获取订单状态样式类
const getStatusClass = (order) => {
  if (order.status === 'shipped' && order.audit_state === 1) {
    return 'status-shipped'
  } else if (order.status === 'shipped') {
    return 'status-out'
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
  if (confirm(`确定要删除订单 ${order.id} 吗？`)) {
    try {
      await request({
        url: `/orders/${order.id}`,
        method: 'DELETE'
      })
      await fetchOrdersData()
    } catch (error) {
      alert('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedOrders.value.length === 0) {
    alert('请先选择要删除的订单')
    return
  }

  if (confirm(`确定要删除选中的 ${selectedOrders.value.length} 个订单吗？`)) {
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
        alert('删除成功')
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
  width: 100%;
}

/* 筛选工具栏 */
.filter-bar {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
  align-items: center;
}

/* 分类滑块 */
.category-tabs {
  display: flex;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.category-tab {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  white-space: nowrap;
}

.category-tab:hover {
  background: #e5e7eb;
  color: #374151;
}

.category-tab.active {
  background: #34d399;
  color: #fff;
  box-shadow: 0 2px 4px rgba(52, 211, 153, 0.3);
}

.search-input {
  flex: 1;
  min-width: 250px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.search-input:focus {
  border-color: #34d399;
}

.filter-select,
.filter-date {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-select:focus,
.filter-date:focus {
  border-color: #34d399;
}

.btn-filter,
.btn-reset {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-filter {
  background: #34d399;
  color: #fff;
}

.btn-filter:hover {
  background: #10b981;
}

.btn-reset {
  background: #f3f4f6;
  color: #6b7280;
}

.btn-reset:hover {
  background: #e5e7eb;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-count {
  font-size: 14px;
  color: #6b7280;
}

.btn-batch {
  padding: 8px 16px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-batch:hover:not(:disabled) {
  background: #dc2626;
}

.btn-batch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 表格容器 */
.table-container {
  background: #fff;
  border-radius: 8px;
  overflow-x: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  position: relative;
}

/* 订单表格 */
.order-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1500px;
}

.order-table thead {
  background: #f9fafb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.order-table th {
  padding: 12px 8px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}

.order-table td {
  padding: 12px 8px;
  font-size: 14px;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.order-table tbody tr {
  transition: background 0.2s;
}

.order-table tbody tr:hover {
  background: #f9fafb;
}

.order-table tbody tr.selected {
  background: #ecfdf5;
}

.order-table tbody tr.insulation-row {
  background: #FFF4D9 !important;
}

.order-table tbody tr.insulation-row.selected {
  background: #FFF0C2 !important;
}

/* 列宽 */
.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-id {
  width: 120px;
}

.col-date {
  width: 100px;
}

.date-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.sort-arrows {
  display: flex;
  flex-direction: column;
  gap: 1px;
  cursor: pointer;
  user-select: none;
}

.arrow {
  font-size: 8px;
  color: #d1d5db;
  transition: color 0.2s;
  line-height: 1;
}

.arrow.active {
  color: #34d399;
}

.sort-arrows:hover .arrow {
  color: #9ca3af;
}

.sort-arrows:hover .arrow.active {
  color: #10b981;
}

.col-customer {
  width: 140px;
}

.col-receiver {
  width: 100px;
}

.col-phone {
  width: 120px;
}

.col-address {
  width: 120px;
}

.col-goods {
  width: 150px;
}

.col-amount {
  width: 100px;
  text-align: right;
}

.col-shipping {
  width: 100px;
}

.col-tracking {
  width: 140px;
  text-align: center;
}

.tracking-number {
  white-space: pre-line;
  line-height: 1.5;
}

.col-receipt {
  width: 100px;
  text-align: center;
}

.col-remark {
  width: 150px;
}

.col-actions {
  width: 200px;
  text-align: center;
  position: sticky;
  right: 0;
  background: #fff;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.05);
  z-index: 5;
}

.order-table tbody tr:hover .col-actions {
  background: #f9fafb;
}

.order-table tbody tr.selected .col-actions {
  background: #ecfdf5;
}

.order-table tbody tr.insulation-row .col-actions {
  background: #FFF4D9 !important;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.btn-action {
  padding: 5px 12px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-logistics {
  background: #e0f2fe;
  color: #0369a1;
}

.btn-logistics:hover {
  background: #bae6fd;
}

.btn-edit {
  background: #fef3c7;
  color: #d97706;
}

.btn-edit:hover {
  background: #fde68a;
}

.btn-copy {
  background: #e0e7ff;
  color: #4f46e5;
}

.btn-copy:hover {
  background: #c7d2fe;
}

.btn-delete {
  background: #fee2e2;
  color: #dc2626;
}

.btn-delete:hover {
  background: #fecaca;
}

.col-status {
  width: 90px;
  text-align: center;
}

.status-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-pending {
  background: #fef3c7;
  color: #d97706;
}

.status-completed {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-out {
  background: #e0e7ff;
  color: #6366f1;
}

.status-shipped {
  background: #d1fae5;
  color: #059669;
}

.btn-ship {
  background: #dbeafe;
  color: #1d4ed8;
}

.btn-ship:hover {
  background: #bfdbfe;
}

/* 发货方式多选筛选 */
.shipping-method-filter {
  position: relative;
  min-width: 160px;
}

.filter-label {
  padding: 9px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.filter-label:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.dropdown-arrow {
  font-size: 10px;
  color: #666;
  transition: transform 0.2s;
  margin-left: 8px;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

.shipping-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  padding: 8px;
}

.shipping-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  font-size: 14px;
  user-select: none;
}

.shipping-option:hover {
  background: #f1f5f9;
}

.shipping-option input[type="checkbox"] {
  margin: 0;
  margin-right: 8px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.shipping-option span {
  flex: 1;
  color: #333;
}

/* 表格元素样式 */
.order-id {
  font-weight: 600;
  color: #2563eb;
}

.logistics-id {
  font-weight: 600;
  color: #7c3aed;
}

.category-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  background: #e3f2fd;
}

.expandable-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cell-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expand-icon {
  flex-shrink: 0;
  cursor: pointer;
  color: #1890ff;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 3px;
  transition: all 0.2s;
  user-select: none;
}

.expand-icon:hover {
  background: #e6f7ff;
  color: #0050b3;
}

.remark-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.shipping-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  background: #f3f4f6;
  transition: all 0.3s;
}

.shipping-tag.clickable {
  cursor: pointer;
}

.shipping-tag.can-edit {
  background: #e6f4ff;
  color: #1677ff;
  border: 1px solid #91caff;
}

.shipping-tag.can-edit:hover {
  background: #bae0ff;
  transform: scale(1.05);
}

.clickable {
  cursor: pointer;
}

.amount-receivable {
  color: #3b82f6;
  font-weight: 600;
}

.amount-received {
  color: #10b981;
  font-weight: 600;
}

.amount-unpaid {
  font-weight: 600;
}

.unpaid-warning {
  color: #ef4444;
}

.tracking-number {
  font-family: inherit;
  color: #374151;
  font-weight: normal;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tracking-number:hover {
  color: #2563eb;
  text-decoration: underline;
}

.no-tracking {
  color: #d1d5db;
}

.receipt-status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.has-receipt {
  color: #10b981;
  background: #d1fae5;
}

.has-receipt:hover {
  background: #a7f3d0;
  transform: scale(1.05);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
}

.empty-content p {
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: #6b7280;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-tabs {
  display: flex;
  gap: 4px;
  background: #f3f4f6;
  padding: 2px;
  border-radius: 6px;
}

.page-size-tab {
  padding: 4px 12px;
  font-size: 13px;
  color: #6b7280;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.page-size-tab:hover {
  color: #374151;
  background: #e5e7eb;
}

.page-size-tab.active {
  color: #fff;
  background: #3b82f6;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
}

.freight-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.freight-label {
  font-size: 14px;
  color: #6b7280;
}

.freight-total {
  font-size: 14px;
  font-weight: 600;
  color: #059669;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-btn {
  padding: 6px 16px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  border-color: #34d399;
  color: #34d399;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}

/* 展开信息弹窗 */
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
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.expand-modal {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.expand-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.expand-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
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

.expand-modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 80px);
}

.expand-modal-body p {
  margin: 0;
  font-size: 15px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 运费列样式 */
.col-freight {
  width: 100px;
  text-align: center;
}

.freight-amount {
  color: #1890ff;
  font-weight: bold;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.freight-amount:hover {
  background: #e6f4ff;
  text-decoration: underline;
}

.freight-empty {
  color: #999;
}

/* 运费明细弹窗样式 */
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
  align-items: center;
  padding: 16px;
  background: #e6f4ff;
  border-radius: 8px;
  border: 2px solid #91caff;
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
</style>
