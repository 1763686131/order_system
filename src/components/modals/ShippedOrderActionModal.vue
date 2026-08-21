<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="shippedOrderActionModal"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-content" style="width: 520px; max-width: 90vw;">
        <div class="modal-close" @click="handleClose">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1L13 13M13 1L1 13" stroke="#ff4d4f" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>

        <div class="modal-header">
          <div class="modal-title">{{ modalTitle }}</div>
          <div class="modal-subtitle">{{ modalSubtitle }}</div>
        </div>

        <!-- 审核内容区 -->
        <div v-show="mode === 'audit'" class="modal-body" style="padding: 20px 30px;">
          <div class="form-item" style="margin-bottom: 18px;">
            <label style="font-weight: bold; color: #555; margin-bottom: 8px; display: block;">物流公司:</label>
            <input
              v-model="carrierName"
              type="text"
              placeholder="请输入物流公司名称（例如：安能物流）"
              style="width: 100%; padding: 10px 14px; font-size: 14px; border: 1px solid #d9d9d9; border-radius: 8px; outline: none; box-sizing: border-box;"
            />
            <div id="auditCarrierTags" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">
              <span v-for="tag in carrierTags" :key="tag"
                @click="carrierName = tag"
                style="cursor: pointer; background: #e6f4ff; color: #1677ff; border: 1px solid #91caff; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; transition: all 0.2s; user-select: none;"
                @mouseover="$event.target.style.background='#bae0ff'"
                @mouseout="$event.target.style.background='#e6f4ff'">
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="form-item">
            <label style="font-weight: bold; color: #555; margin-bottom: 8px; display: block;">物流单号:</label>
            <input
              v-model="logisticsNo"
              type="text"
              placeholder="请输入物流单号（例如：552546612）"
              style="width: 100%; padding: 10px 14px; font-size: 14px; border: 1px solid #d9d9d9; border-radius: 8px; outline: none; box-sizing: border-box;"
            />
          </div>
        </div>

        <!-- 回单内容区 -->
        <div v-show="mode === 'receipt' || mode === 'view_receipt'"
          class="modal-body"
          style="padding: 20px 30px; display: flex; justify-content: center; align-items: center;">
          <div
            id="receiptContent"
            style="position: relative; width: 100%; max-width: 400px; min-height: 320px; border: 2px dashed #d9d9d9; border-radius: 12px; display: flex; justify-content: center; align-items: center; background: #fafafa; cursor: pointer; overflow: hidden;"
            @click="mode === 'receipt' && $refs.fileInput.click()"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              style="display: none;"
              @change="handleFileSelect"
            />

            <div v-show="!previewSrc" style="text-align: center; color: #999; padding: 20px;">
              <div style="font-size: 48px; margin-bottom: 10px;">📷</div>
              <div style="font-size: 14px;">点击选择图片或拖拽到此处</div>
            </div>

            <img
              v-show="previewSrc"
              :src="previewSrc"
              style="max-width: 100%; max-height: 400px; display: block; object-fit: contain;"
              @click.stop="showFullImage"
            />

            <button
              v-show="previewSrc && mode === 'receipt'"
              @click.stop="rotateImage"
              style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; border-radius: 50%; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border: 2px solid #1890ff; display: flex; justify-content: center; align-items: center; cursor: pointer; font-size: 24px; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: all 0.2s;"
              @mouseover="$event.target.style.transform='translate(-50%, -50%) scale(1.1)'"
              @mouseout="$event.target.style.transform='translate(-50%, -50%) scale(1)'"
            >
              🔄
            </button>
          </div>
        </div>

        <!-- 审核模式按钮 -->
        <div v-show="mode === 'audit'" style="display: flex; gap: 12px; padding: 0 30px 24px 30px;">
          <button
            class="modal-btn-confirm"
            style="flex: 1; background-color: #ff4d4f;"
            @click="handleRevokeShip"
          >
            撤销出库
          </button>
          <button
            class="modal-btn-confirm"
            style="flex: 1; background-color: #52c41a;"
            @click="handleConfirmAudit"
          >
            确认审核
          </button>
        </div>

        <!-- 回单上传模式按钮 -->
        <div v-show="mode === 'receipt'" style="display: flex; gap: 12px; padding: 0 30px 24px 30px;">
          <button
            v-if="userStore.hasPerm('shipped.delete_receipt')"
            class="modal-btn-confirm"
            style="flex: 1; background-color: #ff4d4f;"
            @click="clearPreview"
          >
            清除图片
          </button>
          <button
            v-if="userStore.hasPerm('shipped.upload_receipt')"
            class="modal-btn-confirm"
            style="flex: 1; background-color: #1890ff;"
            @click="handleUploadReceipt"
          >
            确认上传
          </button>
        </div>

        <!-- 回单查看模式按钮 -->
        <div v-show="mode === 'view_receipt'" style="display: flex; gap: 12px; padding: 0 30px 24px 30px;">
          <button
            class="modal-btn-confirm"
            style="flex: 1; background-color: #52c41a;"
            @click="downloadImage"
          >
            下载图片
          </button>
          <button
            v-if="userStore.hasPerm('shipped.delete_receipt')"
            class="modal-btn-confirm"
            style="flex: 1; background-color: #ff4d4f;"
            @click="handleDeleteReceipt"
          >
            删除图片
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import request from '@/api/request'

