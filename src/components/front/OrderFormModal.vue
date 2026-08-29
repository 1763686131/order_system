<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="old-modal-mask"
      @click.self="handleClose"
    >
      <div class="old-modal-box" style="max-width: 880px; width: 92%;">
        <div class="old-modal-header">
          <span>{{ isEditMode ? '修改订单信息' : '发布系统新订单' }}</span>
          <span class="old-close-x" @click="handleClose">&times;</span>
        </div>

        <div class="old-modal-body order-modal-body" style="padding: 20px; display: flex; gap: 24px;">
          <input v-if="isEditMode" type="hidden" :value="currentOrderId" />

          <!-- 左侧面板 -->
          <div class="order-modal-left" style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
            <!-- 编辑模式：日期+类型 -->
            <div v-if="isEditMode" style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1.2;">
                <label style="font-weight: bold; color: #333; margin-bottom: 6px; display: block; font-size: 13px;">创建生成时间:</label>
                <input
                  v-model="formData.date"
                  type="text"
                  style="width: 100%; background: #f5f5f5; color: #888; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px;"
                  readonly
                />
              </div>
              <div class="form-item" style="flex: 1;">
                <label style="font-weight: bold; color: #333; margin-bottom: 6px; display: block; font-size: 13px;">订单类型参数:</label>
                <select
                  v-model="formData.type"
                  style="width: 100%; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px;"
                >
                  <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}订单</option>
                </select>
              </div>
            </div>

            <!-- 新建模式：只有类型 -->
            <div v-if="!isEditMode" class="form-item">
              <label style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">订单类型参数:</label>
              <select
                v-model="formData.type"
                style="width: 100%; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 6px;"
              >
                <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}订单</option>
              </select>
            </div>

            <!-- 文本粘贴区 -->
            <div class="form-item" style="flex: 1; display: flex; flex-direction: column;">
              <label style="font-weight: bold; color: #333; margin-bottom: 6px; display: block;">
                {{ isEditMode ? '文本粘贴区:' : '文本粘贴区 (请按格式粘贴):' }}
              </label>
              <textarea
                v-model="pasteText"
                class="textarea-tall"
                :style="{
                  background: '#f9f9f9',
                  flex: 1,
                  minHeight: isEditMode ? '200px' : '220px',
                  padding: '12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  resize: 'none',
                  fontSize: '14px',
                  lineHeight: 1.5
                }"
                :placeholder="isEditMode ? '重新粘贴规范文本重算右侧数据...' : '第一行: 客户名\n第二行: 收货人 电话 地址\n第三行起: 货物规格'"
              ></textarea>
            </div>

            <!-- 智能识别按钮 -->
            <button
              type="button"
              class="btn-success"
              style="width: 100%; font-size: 15px; padding: 12px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; box-shadow: 0 4px 12px rgba(82,196,26,0.25);"
              @click="smartParse"
            >
              {{ isEditMode ? '⚡ 一键重新提取并填充右侧表单' : '⚡ 一键智能识别并填充右侧表单' }}
            </button>
          </div>

          <!-- 右侧面板 -->
          <div class="order-modal-right" style="flex: 1.2; background: #f9fafc; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">{{ isEditMode ? '制单归属:' : '制单归属 (如: 陶芸):' }}</label>
                <input v-model="formData.order_client" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
              <div class="form-item" style="flex: 1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">收货姓名:</label>
                <input v-model="formData.receiver_name" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货电话:</label>
              <input
                v-model="formData.receiver_phone"
                :placeholder="isEditMode ? '' : '11位手机或座机'"
                style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
              />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 收货地址:</label>
              <input v-model="formData.receiver_address" style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;" />
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物名称:</label>
              <textarea
                v-model="formData.goods_name"
                style="min-height:48px; width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px; resize: vertical;"
              ></textarea>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;"><span style="color:red;">*</span> 货物重量:</label>
                <input
                  v-model="formData.goods_weight"
                  :placeholder="isEditMode ? '' : '自动计算或手填'"
                  style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
                />
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物数量:</label>
                <input
                  v-model="formData.goods_quantity"
                  :placeholder="isEditMode ? '' : '例如: 56件'"
                  style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
                />
              </div>
            </div>

            <div style="display: flex; gap: 10px;">
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">货物包装:</label>
                <select
                  v-model="formData.goods_packaging"
                  style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
                >
                  <option value="桶装">桶装</option>
                  <option value="袋装">袋装</option>
                  <option value="托盘">托盘</option>
                  <option value="纸箱">纸箱</option>
                </select>
              </div>
              <div class="form-item" style="flex:1;">
                <label style="font-size: 13px; color: #666; font-weight: bold;">物流服务:</label>
                <select
                  v-model="formData.logistics_service"
                  style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
                >
                  <option value="送货上门+回单拍照回传">送货上门+回单拍照回传</option>
                  <option value="送货上门+回单邮回">送货上门+回单邮回</option>
                  <option value="送货上门">送货上门</option>
                  <option value="用户自提">用户自提</option>
                </select>
              </div>
            </div>

            <div class="form-item">
              <label style="font-size: 13px; color: #666; font-weight: bold;">附加备注信息:</label>
              <input
                v-model="formData.order_remark"
                :placeholder="isEditMode ? '' : '选填，例如：加急、替换等...'"
                style="width:100%; padding: 6px 10px; border:1px solid #d9d9d9; border-radius: 4px;"
              />
            </div>
          </div>
        </div>

        <!-- 底部按钮组 -->
        <div class="old-modal-footer">
          <button
            v-if="isEditMode && userStore.hasPerm('order.delete')"
            class="btn-danger"
            @click="deleteOrder"
          >
            删除订单
          </button>
          <button type="button" class="btn-calc" @click="toggleCalculator">辅助计算</button>
          <button class="btn-default" @click="handleClose">取消</button>
          <button class="btn-primary" @click="submitOrder">
            {{ isEditMode ? '确认修改' : '上传并发布订单' }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import request from '@/api/request'
import { getStores } from '@/utils/storeHelper'

const userStore = useUserStore()
const orderStore = useOrderStore()

const visible = ref(false)
const isEditMode = ref(false)
const currentOrderId = ref(null)
const pasteText = ref('')
const stores = ref([])

// 加载门店列表
onMounted(async () => {
  const allStores = await getStores()
  // 只显示状态为 active 的门店
  stores.value = allStores.filter(store => store.status === 'active')
})

const formData = ref({
  type: 0,
  date: '',
  order_client: '',
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  goods_name: '',
  goods_weight: '',
  goods_quantity: '',
  goods_packaging: '桶装',
  logistics_service: '送货上门+回单拍照回传',
  order_remark: ''
})

// 打开弹窗
const open = (order = null) => {
  if (order) {
    // 编辑模式
    isEditMode.value = true
    currentOrderId.value = order.id
    formData.value = {
      type: order.type || 0,
      date: order.date || '',
      order_client: order.order_client || '',
      receiver_name: order.receiver_name || '',
      receiver_phone: order.receiver_phone || '',
      receiver_address: order.receiver_address || '',
      goods_name: order.goods_name || '',
      goods_weight: order.goods_weight || '',
      goods_quantity: order.goods_quantity || '',
      goods_packaging: order.goods_packaging || '桶装',
      logistics_service: order.logistics_service || '送货上门+回单拍照回传',
      order_remark: order.order_remark || ''
    }
    // 使用原始存储的title内容填充粘贴区
    pasteText.value = order.title || ''
  } else {
    // 新建模式
    isEditMode.value = false
    currentOrderId.value = null
    formData.value = {
      type: 0,
      date: '',
      order_client: '',
      receiver_name: '',
      receiver_phone: '',
      receiver_address: '',
      goods_name: '',
      goods_weight: '',
      goods_quantity: '',
      goods_packaging: '桶装',
      logistics_service: '送货上门+回单拍照回传',
      order_remark: ''
    }
    pasteText.value = ''
  }
  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 智能解析
const smartParse = () => {
  const text = pasteText.value
  if (!text.trim()) {
    return alert('请先在上方输入框粘贴或填写内容，再点击识别！')
  }

  const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '')
  if (lines.length === 0) return

  // 模式1：系统标准化复制文本
  if (text.startsWith('【中固订单】') || text.startsWith('【绝缘订单】')) {
    formData.value.type = text.startsWith('【中固订单】') ? 0 : 1

    const dataMap = {}
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const separatorIndex = line.includes('：') ? line.indexOf('：') : line.indexOf(':')
      if (separatorIndex !== -1) {
        const key = line.substring(0, separatorIndex).trim()
        const val = line.substring(separatorIndex + 1).trim()
        dataMap[key] = val
      }
    }

    formData.value.order_client = dataMap['制单归属'] || ''
    formData.value.receiver_name = dataMap['姓名'] || ''
    formData.value.receiver_phone = dataMap['电话'] || ''
    formData.value.receiver_address = dataMap['地址'] || ''
    formData.value.goods_name = dataMap['名称'] || ''
    formData.value.goods_weight = dataMap['重量'] || ''
    formData.value.goods_quantity = dataMap['件数'] || ''
    formData.value.goods_packaging = dataMap['包装'] || '桶装'
    formData.value.logistics_service = dataMap['服务'] || '送货上门+回单拍照回传'

    alert('✅ 检测到标准化系统复制格式，表单已精准无缝填充！')
    return
  }

  // 模式2：模糊提取与重量算术引擎
  formData.value.order_client = lines[0].replace(/[:：]$/, '').trim()

  if (lines.length > 1) {
    let line2 = lines[1]
    let phoneMatch = line2.match(/(1[3-9]\d{9}|0\d{2,3}-\d{7,8})/)
    let phone = phoneMatch ? phoneMatch[0] : ''
    let name = '', address = ''
    let strWithoutPhone = line2.replace(phone, '').replace(/(?:电话|联系方式|手机)[:：]?\s*/g, '')
    let nameMatch = strWithoutPhone.match(/(?:姓名|收货人)[:：]\s*([^\s。，,;；]{1,5})/)

    if (nameMatch) {
      name = nameMatch[1]
      strWithoutPhone = strWithoutPhone.replace(nameMatch[0], '')
    } else {
      let qMatch = strWithoutPhone.match(/[?？]\s*([^\s。，,;；:：]{1,4})/)
      if (qMatch) {
        name = qMatch[1]
        strWithoutPhone = strWithoutPhone.replace(qMatch[0], '')
      }
    }

    let addrMatch = strWithoutPhone.match(/(?:地址)[:：]?\s*(.*)/)
    if (addrMatch) {
      address = addrMatch[1]
      strWithoutPhone = strWithoutPhone.replace(addrMatch[0], '')
    } else {
      address = strWithoutPhone
    }

    if (!name) {
      let parts = address.split(/[\s。，,;；]+/).filter(p => p.trim() !== '')
      let potentialName = parts.find(p => p.length >= 2 && p.length <= 4 && !/[省市区县镇村街道路号栋室楼]/.test(p))
      if (potentialName) {
        name = potentialName
        address = address.replace(potentialName, '')
      } else {
        let fallbackParts = line2.split(phone)
        name = fallbackParts[0].replace(/收货人|电话|联系方式|:|：/g, '').trim()
        address = (fallbackParts[1] || '').replace(/^[。，,.;:\s]+/, '').trim()
        if (name.length > 6 && address.length <= 6) {
          let temp = name
          name = address
          address = temp
        }
      }
    }

    formData.value.receiver_name = name.replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '').replace(/[?？]/g, '')
    formData.value.receiver_phone = phone
    formData.value.receiver_address = address.replace(/(?:地址)[:：]?/g, '').replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '')
  }

  if (lines.length > 2) {
    let goodsStr = lines.slice(2).join('\n')
    formData.value.goods_name = goodsStr

    let totalWeight = 0
    let tempStr = goodsStr
    let calcRegex1 = /(\d+(?:\.\d+)?)\s*(?:[A-Za-z一-龥]{0,6})?\s*([*xX✖️×\/÷])\s*(\d+(?:\.\d+)?)/g
    let match

    while ((match = calcRegex1.exec(tempStr)) !== null) {
      let val = /[*/÷]/.test(match[2])
        ? (/[*xX✖️×]/.test(match[2])
          ? parseFloat(match[1]) * parseFloat(match[3])
          : parseFloat(match[1]) / parseFloat(match[3]))
        : 0
      if (tempStr.substring(0, match.index).trim().endsWith('-')) {
        totalWeight -= val
      } else {
        totalWeight += val
      }
      tempStr = tempStr.substring(0, match.index) + ' '.repeat(match[0].length) + tempStr.substring(match.index + match[0].length)
    }

    let calcRegex2 = /([+-])\s*(\d+(?:\.\d+)?)/g
    while ((match = calcRegex2.exec(tempStr)) !== null) {
      if (match[1] === '+') {
        totalWeight += parseFloat(match[2])
      } else {
        totalWeight -= parseFloat(match[2])
      }
    }

    if (totalWeight !== 0) {
      formData.value.goods_weight = (Math.round(totalWeight * 100) / 100) + 'kg'
    } else {
      formData.value.goods_weight = ''
    }
  }
}

