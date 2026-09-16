<template>
  <teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="visible"
        id="shippedOrderActionModal"
        class="modal-overlay"
        @click.self="closeShippedActionModal"
      >
        <section
          class="action-modal"
          :class="{ 'is-dragging': isDragging }"
          :style="{ transform: `translate(${modalX}px, ${modalY}px)` }"
          role="dialog"
          aria-modal="true"
          aria-labelledby="actionModalTitle"
          aria-describedby="actionModalSubtitle"
          @mousedown="handleMouseDown"
        >
          <header class="modal-header">
            <div class="modal-heading">
              <div class="modal-heading-icon" aria-hidden="true">
                <svg v-if="isReceiptMode" viewBox="0 0 24 24">
                  <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v13a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 18.5z"></path>
                  <path d="m7.5 16 3.2-3.5 2.4 2.4 1.8-2 2.1 3.1"></path>
                  <circle cx="15.5" cy="8" r="1.5"></circle>
                </svg>
                <svg v-else viewBox="0 0 24 24">
                  <path d="M3 6h11v11H3zM14 10h3.5l3.5 4v3h-7z"></path>
                  <circle cx="7" cy="18" r="2"></circle>
                  <circle cx="18" cy="18" r="2"></circle>
                </svg>
              </div>
              <div class="modal-heading-copy">
                <span class="modal-eyebrow">{{ isReceiptMode ? '回单管理' : '物流管理' }}</span>
                <h2 id="actionModalTitle">{{ modalTitle }}</h2>
                <p id="actionModalSubtitle">{{ modalSubtitle }}</p>
              </div>
            </div>
            <button
              type="button"
              class="modal-close-button"
              title="关闭"
              aria-label="关闭弹窗"
              @mousedown.stop
              @click="closeShippedActionModal"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12M18 6 6 18"></path>
              </svg>
            </button>
          </header>

          <div class="action-modal-body">
            <input id="actionTargetOrderId" type="hidden" :value="targetOrderId" />

            <section
              v-if="isLogisticsMode"
              id="auditContent"
              class="content-card logistics-card"
              aria-label="物流与费用信息"
            >
              <div class="card-header">
                <div>
                  <h3>基础信息</h3>
                  <p>确认客户与发货方式后填写承运信息</p>
                </div>
              </div>

              <div class="card-body">
                <div class="summary-grid">
                  <div class="summary-item">
                    <span>客户名称</span>
                    <strong :title="currentOrderInfo.customer || '-'">
                      {{ currentOrderInfo.customer || '-' }}
                    </strong>
                  </div>
                  <div class="form-item">
                    <label for="shippingMethodSelect">发货方式</label>
                    <select
                      id="shippingMethodSelect"
                      v-model="shippingMethod"
                      class="modern-input"
                    >
                      <option
                        v-for="option in shippingMethodOptions"
                        :key="option.value"
                        :value="option.value"
                      >
                        {{ option.label }}
                      </option>
                    </select>
                  </div>
                </div>

                <div v-if="shippingMethod === '4'" class="form-item custom-method-field">
                  <label for="shippingCustom">自定义发货方式</label>
                  <input
                    id="shippingCustom"
                    v-model="shippingCustom"
                    class="modern-input"
                    placeholder="请输入发货方式名称"
                  />
                </div>
              </div>
            </section>

            <section
              v-if="isLogisticsMode && currentOrderInfo.goodsInfo"
              class="content-card"
              aria-label="订单商品信息"
            >
              <div class="card-header compact">
                <div>
                  <h3>订单商品信息</h3>
                  <p>当前订单的商品与件数摘要</p>
                </div>
              </div>
              <pre class="goods-summary">{{ currentOrderInfo.goodsInfo }}</pre>
            </section>

            <section
              v-if="isLogisticsMode"
              class="content-card"
              aria-label="物流与费用录入"
            >
              <div class="card-header">
                <div>
                  <h3>物流与费用</h3>
                  <p>物流单号可选填，费用将计入本次物流记录</p>
                </div>
              </div>

              <div class="card-body">
                <div v-if="carrierTags.length" id="auditCarrierTags" class="carrier-tags">
                  <span class="carrier-tags-label">常用承运商</span>
                  <button
                    v-for="tag in carrierTags"
                    :key="tag"
                    type="button"
                    class="carrier-tag"
                    :class="{ active: carrierName === tag }"
                    @click="carrierName = tag"
                  >
                    {{ tag }}
                  </button>
                </div>

                <div class="form-grid">
                  <div class="form-item">
                    <label for="auditCarrierName">物流公司 / 承运车队</label>
                    <input
                      id="auditCarrierName"
                      v-model="carrierName"
                      class="modern-input"
                      placeholder="如：三志物流、顺丰快递"
                    />
                  </div>

                  <div class="form-item">
                    <label for="auditLogisticsNo">
                      物流单号 / 运输凭证
                      <span class="optional-text">选填</span>
                    </label>
                    <input
                      id="auditLogisticsNo"
                      v-model="logisticsNo"
                      class="modern-input"
                      placeholder="请输入运单号、司机电话等"
                    />
                  </div>
                </div>

                <div class="cost-section">
                  <div class="form-item freight-field">
                    <label for="freightCost">运费</label>
                    <div class="money-input">
                      <span aria-hidden="true">¥</span>
                      <input
                        id="freightCost"
                        v-model.number="freightCost"
                        type="number"
                        class="modern-input"
                        placeholder="0.00"
                        step="0.01"
                        min="0"
                      />
                    </div>
                  </div>

                  <div class="other-costs">
                    <div class="field-heading">
                      <div>
                        <strong>其它费用</strong>
                        <span>装卸、送货等附加费用</span>
                      </div>
                      <button type="button" class="text-action" @click="addOtherCost">
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M12 5v14M5 12h14"></path>
                        </svg>
                        添加费用
                      </button>
                    </div>

                    <div v-if="otherCosts.length" class="cost-list">
                      <div
                        v-for="(item, index) in otherCosts"
                        :key="index"
                        class="cost-row"
                      >
                        <input
                          v-model="item.note"
                          type="text"
                          class="modern-input"
                          placeholder="费用说明"
                          :aria-label="`第 ${index + 1} 项其它费用说明`"
                        />
                        <div class="money-input">
                          <span aria-hidden="true">¥</span>
                          <input
                            v-model.number="item.amount"
                            type="number"
                            class="modern-input"
                            placeholder="0.00"
                            step="0.01"
                            min="0"
                            :aria-label="`第 ${index + 1} 项其它费用金额`"
                          />
                        </div>
                        <button
                          type="button"
                          class="remove-cost-button"
                          title="删除该费用"
                          :aria-label="`删除第 ${index + 1} 项其它费用`"
                          @click="removeOtherCost(index)"
                        >
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5"></path>
                          </svg>
                        </button>
                      </div>
                    </div>
                    <div v-else class="empty-costs">暂无其它费用，可按需添加。</div>
                  </div>
                </div>

                <div class="total-strip">
                  <div>
                    <span>费用合计</span>
                    <small>运费与其它费用总和</small>
                  </div>
                  <strong>¥ {{ totalCost.toFixed(2) }}</strong>
                </div>
              </div>
            </section>

            <section
              v-if="isReceiptMode"
              class="content-card receipt-card"
              aria-label="回单凭证"
            >
              <div class="card-header">
                <div>
                  <h3>{{ currentMode === 'view_receipt' ? '回单图片' : '上传回单' }}</h3>
                  <p>
                    {{ currentMode === 'view_receipt'
                      ? '点击图片可放大查看'
                      : '支持点击选择或将图片拖入下方区域' }}
                  </p>
                </div>
                <span class="file-type-label">JPG / PNG</span>
              </div>

              <div class="receipt-card-body">
                <div
                  id="receiptContent"
                  class="receipt-uploader"
                  @dragenter.prevent="handleDragEnter"
                  @dragover.prevent="handleDragOver"
                  @dragleave.prevent="handleDragLeave"
                  @drop.prevent="handleDrop"
                >
                  <input
                    id="receiptImageInput"
                    type="file"
                    accept="image/*"
                    class="visually-hidden"
                    @change="previewReceiptImage"
                  />

                  <button
                    id="receiptUploadPrompt"
                    type="button"
                    class="receipt-upload-prompt"
                    @click="triggerFileInput"
                  >
                    <span class="upload-icon" aria-hidden="true">
                      <svg viewBox="0 0 24 24">
                        <path d="M12 16V4M7 9l5-5 5 5"></path>
                        <path d="M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"></path>
                      </svg>
                    </span>
                    <strong>选择或拖入回单图片</strong>
                    <span>建议上传清晰、完整的回单凭证</span>
                  </button>

                  <img
                    id="receiptImagePreview"
                    src=""
                    class="receipt-image-preview"
                    alt="回单图片预览"
                    @click="openLargeImagePreview"
                  />

                  <button
                    id="receiptRotateBtn"
                    type="button"
                    class="receipt-rotate-button"
                    title="顺时针旋转图片"
                    aria-label="顺时针旋转图片"
                    @click.stop="rotateReceiptImage"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M21 2v6h-6"></path>
                      <path d="M21 13a9 9 0 1 1-3-7.7L21 8"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </section>
          </div>

          <footer class="action-modal-footer">
            <button
              type="button"
              class="button button-secondary"
              @click="closeShippedActionModal"
            >
              关闭
            </button>
            <div class="footer-actions">
              <button
                v-if="currentMode === 'audit'"
                id="btnAuditRevoke"
                type="button"
                class="button button-danger"
                @click="submitRevokeShipOrder"
              >
                撤销出库
              </button>
              <button
                v-if="currentMode === 'audit'"
                id="btnAuditConfirm"
                type="button"
                class="button button-primary"
                @click="submitAuditShipOrder"
              >
                确认审核
              </button>
              <button
                v-if="currentMode === 'entry' || currentMode === 'edit'"
                id="btnEditConfirm"
                type="button"
                class="button button-primary"
                @click="submitEditShipOrder"
              >
                {{ logisticsSubmitText }}
              </button>
              <button
                v-if="currentMode === 'receipt'"
                id="btnReceiptDelete"
                type="button"
                class="button button-secondary"
                @click="clearReceiptImage"
              >
                清除图片
              </button>
              <button
                v-if="currentMode === 'receipt'"
                id="btnReceiptUpload"
                type="button"
                class="button button-primary"
                @click="submitReceiptImage"
              >
                确认上传
              </button>
              <button
                v-if="canDeleteReceipt"
                id="btnRealDeleteReceipt"
                type="button"
                class="button button-danger"
                @click="deleteRealReceiptImage"
              >
                删除凭证
              </button>
              <button
                v-if="currentMode === 'view_receipt'"
                id="btnDownloadReceipt"
                type="button"
                class="button button-primary"
                @click="downloadReceiptImage"
              >
                下载凭证
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>

    <!-- 大图预览模态框 -->
    <div
      v-if="showLargePreview"
      class="large-preview"
      @click="closeLargePreview"
    >
      <button
        type="button"
        class="large-preview-close"
        title="关闭预览"
        aria-label="关闭图片预览"
        @click="closeLargePreview"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m6 6 12 12M18 6 6 18"></path>
        </svg>
      </button>
      <img
        :src="largePreviewSrc"
        alt="回单图片大图预览"
        @click.stop
      />
    </div>

    <!-- 顶部消息提示 -->
    <Transition name="notice">
      <div
        v-if="messageVisible"
        class="page-notice"
        :class="`notice-${messageType}`"
        role="status"
        aria-live="polite"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path v-if="messageType === 'success'" d="m8 12 2.7 2.7L16.5 9"></path>
          <path v-else d="M12 8v5M12 17h.01"></path>
        </svg>
        {{ messageText }}
      </div>
    </Transition>
  </teleport>

  <CustomModal
    v-model:visible="deleteConfirmVisible"
    type="warning"
    title="删除回单凭证"
    message="确定要彻底删除这张回单图片吗？此操作会同时删除数据库记录和图片文件，且无法恢复。"
    confirm-text="确定删除"
    cancel-text="取消"
    danger
    @confirm="confirmDeleteReceiptImage"
  />
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'

