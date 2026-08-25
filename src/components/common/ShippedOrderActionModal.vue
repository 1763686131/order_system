<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="shippedOrderActionModal"
      class="modal-overlay"
      style="display: flex;"
      @click.self="closeShippedActionModal"
    >
      <div class="modal-content" style="width: 420px; border-radius: 12px; padding: 24px;">
        <div class="modal-header" style="margin-bottom: 20px;">
          <div id="actionModalTitle" style="font-size: 18px; font-weight: bold; color: #333;">
            {{ modalTitle }}
          </div>
          <div id="actionModalSubtitle" style="font-size: 13px; color: #777; margin-top: 4px;">
            {{ modalSubtitle }}
          </div>
        </div>

        <input id="actionTargetOrderId" type="hidden" :value="targetOrderId" />

        <!-- 审核填写物流单号窗口 -->
        <div id="auditContent" style="display: block;">
          <div class="form-item" style="margin-bottom: 20px;">
            <label for="auditCarrierName" style="font-weight: bold; color: #4a4a4a; margin-bottom: 10px; display: block; font-size: 14px;">
              物流公司 / 承运车队名称
            </label>
            <input
              id="auditCarrierName"
              v-model="carrierName"
              class="modern-input"
              placeholder="如：三志物流、顺丰快递、安能快运..."
            />

            <div id="auditCarrierTags" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; min-height: 24px; align-items: center;">
              <span
                v-for="tag in carrierTags"
                :key="tag"
                @click="carrierName = tag"
                style="cursor: pointer; background: #e6f4ff; color: #1677ff; border: 1px solid #91caff; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; transition: all 0.2s; user-select: none;"
                @mouseover="$event.target.style.background='#bae0ff'"
                @mouseout="$event.target.style.background='#e6f4ff'"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="form-item" style="margin-bottom: 24px;">
            <label for="auditLogisticsNo" style="font-weight: bold; color: #4a4a4a; margin-bottom: 10px; display: block; font-size: 14px;">
              物流单号 / 运输凭证信息 <span style="color:#999; font-weight:normal; font-size: 12px;">(选填)</span>
            </label>
            <input
              id="auditLogisticsNo"
              v-model="logisticsNo"
              class="modern-input"
              placeholder="请输入运单号、司机电话等凭证"
            />
          </div>
        </div>

        <!-- 回单内容区 -->
        <div
          id="receiptContent"
          style="display: none; position: relative; width: 100%; height: 160px; background: #fafafa; border: 1px dashed #d9d9d9; border-radius: 8px; margin-bottom: 8px; overflow: hidden;"
          @dragenter.prevent="handleDragEnter"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <input
            id="receiptImageInput"
            type="file"
            accept="image/*"
            style="display: none;"
            @change="previewReceiptImage"
          />

          <div
            id="receiptUploadPrompt"
            style="position: absolute; top: 0; left: 0; display: flex; flex-direction: column; align-items: center; width: 100%; height: 100%; justify-content: center; cursor: pointer;"
            @click="triggerFileInput"
          >
            <div style="font-size: 48px; color: #ccc; line-height: 1; font-weight: 300;">+</div>
            <div style="color: #999; font-size: 13px; margin-top: 8px;">点击此处上传回单图片</div>
          </div>

          <img
            id="receiptImagePreview"
            src=""
            style="display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; background: #eee; cursor: zoom-in;"
            @click="openLargeImagePreview"
          />

          <div
            id="receiptRotateBtn"
            style="display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 56px; height: 56px; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 50%; cursor: pointer; z-index: 10; align-items: center; justify-content: center; box-shadow: 0 8px 32px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.4); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);"
            @click.stop="rotateReceiptImage"
            @mouseover="handleRotateBtnHover($event, true)"
            @mouseout="handleRotateBtnHover($event, false)"
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1890ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 2v6h-6"></path>
              <path d="M21 13a9 9 0 1 1-3-7.7L21 8"></path>
            </svg>
          </div>
        </div>

        <!-- 按钮组 -->
        <div class="modal-btn-group" style="display: flex; gap: 12px; justify-content: center; margin-top: 24px; width: 100%;">
          <button id="btnAuditRevoke" @click="submitRevokeShipOrder">撤销出库</button>
          <button id="btnAuditConfirm" @click="submitAuditShipOrder">确认审核</button>
          <button id="btnReceiptDelete" @click="clearReceiptImage">清除图片</button>
          <button id="btnReceiptUpload" @click="submitReceiptImage">确认上传</button>
          <button id="btnRealDeleteReceipt" @click="deleteRealReceiptImage">删除凭证</button>
          <button id="btnDownloadReceipt" @click="downloadReceiptImage">下载凭证</button>
          <button id="btnModalReturn" @click="closeShippedActionModal">返回</button>
        </div>
      </div>
    </div>

    <!-- 大图预览模态框 -->
    <div
      v-if="showLargePreview"
      style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.9); display: flex; align-items: center; justify-content: center; z-index: 100001; cursor: zoom-out;"
      @click="closeLargePreview"
    >
      <img
        :src="largePreviewSrc"
        style="max-width: 90%; max-height: 90%; object-fit: contain;"
        @click.stop
      />
    </div>
  </teleport>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import request from '@/api/request'

