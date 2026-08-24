<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="searchOrderModal"
      class="search-modal-overlay"
      @click="handleOverlayClick"
    >
      <span class="search-close-btn" @click="handleClose">&times;</span>
      <div class="search-modal-wrapper">
        <div class="search-header-area">
          <div class="search-input-pill-group">
            <input
              v-model="searchQuery"
              ref="searchInput"
              type="text"
              id="searchInput"
              class="search-pill-input"
              placeholder="请输入订单号、客户姓名或电话..."
              autocomplete="off"
              @keyup.enter="performSearch"
            />
            <button class="search-pill-btn" @click="performSearch">搜索</button>
          </div>
        </div>

        <div id="searchResults" class="search-results-list" v-html="resultsHtml"></div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const visible = ref(false)
const searchQuery = ref('')
const resultsHtml = ref('')
const searchInput = ref(null)

const userStore = useUserStore()

const SEARCH_PAGE_SIZE = 10
let globalFilteredSearchData = []
let globalSearchKeyword = ''
let searchRenderIndex = 0

// 高亮关键字
const highlightKeyword = (text, keywordString) => {
  if (!text || !keywordString) return text
  const keywords = keywordString.trim().split(/\s+/).filter(k => k)
  if (keywords.length === 0) return text
  const escapedKeywords = keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const regex = new RegExp(`(${escapedKeywords.join('|')})`, 'gi')
  return text.replace(regex, '<span class="highlight-matched">$1</span>')
}

// 执行搜索
const performSearch = async () => {
  const keywordString = searchQuery.value.trim()
  if (!keywordString) return

  // 渲染 Loading 动画
  resultsHtml.value = `
    <div style="text-align: center; padding: 60px 0; color: #ffffff;">
      <div class="search-loading-spinner" style="display:inline-block; width:28px; height:28px; border:3px solid rgba(255,255,255,0.2); border-top-color:#ffffff; border-radius:50%; animation:spin 0.8s linear infinite; margin-bottom:12px;"></div>
      <div style="font-size: 15px; letter-spacing: 1px; opacity: 0.9;">正在检索数据库，请稍候...</div>
    </div>
    <style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>
  `

  try {
    const response = await request({ url: '/orders', method: 'GET' })
    const dbData = Array.isArray(response) ? response : (response.data || [])

    // 多关键字 AND 匹配
    const searchTerms = keywordString.toLowerCase().split(/\s+/).filter(k => k)

    let filteredData = dbData.filter(item => {
      const combinedCoreString = `${item.order_client || ''} ${item.receiver_name || ''} ${item.receiver_phone || ''} ${item.logistics_no || ''}`.toLowerCase()
      return searchTerms.every(term => combinedCoreString.includes(term))
    })

    // 按时间倒序排序
    filteredData.sort((a, b) => {
      const timeA = new Date(a.shipped_date || a.completed_date || a.date || 0).getTime()
      const timeB = new Date(b.shipped_date || b.completed_date || b.date || 0).getTime()
      return timeB - timeA
    })

    globalFilteredSearchData = filteredData
    globalSearchKeyword = keywordString
    searchRenderIndex = 0

    if (filteredData.length === 0) {
      resultsHtml.value = `
        <div style="text-align: center; color: #ffffff; margin-top: 60px;">
          <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.8;">📭</div>
          <div style="font-size: 18px; font-weight: 500;">未找到与 "<span style="color:#ef4444; font-weight:bold;">${keywordString}</span>" 相关的核心订单信息</div>
          <div style="font-size: 14px; margin-top: 8px; opacity: 0.6;">(仅支持搜索：订单名、收件人、电话、物流单号)</div>
        </div>
      `
    } else {
      renderSearchPage()
    }
  } catch (error) {
    console.error('搜索拉取数据库失败:', error)
    resultsHtml.value = `
      <div style="text-align: center; color: #ef4444; margin-top: 60px;">
        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
        <div style="font-size: 18px;">网络异常，无法连接到数据库</div>
      </div>
    `
  }
}