const userStore = useUserStore()
const orderStore = useOrderStore()

const emit = defineEmits(['refresh'])

const visible = ref(false)
const targetOrderId = ref(null)
const modalTitle = ref('已出库订单管理')
const modalSubtitle = ref('请选择对当前出库订单的操作指令')
const logisticsSubmitText = ref('修改完成')
const currentMode = ref('entry')
const deleteConfirmVisible = ref(false)

const isLogisticsMode = computed(() =>
  ['audit', 'entry', 'edit'].includes(currentMode.value)
)
const isReceiptMode = computed(() =>
  ['receipt', 'view_receipt'].includes(currentMode.value)
)
const canDeleteReceipt = computed(() =>
  currentMode.value === 'view_receipt' && userStore.hasPerm('shipped.delete_receipt')
)

// 当前订单信息
const currentOrderInfo = ref({
  customer: '',
  goodsInfo: '' // 新增：商品信息文本
})

// 消息提示状态
const messageVisible = ref(false)
const messageText = ref('')
const messageType = ref('success')

// 拖动相关状态
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const modalX = ref(0)
const modalY = ref(0)

// 显示顶部消息提示
const showMessage = (text, type = 'success') => {
  messageText.value = text
  messageType.value = type
  messageVisible.value = true

  setTimeout(() => {
    messageVisible.value = false
  }, 3000)
}

