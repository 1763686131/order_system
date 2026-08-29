/**
 * 门店工具类
 * 提供门店相关的辅助方法
 */

import request from '@/api/request'

// 门店缓存
let storesCache = null
let cacheTime = 0
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 获取所有门店（带缓存）
 */
export async function getStores(forceRefresh = false) {
  const now = Date.now()

  if (!forceRefresh && storesCache && (now - cacheTime) < CACHE_DURATION) {
    return storesCache
  }

  try {
    const stores = await request({
      url: '/stores',
      method: 'GET'
    })

    storesCache = stores
    cacheTime = now
    return stores
  } catch (error) {
    console.error('获取门店列表失败:', error)
    return []
  }
}

/**
 * 根据 store_id 获取门店信息
 * @param {number} storeId - 门店ID
 * @returns {object|null}
 */
export async function getStoreById(storeId) {
  const stores = await getStores()
  return stores.find(s => s.id === storeId) || null
}

/**
 * 根据 code 获取门店信息
 * @param {string} code - 门店编码
 * @returns {object|null}
 */
export async function getStoreByCode(code) {
  const stores = await getStores()
  return stores.find(s => s.code === code) || null
}

/**
 * 获取门店名称
 * @param {number} storeId - 门店ID
 * @returns {string}
 */
export async function getStoreName(storeId) {
  const store = await getStoreById(storeId)
  return store ? store.name : '未知门店'
}

/**
 * 批量获取订单的门店信息
 * @param {Array} orders - 订单列表
 * @returns {Array} 带门店信息的订单列表
 */
export async function enrichOrdersWithStore(orders) {
  const stores = await getStores()
  const storeMap = {}

  stores.forEach(store => {
    storeMap[store.id] = store
  })

  return orders.map(order => ({
    ...order,
    store: storeMap[order.store_id] || null,
    store_name: storeMap[order.store_id]?.name || '未知门店'
  }))
}

/**
 * 根据门店ID筛选订单
 * @param {Array} orders - 订单列表
 * @param {number} storeId - 门店ID
 * @returns {Array}
 */
export function filterOrdersByStore(orders, storeId) {
  if (!storeId) return orders
  return orders.filter(order => order.store_id === storeId)
}

/**
 * 获取门店选项列表（用于下拉框）
 * @param {boolean} includeAll - 是否包含"全部"选项
 * @returns {Array}
 */
export async function getStoreOptions(includeAll = false) {
  const stores = await getStores()
  const options = stores
    .filter(s => s.status === 'active')
    .map(s => ({
      label: s.name,
      value: s.id,
      code: s.code
    }))

  if (includeAll) {
    options.unshift({ label: '全部门店', value: null, code: 'all' })
  }

  return options
}

/**
 * 门店ID映射（用于兼容旧的type字段）
 * @deprecated 迁移完成后可删除
 */
export const STORE_TYPE_MAP = {
  0: 2, // 中固
  1: 1  // 绝缘
}

/**
 * 将旧的type转换为store_id
 * @deprecated 迁移完成后可删除
 * @param {number} type - 旧的type值
 * @returns {number}
 */
export function typeToStoreId(type) {
  return STORE_TYPE_MAP[type] || 2
}

/**
 * 清除门店缓存
 */
export function clearStoreCache() {
  storesCache = null
  cacheTime = 0
}