// 分页渲染引擎
const renderSearchPage = () => {
  const dataToRender = globalFilteredSearchData.slice(
    searchRenderIndex,
    searchRenderIndex + SEARCH_PAGE_SIZE
  )

  let htmlString = ''

  dataToRender.forEach((item, index) => {
    const titleText = `${item.order_client || '未知订单'} - ${item.receiver_name || '未知收件人'}`
    const highlightedTitle = highlightKeyword(titleText, globalSearchKeyword)

    let logisticsHtml = ''
    if (item.logistics_no) {
      const highlightedLogNo = highlightKeyword(item.logistics_no, globalSearchKeyword)
      logisticsHtml = `
        <div class="logistics-badge">
          <span class="log-no-text">单号：${highlightedLogNo}</span>
          <button class="btn-copy-log" onclick="window.copySearchLogisticsNo(event, '${item.logistics_no}')">复制</button>
        </div>
      `
    }

    // 基础信息
    let infoArr = []
    if (item.receiver_phone) infoArr.push(`电话：${item.receiver_phone}`)
    if (item.receiver_address) infoArr.push(`地址：${item.receiver_address}`)
    const highlightedInfo = highlightKeyword(infoArr.join(' | '), globalSearchKeyword)

    // 三大彩色标签
    let tagsHtml = ''
    let tagsList = []
    if (item.goods_weight && item.goods_weight.trim() !== '') {
      const highlightedWeight = highlightKeyword(item.goods_weight, globalSearchKeyword)
      tagsList.push(`<span class="goods-tag tag-weight">重量/数量：${highlightedWeight}</span>`)
    }
    if (item.goods_quantity && item.goods_quantity.trim() !== '') {
      const highlightedQty = highlightKeyword(item.goods_quantity, globalSearchKeyword)
      tagsList.push(`<span class="goods-tag tag-quantity">件数：${highlightedQty}</span>`)
    }
    if (item.goods_packaging && item.goods_packaging.trim() !== '') {
      const highlightedPkg = highlightKeyword(item.goods_packaging, globalSearchKeyword)
      tagsList.push(`<span class="goods-tag tag-packaging">包装：${highlightedPkg}</span>`)
    }
    if (tagsList.length > 0) {
      tagsHtml = `<div class="goods-info-tags">${tagsList.join('')}</div>`
    }

    // 货物明细 4 列布局
    let goodsColumnsHtml = ''
    if (item.goods_name && item.goods_name.trim() !== '') {
      const lines = item.goods_name.split('\n').map(l => l.trim()).filter(l => l)

      if (lines.length > 0) {
        const chunkSize = 4
        const columns = []

        for (let i = 0; i < lines.length; i += chunkSize) {
          columns.push(lines.slice(i, i + chunkSize))
        }

        const colsInnerHtml = columns.map(colLines => {
          const colContent = colLines.map(line => highlightKeyword(line, globalSearchKeyword)).join('<br>')
          return `<div class="goods-column">${colContent}</div>`
        }).join('')

        goodsColumnsHtml = `
          <div class="goods-columns-wrapper">
            <div class="goods-columns-header">货物明细：</div>
            <div class="goods-columns-flex">
              ${colsInnerHtml}
            </div>
          </div>
        `
      }
    }

    // 组装左侧内容
    let leftContentHtml = ''
    if (highlightedInfo) leftContentHtml += `<div style="font-size: 15px; margin-top: 4px;">${highlightedInfo}</div>`
    if (tagsHtml) leftContentHtml += tagsHtml
    if (goodsColumnsHtml) leftContentHtml += goodsColumnsHtml

    // 状态与时间
    let statusText = "未知状态"
    let statusClass = "status-pending"
    let borderColor = "#94a3b8"
    let displayDate = item.shipped_date || item.completed_date || item.date || "暂无时间"

    if (item.status === 'shipped' || item.status === 'completed') {
      statusText = item.status === 'shipped' ? "已出库" : "已完成"
      statusClass = "status-completed"
      borderColor = "#22c55e"
    } else if (item.status === 'pending') {
      statusText = "未完成"
      statusClass = "status-pending"
      borderColor = "#ef4444"
    }

    // 剪贴板全量复制模板
    const typeText = (item.type == 1) ? '绝缘订单' : '中固订单'
    const shortGoodsName = (item.goods_name || '').replace(/\n/g, ' ').trim()

    let clipText = `【${typeText}】\n`
    clipText += `姓名：${item.receiver_name || ''}\n`
    clipText += `电话：${item.receiver_phone || ''}\n`
    clipText += `地址：${item.receiver_address || ''}\n`
    clipText += `名称：${shortGoodsName}\n`
    clipText += `重量：${item.goods_weight || ''}\n`
    clipText += `件数：${item.goods_quantity || ''}\n`
    clipText += `包装：${item.goods_packaging || ''}\n`
    clipText += `服务：${item.logistics_service || ''}\n`
    clipText += `备注：${item.remark || ''}\n`

    const safeClipText = encodeURIComponent(clipText)

    // 回单按钮 - 有回单显示"回单"预览，没有回单显示"上传回单"
    let receiptBtnHtml = ''
    if (item.receipt_img_url && item.receipt_img_url.trim() !== '') {
      receiptBtnHtml = `<button class="btn-action-sm" onclick="window.viewSearchReceipt(event, ${item.id}, '${item.receipt_img_url}')" style="background-color: #FDECEE; color: #F26E83; border: 1px solid #FDECEE;">回单</button>`
    } else {
      // 没有回单，显示上传按钮
      receiptBtnHtml = `<button class="btn-action-sm" onclick="window.uploadSearchReceipt(event, ${item.id})" style="background-color: #FDECEE; color: #F26E83; border: 1px solid #FDECEE;">上传回单</button>`
    }

    const delay = (index % SEARCH_PAGE_SIZE) * 0.05

    htmlString += `
      <div class="search-result-item" style="animation-delay: ${delay}s; border-left-color: ${borderColor}; align-items: flex-start;">
        <div class="item-left" style="flex: 1; padding-right: 20px;">
          <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div class="item-title">${highlightedTitle}</div>
            ${logisticsHtml}
          </div>
          <div class="item-subtitle" style="line-height: 1.6;">
            ${leftContentHtml}
          </div>
        </div>

        <div class="item-right" style="min-width: 220px; display: flex; flex-direction: column; align-items: flex-end; margin-top: 4px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <button class="btn-action-sm" onclick="window.copyFullOrderInfo(event, '${safeClipText}')">复制</button>
            ${receiptBtnHtml}
            <span class="item-status ${statusClass}">${statusText}</span>
          </div>
          <div class="item-date" style="margin-top: 12px;">时间: ${displayDate}</div>
        </div>
      </div>
    `
  })

  searchRenderIndex += dataToRender.length

  // 加载更多按钮
  if (searchRenderIndex < globalFilteredSearchData.length) {
    const remaining = globalFilteredSearchData.length - searchRenderIndex
    htmlString += `
      <div id="loadMoreSearchBtnContainer" style="text-align: center; margin-top: 24px; margin-bottom: 24px;">
        <button onclick="window.renderSearchPage()" style="background: #f8fafc; border: 1px solid #cbd5e1; color: #3b82f6; padding: 10px 32px; border-radius: 30px; font-size: 15px; font-weight: bold; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.1);" onmouseover="this.style.background='#e2e8f0'" onmouseout="this.style.background='#f8fafc'">
          ⬇️ 点击加载更多 (还有 ${remaining} 条未展示)
        </button>
      </div>
    `
  } else {
    htmlString += `
      <div style="text-align: center; color: #ffffff; margin-top: 24px; margin-bottom: 24px; font-size: 14px; opacity: 0.7; letter-spacing: 1px;">
        到底啦！已加载所有 ${globalFilteredSearchData.length} 条相关数据...
      </div>
    `
  }

  if (searchRenderIndex === dataToRender.length) {
    resultsHtml.value = htmlString
  } else {
    resultsHtml.value += htmlString
  }
}