// 从本地存储加载弹窗位置
const loadModalPosition = () => {
  try {
    const savedPosition = localStorage.getItem('shippedActionModalPosition')
    if (savedPosition) {
      const { x, y } = JSON.parse(savedPosition)
      modalX.value = x
      modalY.value = y
    } else {
      // 默认居中
      modalX.value = 0
      modalY.value = 0
    }
  } catch (e) {
    console.error('加载弹窗位置失败', e)
    modalX.value = 0
    modalY.value = 0
  }
}

// 保存弹窗位置到本地存储
const saveModalPosition = () => {
  try {
    localStorage.setItem('shippedActionModalPosition', JSON.stringify({
      x: modalX.value,
      y: modalY.value
    }))
  } catch (e) {
    console.error('保存弹窗位置失败', e)
  }
}

// 开始拖动
const handleMouseDown = (event) => {
  // 只允许点击头部区域拖动
  if (!event.target.closest('.modal-header')) return

  isDragging.value = true
  dragStartX.value = event.clientX - modalX.value
  dragStartY.value = event.clientY - modalY.value

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)

  event.preventDefault()
}

// 拖动中
const handleMouseMove = (event) => {
  if (!isDragging.value) return

  modalX.value = event.clientX - dragStartX.value
  modalY.value = event.clientY - dragStartY.value

  event.preventDefault()
}

