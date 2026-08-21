import request from './request'

// 更新订单状态
export function updateOrderStatus(orderId, status) {
  return request({
    url: `/orders/${orderId}`,
    method: 'PUT',
    data: { status }
  })
}

// 获取订单列表
export function getOrders() {
  return request({
    url: '/orders',
    method: 'GET'
  })
}

// 创建订单
export function createOrder(orderData) {
  return request({
    url: '/orders',
    method: 'POST',
    data: orderData
  })
}

// 更新订单（编辑）
export function updateOrder(orderId, orderData) {
  return request({
    url: `/orders/${orderId}/edit`,
    method: 'PUT',
    data: orderData
  })
}

// 删除订单
export function deleteOrder(orderId) {
  return request({
    url: `/orders/${orderId}`,
    method: 'DELETE'
  })
}

// 订单出库
export function shipOrder(orderId, shipData) {
  return request({
    url: `/orders/${orderId}`,
    method: 'PUT',
    data: shipData
  })
}

// 搜索订单
export function searchOrders(keyword) {
  return request({
    url: '/orders/search',
    method: 'GET',
    params: { keyword }
  })
}