// 点击覆盖层关闭
const handleOverlayClick = (e) => {
  if (e.target.id === 'searchOrderModal') {
    handleClose()
  }
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
  searchQuery.value = ''
  resultsHtml.value = ''
  globalFilteredSearchData = []
  globalSearchKeyword = ''
  searchRenderIndex = 0
}

// 打开弹窗
const open = () => {
  searchQuery.value = ''
  resultsHtml.value = ''
  globalFilteredSearchData = []
  globalSearchKeyword = ''
  searchRenderIndex = 0
  visible.value = true
  nextTick(() => {
    searchInput.value?.focus()
  })
}

// ESC 键关闭
const handleKeydown = (e) => {
  if (e.key === 'Escape' && visible.value) {
    handleClose()
  }
}

// 暴露给 window 的全局函数
const setupGlobalFunctions = () => {
  window.renderSearchPage = renderSearchPage

  window.copySearchLogisticsNo = (e, logNo) => {
    e.stopPropagation()
    const btn = e.target
    const originalText = btn.innerText
    const showSuccess = () => {
      btn.innerText = '✓ 已复制'
      btn.style.background = '#22c55e'
      btn.style.color = '#ffffff'
      btn.style.borderColor = '#22c55e'
      setTimeout(() => {
        btn.innerText = originalText
        btn.style.background = ''
        btn.style.color = ''
        btn.style.borderColor = ''
      }, 2000)
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(logNo).then(showSuccess)
    }
  }

  window.copyFullOrderInfo = (e, encodedText) => {
    e.stopPropagation()
    const btn = e.target
    const originalText = btn.innerText
    const textToCopy = decodeURIComponent(encodedText)

    const showSuccess = () => {
      btn.innerText = '✓ 复制成功'
      btn.style.background = '#3b82f6'
      btn.style.color = '#ffffff'
      btn.style.borderColor = '#3b82f6'
      setTimeout(() => {
        btn.innerText = originalText
        btn.style.background = ''
        btn.style.color = ''
        btn.style.borderColor = ''
      }, 2000)
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(textToCopy).then(showSuccess).catch(err => {
        console.error('复制失败:', err)
        alert('复制失败，请手动操作')
      })
    } else {
      let textArea = document.createElement("textarea")
      textArea.value = textToCopy
      textArea.style.position = "fixed"
      textArea.style.opacity = "0"
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      try {
        document.execCommand('copy')
        showSuccess()
      } catch (err) {}
      textArea.remove()
    }
  }

  window.viewSearchReceipt = (e, orderId, imgUrl) => {
    e.stopPropagation()
    if (window.openShippedOrderActionModal) {
      window.openShippedOrderActionModal(orderId, 'view_receipt', imgUrl)
    } else {
      alert('系统错误：未找到回单操作弹窗！')
    }
  }

  window.uploadSearchReceipt = (e, orderId) => {
    e.stopPropagation()
    if (window.openShippedOrderActionModal) {
      window.openShippedOrderActionModal(orderId, 'receipt')
    } else {
      alert('系统错误：未找到回单操作弹窗！')
    }
  }
}

onMounted(() => {
  setupGlobalFunctions()
  window.addEventListener('open-search-order-modal', open)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('open-search-order-modal', open)
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({
  open
})
</script>

<style scoped>
/* 移除所有 scoped 样式，让全局 CSS 接管 */
</style>