// 结束拖动
const handleMouseUp = () => {
  if (isDragging.value) {
    isDragging.value = false
    saveModalPosition()

    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
}

// 审核相关
const carrierName = ref('')
const logisticsNo = ref('')
const carrierTags = ref([])
const shippingMethod = ref('0')
const shippingCustom = ref('')
const shippingMethodOptions = [
  { value: '0', label: '物流' },
  { value: '1', label: '零担快运' },
  { value: '2', label: '快递' },
  { value: '3', label: '专车' },
  { value: '4', label: '其它' }
]

// 运费相关
const freightCost = ref(0)
const otherCosts = ref([]) // 其它费用数组

// 添加其它费用项
const addOtherCost = () => {
  otherCosts.value.push({
    note: '',
    amount: 0
  })
}

// 删除其它费用项
const removeOtherCost = (index) => {
  otherCosts.value.splice(index, 1)
}

// 计算总金额
const totalCost = computed(() => {
  const freight = Number(freightCost.value) || 0
  const othersSum = otherCosts.value.reduce((sum, item) => {
    return sum + (Number(item.amount) || 0)
  }, 0)
  return freight + othersSum
})

// 回单相关
const showLargePreview = ref(false)
const largePreviewSrc = ref('')
const originalReceiptImg = new Image()
let currentReceiptRotation = 0

// 全局变量，用于存储当前所有订单（照搬原生）
let allOrdersLocal = []

// 获取商品信息文本（新旧订单兼容）
const getGoodsDisplayText = (order) => {
  if (!order) return ''

  // 新订单：显示商品明细列表
  if (order.order_goods && order.order_goods.length > 0) {
    const lines = order.order_goods.map((item, index) =>
      `${index + 1}. ${item.goods_name} ${item.spec} x${item.quantity}${item.unit || ''} (${item.packages}件)`
    )
    const totalQty = order.order_goods.reduce((sum, item) => sum + (item.quantity || 0), 0)
    const totalPkg = order.order_goods.reduce((sum, item) => sum + (item.packages || 0), 0)
    const unit = order.order_goods[0]?.unit || ''
    return lines.join('\n') + `\n总计：${totalQty}${unit}，${totalPkg}件`
  }

  // 旧订单：显示原始文本
  return `商品：${order.goods_name || '-'}\n重量：${order.goods_weight || '-'}\n件数：${order.goods_quantity || '-'}`
}

// 加载物流公司标签
const fetchCarrierTags = async () => {
  try {
    const response = await request({ url: '/carrier_tags', method: 'GET' })
    if (Array.isArray(response) && response.length > 0) {
      carrierTags.value = response
    } else {
      carrierTags.value = []
    }
  } catch (error) {
    carrierTags.value = []
  }
}

// 清除回单图片
const clearReceiptImage = () => {
  const input = document.getElementById('receiptImageInput')
  const preview = document.getElementById('receiptImagePreview')
  const prompt = document.getElementById('receiptUploadPrompt')
  const rotateBtn = document.getElementById('receiptRotateBtn')

  if (input) input.value = ''
  if (preview) {
    preview.src = ''
    preview.style.display = 'none'
  }
  if (prompt) prompt.style.display = 'flex'
  if (rotateBtn) rotateBtn.style.display = 'none'

  currentReceiptRotation = 0
}

const loadOrderLogistics = (order) => {
  if (!order) return

  let fullNo = order.logistics_no || ''
  if (['暂未录入单号', '无单号记录', '暂无记录'].includes(fullNo)) {
    fullNo = ''
  }

  if (fullNo.includes('-')) {
    const parts = fullNo.split('-')
    carrierName.value = parts[0] || ''
    logisticsNo.value = parts.slice(1).join('-') || ''
  } else {
    carrierName.value = ''
    logisticsNo.value = fullNo
  }

  if (!Array.isArray(order.freight_costs)) return

  order.freight_costs.forEach(item => {
    if (item.type === 'freight') {
      freightCost.value = item.amount || 0
    } else if (item.type === 'other') {
      otherCosts.value.push({
        note: item.note || '',
        amount: item.amount || 0
      })
    }
  })
}

const renderReceiptImage = (order) => {
  const preview = document.getElementById('receiptImagePreview')
  const prompt = document.getElementById('receiptUploadPrompt')
  const rotateBtn = document.getElementById('receiptRotateBtn')

  if (!order?.receipt_img_url) {
    clearReceiptImage()
    return
  }

  if (preview) {
    preview.src = order.receipt_img_url
    preview.style.display = 'block'
  }
  if (prompt) prompt.style.display = 'none'
  if (rotateBtn) rotateBtn.style.display = 'none'
}

// 打开弹窗
const open = (orderId, mode) => {
  targetOrderId.value = orderId
  currentMode.value = mode
  deleteConfirmVisible.value = false

  allOrdersLocal = orderStore.allOrders
  const order = allOrdersLocal.find(o => String(o.id) === String(orderId))

  carrierName.value = ''
  logisticsNo.value = ''
  freightCost.value = 0
  otherCosts.value = []
  shippingMethod.value = '0'
  shippingCustom.value = ''
  currentOrderInfo.value = {
    customer: order?.order_client || '',
    goodsInfo: getGoodsDisplayText(order)
  }

  if (order) {
    const existingMethod = String(order.shipping_method ?? '')
    shippingMethod.value = shippingMethodOptions.some(option => option.value === existingMethod)
      ? existingMethod
      : '0'
    shippingCustom.value = order.shipping_custom || ''
  }

  if (mode === 'audit') {
    modalTitle.value = '已出库订单管理'
    modalSubtitle.value = '核对物流与费用信息，并选择审核或撤销出库'
  } else if (mode === 'entry' || mode === 'edit') {
    const isEntryMode = mode === 'entry'
    modalTitle.value = isEntryMode ? '录入物流与运费信息' : '修改物流与运费信息'
    modalSubtitle.value = isEntryMode
      ? '补充承运、单号与费用信息'
      : '更新该订单已有的物流与费用信息'
    logisticsSubmitText.value = isEntryMode ? '录入完成' : '修改完成'
  } else if (mode === 'receipt') {
    modalTitle.value = '回单凭证管理'
    modalSubtitle.value = '上传或替换该订单的发货回单图片'
  } else if (mode === 'view_receipt') {
    modalTitle.value = '回单凭证详情'
    modalSubtitle.value = '查看、下载或删除该订单的回单凭证'
  }

  if (['audit', 'entry', 'edit'].includes(mode)) {
    loadOrderLogistics(order)
    fetchCarrierTags()
  }

  loadModalPosition()
  visible.value = true

  if (['receipt', 'view_receipt'].includes(mode)) {
    nextTick(() => renderReceiptImage(order))
  }
}

// 关闭弹窗
const closeShippedActionModal = () => {
  visible.value = false
  deleteConfirmVisible.value = false
  clearReceiptImage()
}

// 1. 撤销出库：已出库订单按流程退回已完成，不直接回到未完成
const submitRevokeShipOrder = async () => {
  const id = targetOrderId.value
  try {
    await request({
      url: `/orders/${id}`,
      method: 'PUT',
      data: { status: 'completed' }
    })
    showMessage('已撤销出库，订单已恢复为已完成状态', 'success')
    closeShippedActionModal()
    emit('refresh')
  } catch (e) {
    showMessage('网络通讯失败，无法完成撤销出库指令', 'error')
  }
}

// 2. 确认审核
const submitAuditShipOrder = async () => {
  const id = targetOrderId.value

  const carrier = carrierName.value.trim()
  const no = logisticsNo.value.trim()

  let finalLogisticsNo = ''
  const shouldPersistCarrier = !['3', '4'].includes(shippingMethod.value)
  if (carrier && no && shouldPersistCarrier) {
    finalLogisticsNo = `${carrier}-${no}`
  } else if (no) {
    finalLogisticsNo = no
  } else {
    finalLogisticsNo = '无单号记录'
  }

  // 构建运费数据数组
  const freightData = []

  // 添加运费项
  if (freightCost.value && Number(freightCost.value) > 0) {
    freightData.push({
      type: 'freight',
      note: '运费',
      amount: Number(freightCost.value)
    })
  }

  // 添加其它费用项
  otherCosts.value.forEach(item => {
    if (item.amount && Number(item.amount) > 0) {
      freightData.push({
        type: 'other',
        note: item.note.trim() || '其它费用',
        amount: Number(item.amount)
      })
    }
  })

  // 保存历史标签。专车和其它属于临时信息，不进入快捷标签库。
  const order = allOrdersLocal.find(o => o.id == id)
  const shouldSaveCarrierTag = ['0', '1', '2'].includes(shippingMethod.value) && carrier !== ''
  if (shouldSaveCarrierTag) {
    try {
      await request({
        url: '/carrier_tags',
        method: 'POST',
        data: { tag: carrier }
      })
    } catch (e) {
      console.error('保存标签失败', e)
    }
  }

  const isAccountOrder = Boolean(
    String(order?.order_number || '').trim() &&
    Array.isArray(order?.order_goods) &&
    order.order_goods.length > 0
  )

  // 新结构销售订单先保存物流，再通过独立审核请求生成客户账户流水。
  // 旧结构订单保留原来的审核状态写入方式。
  try {
    const logisticsPayload = {
      status: 'shipped',
      audit_state: isAccountOrder ? 0 : 1,
      shipping_method: Number(shippingMethod.value),
      shipping_custom: shippingMethod.value === '4' ? shippingCustom.value.trim() : '',
      logistics_no: finalLogisticsNo,
      freight_costs: freightData
    }

    await request({
      url: `/orders/${id}`,
      method: 'PUT',
      data: logisticsPayload
    })

    if (isAccountOrder) {
      await request({
        url: `/orders/${id}`,
        method: 'PUT',
        data: { audit_state: 1 }
      })
    }

    showMessage(
      isAccountOrder ? '物流信息已保存，订单审核入账成功！' : '物流信息录入成功！',
      'success'
    )
    closeShippedActionModal()
    emit('refresh')
  } catch (e) {
    showMessage(
      e?.response?.data?.message || '网络通信异常，未能成功完成审核',
      'error'
    )
  }
}

// 3. 修改物流和运费信息
const submitEditShipOrder = async () => {
  const id = targetOrderId.value

  const carrier = carrierName.value.trim()
  const no = logisticsNo.value.trim()

  let finalLogisticsNo = ''
  const shouldPersistCarrier = !['3', '4'].includes(shippingMethod.value)
  if (carrier && no && shouldPersistCarrier) {
    finalLogisticsNo = `${carrier}-${no}`
  } else if (no) {
    finalLogisticsNo = no
  } else {
    finalLogisticsNo = '无单号记录'
  }

  // 构建运费数据数组
  const freightData = []

  // 添加运费项
  if (freightCost.value && Number(freightCost.value) > 0) {
    freightData.push({
      type: 'freight',
      note: '运费',
      amount: Number(freightCost.value)
    })
  }

  // 添加其它费用项
  otherCosts.value.forEach(item => {
    if (item.amount && Number(item.amount) > 0) {
      freightData.push({
        type: 'other',
        note: item.note.trim() || '其它费用',
        amount: Number(item.amount)
      })
    }
  })

  const isEntryMode = currentMode.value === 'entry'
  const payload = {
    shipping_method: Number(shippingMethod.value),
    shipping_custom: shippingMethod.value === '4' ? shippingCustom.value.trim() : '',
    logistics_no: finalLogisticsNo,
    freight_costs: freightData
  }
  if (isEntryMode) {
    payload.status = 'shipped'
  }

  // 提交给后端
  try {
    await request({
      url: `/orders/${id}`,
      method: 'PUT',
      data: payload
    })

    if (['0', '1', '2'].includes(shippingMethod.value) && carrier) {
      try {
        await request({
          url: '/carrier_tags',
          method: 'POST',
          data: { tag: carrier }
        })
      } catch (error) {
        console.error('保存承运商快捷标签失败:', error)
      }
    }

    const actionText = isEntryMode ? '录入' : '修改'
    showMessage(`物流与运费信息${actionText}成功！`, 'success')
    closeShippedActionModal()
    emit('refresh')
  } catch (e) {
    showMessage('网络通信异常，未能成功修改', 'error')
  }
}

// 触发文件选择
const triggerFileInput = () => {
  const input = document.getElementById('receiptImageInput')
  if (input) input.click()
}

// 拖拽上传处理
const handleDragEnter = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#e9f8f3'
    receiptContent.style.border = '2px dashed #0f9f78'
  }
}

