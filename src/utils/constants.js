// 订单状态常量
export const ORDER_STATUS = {
  PENDING: 0,      // 未完成
  COMPLETED: 1,    // 已完成
  SHIPPED: 2       // 已出库
}

// 订单类型常量
export const ORDER_TYPE = {
  ZHONGGU: 0,      // 中固订单
  JUEYUAN: 1       // 绝缘订单
}

// 权限常量
export const PERMISSIONS = {
  ORDER_READ: 'touch.order.read',
  ORDER_COMPLETE: 'touch.order.complete',
  ORDER_REOPEN: 'touch.order.reopen',
  ORDER_COPY: 'touch.order.copy',
  ORDER_DELETE: 'touch.order.delete',
  SHIPMENT_AUDIT: 'touch.shipment.audit',
  RECEIPT_READ: 'touch.receipt.read',
  RECEIPT_UPLOAD: 'touch.receipt.upload',
  RECEIPT_DELETE: 'touch.receipt.delete',
  MATERIAL_READ: 'touch.material.read',
  MATERIAL_CREATE: 'touch.material.create',
  MATERIAL_AUDIT: 'touch.material.audit'
}

// 用户角色常量
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin'
}

// 物流类型
export const LOGISTICS_TYPES = {
  0: '物流',
  1: '零担快运',
  2: '快递',
  3: '专车',
  4: '其它'
}
