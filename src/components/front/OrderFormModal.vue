<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="old-modal-mask"
    >
      <div class="old-modal-box" style="max-width: 880px; width: 92%;">
        <div class="old-modal-header">
          <span>{{ isEditMode ? '编辑订单信息' : '发布系统新订单' }}</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body order-modal-body" style="padding: 20px; display: flex; gap: 24px;">
          <!-- 左侧面板 -->
          <div class="order-modal-left" style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
            <div class="form-item">
              <label for="orderType" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">订单类型参数:</label>
              <select v-model="formData.type" id="orderType" style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;">
                <option :value="0">中固订单</option>
                <option :value="1">绝缘订单</option>
              </select>
            </div>

            <div class="form-item" style="flex: 1; display: flex; flex-direction: column;">
              <label for="pasteArea" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">
                文本粘贴区 (请按格式粘贴):
                <span v-if="calculatedSum" style="color: #52c41a; font-size: 13px; margin-left: 12px;">
                  📊 自动计算结果: {{ calculatedSum }}
                </span>
              </label>
              <textarea
                v-model="pasteText"
                id="pasteArea"
                class="textarea-tall"
                style="background:#f9f9f9; flex: 1; min-height: 320px; padding: 12px; border: 1px solid #d9d9d9; border-radius: 6px; resize: vertical; font-size: 14px; line-height: 1.5;"
                placeholder="第一行: 客户名&#10;第二行: 收货人 电话 地址&#10;第三行起: 货物规格&#10;支持自动计算：例如 10+20*3 会自动计算为 70"
              ></textarea>
            </div>

            <button
              type="button"
              class="btn-success"
              style="width: 100%; font-size: 15px; padding: 12px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; box-shadow: 0 4px 12px rgba(82,196,26,0.25);"
              @click="smartParse"
            >
              ⚡ 一键智能识别并填充右侧表单
            </button>

            <!-- 订单基础信息（编辑模式） -->
            <div v-if="isEditMode" style="padding: 12px 16px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px;">
              <div style="font-size: 13px; color: #0369a1; line-height: 1.8;">
                <div><strong>订单ID:</strong> {{ currentOrderId }}</div>
                <div><strong>创建日期:</strong> {{ formData.date || '未知' }}</div>
                <div><strong>当前状态:</strong> {{ getStatusText(formData.status) }}</div>
              </div>
            </div>
          </div>

          <!-- 右侧面板 -->
          <div class="order-modal-right" style="flex: 1.2; background: #f9fafc; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">制单归属 (如: 陶芸):</label>
                <input v-model="formData.order_client" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">收货姓名:</label>
                <input v-model="formData.receiver_name" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货电话:</label>
              <input v-model="formData.receiver_phone" placeholder="11位手机或座机" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货地址:</label>
              <input v-model="formData.receiver_address" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物名称:</label>
              <textarea v-model="formData.goods_name" style="height:48px; width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px; resize: none;"></textarea>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物重量:</label>
                <input v-model="formData.goods_weight" placeholder="自动计算或手填" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物数量:</label>
                <input v-model="formData.goods_quantity" placeholder="例如: 56件" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物包装:</label>
                <select v-model="formData.goods_packaging" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="桶装">桶装</option>
                  <option value="袋装">袋装</option>
                  <option value="托盘">托盘</option>
                  <option value="纸箱">纸箱</option>
                </select>
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">物流服务:</label>
                <select v-model="formData.logistics_service" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="送货上门+回单拍照回传">送货上门+回单拍照回传</option>
                  <option value="送货上门+回单邮回">送货上门+回单邮回</option>
                  <option value="送货上门">送货上门</option>
                  <option value="用户自提">用户自提</option>
                </select>
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;">附加备注信息:</label>
              <input v-model="formData.remark" placeholder="选填，例如：加急、替换等..." style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>
          </div>
        </div>

        <div class="old-modal-footer">
          <button type="button" class="btn-calc" @click="toggleCalculator">辅助计算</button>
          <button v-if="isEditMode" type="button" class="btn-danger" @click="handleDelete">删除订单</button>
          <button class="btn-default" @click="handleClose">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="loading">
            {{ loading ? '提交中...' : (isEditMode ? '保存修改' : '上传并发布订单') }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()

const visible = ref(false)
const loading = ref(false)
const pasteText = ref('')
const isEditMode = ref(false)
const currentOrderId = ref(null)

const formData = ref({
  type: 0,
  order_client: '',
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  goods_name: '',
  goods_weight: '',
  goods_quantity: '',
  goods_packaging: '桶装',
  logistics_service: '送货上门+回单拍照回传',
  remark: '',
  date: '',
  status: 'pending',
  title: ''
})

// 计算文本粘贴区中的数学表达式
const calculatedSum = computed(() => {
  if (!pasteText.value) return ''

  // 匹配所有包含数学运算的行
  const lines = pasteText.value.split('\n')
  const results = []

  for (const line of lines) {
    // 匹配数学表达式（支持 +、-、*、/）
    const mathMatch = line.match(/[\d.]+[\s]*[+\-*/][\s]*[\d.]+/)
    if (mathMatch) {
      try {
        // 安全计算表达式
        const expr = line.match(/([\d.+\-*/\s()]+)/)?.[0]
        if (expr) {
          const result = Function('"use strict"; return (' + expr + ')')()
          if (!isNaN(result) && isFinite(result)) {
            results.push(`${expr.trim()} = ${result}`)
          }
        }
      } catch (e) {
        // 忽略计算错误
      }
    }
  }

  return results.length > 0 ? results.join(' | ') : ''
})

// 获取当前日期
const getCurrentDate = () => {
  const now = new Date()
  const Y = now.getFullYear()
  const M = String(now.getMonth() + 1).padStart(2, '0')
  const D = String(now.getDate()).padStart(2, '0')
  return `${Y}-${M}-${D}`
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '未完成',
    'completed': '已完成',
    'shipped': '已出库'
  }
  return statusMap[status] || status
}

