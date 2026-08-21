<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="createOrderModal"
      class="old-modal-mask"
    >
      <div class="old-modal-box" style="max-width: 880px; width: 92%;">
        <div class="old-modal-header">
          <span>发布系统新订单</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body order-modal-body" style="padding: 20px; display: flex; gap: 24px;">
          <!-- 左侧面板 -->
          <div class="order-modal-left" style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
            <div class="form-item">
              <label for="newOrderType" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">订单类型参数:</label>
              <select v-model="formData.type" id="newOrderType" style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;">
                <option :value="0">中固订单</option>
                <option :value="1">绝缘订单</option>
              </select>
            </div>

            <div class="form-item" style="flex: 1; display: flex; flex-direction: column;">
              <label for="newOrderTitle" style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">文本粘贴区 (请按格式粘贴):</label>
              <textarea
                v-model="pasteText"
                id="newOrderTitle"
                class="textarea-tall"
                style="background:#f9f9f9; flex: 1; min-height: 220px; padding: 12px; border: 1px solid #d9d9d9; border-radius: 6px; resize: none; font-size: 14px; line-height: 1.5;"
                placeholder="第一行: 客户名&#10;第二行: 收货人 电话 地址&#10;第三行起: 货物规格"
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
          </div>

          <!-- 右侧面板 -->
          <div class="order-modal-right" style="flex: 1.2; background: #f9fafc; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">制单归属 (如: 陶芸):</label>
                <input v-model="formData.order_client" id="newOrderClient" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">收货姓名:</label>
                <input v-model="formData.receiver_name" id="newReceiverName" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货电话:</label>
              <input v-model="formData.receiver_phone" id="newReceiverPhone" placeholder="11位手机或座机" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货地址:</label>
              <input v-model="formData.receiver_address" id="newReceiverAddress" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物名称:</label>
              <textarea v-model="formData.goods_name" id="newGoodsName" style="height:48px; width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px; resize: none;"></textarea>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物重量:</label>
                <input v-model="formData.goods_weight" id="newGoodsWeight" placeholder="自动计算或手填" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物数量:</label>
                <input v-model="formData.goods_quantity" id="newGoodsQuantity" placeholder="例如: 56件" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物包装:</label>
                <select v-model="formData.goods_packaging" id="newGoodsPackaging" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="桶装">桶装</option>
                  <option value="袋装">袋装</option>
                  <option value="托盘">托盘</option>
                  <option value="纸箱">纸箱</option>
                </select>
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">物流服务:</label>
                <select v-model="formData.logistics_service" id="newLogisticsService" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;">
                  <option value="送货上门+回单拍照回传">送货上门+回单拍照回传</option>
                  <option value="送货上门+回单邮回">送货上门+回单邮回</option>
                  <option value="送货上门">送货上门</option>
                  <option value="用户自提">用户自提</option>
                </select>
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;">附加备注信息:</label>
              <input v-model="formData.remark" id="newOrderRemark" placeholder="选填，例如：加急、替换等..." style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>
          </div>
        </div>

        <div class="old-modal-footer">
          <button type="button" class="btn-calc" @click="toggleCalculator">辅助计算</button>
          <button class="btn-default" @click="handleClose">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="loading">{{ loading ? '提交中...' : '上传并发布订单' }}</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()

const visible = ref(false)
const loading = ref(false)
const pasteText = ref('')

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
  remark: ''
})

// 获取当前日期
const getCurrentDate = () => {
  const now = new Date()
  const Y = now.getFullYear()
  const M = String(now.getMonth() + 1).padStart(2, '0')
  const D = String(now.getDate()).padStart(2, '0')
  return `${Y}-${M}-${D}`
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

// 打开弹窗
const open = () => {
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
    remark: ''
  }
  pasteText.value = ''
  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 提交订单
const handleSubmit = async () => {
  const payload = {
    date: getCurrentDate(),
    title: '',
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
    remark: formData.value.remark.trim()
  }

  const errMsg = validatePayload(payload)
  if (errMsg) {
    return alert('发单失败：' + errMsg)
  }

  loading.value = true

  try {
    await orderStore.createOrder(payload)
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
    window.dispatchEvent(new CustomEvent('switch-tab', { detail: { index: 0 } }))
  } catch (error) {
    alert('新建订单失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 暴露方法
defineExpose({
  open
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('open-create-order-modal', () => {
    open()
  })
})
</script>

<style scoped>
/* 样式已在全局 CSS 中定义 */
</style>
