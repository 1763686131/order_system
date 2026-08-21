/**
 * 格式化日期时间
 * @param {string|Date} date 日期
 * @param {string} format 格式 'date' | 'datetime' | 'time'
 * @returns {string}
 */
export function formatDate(date, format = 'datetime') {
  if (!date) return '-'

  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  if (format === 'date') {
    return `${year}-${month}-${day}`
  } else if (format === 'time') {
    return `${hours}:${minutes}:${seconds}`
  } else {
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }
}

/**
 * 防抖函数
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 节流函数
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
export function throttle(fn, delay = 300) {
  let last = 0
  return function (...args) {
    const now = Date.now()
    if (now - last >= delay) {
      last = now
      fn.apply(this, args)
    }
  }
}

/**
 * 深拷贝
 * @param {*} obj
 * @returns {*}
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof Array) return obj.map(item => deepClone(item))

  const cloneObj = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloneObj[key] = deepClone(obj[key])
    }
  }
  return cloneObj
}

/**
 * 生成唯一 ID
 * @returns {string}
 */
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * 解析订单文本（智能识别）
 * @param {string} text 原始文本
 * @returns {object}
 */
export function parseOrderText(text) {
  const lines = text.split('\n').filter(l => l.trim())
  const result = {
    client: '',
    receiver_name: '',
    receiver_phone: '',
    receiver_address: '',
    goods_name: '',
    goods_weight: '',
    goods_quantity: ''
  }

  if (lines.length < 2) return result

  // 第一行：客户名
  result.client = lines[0].trim()

  // 第二行：收货人 电话 地址
  const contactLine = lines[1]
  const phoneMatch = contactLine.match(/1[3-9]\d{9}/)
  if (phoneMatch) {
    result.receiver_phone = phoneMatch[0]
    const parts = contactLine.split(phoneMatch[0])
    result.receiver_name = parts[0].trim()
    result.receiver_address = parts[1].trim()
  }

  // 第三行起：货物信息
  if (lines.length > 2) {
    const goodsLines = lines.slice(2)
    result.goods_name = goodsLines.join('\n')

    // 尝试提取重量
    const weightMatch = result.goods_name.match(/(\d+(?:\.\d+)?)\s*(?:kg|公斤|千克)/i)
    if (weightMatch) {
      result.goods_weight = weightMatch[1]
    }

    // 尝试提取数量
    const quantityMatch = result.goods_name.match(/(\d+)\s*(?:件|个|桶|袋)/i)
    if (quantityMatch) {
      result.goods_quantity = quantityMatch[0]
    }
  }

  return result
}

/**
 * 验证手机号
 * @param {string} phone
 * @returns {boolean}
 */
export function validatePhone(phone) {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * 文件大小格式化
 * @param {number} bytes
 * @returns {string}
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