// 提交订单
const submitOrder = async () => {
  // 验证必填项
  if (!formData.value.receiver_phone || !formData.value.receiver_address || !formData.value.goods_name || !formData.value.goods_weight) {
    return alert('【收货电话】、【地址】、【名称】、【重量】为必填项！')
  }

  if (!/^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/.test(formData.value.receiver_phone)) {
    return alert('【收货电话】格式不正确！必须是11位手机号或带区号的座机。')
  }

  try {
    if (isEditMode.value) {
      // 修改订单 - 使用专门的编辑端点
      await request({
        url: `/orders/${currentOrderId.value}/edit`,
        method: 'PUT',
        data: formData.value
      })
      alert('订单修改成功！')
      handleClose()
      // 延迟100ms后刷新，确保后端数据已更新
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('refresh-orders'))
      }, 100)
    } else {
      // 新建订单
      await request({
        url: '/orders',
        method: 'POST',
        data: formData.value
      })
      alert('订单发布成功！')
      handleClose()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    }
  } catch (error) {
    alert('操作失败：' + (error.message || '未知错误'))
  }
}

// 删除订单
const deleteOrder = async () => {
  if (!confirm('确定要删除这个订单吗？此操作不可恢复！')) {
    return
  }

  try {
    await request({
      url: `/orders/${currentOrderId.value}`,
      method: 'DELETE'
    })
    alert('订单已删除！')
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('删除失败：' + (error.message || '未知错误'))
  }
}

