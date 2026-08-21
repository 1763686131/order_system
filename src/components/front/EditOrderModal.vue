<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="editOrderModal"
      class="old-modal-mask"
    >
      <div class="old-modal-box" style="max-width: 880px; width: 92%;">
        <div class="old-modal-header">
          <span>修改订单信息</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body order-modal-body" style="padding: 20px; display: flex; gap: 24px;">
          <!-- 左侧面板 -->
          <div class="order-modal-left" style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1.2;">
                <label for="editOrderDate" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block; font-size: 13px;">创建生成时间:</label>
                <input v-model="formData.date" id="editOrderDate" type="text" style="width: 100%; background: #f5f5f5; color: #888; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px;" readonly />
              </div>
              <div class="form-item" style="flex: 1;">
                <label for="editOrderType" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block; font-size: 13px;">订单类型参数:</label>
                <select v-model="formData.type" id="editOrderType" style="width: 100%; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px;">
                  <option :value="0">中固订单</option>
                  <option :value="1">绝缘订单</option>
                </select>
              </div>
            </div>

            <div class="form-item" style="flex: 1; display: flex; flex-direction: column;">
              <label for="editOrderTitle" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">文本粘贴区:</label>
              <textarea
                v-model="pasteText"
                id="editOrderTitle"
                class="textarea-tall"
                style="background:#f9f9f9; flex: 1; min-height: 200px; padding: 12px; border: 1px solid #d9d9d9; border-radius: 6px; resize: none; font-size: 14px; line-height: 1.5;"
                placeholder="重新粘贴规范文本重算右侧数据..."
              ></textarea>
            </div>

            <button
              type="button"
              class="btn-success"
              style="width: 100%; font-size: 15px; padding: 12px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; box-shadow: 0 4px 12px rgba(82,196,26,0.25);"
              @click="smartParse"
            >
              ⚡ 一键重新提取并填充右侧表单
            </button>
          </div>

          <!-- 右侧面板 -->
          <div class="order-modal-right" style="flex: 1.2; background: #f9fafc; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">制单归属:</label>
                <input v-model="formData.order_client" id="editOrderClient" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">收货姓名:</label>
                <input v-model="formData.receiver_name" id="editReceiverName" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货电话:</label>
              <input v-model="formData.receiver_phone" id="editReceiverPhone" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货地址:</label>
              <input v-model="formData.receiver_address" id="editReceiverAddress" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物名称:</label>
              <textarea v-model="formData.goods_name" id="editGoodsName" style="height:48px; width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px; resize: none;"></textarea>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物重量:</label>
                <input v-model="formData.goods_weight" id="editGoodsWeight" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物数量:</label>
                <input v-model="formData.goods_quantity" id="editGoodsQuantity" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物包装:</label>
                <select v-model="formData.goods_packaging" id="editGoodsPackaging" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="桶装">桶装</option>
                  <option value="袋装">袋装</option>
                  <option value="托盘">托盘</option>
                  <option value="纸箱">纸箱</option>
                </select>
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">物流服务:</label>
                <select v-model="formData.logistics_service" id="editLogisticsService" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="送货上门+回单拍照回传">送货上门+回单拍照回传</option>
                  <option value="送货上门+回单邮回">送货上门+回单邮回</option>
                  <option value="送货上门">送货上门</option>
                  <option value="用户自提">用户自提</option>
                </select>
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;">附加备注信息:</label>
              <input v-model="formData.remark" id="editOrderRemark" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>
          </div>
        </div>

        <div class="old-modal-footer">
          <button
            v-if="userStore.hasPerm('pending.delete') || userStore.hasPerm('completed.delete')"
            id="btnDeleteOrderInEdit"
            class="btn-danger"
            @click="handleDelete"
          >
            删除订单
          </button>
          <button type="button" class="btn-calc" @click="toggleCalculator">辅助计算</button>
          <button class="btn-default" @click="handleClose">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="loading">{{ loading ? '保存中...' : '确认修改' }}</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()

const userStore = useUserStore()
const orderStore = useOrderStore()

const visible = ref(false)
const loading = ref(false)
const targetOrderId = ref(null)
const pasteText = ref('')

const formData = ref({
  date: '',
  type: 0,
  title: '',
  order_client: '',
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  goods_name: '',
  goods_weight: '',
  goods_quantity: '',
  goods_packaging: '桶装',
  logistics_service: '送货上门+回单拍照回传',
  remark: ''
})

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

// 打开弹窗
const open = (orderId) => {
  const order = orderStore.allOrders.find(o => o.id === orderId)
  if (!order) return

  targetOrderId.value = orderId
  formData.value = {
    date: order.date || '',
    type: order.type !== undefined ? order.type : 0,
    title: order.title || '',
    order_client: order.order_client || '',
    receiver_name: order.receiver_name || '',
    receiver_phone: order.receiver_phone || '',
    receiver_address: order.receiver_address || '',
    goods_name: order.goods_name || '',
    goods_weight: order.goods_weight || '',
    goods_quantity: order.goods_quantity || '',
    goods_packaging: order.goods_packaging || '桶装',
    logistics_service: order.logistics_service || '送货上门+回单拍照回传',
    remark: order.remark || ''
  }
  pasteText.value = ''

  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 提交修改
const handleSubmit = async () => {
  const payload = {
    title: formData.value.title,
    type: formData.value.type,
    date: formData.value.date,
    order_client: formData.value.order_client.trim(),
    receiver_name: formData.value.receiver_name.trim(),
    receiver_phone: formData.value.receiver_phone.trim(),
    receiver_address: formData.value.receiver_address.trim(),
    goods_name: formData.value.goods_name.trim(),
    goods_weight: formData.value.goods_weight.trim(),
    goods_quantity: formData.value.goods_quantity.trim(),
    goods_packaging: formData.value.goods_packaging,
    logistics_service: formData.value.logistics_service,
    remark: formData.value.remark.trim()
  }

  const errMsg = validatePayload(payload)
  if (errMsg) {
    return alert('修改失败：' + errMsg)
  }

  loading.value = true

  try {
    await orderStore.updateOrderById(targetOrderId.value, payload)
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('修改订单失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 删除订单
const handleDelete = async () => {
  if (!confirm('安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！')) {
    return
  }

  try {
    await orderStore.deleteOrderById(targetOrderId.value)
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('物理删除请求异常')
  }
}

// 暴露方法
defineExpose({
  open
})
</script>

<style scoped>
/* 样式已在全局 CSS 中定义 */
</style>