const userStore = useUserStore()
const orderStore = useOrderStore()

const visible = ref(false)
const targetOrderId = ref(null)
const modalTitle = ref('已出库订单管理')
const modalSubtitle = ref('请选择对当前出库订单的操作指令')

// 审核相关
const carrierName = ref('')
const logisticsNo = ref('')
const carrierTags = ref([])

// 回单相关
const showLargePreview = ref(false)
const largePreviewSrc = ref('')
const originalReceiptImg = new Image()
let currentReceiptRotation = 0

// 全局变量，用于存储当前所有订单（照搬原生）
let allOrdersLocal = []

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

// 打开弹窗 - 完全照搬原生逻辑
const open = (orderId, mode) => {
  targetOrderId.value = orderId

  // 同步本地订单数据
  allOrdersLocal = orderStore.allOrders

  const title = document.getElementById('actionModalTitle')
  const subtitle = document.getElementById('actionModalSubtitle')
  const auditContent = document.getElementById('auditContent')
  const receiptContent = document.getElementById('receiptContent')

  const btnAuditRevoke = document.getElementById('btnAuditRevoke')
  const btnAuditConfirm = document.getElementById('btnAuditConfirm')
  const btnReceiptDelete = document.getElementById('btnReceiptDelete')
  const btnReceiptUpload = document.getElementById('btnReceiptUpload')
  const btnRealDelete = document.getElementById('btnRealDeleteReceipt')
  const btnDownload = document.getElementById('btnDownloadReceipt')

  // 先显示弹窗
  visible.value = true

  // 等待DOM渲染
  nextTick(() => {
    // 重新获取DOM元素
    const titleEl = document.getElementById('actionModalTitle')
    const subtitleEl = document.getElementById('actionModalSubtitle')
    const auditContentEl = document.getElementById('auditContent')
    const receiptContentEl = document.getElementById('receiptContent')
    const btnAuditRevokeEl = document.getElementById('btnAuditRevoke')
    const btnAuditConfirmEl = document.getElementById('btnAuditConfirm')
    const btnReceiptDeleteEl = document.getElementById('btnReceiptDelete')
    const btnReceiptUploadEl = document.getElementById('btnReceiptUpload')
    const btnRealDeleteEl = document.getElementById('btnRealDeleteReceipt')
    const btnDownloadEl = document.getElementById('btnDownloadReceipt')

    if (btnRealDeleteEl) btnRealDeleteEl.style.display = 'none'
    if (btnDownloadEl) btnDownloadEl.style.display = 'none'

    // 状态 A：进入【审核模式】
    if (mode === 'audit') {
      modalTitle.value = '已出库订单管理'
      modalSubtitle.value = '请选择对当前出库订单的操作指令'

      auditContentEl.style.display = 'block'
      receiptContentEl.style.display = 'none'

      btnAuditRevokeEl.style.display = 'block'
      btnAuditConfirmEl.style.display = 'block'
      btnReceiptDeleteEl.style.display = 'none'
      btnReceiptUploadEl.style.display = 'none'

      // 加载历史快捷标签
      fetchCarrierTags()

      // 解析回显已有的单号数据
      const order = allOrdersLocal.find(o => o.id === orderId)
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
    }
    // 状态 B：进入【回单模式】
    else if (mode === 'receipt') {
      modalTitle.value = '回单凭证管理'
      modalSubtitle.value = '请上传或管理该订单的发货回单图片'

      auditContentEl.style.display = 'none'
      receiptContentEl.style.display = 'flex'

      btnAuditRevokeEl.style.display = 'none'
      btnAuditConfirmEl.style.display = 'none'
      btnReceiptDeleteEl.style.display = 'block'
      btnReceiptUploadEl.style.display = 'block'

      // 权限控制
      if (userStore.hasPerm('shipped.delete_receipt')) {
        btnReceiptDeleteEl.style.display = 'inline-block'
      } else {
        btnReceiptDeleteEl.style.display = 'none'
      }

      if (userStore.hasPerm('shipped.upload_receipt')) {
        btnReceiptUploadEl.style.display = 'inline-block'
      } else {
        btnReceiptUploadEl.style.display = 'none'
      }

      // 清除图片按钮点击事件
      if (btnReceiptDeleteEl) {
        btnReceiptDeleteEl.onclick = function() {
          clearReceiptImage()
        }
      }

      // 智能加载状态
      const order = allOrdersLocal.find(o => o.id === orderId)
      const preview = document.getElementById('receiptImagePreview')
      const prompt = document.getElementById('receiptUploadPrompt')

      if (order && order.receipt_img_url) {
        if (preview) {
          preview.src = order.receipt_img_url
          preview.style.display = 'block'
        }
        if (prompt) prompt.style.display = 'none'
      } else {
        clearReceiptImage()
      }
    }
    // 状态 C：进入【已存回单查看与真删除模式】
    else if (mode === 'view_receipt') {
      modalTitle.value = '回单凭证详情'
      modalSubtitle.value = '您可以查看大图、下载图片或从系统中彻底删除该回单'

      auditContentEl.style.display = 'none'
      receiptContentEl.style.display = 'flex'

      btnAuditRevokeEl.style.display = 'none'
      btnAuditConfirmEl.style.display = 'none'
      btnReceiptUploadEl.style.display = 'none'
      btnReceiptDeleteEl.style.display = 'none'

      if (btnRealDeleteEl) btnRealDeleteEl.style.display = 'block'
      if (btnDownloadEl) btnDownloadEl.style.display = 'block'

      // 渲染已存在的图片回显
      const order = allOrdersLocal.find(o => o.id === orderId)
      const preview = document.getElementById('receiptImagePreview')
      const prompt = document.getElementById('receiptUploadPrompt')

      if (btnDownloadEl) btnDownloadEl.style.display = 'inline-block'

      if (userStore.hasPerm('shipped.delete_receipt')) {
        if (btnRealDeleteEl) btnRealDeleteEl.style.display = 'inline-block'
      } else {
        if (btnRealDeleteEl) btnRealDeleteEl.style.display = 'none'
      }

      if (order && order.receipt_img_url) {
        if (preview) {
          preview.src = order.receipt_img_url
          preview.style.display = 'block'
        }
        if (prompt) prompt.style.display = 'none'
      }
    }

    // 统一唤起弹窗
    document.getElementById('shippedOrderActionModal').style.display = 'flex'
  })
}