// 智能解析
const smartParse = () => {
  const text = pasteText.value.trim()
  if (!text) return

  const lines = text.split('\n').map(l => l.trim()).filter(l => l)

  if (lines.length === 0) return

  // 第一行：客户名
  if (lines[0]) {
    formData.value.order_client = lines[0]
  }

  // 第二行：收货人 电话 地址
  if (lines[1]) {
    const parts = lines[1].split(/\s+/)
    if (parts.length >= 1) formData.value.receiver_name = parts[0]
    if (parts.length >= 2) formData.value.receiver_phone = parts[1]
    if (parts.length >= 3) formData.value.receiver_address = parts.slice(2).join(' ')
  }

  // 第三行起：货物规格
  if (lines.length > 2) {
    formData.value.goods_name = lines.slice(2).join('\n')
  }
}

// 切换计算器
const toggleCalculator = () => {
  window.dispatchEvent(new CustomEvent('toggle-calculator'))
}

// 验证表单
const validatePayload = (payload) => {
  if (!payload.order_client || payload.order_client.trim() === '') return '订单归属不能为空'
  if (!payload.goods_name || payload.goods_name.trim() === '') return '货物名称不能为空'
  return null
}

// 打开弹窗 - 新增模式
const open = () => {
  isEditMode.value = false
  currentOrderId.value = null
  formData.value = {
    type: 0,
    order_client: '',
    receiver_name: '',
    receiver_phone: '',
    receiver_address: '',
    goods_name: '',
    goods_weight: '',
    goods_quantity: '',
    goods_packaging: '桶装',
    logistics_service: '送货上门+回单拍照回传',
    remark: '',
    date: '',
    status: 'pending'
  }
  pasteText.value = ''
  visible.value = true
}