const userStore = useUserStore()
const orderStore = useOrderStore()

const visible = ref(false)
const mode = ref('audit') // 'audit' | 'receipt' | 'view_receipt'
const targetOrderId = ref(null)
const modalTitle = ref('')
const modalSubtitle = ref('')

// 审核相关
const carrierName = ref('')
const logisticsNo = ref('')
const carrierTags = ref([])

// 回单相关
const previewSrc = ref('')
const originalImage = ref(new Image())
const currentRotation = ref(0)
const fileInput = ref(null)

// 加载物流公司标签
const fetchCarrierTags = async () => {
  try {
    const response = await request({ url: '/carrier_tags', method: 'GET' })
    carrierTags.value = Array.isArray(response) ? response : []
  } catch (error) {
    carrierTags.value = []
  }
}

// 打开弹窗
const open = (orderId, modalMode) => {
  targetOrderId.value = orderId
  mode.value = modalMode

  const order = orderStore.allOrders.find(o => o.id === orderId)

  if (modalMode === 'audit') {
    modalTitle.value = '已出库订单管理'
    modalSubtitle.value = '请选择对当前出库订单的操作指令'

    // 加载标签
    fetchCarrierTags()

    // 解析已有单号
    if (order) {
      let fullNo = order.logistics_no || ''
      if (fullNo === '暂未录入单号' || fullNo === '无单号记录' || fullNo === '暂无记录') {
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
    }
  } else if (modalMode === 'receipt') {
    modalTitle.value = '回单凭证管理'
    modalSubtitle.value = '请上传或管理该订单的发货回单图片'

    // 如果订单已有回单，显示
    if (order && order.receipt_img_url) {
      previewSrc.value = order.receipt_img_url
    } else {
      clearPreview()
    }
  } else if (modalMode === 'view_receipt') {
    modalTitle.value = '回单凭证详情'
    modalSubtitle.value = '您可以查看大图、下载图片或从系统中彻底删除该回单'

    if (order && order.receipt_img_url) {
      previewSrc.value = order.receipt_img_url
    }
  }

  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
  clearPreview()
}

// 撤销出库
const handleRevokeShip = async () => {
  try {
    await request({
      url: `/orders/${targetOrderId.value}`,
      method: 'PUT',
      data: { status: 'completed' }
    })
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('网络通讯失败，无法完成撤销出库指令')
  }
}

// 确认审核
const handleConfirmAudit = async () => {
  const carrier = carrierName.value.trim()
  const no = logisticsNo.value.trim()

  let finalLogisticsNo = ''
  if (carrier && no) {
    finalLogisticsNo = `${carrier}-${no}`
  } else if (carrier) {
    finalLogisticsNo = carrier
  } else if (no) {
    finalLogisticsNo = no
  } else {
    finalLogisticsNo = '无单号记录'
  }

  // 保存标签（如果不是专车）
  const order = orderStore.allOrders.find(o => o.id === targetOrderId.value)
  const isSpecialTruck = order && (order.shipping_method === 3 || order.shipping_method === '3')

  if (!isSpecialTruck && carrier !== '') {
    try {
      await request({
        url: '/carrier_tags',
        method: 'POST',
        data: { tag: carrier }
      })
    } catch (error) {
      console.error('保存标签失败', error)
    }
  }

  try {
    await request({
      url: `/orders/${targetOrderId.value}`,
      method: 'PUT',
      data: {
        status: 'shipped',
        audit_state: 1,
        logistics_no: finalLogisticsNo
      }
    })
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    alert('网络通信异常，未能成功写入确认审核标识')
  }
}

// 文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      currentRotation.value = 0
      originalImage.value.onload = () => {
        previewSrc.value = e.target.result
      }
      originalImage.value.src = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// 拖拽上传
const handleDrop = (event) => {
  if (mode.value !== 'receipt') return

  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      currentRotation.value = 0
      originalImage.value.onload = () => {
        previewSrc.value = e.target.result
      }
      originalImage.value.src = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// 旋转图片
const rotateImage = () => {
  currentRotation.value = (currentRotation.value + 90) % 360

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  if (currentRotation.value === 90 || currentRotation.value === 270) {
    canvas.width = originalImage.value.height
    canvas.height = originalImage.value.width
  } else {
    canvas.width = originalImage.value.width
    canvas.height = originalImage.value.height
  }

  ctx.translate(canvas.width / 2, canvas.height / 2)
  ctx.rotate(currentRotation.value * Math.PI / 180)
  ctx.drawImage(originalImage.value, -originalImage.value.width / 2, -originalImage.value.height / 2)

  previewSrc.value = canvas.toDataURL('image/jpeg', 0.95)
}

// 清除预览
const clearPreview = () => {
  previewSrc.value = ''
  currentRotation.value = 0
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 上传回单
const handleUploadReceipt = async () => {
  if (!previewSrc.value) {
    return alert('请先点击虚线框选择一张图片！')
  }

  // 转换 Base64 为 File
  const dataURItoFile = (dataURI, filename) => {
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
    fileToUpload = dataURItoFile(previewSrc.value, `receipt_${Date.now()}.jpg`)
  } catch (error) {
    return alert('图片数据解析异常，请重新选择图片！')
  }

  const formData = new FormData()
  formData.append('receipt_image', fileToUpload)

  try {
    const response = await fetch(`/api/orders/${targetOrderId.value}/upload_receipt`, {
      method: 'POST',
      headers: {
        'Username': String(userStore.user.username),
        'Role': String(userStore.user.role)
      },
      body: formData
    })

    if (response.ok) {
      alert('图片上传成功！')
      handleClose()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    } else {
      alert('上传失败，请检查网络或后端接口。')
    }
  } catch (error) {
    alert('网络通信异常！')
  }
}

// 删除回单
const handleDeleteReceipt = async () => {
  if (!confirm('确定要从数据库和硬盘中【彻底删除】这张回单图片吗？此操作不可恢复！')) {
    return
  }

  try {
    const response = await request({
      url: `/orders/${targetOrderId.value}/receipt`,
      method: 'DELETE'
    })

    if (response.success) {
      alert('回单图片已彻底删除！')
      handleClose()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    } else {
      alert(response.message || '删除失败')
    }
  } catch (error) {
    alert('网络错误，删除失败')
  }
}

// 下载图片
const downloadImage = () => {
  if (!previewSrc.value) {
    return alert('没有可下载的图片')
  }

  const a = document.createElement('a')
  a.href = previewSrc.value
  a.download = `发货回单_${Date.now()}.jpg`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// 查看大图
const showFullImage = () => {
  if (previewSrc.value) {
    window.open(previewSrc.value, '_blank')
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