// 关闭弹窗
const closeShippedActionModal = () => {
  visible.value = false
  clearReceiptImage()
}

// 1. 撤销出库
const submitRevokeShipOrder = async () => {
  const id = targetOrderId.value
  try {
    await request({
      url: `/orders/${id}`,
      method: 'PUT',
      data: { status: 'completed' }
    })
    closeShippedActionModal()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (e) {
    alert('网络通讯失败，无法完成撤销出库指令')
  }
}

// 2. 确认审核
const submitAuditShipOrder = async () => {
  const id = targetOrderId.value

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

  // 保存历史标签
  const order = allOrdersLocal.find(o => o.id == id)
  const isSpecialTruck = order && (order.shipping_method === 3 || order.shipping_method === '3')
  if (!isSpecialTruck && carrier !== '') {
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

  // 提交给后端
  try {
    await request({
      url: `/orders/${id}`,
      method: 'PUT',
      data: {
        status: 'shipped',
        audit_state: 1,
        logistics_no: finalLogisticsNo
      }
    })
    closeShippedActionModal()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (e) {
    alert('网络通信异常，未能成功写入确认审核标识')
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
    receiptContent.style.background = '#fff0f6'
    receiptContent.style.border = '2px dashed #eb2f96'
  }
}

const handleDragOver = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#fff0f6'
    receiptContent.style.border = '2px dashed #eb2f96'
  }
}

const handleDragLeave = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#fafafa'
    receiptContent.style.border = '1px dashed #d9d9d9'
  }
}

