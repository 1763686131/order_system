<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="shippedOrderActionModal"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-content" style="width: 420px; border-radius: 12px; padding: 24px;">
        <div class="modal-header" style="margin-bottom: 20px;">
          <div class="modal-title" id="actionModalTitle" style="font-size: 18px; font-weight: bold; color: #333;">
            {{ modalTitle }}
          </div>
          <div class="modal-subtitle" id="actionModalSubtitle" style="font-size: 13px; color: #777; margin-top: 4px;">
            {{ modalSubtitle }}
          </div>
        </div>

        <input id="actionTargetOrderId" type="hidden" :value="targetOrderId" />

        <!-- 审核填写物流单号窗口 -->
        <div id="auditContent" v-show="mode === 'audit'" style="display: block;">
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
          v-show="mode === 'receipt' || mode === 'view_receipt'"
          :style="{
            position: 'relative',
            width: '100%',
            height: '160px',
            background: isDragging ? '#fff0f6' : '#fafafa',
            border: isDragging ? '2px dashed #eb2f96' : '1px dashed #d9d9d9',
            borderRadius: '8px',
            marginBottom: '8px',
            overflow: 'hidden',
            transition: 'all 0.2s'
          }"
          @dragenter.prevent="handleDragEnter"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <input
            ref="receiptImageInput"
            id="receiptImageInput"
            type="file"
            accept="image/*"
            style="display: none;"
            @change="previewReceiptImage"
          />

          <div
            id="receiptUploadPrompt"
            v-show="!previewSrc"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              height: '100%',
              justifyContent: 'center',
              cursor: 'pointer'
            }"
            @click="$refs.receiptImageInput.click()"
          >
            <div style="font-size: 48px; color: #ccc; line-height: 1; font-weight: 300;">+</div>
            <div style="color: #999; font-size: 13px; margin-top: 8px;">点击此处上传回单图片</div>
          </div>

          <img
            id="receiptImagePreview"
            ref="receiptImagePreview"
            :src="previewSrc"
            v-show="previewSrc"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              background: '#eee',
              cursor: 'zoom-in'
            }"
            @click="openLargeImagePreview"
          />

          <div
            id="receiptRotateBtn"
            v-show="previewSrc && mode === 'receipt'"
            :style="{
              display: previewSrc && mode === 'receipt' ? 'flex' : 'none',
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '56px',
              height: '56px',
              background: 'rgba(255, 255, 255, 0.25)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              borderRadius: '50%',
              cursor: 'pointer',
              zIndex: 10,
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
              border: '1px solid rgba(255,255,255,0.4)',
              transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'
            }"
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
          <!-- 审核模式按钮 -->
          <button
            id="btnAuditRevoke"
            v-show="mode === 'audit'"
            @click="submitRevokeShipOrder"
          >
            撤销出库
          </button>
          <button
            id="btnAuditConfirm"
            v-show="mode === 'audit'"
            @click="submitAuditShipOrder"
          >
            确认审核
          </button>

          <!-- 回单上传模式按钮 -->
          <button
            id="btnReceiptDelete"
            v-show="mode === 'receipt' && userStore.hasPerm('shipped.delete_receipt')"
            @click="clearReceiptImage"
            style="display: none;"
          >
            清除图片
          </button>
          <button
            id="btnReceiptUpload"
            v-show="mode === 'receipt' && userStore.hasPerm('shipped.upload_receipt')"
            @click="submitReceiptImage"
            style="display: none;"
          >
            确认上传
          </button>

          <!-- 回单查看模式按钮 -->
          <button
            id="btnRealDeleteReceipt"
            v-show="mode === 'view_receipt' && previewSrc && userStore.hasPerm('shipped.delete_receipt')"
            @click="deleteRealReceiptImage"
            style="display: none;"
          >
            删除凭证
          </button>
          <button
            id="btnDownloadReceipt"
            v-show="mode === 'view_receipt' && previewSrc"
            @click="downloadReceiptImage"
            style="display: none;"
          >
            下载凭证
          </button>
          <button
            id="btnUploadReceiptInView"
            v-show="mode === 'view_receipt' && !previewSrc && userStore.hasPerm('shipped.upload_receipt')"
            @click="switchToUploadMode"
            style="display: none;"
          >
            上传回单
          </button>

          <!-- 返回按钮（所有模式都显示） -->
          <button id="btnModalReturn" @click="closeShippedActionModal">返回</button>
        </div>
      </div>
    </div>

    <!-- 大图预览模态框 -->
    <div
      v-if="showLargePreview"
      :style="{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        background: 'rgba(0, 0, 0, 0.9)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100001,
        cursor: 'zoom-out'
      }"
      @click="closeLargePreview"
    >
      <img
        :src="previewSrc"
        :style="{
          maxWidth: '90%',
          maxHeight: '90%',
          objectFit: 'contain'
        }"
        @click.stop
      />
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import request from '@/api/request'

