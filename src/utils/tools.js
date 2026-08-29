/**
 * 工具函数集合
 * 包含：格式化、计算、验证等纯函数
 */

// ============================================
// 日期时间格式化
// ============================================

/**
 * 格式化日期时间
 * @param {string} dateStr - 日期字符串
 * @param {string} format - 格式：'date' | 'datetime' | 'time'
 * @returns {string}
 */
export function formatDate(dateStr, format = 'datetime') {
  if (!dateStr) return '未知时间'

  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')

  if (format === 'date') {
    return `${year}-${month}-${day}`
  } else if (format === 'time') {
    return `${hour}:${minute}:${second}`
  } else {
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`
  }
}

/**
 * 获取当前日期字符串 YYYY-MM-DD
 * @returns {string}
 */
export function getCurrentDate() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 获取N天前的日期字符串
 * @param {number} days - 天数
 * @returns {string}
 */
export function getDaysAgo(days) {
  const date = new Date()
  date.setDate(date.getDate() - days)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// ============================================
// 文本处理
// ============================================

/**
 * 计算文本缩放比例（根据字符宽度）
 * @param {string} text - 文本内容
 * @param {number} maxChars - 最大字符数
 * @param {boolean} isHighlightMode - 是否高亮模式
 * @returns {number}
 */
export function calculateTextScale(text, maxChars = 12, isHighlightMode = false) {
  if (!text) return 1
  let len = 0

  for (let i = 0; i < text.length; i++) {
    const char = text[i]

    if (char.match(/[一-龥]/)) {
      len += 1
    } else if (isHighlightMode && char.match(/[a-zA-Z0-9.]/)) {
      if (char.match(/[A-Z]/)) len += 1.8
      else if (char.match(/[0-9]/)) len += 1.4
      else len += 1.1
    } else {
      if (char.match(/[A-Z]/)) len += 0.9
      else if (char.match(/[0-9]/)) len += 0.7
      else len += 0.55
    }
  }

  if (len <= maxChars) return 1
  const scale = maxChars / len
  return Math.max(scale, 0.35)
}

/**
 * 高亮文本中的数字和字母
 * @param {string} text - 文本内容
 * @returns {string}
 */
export function highlightText(text) {
  if (!text) return ''
  return text.replace(/([a-zA-Z0-9.]+)/g, '<span class="text-red-large">$1</span>')
}

/**
 * 清理货物名称中的数学符号
 * @param {string} text - 货物名称
 * @returns {string}
 */
export function cleanGoodsName(text) {
  if (!text) return ''
  return text
    .replace(/[+\-*\/=＋－×÷]/g, ' ')  // 将数学符号替换为空格
    .replace(/[ \t]+/g, ' ')           // 合并连续的空格和Tab
    .trim()                             // 清理首尾多余空格
}

// ============================================
// 数据验证
// ============================================

/**
 * 验证手机号码
 * @param {string} phone - 手机号
 * @returns {boolean}
 */
export function validatePhone(phone) {
  if (!phone) return false
  // 支持11位手机号或座机号
  return /^1[3-9]\d{9}$/.test(phone) || /^\d{3,4}-?\d{7,8}$/.test(phone)
}

/**
 * 验证必填字段
 * @param {object} data - 数据对象
 * @param {array} requiredFields - 必填字段数组
 * @returns {object} { valid: boolean, missing: array }
 */
export function validateRequired(data, requiredFields) {
  const missing = []

  for (const field of requiredFields) {
    if (!data[field] || String(data[field]).trim() === '') {
      missing.push(field)
    }
  }

  return {
    valid: missing.length === 0,
    missing
  }
}

// ============================================
// 图片处理
// ============================================

/**
 * Base64 转 File 对象
 * @param {string} dataURI - Base64 数据
 * @param {string} filename - 文件名
 * @returns {File}
 */
export function dataURItoFile(dataURI, filename) {
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

/**
 * 图片旋转（使用 Canvas）
 * @param {Image} img - 原始图片对象
 * @param {number} rotation - 旋转角度（0, 90, 180, 270）
 * @returns {string} - Base64 数据
 */
export function rotateImage(img, rotation) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  // 根据角度交换宽高
  if (rotation === 90 || rotation === 270) {
    canvas.width = img.height
    canvas.height = img.width
  } else {
    canvas.width = img.width
    canvas.height = img.height
  }

  // 旋转并绘制
  ctx.translate(canvas.width / 2, canvas.height / 2)
  ctx.rotate((rotation * Math.PI) / 180)
  ctx.drawImage(img, -img.width / 2, -img.height / 2)

  return canvas.toDataURL('image/jpeg', 0.95)
}

// ============================================
// 智能解析（订单粘贴文本）
// ============================================

/**
 * 智能解析订单粘贴文本
 * @param {string} text - 粘贴的文本内容
 * @returns {object} - 解析后的订单数据
 */
export function parseOrderText(text) {
  if (!text || !text.trim()) {
    return {}
  }

  const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '')

  if (lines.length === 0) {
    return {}
  }

  const result = {
    order_client: '',
    receiver_name: '',
    receiver_phone: '',
    receiver_address: '',
    goods_name: ''
  }

  // 第一行：客户归属
  if (lines[0]) {
    result.order_client = lines[0]
  }

  // 第二行：收货人 电话 地址
  if (lines[1]) {
    const contactLine = lines[1]

    // 提取电话号码
    const phoneMatch = contactLine.match(/1[3-9]\d{9}|\d{3,4}-?\d{7,8}/)
    if (phoneMatch) {
      result.receiver_phone = phoneMatch[0]

      // 电话前面的是姓名
      const beforePhone = contactLine.substring(0, contactLine.indexOf(phoneMatch[0])).trim()
      if (beforePhone) {
        result.receiver_name = beforePhone
      }

      // 电话后面的是地址
      const afterPhone = contactLine.substring(contactLine.indexOf(phoneMatch[0]) + phoneMatch[0].length).trim()
      if (afterPhone) {
        result.receiver_address = afterPhone
      }
    }
  }

  // 第三行起：货物名称
  if (lines.length > 2) {
    result.goods_name = lines.slice(2).join('\n')
  }

  return result
}

// ============================================
// 复制到剪贴板
// ============================================

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy:', error)
    return false
  }
}

/**
 * 格式化订单信息为可复制的文本
 * @param {object} order - 订单对象
 * @param {boolean} isEmployee - 是否为员工（员工不显示电话和服务）
 * @returns {string}
 */
export function formatOrderForCopy(order, isEmployee = false) {
  // 订单类型文本
  const typeText = (order.type == 1) ? '绝缘订单' : '中固订单'

  // 名称字符数量限制
  let nameLimit = (order.type == 1) ? 8 : 9
  let shortGoodsName = (order.goods_name || '').replace(/\n/g, '').trim().substring(0, nameLimit)

  // 构建复制文本（原生格式）
  let clipText = `【${typeText}】\n`
  if (order.receiver_name) clipText += `姓名：${order.receiver_name}\n`
  if (!isEmployee && order.receiver_phone) clipText += `电话：${order.receiver_phone}\n`
  if (order.receiver_address) clipText += `地址：${order.receiver_address}\n`
  if (shortGoodsName) clipText += `名称：${shortGoodsName}\n`
  if (order.goods_weight) clipText += `重量：${order.goods_weight}\n`
  if (order.goods_quantity) clipText += `件数：${order.goods_quantity}\n`
  if (order.goods_packaging) clipText += `包装：${order.goods_packaging}\n`
  if (!isEmployee && order.logistics_service) clipText += `服务：${order.logistics_service}\n`
  if (order.remark) clipText += `备注：${order.remark}\n`

  return clipText
}

// ============================================
// 设备检测
// ============================================

/**
 * 检测是否为移动设备
 * @returns {boolean}
 */
export function isMobile() {
  return window.innerWidth <= 768
}

/**
 * 检测是否为触摸设备
 * @returns {boolean}
 */
export function isTouchDevice() {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

// ============================================
// 拖拽上传
// ============================================

/**
 * 启用拖拽上传功能
 * @param {string} containerId - 容器元素ID
 * @param {string} inputId - 文件输入框ID
 * @param {function} callback - 文件选择回调
 */
export function enableDragAndDropUpload(containerId, inputId, callback) {
  const container = document.getElementById(containerId)
  const input = document.getElementById(inputId)

  if (!container || !input) return

  container.addEventListener('dragover', (e) => {
    e.preventDefault()
    e.stopPropagation()
    container.style.borderColor = '#1890ff'
    container.style.background = '#e6f7ff'
  })

  container.addEventListener('dragleave', (e) => {
    e.preventDefault()
    e.stopPropagation()
    container.style.borderColor = '#d9d9d9'
    container.style.background = '#fafafa'
  })

  container.addEventListener('drop', (e) => {
    e.preventDefault()
    e.stopPropagation()
    container.style.borderColor = '#d9d9d9'
    container.style.background = '#fafafa'

    const files = e.dataTransfer.files
    if (files.length > 0 && files[0].type.startsWith('image/')) {
      // 模拟文件输入
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(files[0])
      input.files = dataTransfer.files

      // 触发回调
      if (callback) {
        callback({ target: input })
      }
    }
  })
}

// ============================================
// 本地存储
// ============================================

/**
 * 保存数据到 localStorage
 * @param {string} key - 键名
 * @param {any} value - 值
 */
export function saveToLocalStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error('Failed to save to localStorage:', error)
  }
}

/**
 * 从 localStorage 读取数据
 * @param {string} key - 键名
 * @param {any} defaultValue - 默认值
 * @returns {any}
 */
export function loadFromLocalStorage(key, defaultValue = null) {
  try {
    const value = localStorage.getItem(key)
    return value ? JSON.parse(value) : defaultValue
  } catch (error) {
    console.error('Failed to load from localStorage:', error)
    return defaultValue
  }
}

/**
 * 从 localStorage 删除数据
 * @param {string} key - 键名
 */
export function removeFromLocalStorage(key) {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error('Failed to remove from localStorage:', error)
  }
}