const handleDragOver = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#e9f8f3'
    receiptContent.style.border = '2px dashed #0f9f78'
  }
}

const handleDragLeave = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#ffffff'
    receiptContent.style.border = '1px dashed #a9e5d2'
  }
}

const handleDrop = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#ffffff'
    receiptContent.style.border = '1px dashed #a9e5d2'
  }

  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = function(e) {
      document.getElementById('receiptUploadPrompt').style.display = 'none'
      const preview = document.getElementById('receiptImagePreview')

      currentReceiptRotation = 0

      originalReceiptImg.onload = function() {
        preview.src = e.target.result
        preview.style.display = 'block'

        const rotateBtn = document.getElementById('receiptRotateBtn')
        if (rotateBtn) rotateBtn.style.display = 'flex'
      }
      originalReceiptImg.src = e.target.result
    }
    reader.readAsDataURL(file)
  } else if (file) {
    showMessage('请选择有效的图片文件（如 JPG、PNG）', 'error')
  }
}

// 3. 回单图片选择与本地预览
const previewReceiptImage = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = function(e) {
      document.getElementById('receiptUploadPrompt').style.display = 'none'
      const preview = document.getElementById('receiptImagePreview')

      currentReceiptRotation = 0

      originalReceiptImg.onload = function() {
        preview.src = e.target.result
        preview.style.display = 'block'

        const rotateBtn = document.getElementById('receiptRotateBtn')
        if (rotateBtn) rotateBtn.style.display = 'flex'
      }
      originalReceiptImg.src = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// 上传图片
const submitReceiptImage = async () => {
  const id = targetOrderId.value
  const preview = document.getElementById('receiptImagePreview')

  if (!preview || !preview.src || preview.style.display === 'none') {
    showMessage('请先选择一张回单图片', 'error')
    return
  }

  function dataURItoFile(dataURI, filename) {
    const arr = dataURI.split(',')
    const mime = arr[0].match(/:(.*?);/)[1]
    const bstr = atob(arr[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n)
    }
    return new File([u8arr], filename, { type: mime })
  }

  let fileToUpload
  try {
    fileToUpload = dataURItoFile(preview.src, `receipt_${Date.now()}.jpg`)
  } catch (error) {
    showMessage('图片解析失败，请重新选择图片', 'error')
    return
  }

  const formData = new FormData()
  formData.append('receipt_image', fileToUpload)

  try {
    const response = await fetch(`/api/orders/${id}/upload_receipt`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      showMessage('图片上传成功！', 'success')
      closeShippedActionModal()
      emit('refresh')
    } else {
      showMessage('上传失败，请检查网络或后端接口', 'error')
    }
  } catch (e) {
    console.error('上传错误:', e)
    showMessage('网络通信异常！', 'error')
  }
}

// 删除按钮
const deleteRealReceiptImage = () => {
  deleteConfirmVisible.value = true
}

const confirmDeleteReceiptImage = async () => {
  const id = targetOrderId.value

  try {
    const res = await request({
      url: `/orders/${id}/receipt`,
      method: 'DELETE'
    })
    if (res.success) {
      showMessage('回单图片已彻底删除！', 'success')
      closeShippedActionModal()
      emit('refresh')
    } else {
      showMessage(res.message || '删除失败', 'error')
    }
  } catch (e) {
    console.error(e)
    showMessage('网络错误，删除失败', 'error')
  }
}

// 下载按钮
const downloadReceiptImage = () => {
  const preview = document.getElementById('receiptImagePreview')
  if (!preview || !preview.src) {
    showMessage('当前没有可下载的回单图片', 'error')
    return
  }
  const a = document.createElement('a')
  a.href = preview.src
  a.download = `发货回单_${Date.now()}.jpg`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// 旋转图片
const rotateReceiptImage = (e) => {
  if (e) {
    e.stopPropagation()
    e.preventDefault()
  }

  currentReceiptRotation = (currentReceiptRotation + 90) % 360

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const img = originalReceiptImg

  if (currentReceiptRotation === 90 || currentReceiptRotation === 270) {
    canvas.width = img.height
    canvas.height = img.width
  } else {
    canvas.width = img.width
    canvas.height = img.height
  }

  ctx.translate(canvas.width / 2, canvas.height / 2)
  ctx.rotate((currentReceiptRotation * Math.PI) / 180)
  ctx.drawImage(img, -img.width / 2, -img.height / 2)

  const preview = document.getElementById('receiptImagePreview')
  if (preview) {
    preview.src = canvas.toDataURL('image/jpeg', 0.95)
  }
}

// 打开大图预览
const openLargeImagePreview = () => {
  const preview = document.getElementById('receiptImagePreview')
  if (preview && preview.src) {
    largePreviewSrc.value = preview.src
    showLargePreview.value = true
  }
}

// 关闭大图预览
const closeLargePreview = () => {
  showLargePreview.value = false
}

// 暴露方法
defineExpose({
  open
})

// 监听来自UnifiedOrderList的编辑事件
const handleEditEvent = (event) => {
  const { orderId, mode } = event.detail
  open(orderId, mode)
}

onMounted(() => {
  window.addEventListener('open-shipped-action-modal', handleEditEvent)
})

onUnmounted(() => {
  window.removeEventListener('open-shipped-action-modal', handleEditEvent)
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
.modal-overlay {
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
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  box-sizing: border-box;
}

.action-modal {
  display: flex;
  width: min(680px, calc(100vw - 48px));
  max-height: min(880px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  background: var(--page-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.2);
  box-sizing: border-box;
  font-size: 14px;
  animation: none !important;
}

.action-modal.is-dragging {
  box-shadow: 0 24px 58px rgba(15, 23, 42, 0.28);
}

.modal-header {
  display: flex;
  min-height: 78px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px 14px 18px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
  cursor: grab;
  user-select: none;
}

.modal-header:active {
  cursor: grabbing;
}

.modal-heading {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.modal-heading-icon {
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

.modal-heading-icon svg,
.modal-close-button svg,
.text-action svg,
.remove-cost-button svg,
.upload-icon svg,
.receipt-rotate-button svg,
.large-preview-close svg,
.page-notice svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.modal-heading-icon svg {
  width: 22px;
  height: 22px;
}

.modal-heading-copy {
  min-width: 0;
}

.modal-eyebrow {
  display: block;
  margin-bottom: 2px;
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.modal-heading-copy h2 {
  margin: 0;
  color: var(--text);
  font-size: 18px;
  font-weight: 650;
  line-height: 1.3;
}

.modal-heading-copy p {
  margin: 3px 0 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-close-button {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.modal-close-button:hover {
  color: var(--text);
  background: #f8fafc;
  border-color: var(--border);
}

.modal-close-button svg {
  width: 19px;
  height: 19px;
}

.action-modal-body {
  display: grid;
  min-height: 0;
  flex: 1 1 auto;
  gap: 14px;
  padding: 16px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.content-card {
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.card-header {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 11px 15px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.card-header.compact {
  min-height: 54px;
}

.card-header h3 {
  margin: 0;
  color: var(--text);
  font-size: 14px;
  font-weight: 650;
  line-height: 1.4;
}

.card-header p {
  margin: 2px 0 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.4;
}

.card-body {
  padding: 15px;
}

.summary-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-item {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  gap: 7px;
  padding: 0 11px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
}

.summary-item span,
.form-item label {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.summary-item strong {
  overflow: hidden;
  color: var(--text);
  font-size: 14px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-item {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.form-item label {
  display: flex;
  align-items: center;
  gap: 7px;
  line-height: 1.4;
}

.custom-method-field {
  margin-top: 14px;
}

.modern-input {
  width: 100%;
  height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  outline: none;
  box-sizing: border-box;
  font: inherit;
  font-size: 13px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.modern-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.modern-input::placeholder {
  color: var(--text-muted);
}

.goods-summary {
  margin: 0;
  padding: 14px 15px;
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.carrier-tags {
  display: flex;
  min-height: 25px;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin-bottom: 14px;
}

.carrier-tags-label {
  margin-right: 2px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.carrier-tag {
  min-height: 25px;
  padding: 3px 9px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid transparent;
  border-radius: 999px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  line-height: 1.3;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.carrier-tag:hover,
.carrier-tag.active {
  background: #d8f2ea;
  border-color: var(--accent-border);
}

.optional-text {
  display: inline-flex;
  min-height: 20px;
  align-items: center;
  padding: 1px 7px;
  color: var(--text-muted);
  background: #f1f5f9;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.cost-section {
  display: grid;
  gap: 14px;
  margin-top: 16px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.freight-field {
  max-width: calc(50% - 7px);
}

.money-input {
  position: relative;
  min-width: 0;
}

.money-input > span {
  position: absolute;
  z-index: 1;
  top: 50%;
  left: 11px;
  color: var(--text-muted);
  font-size: 13px;
  transform: translateY(-50%);
  pointer-events: none;
}

.money-input .modern-input {
  padding-left: 28px;
  font-variant-numeric: tabular-nums;
}

.other-costs {
  display: grid;
  gap: 10px;
}

.field-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.field-heading > div {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 8px;
}

.field-heading strong {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-heading span,
.empty-costs {
  color: var(--text-muted);
  font-size: 12px;
}

.text-action {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  gap: 5px;
  padding: 0 9px;
  color: var(--accent-dark);
  background: var(--panel-bg);
  border: 1px solid var(--accent-border);
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  transition: background 0.18s ease;
}

.text-action:hover {
  background: var(--accent-soft);
}

.text-action svg {
  width: 15px;
  height: 15px;
}

.cost-list {
  display: grid;
  gap: 8px;
}

.cost-row {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(130px, 0.8fr) 38px;
  gap: 8px;
}

.remove-cost-button {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #b4232f;
  background: #fff;
  border: 1px solid #fecdd3;
  border-radius: 5px;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.remove-cost-button:hover {
  color: #fff;
  background: #ef4444;
  border-color: #ef4444;
}

.remove-cost-button svg {
  width: 17px;
  height: 17px;
}

.empty-costs {
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px dashed var(--border-strong);
  border-radius: 5px;
  text-align: center;
}

.total-strip {
  display: flex;
  min-height: 60px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
  box-sizing: border-box;
}

.total-strip > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.total-strip span {
  color: var(--text);
  font-size: 13px;
  font-weight: 650;
}

.total-strip small {
  color: var(--text-muted);
  font-size: 11px;
}

.total-strip strong {
  color: var(--accent-dark);
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.file-type-label {
  display: inline-flex;
  min-height: 25px;
  align-items: center;
  padding: 3px 9px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.receipt-card-body {
  padding: 15px;
}

.receipt-uploader {
  position: relative;
  width: 100%;
  height: 280px;
  overflow: hidden;
  background: #fff;
  border: 1px dashed var(--accent-border);
  border-radius: 7px;
  box-sizing: border-box;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.receipt-upload-prompt {
  position: absolute;
  inset: 0;
  display: flex;
  width: 100%;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 20px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  cursor: pointer;
}

.receipt-upload-prompt:hover {
  background: var(--accent-soft);
}

.receipt-upload-prompt strong {
  color: var(--text);
  font-size: 14px;
  font-weight: 650;
}

.receipt-upload-prompt > span:last-child {
  color: var(--text-muted);
  font-size: 12px;
}

.upload-icon {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  margin-bottom: 3px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 50%;
}

.upload-icon svg {
  width: 22px;
  height: 22px;
}

.receipt-image-preview {
  position: absolute;
  inset: 0;
  display: none;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f8fafc;
  cursor: zoom-in;
}

.receipt-rotate-button {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 2;
  display: none;
  width: 52px;
  height: 52px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--accent-dark);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.96);
  border-radius: 50%;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: background 0.18s ease, transform 0.18s ease;
}

.receipt-rotate-button:hover {
  background: #fff;
  transform: translate(-50%, -50%) scale(1.06);
}

.receipt-rotate-button svg {
  width: 25px;
  height: 25px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.action-modal-footer {
  display: flex;
  min-height: 68px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  background: var(--panel-bg);
  border-top: 1px solid var(--border);
  box-sizing: border-box;
}

.footer-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 96px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease,
    box-shadow 0.18s ease, transform 0.18s ease;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.button-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.22);
  transform: translateY(-1px);
}

.button-secondary {
  color: var(--text-secondary);
  background: var(--panel-bg);
  border-color: var(--border-strong);
}

.button-secondary:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-danger {
  color: #fff;
  background: #ef4444;
  border-color: #ef4444;
}

.button-danger:hover {
  background: #dc2626;
  border-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.22);
  transform: translateY(-1px);
}

button:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.large-preview {
  position: fixed;
  inset: 0;
  z-index: 100001;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.92);
  box-sizing: border-box;
  cursor: zoom-out;
}

.large-preview img {
  max-width: 92%;
  max-height: 92%;
  object-fit: contain;
  cursor: default;
}

.large-preview-close {
  position: absolute;
  top: 20px;
  right: 20px;
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 5px;
  cursor: pointer;
}

.large-preview-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.large-preview-close svg {
  width: 20px;
  height: 20px;
}

.page-notice {
  position: fixed;
  top: 24px;
  left: 50%;
  z-index: 100002;
  display: flex;
  min-width: 0;
  max-width: min(520px, calc(100vw - 32px));
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 10px 16px;
  color: #172033;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  transform: translateX(-50%);
  box-sizing: border-box;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.page-notice svg {
  width: 19px;
  height: 19px;
  flex: 0 0 19px;
}

.notice-success svg {
  color: #0f9f78;
}

.notice-error svg {
  color: #dc3545;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
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

@media (max-width: 780px) {
  .modal-overlay {
    padding: 16px;
  }

  .action-modal {
    width: calc(100vw - 32px);
    max-height: calc(100vh - 32px);
  }

  .modal-header {
    padding-right: 12px;
    padding-left: 14px;
  }

  .modal-heading-copy p {
    white-space: normal;
  }

  .action-modal-body {
    padding: 12px;
  }

  .summary-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .summary-item {
    min-height: 60px;
  }

  .freight-field {
    max-width: none;
  }

  .cost-row {
    grid-template-columns: minmax(0, 1fr) 38px;
  }

  .cost-row > .money-input {
    grid-column: 1;
  }

  .cost-row > .remove-cost-button {
    grid-row: 1 / span 2;
    grid-column: 2;
    align-self: center;
  }

  .receipt-uploader {
    height: 230px;
  }

  .action-modal-footer {
    align-items: stretch;
    flex-direction: column-reverse;
  }

  .footer-actions,
  .action-modal-footer > .button {
    width: 100%;
  }

  .footer-actions .button {
    min-width: 0;
    flex: 1 1 120px;
  }

  .page-notice {
    top: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .modal-fade-enter-active,
  .modal-fade-leave-active,
  .notice-enter-active,
  .notice-leave-active {
    transition: none;
  }
}
</style>
