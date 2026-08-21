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
  PENDING_ADD: 'pending.add',
  PENDING_EDIT: 'pending.edit',
  PENDING_DELETE: 'pending.delete',
  PENDING_STATUS: 'pending.status',

  COMPLETED_EDIT: 'completed.edit',
  COMPLETED_DELETE: 'completed.delete',
  COMPLETED_SHIP: 'completed.ship',

  SHIPPED_AUDIT: 'shipped.audit',
  SHIPPED_RECEIPT: 'shipped.receipt',
  SHIPPED_REVOKE: 'shipped.revoke',

  MATERIAL_ADD: 'material.add',
  MATERIAL_VIEW: 'material.view',

  SYSTEM_USER_MANAGE: 'system.user_manage'
}

// 用户角色常量
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  EMPLOYEE: 'employee',
  OPERATOR: 'operator'
}

// 物流类型
export const LOGISTICS_TYPES = {
  0: '物流',
  1: '零担快运',
  2: '快递',
  3: '专车',
  4: '其它'
}