// 打开计算器
const toggleCalculator = () => {
  window.dispatchEvent(new Event('toggle-calculator'))
}

// 打开编辑模式（通过订单ID）
const openEdit = (orderId) => {
  const orderStore = useOrderStore()
  const order = orderStore.allOrders.find(o => o.id === orderId)
  if (order) {
    open(order)
  } else {
    alert('订单信息未找到，请刷新页面后重试')
  }
}

// 暴露方法
defineExpose({
  open,
  openEdit
})
</script>

<style scoped>
/* 按钮样式 - 从原生CSS移植 */
.old-modal-footer {
  display: flex;
  gap: 10px;
  padding: 20px 30px;
  border-top: 1px solid #E8EBF0;
  background: #FAFBFC;
}

.old-modal-footer button {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  border: none;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 删除订单按钮 */
.old-modal-footer .btn-danger {
  background: #FDECEE !important;
  color: #F46E83 !important;
  margin-right: auto !important;
}

.old-modal-footer .btn-danger:hover {
  background: #fbcdd1 !important;
  transform: translateY(-1px);
}

/* 取消按钮 */
.old-modal-footer .btn-default {
  background: #F0F2F5 !important;
  color: #666666 !important;
}

.old-modal-footer .btn-default:hover {
  background: #e4e7ed !important;
  color: #333333 !important;
  transform: translateY(-1px);
}

/* 确认修改/发布按钮 */
.old-modal-footer .btn-primary {
  background: #1890FF !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.25) !important;
}

.old-modal-footer .btn-primary:hover {
  background: #40a9ff !important;
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.35) !important;
  transform: translateY(-1px);
}

/* 辅助计算按钮 */
.old-modal-footer .btn-calc {
  background: #FFF7E6 !important;
  color: #FA8C16 !important;
}

.old-modal-footer .btn-calc:hover {
  background: #FFE7BA !important;
  transform: translateY(-1px);
}

/* 点击反馈效果 */
.old-modal-footer button:active {
  transform: scale(0.97) !important;
}
</style>