// 打开弹窗 - 编辑模式
const openEdit = (orderId) => {
  const order = orderStore.allOrders.find(o => o.id === orderId)
  if (!order) {
    alert('订单不存在')
    return
  }

  isEditMode.value = true
  currentOrderId.value = orderId
  formData.value = {
    type: order.type || 0,
    order_client: order.order_client || '',
    receiver_name: order.receiver_name || '',
    receiver_phone: order.receiver_phone || '',
    receiver_address: order.receiver_address || '',
    goods_name: order.goods_name || '',
    goods_weight: order.goods_weight || '',
    goods_quantity: order.goods_quantity || '',
    goods_packaging: order.goods_packaging || '桶装',
    logistics_service: order.logistics_service || '送货上门+回单拍照回传',
    remark: order.remark || '',
    date: order.date || '',
    status: order.status || 'pending',
    title: order.title || ''
  }
  // 编辑模式下，从 title 加载文本粘贴区内容
  pasteText.value = order.title || ''
  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 提交订单
const handleSubmit = async () => {
  const payload = {
    type: formData.value.type,
    order_client: formData.value.order_client.trim(),
    receiver_name: formData.value.receiver_name.trim(),
    receiver_phone: formData.value.receiver_phone.trim(),
    receiver_address: formData.value.receiver_address.trim(),
    goods_name: formData.value.goods_name.trim(),
    goods_weight: formData.value.goods_weight.trim(),
    goods_quantity: formData.value.goods_quantity.trim(),
    goods_packaging: formData.value.goods_packaging,
    logistics_service: formData.value.logistics_service,
    remark: formData.value.remark.trim(),
    title: pasteText.value.trim()  // 保存文本粘贴区内容到 title
  }

  // 新增模式需要添加日期
  if (!isEditMode.value) {
    payload.date = getCurrentDate()
  }

  const errMsg = validatePayload(payload)
  if (errMsg) {
    return alert('提交失败：' + errMsg)
  }

  loading.value = true

  try {
    if (isEditMode.value) {
      // 编辑模式
      await orderStore.updateOrderById(currentOrderId.value, payload)
      alert('订单更新成功！')
    } else {
      // 新增模式
      await orderStore.createOrder(payload)
      window.dispatchEvent(new CustomEvent('switch-tab', { detail: { index: 0 } }))
    }

    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert(isEditMode.value ? '更新订单失败，请检查网络连接' : '新建订单失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 删除订单
const handleDelete = async () => {
  if (!confirm('确定要删除这条订单记录吗？此操作无法撤销！')) {
    return
  }

  try {
    await orderStore.deleteOrderById(currentOrderId.value)
    alert('订单已删除')
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('删除失败，请检查网络连接')
  }
}

// 暴露方法
defineExpose({
  open,
  openEdit
})
</script>

<style scoped>
/* 弹窗遮罩层 */
.old-modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 9998;
  display: flex;
  justify-content: center;
  align-items: center;
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

/* 弹窗容器 */
.old-modal-box {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: slideIn 0.3s ease;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 弹窗头部 */
.old-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #1890ff;
  color: white;
  font-size: 18px;
  font-weight: bold;
}

.old-close-x {
  font-size: 28px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.old-close-x:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(90deg);
}

/* 弹窗内容区 */
.old-modal-body {
  overflow-y: auto;
  flex: 1;
}

/* 表单项 */
.form-item {
  display: flex;
  flex-direction: column;
}

.form-item label {
  font-size: 13px;
  color: #666;
  font-weight: bold;
  margin-bottom: 4px;
}

.form-item input,
.form-item select,
.form-item textarea {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-item input:focus,
.form-item select:focus,
.form-item textarea:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

/* 文本域 */
textarea {
  resize: vertical;
  min-height: 48px;
  max-height: 180px;
  overflow-y: auto;
}

/* 弹窗底部 */
.old-modal-footer {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-top: 1px solid #f0f2f5;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

/* 底部按钮统一样式 */
.old-modal-footer button {
  padding: 0 24px;
  min-width: 96px;
  height: 38px;
  border-radius: 19px;
  border: none;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  outline: none;
  box-shadow: none;
  margin: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 取消按钮 */
.btn-default {
  background: #f0f2f5;
  color: #666666;
}

.btn-default:hover {
  background: #e4e7ed;
  color: #333333;
  transform: translateY(-1px);
}

/* 主要按钮 */
.btn-primary {
  background: #1890ff;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.25);
}

.btn-primary:hover {
  background: #40a9ff;
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.35);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: #d9d9d9;
  color: #999;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-primary:disabled:hover {
  transform: none;
}

/* 删除按钮 */
.btn-danger {
  background: #fdecee;
  color: #f46e83;
  margin-right: auto;
}

.btn-danger:hover {
  background: #fbcdd1;
  transform: translateY(-1px);
}

/* 计算器按钮 */
.btn-calc {
  background: #fff7e6;
  color: #fa8c16;
}

.btn-calc:hover {
  background: #ffe7ba;
  transform: translateY(-1px);
}

/* 成功按钮 */
.btn-success {
  background: #52c41a;
  color: white;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.25);
}

.btn-success:hover {
  background: #73d13d;
  box-shadow: 0 6px 16px rgba(82, 196, 26, 0.35);
  transform: translateY(-1px);
}

/* 按钮点击效果 */
.old-modal-footer button:active {
  transform: scale(0.97);
}

/* 响应式 */
@media (max-width: 768px) {
  .old-modal-box {
    width: 95%;
    max-height: 95vh;
  }

  .order-modal-body {
    flex-direction: column;
    gap: 16px;
  }

  .order-modal-left,
  .order-modal-right {
    flex: 1;
  }

  .old-modal-footer {
    flex-wrap: wrap;
    gap: 8px;
  }

  .old-modal-footer button {
    min-width: 80px;
    padding: 0 16px;
  }
}
</style>