const handleDrop = (event) => {
  const receiptContent = document.getElementById('receiptContent')
  if (receiptContent) {
    receiptContent.style.background = '#fafafa'
    receiptContent.style.border = '1px dashed #d9d9d9'
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
    alert('安全拦截：请拖入有效的图片文件（如 jpg, png 等）！')
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
    return alert('请先点击虚线框选择一张图片！')
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
    return alert('图片数据解析异常，请重新选择图片！')
  }

  const formData = new FormData()
  formData.append('receipt_image', fileToUpload)

  try {
    const response = await fetch(`http://localhost:3000/api/orders/${id}/upload_receipt`, {
      method: 'POST',
      headers: {
        'Username': String(userStore.user?.username || ''),
        'Role': String(userStore.user?.role || '')
      },
      body: formData
    })

    if (response.ok) {
      alert('图片上传成功！')
      closeShippedActionModal()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    } else {
      alert('上传失败，请检查网络或后端接口。')
    }
  } catch (e) {
    console.error('上传错误:', e)
    alert('网络通信异常！')
  }
}

// 删除按钮
const deleteRealReceiptImage = async () => {
  const id = targetOrderId.value
  if (!confirm('确定要从数据库和硬盘中【彻底删除】这张回单图片吗？此操作不可恢复！')) {
    return
  }

  try {
    const res = await request({
      url: `/orders/${id}/receipt`,
      method: 'DELETE'
    })
    if (res.success) {
      alert('回单图片已彻底删除！')
      closeShippedActionModal()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    } else {
      alert(res.message || '删除失败')
    }
  } catch (e) {
    console.error(e)
    alert('网络错误，删除失败')
  }
}

// 下载按钮
const downloadReceiptImage = () => {
  const preview = document.getElementById('receiptImagePreview')
  if (!preview || !preview.src) {
    return alert('没有可下载的图片')
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

// 旋转按钮悬停效果
const handleRotateBtnHover = (event, isHover) => {
  const btn = event.currentTarget
  if (isHover) {
    btn.style.transform = 'translate(-50%, -50%) scale(1.1)'
    btn.style.background = 'rgba(255, 255, 255, 0.4)'
  } else {
    btn.style.transform = 'translate(-50%, -50%) scale(1)'
    btn.style.background = 'rgba(255, 255, 255, 0.25)'
  }
}

// 暴露方法
defineExpose({
  open
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modern-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s;
}

.modern-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.modal-btn-group button {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  background: #1890ff;
  color: white;
}

.modal-btn-group button:hover {
  opacity: 0.8;
}
</style>