const userStore = useUserStore()
const orderStore = useOrderStore()

const visible = ref(false)
const mode = ref('audit')
const targetOrderId = ref(null)
const modalTitle = ref('已出库订单管理')
const modalSubtitle = ref('请选择对当前出库订单的操作指令')

// 审核相关
const carrierName = ref('')
const logisticsNo = ref('')
const carrierTags = ref([])

// 回单相关
const previewSrc = ref('')
const originalReceiptImg = ref(new Image())
const currentReceiptRotation = ref(0)
const receiptImageInput = ref(null)
const isDragging = ref(false)
const showLargePreview = ref(false)

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
  if (receiptImageInput.value) {
    receiptImageInput.value.value = ''
  }
  previewSrc.value = ''
  currentReceiptRotation.value = 0
  originalReceiptImg.value = new Image()
}

// 打开弹窗
const open = (orderId, modalMode) => {
  // 重置旋转按钮
  currentReceiptRotation.value = 0

  targetOrderId.value = orderId
  mode.value = modalMode

  const order = orderStore.allOrders.find(o => o.id === orderId)

  // 状态 A：进入【审核模式】
  if (modalMode === 'audit') {
    modalTitle.value = '已出库订单管理'
    modalSubtitle.value = '请选择对当前出库订单的操作指令'

    // 加载历史快捷标签
    fetchCarrierTags()

    // 解析回显已有的单号数据
    if (order) {
      let fullNo = order.logistics_no || ''
      // 清理掉占位字符
      if (fullNo === '暂未录入单号' || fullNo === '无单号记录' || fullNo === '暂无记录') {
        fullNo = ''
      }

      if (fullNo.includes('-')) {
        // 如果数据库中已经是 "安能物流-552546612" 格式，拆开回显
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
  else if (modalMode === 'receipt') {
    modalTitle.value = '回单凭证管理'
    modalSubtitle.value = '请上传或管理该订单的发货回单图片'

    // 智能加载状态（如果该订单数据库已经有图则显图；如果没图，彻底清空上一张残留）
    if (order && order.receipt_img_url) {
      previewSrc.value = order.receipt_img_url
    } else {
      clearReceiptImage()
    }
  }
  // 状态 C：进入【已存回单查看与真删除模式】
  else if (modalMode === 'view_receipt') {
    modalTitle.value = '回单凭证详情'
    modalSubtitle.value = '您可以查看大图、下载图片或从系统中彻底删除该回单'

    // 渲染已存在的图片回显
    if (order && order.receipt_img_url) {
      previewSrc.value = order.receipt_img_url
    }
  }

  visible.value = true
}

// 从查看模式切换到上传模式
const switchToUploadMode = () => {
  mode.value = 'receipt'
  modalTitle.value = '回单凭证管理'
  modalSubtitle.value = '请上传或管理该订单的发货回单图片'
  clearReceiptImage()
}

// 关闭弹窗
const closeShippedActionModal = () => {
  visible.value = false
  // 在点击"返回"或者关闭弹窗的瞬间，顺手执行一次全清理，消灭任何残影
  clearReceiptImage()
}

const handleClose = () => {
  closeShippedActionModal()
}

// 1. 撤销出库功能：将订单状态推回到已完成 (completed) 状态列表
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

// 2. 确认审核功能：抓取物流名字和单号，拼接后统一提交
const submitAuditShipOrder = async () => {
  const id = targetOrderId.value

  const carrier = carrierName.value.trim()
  const no = logisticsNo.value.trim()

  // 核心修复：把文字用减号拼接起来（例如：安能快运-552546612）
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

  // (可选) 保存历史标签：如果是专车(发货方式为3)则不记录到词库
  const order = orderStore.allOrders.find(o => o.id == id)
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

// 3. 回单图片选择与本地预览
const previewReceiptImage = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      // 重置旋转状态
      currentReceiptRotation.value = 0

      // 等待图片装载到内存中，以备 Canvas 提取
      originalReceiptImg.value.onload = () => {
        previewSrc.value = e.target.result
      }
      originalReceiptImg.value.src = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// 拖拽上传
const handleDrop = (event) => {
  isDragging.value = false
  if (mode.value !== 'receipt') return

  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      currentReceiptRotation.value = 0
      originalReceiptImg.value.onload = () => {
        previewSrc.value = e.target.result
      }
      originalReceiptImg.value.src = e.target.result
    }
    reader.readAsDataURL(file)
  } else if (file) {
    alert('安全拦截：请拖入有效的图片文件（如 jpg, png 等）！')
  }
}

// 上传图片
const submitReceiptImage = async () => {
  const id = targetOrderId.value

  // 拦截判定：如果没有图或者图是隐藏的，不允许上传
  if (!previewSrc.value) {
    return alert('请先点击虚线框选择一张图片！')
  }

  // 将 Base64 重绘为标准的 File 二进制对象
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
    // 利用系统时间戳给新图片命名，防止浏览器或后端缓存冲突
    fileToUpload = dataURItoFile(previewSrc.value, `receipt_${Date.now()}.jpg`)
  } catch (error) {
    return alert('图片数据解析异常，请重新选择图片！')
  }

  // 原样打包进 FormData
  const formData = new FormData()
  formData.append('receipt_image', fileToUpload)

  try {
    const response = await fetch('/api/orders/' + id + '/upload_receipt', {
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

// HTML5 Canvas 物理级图像重绘与旋转引擎
const rotateReceiptImage = (e) => {
  // 阻止事件冒泡，防止点击旋转按钮时误触触发底部的"大图预览"
  if (e) {
    e.stopPropagation()
    e.preventDefault()
  }

  // 每次点击顺时针累加旋转 90 度
  currentReceiptRotation.value = (currentReceiptRotation.value + 90) % 360

  // 创建虚拟画布重绘图片
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  // 根据角度交换宽高（90度和270度时，宽高互换）
  if (currentReceiptRotation.value === 90 || currentReceiptRotation.value === 270) {
    canvas.width = originalReceiptImg.value.height
    canvas.height = originalReceiptImg.value.width
  } else {
    canvas.width = originalReceiptImg.value.width
    canvas.height = originalReceiptImg.value.height
  }

  // 将画布中心点移动到正中 -> 旋转画布 -> 重新铺上图片
  ctx.translate(canvas.width / 2, canvas.height / 2)
  ctx.rotate((currentReceiptRotation.value * Math.PI) / 180)
  ctx.drawImage(
    originalReceiptImg.value,
    -originalReceiptImg.value.width / 2,
    -originalReceiptImg.value.height / 2
  )

  // 把物理重绘后的新图像，以高质量 Base64 重新渲染到预览框中
  previewSrc.value = canvas.toDataURL('image/jpeg', 0.95)
}

// 查看大图预览
const openLargeImagePreview = () => {
  if (previewSrc.value) {
    showLargePreview.value = true
  }
}

// 关闭大图预览
const closeLargePreview = () => {
  showLargePreview.value = false
}

// 旋转按钮悬停效果
const handleRotateBtnHover = (event, isHover) => {
  if (isHover) {
    event.target.style.transform = 'scale(1.1)'
    event.target.style.background = 'rgba(255, 255, 255, 0.4)'
  } else {
    event.target.style.transform = 'scale(1)'
    event.target.style.background = 'rgba(255, 255, 255, 0.25)'
  }
}

// 监听模式变化，同步显示样式
watch(
  () => mode.value,
  (newMode) => {
    // 强制更新 receiptContent 的 display 样式
    setTimeout(() => {
      const receiptContent = document.getElementById('receiptContent')
      if (receiptContent) {
        if (newMode === 'receipt' || newMode === 'view_receipt') {
          receiptContent.style.display = 'flex'
        } else {
          receiptContent.style.display = 'none'
        }
      }

      // 旋转按钮显示控制
      const rotateBtn = document.getElementById('receiptRotateBtn')
      if (rotateBtn) {
        if (previewSrc.value && newMode === 'receipt') {
          rotateBtn.style.display = 'flex'
        } else {
          rotateBtn.style.display = 'none'
        }
      }

      // 按钮显示控制
      const btnAuditRevoke = document.getElementById('btnAuditRevoke')
      const btnAuditConfirm = document.getElementById('btnAuditConfirm')
      const btnReceiptDelete = document.getElementById('btnReceiptDelete')
      const btnReceiptUpload = document.getElementById('btnReceiptUpload')
      const btnRealDelete = document.getElementById('btnRealDeleteReceipt')
      const btnDownload = document.getElementById('btnDownloadReceipt')

      if (newMode === 'audit') {
        if (btnAuditRevoke) btnAuditRevoke.style.display = 'block'
        if (btnAuditConfirm) btnAuditConfirm.style.display = 'block'
        if (btnReceiptDelete) btnReceiptDelete.style.display = 'none'
        if (btnReceiptUpload) btnReceiptUpload.style.display = 'none'
        if (btnRealDelete) btnRealDelete.style.display = 'none'
        if (btnDownload) btnDownload.style.display = 'none'
      } else if (newMode === 'receipt') {
        if (btnAuditRevoke) btnAuditRevoke.style.display = 'none'
        if (btnAuditConfirm) btnAuditConfirm.style.display = 'none'
        if (btnReceiptDelete && userStore.hasPerm('shipped.delete_receipt')) {
          btnReceiptDelete.style.display = 'inline-block'
        }
        if (btnReceiptUpload && userStore.hasPerm('shipped.upload_receipt')) {
          btnReceiptUpload.style.display = 'inline-block'
        }
        if (btnRealDelete) btnRealDelete.style.display = 'none'
        if (btnDownload) btnDownload.style.display = 'none'
      } else if (newMode === 'view_receipt') {
        if (btnAuditRevoke) btnAuditRevoke.style.display = 'none'
        if (btnAuditConfirm) btnAuditConfirm.style.display = 'none'
        if (btnReceiptDelete) btnReceiptDelete.style.display = 'none'
        if (btnReceiptUpload) btnReceiptUpload.style.display = 'none'
        if (btnDownload) btnDownload.style.display = 'inline-block'
        if (btnRealDelete && userStore.hasPerm('shipped.delete_receipt')) {
          btnRealDelete.style.display = 'inline-block'
        }
      }
    }, 0)
  },
  { immediate: true }
)

// 监听预览图变化，控制旋转按钮显示
watch(
  () => previewSrc.value,
  (newSrc) => {
    setTimeout(() => {
      const rotateBtn = document.getElementById('receiptRotateBtn')
      const preview = document.getElementById('receiptImagePreview')
      const prompt = document.getElementById('receiptUploadPrompt')

      if (rotateBtn) {
        if (newSrc && mode.value === 'receipt') {
          rotateBtn.style.display = 'flex'
        } else {
          rotateBtn.style.display = 'none'
        }
      }

      if (preview) {
        if (newSrc) {
          preview.style.display = 'block'
        } else {
          preview.style.display = 'none'
        }
      }

      if (prompt) {
        if (newSrc) {
          prompt.style.display = 'none'
        } else {
          prompt.style.display = 'flex'
        }
      }
    }, 0)
  }
)

// 暴露方法
defineExpose({
  open
})
</script>

<style scoped>
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
</style>
